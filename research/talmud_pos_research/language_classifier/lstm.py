# -*- coding: utf-8 -*-
import sys
import random,json,codecs
from collections import OrderedDict
from collections import defaultdict
from itertools import count

import dynet as dy
import numpy as np
import os,argparse,re,codecs
from os import listdir
from os.path import isfile, join

# set the seed
random.seed(2823274491)

#filename_to_load = '' #'epoch_9-11-3/langtagger_model_embdim20_hiddim40_lyr2_e9_trainloss0.179809275561_trainprec95.34_valprec95.8651582151.model'
#filename_to_load = 'epoch_10-11-4-with-Tanakh/langtagger_model_embdim20_hiddim40_lyr2_e10_trainloss0.206057158064_trainprec94.26_valprec93.2793903924.model'
filename_to_load = 'epoch_9-11-4-with-better-ambiguous/langtagger_model_embdim20_hiddim40_lyr2_e9_trainloss0.23960972284_trainprec93.48_valprec93.1008844017.model'
START_EPOCH = 0

# argument parse
parser = argparse.ArgumentParser()
parser.add_argument('-hiddim', '-hiddendim', help='Size of the RNN hidden layer, default 100', default=40,
                    required=False)
parser.add_argument('-embeddim', '-embeddingdim', help='Size of the embeddings, default 50', default=20, required=False)
parser.add_argument('-layers', '-mlplayers', help='Number of MLP layers, can only be 2 or 3', default=2, required=False)
parser.add_argument('-bilstmlayers', '-lstmlayers', help='Number of BILSTM layers, default 2', default=2,
                    required=False)
parser.add_argument('-model', '-modeltoload', help='Filename of model to load', default='', required=False)
args = vars(parser.parse_known_args()[0])

# get the params
HIDDEN_DIM = int(args['hiddim'])
EMBED_DIM = int(args['embeddim'])
BILSTM_LAYERS = int(args['bilstmlayers'])
fDo_3_Layers = int(args['layers']) == 3
sLAYERS = '3' if fDo_3_Layers else '2'
Filename_to_log = 'postagger_log_embdim' + str(EMBED_DIM) + '_hiddim' + str(HIDDEN_DIM) + '_lyr' + sLAYERS + '.txt'


def log_message(message):
    print message
    with codecs.open(Filename_to_log, "a", encoding="utf8") as myfile:
        myfile.write("\n" + message)


if args['model']:
    filename_to_load = args['model']
    START_EPOCH = int(re.search("_e(\d+)", filename_to_load).group(1)) + 1

log_message('EMBED_DIM: ' + str(EMBED_DIM))
log_message('HIDDEN_DIM: ' + str(HIDDEN_DIM))
log_message('BILSTM_LAYERS: ' + str(BILSTM_LAYERS))
log_message('MLP Layers: ' + sLAYERS)
if filename_to_load:
    log_message('Loading model: ' + filename_to_load)
    log_message('Starting epoch: ' + str(START_EPOCH))


def read_data(dir=''):
    if not dir:
        dir = 'lstm_training.json'
    training_set = json.load(codecs.open(dir, "rb", encoding="utf-8"))

    tags = ['aramaic','mishnaic','ambiguous']
    training_set = [{'word':w['word'],'tag':tags.index(w['tag'])} for w in training_set]
    return training_set


# Classes:
# 1] Vocabulary class (the dictionary for char-to-int)
# 2] WordEncoder (actually, it'll be a char encoder)
# 3] Simple character BiLSTM
# 4] MLP
# 5] ConfusionMatrix
class Vocabulary(object):
    def __init__(self):
        self.all_items = []
        self.c2i = {}

    def add_text(self, paragraph):
        self.all_items.extend(paragraph)

    def finalize(self, fAddBOS=True):
        self.vocab = sorted(list(set(self.all_items)))
        c2i_start = 1 if fAddBOS else 0
        self.c2i = {c: i for i, c in enumerate(self.vocab, c2i_start)}
        self.i2c = self.vocab
        if fAddBOS:
            self.c2i['*BOS*'] = 0
            self.i2c = ['*BOS*'] + self.vocab
        self.all_items = None

    # debug
    def get_c2i(self):
        return self.c2i

    def size(self):
        return len(self.i2c)

    def __getitem__(self, c):
        return self.c2i.get(c, 0)

    def getItem(self, i):
        return self.i2c[i]


class WordEncoder(object):
    def __init__(self, name, dim, model, vocab):
        self.vocab = vocab
        self.enc = model.add_lookup_parameters((vocab.size(), dim))

    def __call__(self, char, DIRECT_LOOKUP=False):
        char_i = char if DIRECT_LOOKUP else self.vocab[char]
        return dy.lookup(self.enc, char_i)


class MLP:
    def __init__(self, model, name, in_dim, hidden_dim, out_dim):
        self.mw = model.add_parameters((hidden_dim, in_dim))
        self.mb = model.add_parameters((hidden_dim))
        if not fDo_3_Layers:
            self.mw2 = model.add_parameters((out_dim, hidden_dim))
            self.mb2 = model.add_parameters((out_dim))
        if fDo_3_Layers:
            self.mw2 = model.add_parameters((hidden_dim, hidden_dim))
            self.mb2 = model.add_parameters((hidden_dim))
            self.mw3 = model.add_parameters((out_dim, hidden_dim))
            self.mb3 = model.add_parameters((out_dim))

    def __call__(self, x):
        W = dy.parameter(self.mw)
        b = dy.parameter(self.mb)
        W2 = dy.parameter(self.mw2)
        b2 = dy.parameter(self.mb2)
        mlp_output = W2 * (dy.tanh(W * x + b)) + b2
        if fDo_3_Layers:
            W3 = dy.parameter(self.mw3)
            b3 = dy.parameter(self.mb3)
            mlp_output = W3 * (dy.tanh(mlp_output)) + b3
        return dy.softmax(mlp_output)


class BILSTMTransducer:
    def __init__(self, LSTM_LAYERS, IN_DIM, OUT_DIM, model):
        self.lstmF = dy.LSTMBuilder(LSTM_LAYERS, IN_DIM, (int)(OUT_DIM / 2), model)
        self.lstmB = dy.LSTMBuilder(LSTM_LAYERS, IN_DIM, (int)(OUT_DIM / 2), model)

    def __call__(self, seq):
        """
        seq is a list of vectors (either character embeddings or bilstm outputs)
        """
        fw = self.lstmF.initial_state()
        bw = self.lstmB.initial_state()
        outf = fw.transduce(seq)
        outb = list(reversed(bw.transduce(reversed(seq))))
        return [dy.concatenate([f, b]) for f, b in zip(outf, outb)]


class ConfusionMatrix:
    def __init__(self, size, vocab):
        self.matrix = np.zeros((size, size))
        self.size = size
        self.vocab = vocab

    def __call__(self, x, y):
        self.matrix[x, y] += 1

    def to_html(self):
        fp_matrix = np.sum(self.matrix, 1)
        fn_matrix = np.sum(self.matrix, 0)

        html = """
                    <html>
                        <head>
                            <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.12.4/jquery.min.js"></script>
                            <script src="confused.js"></script>
                            <style>.good{background-color:green;color:white}.bad{background-color:red;color:white}table{table-layout:fixed}td{text-align:center;padding:10px;border:solid 1px black}</style>
                        </head>
                        <body><h2>A Confusing Matrix</h2><table>"""
        first_row = "<tr><td></td>"
        for i in range(self.size):
            first_row += "<td data-col-head={}>{}</td>".format(i, self.vocab[i])
        first_row += "<td>False Positives</td></tr>"
        html += first_row
        for i in range(self.size):
            html += "<tr><td data-row-head={}>{}</td>".format(i, self.vocab[i])
            for j in range(self.size):
                classy = "good" if i == j else "bad"
                opacity = self.matrix[i, j] / (np.mean(self.matrix[self.matrix > 0]))
                if opacity < 0.2: opacity = 0.2
                if opacity > 1.0: opacity = 1.0
                html += "<td data-i={} data-j={} class=\"{}\" style=\"opacity:{}\">{}</td>".format(i, j, classy,
                                                                                                   opacity,
                                                                                                   self.matrix[i, j])

            html += "<td>{}</td></tr>".format(round(100.0 * (fp_matrix[i] - self.matrix[i, i]) / fp_matrix[i], 2))
        # add confusion table for each class
        stats = {"precision": self.precision, "recall": self.recall, "F1": self.f1}

        html += "<tr><td>False Negatives</td>"
        for i in range(self.size):
            html += "<td>{}</td>".format(round(100.0 * (fn_matrix[i] - self.matrix[i, i]) / fn_matrix[i], 2))
        html += "</tr>"

        for k, v in stats.items():
            html += "<tr><td>{}</td>".format(k)
            for j in range(self.size):
                tp = self.matrix[j, j]
                fp = fp_matrix[j] - tp
                fn = fn_matrix[j] - tp
                html += "<td>{}</td>".format(round(100 * v(tp, fp, fn), 2))
            html += "</tr>"
        html += "</table><h2>Table of Confusion</h2>"
        total_tp = sum([self.matrix[i, i] for i in range(self.size)])
        total_fp = np.sum(fp_matrix) - total_tp
        total_fn = np.sum(fn_matrix) - total_tp
        html += "<h3>Precision: {}</h3>".format(round(100 * self.precision(total_tp, total_fp, total_fn), 2))
        html += "<h3>Recall: {}</h3>".format(round(100 * self.recall(total_tp, total_fp, total_fn), 2))
        html += "<h3>F1: {}</h3>".format(round(100 * self.f1(total_tp, total_fp, total_fn), 2))

        html += "</body></html>"
        return html

    def f1(self, tp, fp, fn):
        return 2.0 * tp / (2.0 * tp + fp + fn) if tp + fp + fn != 0 else 0.0

    def recall(self, tp, fp, fn):
        return 1.0 * tp / (tp + fn) if tp + fn != 0 else 0.0

    def precision(self, tp, fp, fn):
        return 1.0 * tp / (tp + fp) if tp + fn != 0 else 0.0

    def clear(self):
        self.matrix = np.zeros((self.size, self.size))


def CalculateLossForWord(word_obj, fValidation=False, fRunning=False):
    dy.renew_cg()

    if not fRunning: gold_lang = word_obj['tag']
    # add a bos before and after
    seq = ['*BOS*'] + list(word_obj['word']) + ['*BOS*']

    # get all the char encodings for the daf
    char_embeds = [let_enc(let) for let in seq]

    # run it through the bilstm
    char_bilstm_outputs = bilstm(char_embeds)
    bilistm_output = dy.concatenate([char_bilstm_outputs[0],char_bilstm_outputs[-1]])

    mlp_input = bilistm_output
    mlp_out = lang_mlp(mlp_input)
    predicted_lang = lang_tags[np.argmax(mlp_out.npvalue())]
    confidence = (mlp_out.npvalue()[:2] / np.sum(mlp_out.npvalue()[:2])).tolist() #skip ambiguous
    # if we aren't doing validation, calculate the loss
    if not fValidation and not fRunning:
        loss = -dy.log(dy.pick(mlp_out, gold_lang))
    # otherwise, set the answer to be the argmax
    elif not fRunning and fValidation:
        loss = None
        lang_conf_matrix(np.argmax(mlp_out.npvalue()), gold_lang)
    else:
        return predicted_lang,confidence

    pos_prec = 1 if predicted_lang == lang_tags[gold_lang] else 0

    tagged_word = { 'word': word_obj['word'], 'tag': predicted_lang, 'confidence':confidence, 'gold_tag':lang_tags[gold_lang]}

    if fValidation:
        return pos_prec, tagged_word

    return loss, pos_prec


def run_network_on_validation(epoch_num):
    val_lang_prec = 0.0
    val_lang_items = 0
    # iterate
    num_words_to_save = 1000
    words_to_save = []


    for idaf, word in enumerate(val_data):
        lang_prec, tagged_word = CalculateLossForWord(word, fValidation=True)
        # increment and continue
        val_lang_prec += lang_prec
        val_lang_items += 1
        if epoch_num >= 0 and idaf % round(1.0 * len(val_data) / num_words_to_save) == 0:
            words_to_save.append(tagged_word)

    # divide
    val_lang_prec = val_lang_prec / val_lang_items * 100 if val_lang_items > 0 else 0.0
    # print the results
    log_message('Validation: pos_prec: ' + str(val_lang_prec))

    objStr = json.dumps(words_to_save, indent=4, ensure_ascii=False)
    if not os.path.exists('epoch_{}'.format(epoch_num)):
        os.makedirs('epoch_{}'.format(epoch_num))
    with open("epoch_{}/tagged.json".format(epoch_num), "w") as f:
        f.write(objStr.encode('utf-8'))
    return val_lang_prec


def print_tagged_corpus_to_html_table(lang_out):
    str = u"<html><head><style>h1{text-align:center;background:grey}td{text-align:center}table{margin-top:20px;margin-bottom:20px;margin-right:auto;margin-left:auto;width:1200px}.aramaic{background-color:blue;color:white}.mishnaic{background-color:red;color:white}.ambiguous{background-color:yellow;color:black}</style><meta charset='utf-8'></head><body>"
    for daf in lang_out:
        str += u"<h1>DAF {}</h1>".format(daf)
        str += u"<table>"
        count = 0
        while count < len(lang_out[daf]):
            row_obj = lang_out[daf][count:count+10]
            row = u"<tr>"
            for w in reversed(row_obj):
                row += u"<td class='{}'>{}</td>".format(w['lang'],w['word'])
            row += u"</tr>"
            #row_sef += u"<td>({}-{})</td></tr>".format(count,count+len(row_obj)-1)
            str += row
            count += 10
        str += u"</table>"
        str += u"</body></html>"
    return str

# read in all the data
all_data = list(read_data())

random.shuffle(all_data)
# train val will be split up 100-780

percent_training = 0.2
split_index = int(round(len(all_data) * percent_training))
train_data = all_data[split_index:]
val_data = all_data[:split_index]

# create the vocabulary
let_vocab = Vocabulary()
lang_tags = ['aramaic','mishnaic','ambiguous']

# iterate through all the dapim and put everything in the vocabulary
for word in all_data:
    let_vocab.add_text(list(word['word']))

let_vocab.finalize()

lang_conf_matrix = ConfusionMatrix(len(lang_tags), lang_tags)

log_message('pos: ' + str(len(lang_tags)))
log_message('let: ' + str(let_vocab.size()))

# debug - write out the vocabularies
# write out to files the pos vocab and the letter vocab
with codecs.open('let_vocab.txt', 'w', encoding='utf8') as f:
    for let, id in let_vocab.get_c2i().items():
        f.write(str(id) + ' : ' + let + '\n')


# to save on memory space, we will clear out all_data from memory
all_data = None

# create the model and all it's parameters
model = dy.Model()

# create the word encoders (an encoder for the chars for the bilstm, and an encoder for the prev-pos lstm)
let_enc = WordEncoder("letenc", EMBED_DIM, model, let_vocab)

# the BiLSTM for all the chars, take input of embed dim, and output of the hidden_dim minus the embed_dim because we will concatenate
# with output from a separate bilstm of just the word
bilstm = BILSTMTransducer(BILSTM_LAYERS, EMBED_DIM, HIDDEN_DIM, model)

# now the class mlp, it will take input of 2*HIDDEN_DIM (A concatenate of the before and after the word) + EMBED_DIM from the prev-pos
# output of 2, unknown\talmud
lang_mlp = MLP(model, "classmlp", 2 * HIDDEN_DIM, HIDDEN_DIM, 3)


# the trainer
trainer = dy.AdamTrainer(model)

# if we are loading in a model
if filename_to_load:
    model.load(filename_to_load)

train_test = False
if train_test:
    run_network_on_validation(START_EPOCH - 1)
    lang_conf_matrix.clear()
    # train!
    for epoch in range(START_EPOCH, 100):
        last_loss, last_lang_prec = 0.0, 0.0
        total_loss, total_lang_prec = 0.0, 0.0
        total_lang_items = 0

        # shuffle the train data
        random.shuffle(train_data)

        items_seen = 0
        # iterate
        for word_obj in train_data:
            # calculate the loss & prec
            loss, lang_prec = CalculateLossForWord(word_obj, fValidation=False)

            # forward propagate
            total_loss += loss.value() if loss else 0.0
            # back propagate
            if loss: loss.backward()
            trainer.update()

            # increment the prec variable
            total_lang_prec += lang_prec
            total_lang_items += 1

            items_seen += 1
            # breakpoint?
            breakpoint = 5000
            if items_seen % breakpoint == 0:
                last_loss = total_loss / breakpoint
                last_lang_prec = total_lang_prec / total_lang_items * 100

                log_message("Words processed: " + str(items_seen) + ", loss: " + str(last_loss) + ', lang_prec: ' + str(
                    last_lang_prec))

                total_loss, total_lang_prec = 0.0, 0.0
                total_lang_items = 0

        log_message('Finished epoch ' + str(epoch))
        val_lang_prec = run_network_on_validation(epoch)
        if not os.path.exists('epoch_{}'.format(epoch)):
            os.makedirs('epoch_{}'.format(epoch))
        filename_to_save = 'epoch_' + str(epoch) + '/langtagger_model_embdim' + str(EMBED_DIM) + '_hiddim' + str(
            HIDDEN_DIM) + '_lyr' + sLAYERS + '_e' + str(epoch)
        filename_to_save += '_trainloss' + str(last_loss) + '_trainprec' + str(last_lang_prec) + '_valprec' + str(
            val_lang_prec) + '.model'
        model.save(filename_to_save)

        f = open("epoch_{}/conf_matrix_e{}.html".format(epoch, epoch), 'w')
        f.write(lang_conf_matrix.to_html())
        f.close()
        lang_conf_matrix.clear()
else:
    #tag all of shas!
    cal_matcher_path = '../../dibur_hamatchil/dh_source_scripts/cal_matcher_output'
    mesechtot_names = ['Berakhot','Shabbat','Eruvin','Pesachim']
    for mesechta in mesechtot_names:
        mesechta_path = '{}/{}/lang_naive_talmud'.format(cal_matcher_path,mesechta)
        if not os.path.exists('{}/{}/lang_tagged'.format(cal_matcher_path, mesechta)):
            os.makedirs('{}/{}/lang_tagged'.format(cal_matcher_path, mesechta))
        if not os.path.exists('{}/{}/html_lang_tagged'.format(cal_matcher_path, mesechta)):
            os.makedirs('{}/{}/html_lang_tagged'.format(cal_matcher_path, mesechta))


        def sortdaf(fname):
            daf = fname.split('lang_naive_talmud_')[1].split('.json')[0]
            daf_int = int(daf[:-1])
            amud_int = 1 if daf[-1] == 'b' else 0
            return daf_int*2 + amud_int
        files = [f for f in listdir(mesechta_path) if isfile(join(mesechta_path, f))]
        files.sort(key=sortdaf)
        html_out = OrderedDict()
        for i_f,f_name in enumerate(files):
            lang_out = []
            cal_matcher_out = json.load(codecs.open('{}/{}'.format(mesechta_path,f_name), "rb", encoding="utf-8"))
            for w in cal_matcher_out['words']:
                lang, confidence = CalculateLossForWord(w, fRunning=True)
                lang_out.append({'word':w['word'],'lang':lang,'confidence':confidence})


            fp = codecs.open("{}/{}/lang_tagged/{}.json".format(cal_matcher_path,mesechta,f_name), "wb", encoding='utf-8')
            json.dump(lang_out, fp, indent=4, encoding='utf-8', ensure_ascii=False)
            fp.close()

            daf = f_name.split('lang_naive_talmud_')[1].split('.json')[0]
            html_out[daf] = lang_out
            if i_f % 10 == 0:
                print '{}/{}'.format(mesechta,f_name)
                html = print_tagged_corpus_to_html_table(html_out)
                fp = codecs.open("{}/{}/html_lang_tagged/{}.html".format(cal_matcher_path, mesechta, daf), "wb",
                                 encoding='utf-8')
                fp.write(html)
                fp.close()
                html_out = OrderedDict()


