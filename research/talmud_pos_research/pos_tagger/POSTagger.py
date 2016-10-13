# -*- coding: utf-8 -*-
import re,sys,random
#sys.path.append("/Users/nss/dynet/dynet")
import numpy as np
from codecs import open
from dynet import *
import argparse
from os.path import join
import os
import os.path
import json

# set the seed
random.seed(2823274491)

filename_to_load = ''
START_EPOCH = 0

# argument parse
parser = argparse.ArgumentParser()
parser.add_argument('-hiddim','-hiddendim', help='Size of the RNN hidden layer, default 100', default=100, required=False)
parser.add_argument('-embeddim','-embeddingdim', help='Size of the embeddings, default 50', default=50, required=False)
parser.add_argument('-layers','-mlplayers', help='Number of MLP layers, can only be 2 or 3', default=2, required=False)
parser.add_argument('-bilstmlayers', '-lstmlayers', help='Number of BILSTM layers, default 2', default=2, required=False)
parser.add_argument('-model', '-modeltoload', help='Filename of model to load', default='', required=False)
args = vars(parser.parse_known_args()[0])

# get the params
HIDDEN_DIM=int(args['hiddim'])
EMBED_DIM=int(args['embeddim'])
BILSTM_LAYERS=int(args['bilstmlayers'])
fDo_3_Layers=int(args['layers']) == 3
sLAYERS = '3' if fDo_3_Layers else '2'
Filename_to_log = 'postagger_log_embdim' + str(EMBED_DIM) + '_hiddim' + str(HIDDEN_DIM) + '_lyr' + sLAYERS + '.txt'

def log_message(message):
    print message
    with open(Filename_to_log, "a", encoding="utf8") as myfile:
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
    if not dir: dir = '../../dibur_hamatchil/dh_source_scripts/cal_matcher_output/'
    
    all_json_files = []
    # collect all the individual filenames
    for dirpath, dirnames, filenames in os.walk(dir):
        all_json_files.extend([join(dirpath, filename) for filename in filenames if filename.endswith('.json') and "lang_naive_talmud" in dirpath])

    total_words = 0
    total_daf = 0

    log_message('Loading path: ' + str(dir))

    # iterate through all the files, and load them in        
    for file in all_json_files:
        with open(file, 'r', encoding='utf8') as f:
            all_text = f.read()
        # parse 
        daf_data = json.loads(all_text)
        
        all_words = []
        for word in daf_data['words']:
            word_s = word['word']
            # class will be 1 if talmud, 0 if unknown
            word_class = 1 if word['class'] != 'unknown' else 0
            word_pos = ''
            # if the class isn't unkown
            if word_class: word_pos = word['POS']
            
            total_words += 1
            all_words.append((word_s, word_class, word_pos))
        
        total_daf += 1
        # yield it
        yield all_words
        
    log_message('Total words: ' + str(total_words))
    log_message('Total daf: ' + str(total_daf))
    
    
# Classes:
# 1] Vocabulary class (the dictionary for char-to-int)
# 2] WordEncoder (actually, it'll be a char encoder)
# 3] Simple character BiLSTM
# 4] MLP
class Vocabulary(object):
    def __init__(self):
        self.all_items = []
        self.c2i = {}
    
    def add_text(self, paragraph):
        self.all_items.extend(paragraph)
        
    def finalize(self, fAddBOS=True):
        self.vocab = sorted(list(set(self.all_items)))
        c2i_start = 1 if fAddBOS else 0
        self.c2i = {c:i for i,c in enumerate(self.vocab, c2i_start)}
        self.i2c = self.vocab
        if fAddBOS:
            self.c2i['<BOS>'] = 0
            self.i2c = ['<BOS>'] + self.vocab
        self.all_items = None
        
    # debug
    def get_c2i(self):
        return self.c2i
        
    def size(self):
        return len(self.i2c)
    
    def __getitem__(self, c):
        return self.c2i.get(c,0)
    
    def getItem(self, i):
        return self.i2c[i]
    
class WordEncoder(object):
    def __init__(self, name, dim, model, vocab):
        self.vocab = vocab
        self.enc = model.add_lookup_parameters((vocab.size(), dim))
    
    def __call__(self, char, DIRECT_LOOKUP=False):
        char_i = char if DIRECT_LOOKUP else self.vocab[char]
        return lookup(self.enc, char_i)
        
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
        W = parameter(self.mw)
        b = parameter(self.mb)
        W2 = parameter(self.mw2)
        b2 = parameter(self.mb2)
        mlp_output = W2*(tanh(W*x+b))+b2
        if fDo_3_Layers:
            W3 = parameter(self.mw3)
            b3 = parameter(self.mb3)
            mlp_output = W3*(tanh(mlpoutput))+b3
        return softmax(mlp_output)
        
class BILSTMTransducer:
    def __init__(self, LSTM_LAYERS, IN_DIM, OUT_DIM, model):
        self.lstmF = LSTMBuilder(LSTM_LAYERS, IN_DIM, (int)(OUT_DIM / 2), model)
        self.lstmB = LSTMBuilder(LSTM_LAYERS, IN_DIM, (int)(OUT_DIM / 2), model)
            
    def __call__(self, seq):
        """
        seq is a list of vectors (either character embeddings or bilstm outputs)
        """
        fw = self.lstmF.initial_state()
        bw = self.lstmB.initial_state()
        outf = fw.transduce(seq)
        outb = list(reversed(bw.transduce(reversed(seq))))
        return [concatenate([f,b]) for f,b in zip(outf,outb)]

def CalculateLossForDaf(daf, fValidation=False):
    renew_cg()

    
    # add a bos before and after
    seq = ['<BOS>'] + list(' '.join([word for word,_,_ in daf])) + ['<BOS>']
    
    # get all the char encodings for the daf
    char_embeds = [let_enc(let) for let in seq]
    
    # run it through the bilstm
    char_bilstm_outputs = bilstm(char_embeds)
    
    # now iterate and get all the separate word representations by concatenating the bilstm output 
    # before and after the word
    word_bilstm_outputs = []
    iLet_start = 0
    for iLet, char in enumerate(seq):
        # if it is a bos, check if it's at the end of the sequence
        if char == '<BOS>':
            if iLet + 1 == len(seq): char = ' '
            else: continue
        # if we are at a space, take this bilstm output and the one at the letter start
        if char == ' ':
            cur_word_bilstm_output = concatenate([char_bilstm_outputs[iLet_start], char_bilstm_outputs[iLet]])
            # add it in
            word_bilstm_outputs.append(cur_word_bilstm_output)
            
            # set the iLet_start ocunter to here
            iLet_start = iLet
    
    # safe-check, make sure word bilstm outputs length is the same as the daf
    if len(word_bilstm_outputs) != len(daf):
        log_message('Size mismatch!! word_bilstm_outputs: ' + str(len(word_bilstm_outputs)) + ', daf: ' + str(len(daf)))
        
    
    prev_pos_lstm_state = prev_pos_lstm.initial_state().add_input(pos_enc('<BOS>'))
    
    all_losses = []
    pos_prec = 0.0
    pos_items = 0
    class_prec = 0.0
    # now iterate through the bilstm outputs, and each word in the daf
    for (word, gold_word_class, gold_word_pos), bilstm_output in zip(daf, word_bilstm_outputs):
        # create the mlp input, a concatenate of the bilstm output and of the prev pos output
        mlp_input = concatenate([bilstm_output, prev_pos_lstm_state.output()])
        
        # run through the class mlp
        class_mjlp_output = class_mlp(mlp_input)
        
        predicted_word_class = np.argmax(class_mlp_output.npvalue())
        # prec
        class_prec += 1 if predicted_word_class == gold_word_class else 0
        
        # if we aren't doing validation, calculate the loss
        if not fValidation:
            all_losses.append(-log(pick(class_mlp_output, gold_word_class)))
            word_class_ans = gold_word_class
        # otherwise, set the answer to be the argmax
        else:
            word_class_ans = predicted_word_class
            
            
        # if the word_class answer is 1, do the pos!
        if word_class_ans:
            # run the pos mlp output
            pos_mlp_output = pos_mlp(mlp_input)
            
            predicted_word_pos = pos_vocab.getItem(np.argmax(pos_mlp_output.npvalue()))
            # prec
            pos_prec += 1 if predicted_word_pos == gold_word_pos else 0
            pos_items += 1
            
            # if we aren't doing validation, calculate the loss
            if not fValidation:
                all_losses.append(-log(pick(pos_mlp_output, pos_vocab[gold_word_pos])))
                word_pos_ans = gold_word_pos
            # otherwise, set the answer to be the argmax
            else:
                word_pos_ans = predicted_word_pos
                
            # run through the prev-pos-mlp
            prev_pos_lstm_state = prev_pos_lstm_state.add_input(pos_enc(word_pos_ans))
        # if the answer is 0, put a '' through the prev-pos lstm 
        else:
            prev_pos_lstm_state = prev_pos_lstm_state.add_input(pos_enc(''))
    
    pos_prec = pos_prec / pos_items if pos_items > 0 else None
    
    if fValidation:
        return class_prec / len(daf), pos_prec
        
    return esum(all_losses), class_prec / len(daf), pos_prec
    
def run_network_on_validation(suffix):
    val_pos_prec, val_class_prec = 0.0, 0.0
    val_pos_items = 0
    # iterate
    for daf in val_data:
        class_prec, pos_prec = CalculateLossForDaf(daf, fValidation=True)
        # increment and continue
        if not pos_prec is None:
            val_pos_prec += pos_prec
            val_pos_items += 1
        val_class_prec += class_prec
        
    # divide
    val_pos_prec = val_pos_prec / val_pos_items * 100 if val_pos_items > 0 else 0.0
    val_class_prec = val_class_prec / len(val_data) * 100
    # print the results
    log_message('Validation: pos_prec: ' + str(val_pos_prec) + ', class_prec: ' + str(val_class_prec))
    
    return val_pos_prec, val_class_prec
    
# read in all the data
all_data = list(read_data())

random.shuffle(all_data)
# train val will be split up 100-780
train_data = all_data[100:]
val_data = all_data[:100]

# create the vocabulary
pos_vocab = Vocabulary()
let_vocab = Vocabulary()

# iterate through all the dapim and put everything in the vocabulary
for daf in all_data:
    let_vocab.add_text(list(' '.join([word for word,_,_ in daf])))
    pos_vocab.add_text([pos for _,_,pos in daf])

pos_vocab.finalize()
let_vocab.finalize()

log_message('pos: ' + str(pos_vocab.size()))
log_message('let: ' + str(let_vocab.size()))

#debug - write out the vocabularies
# write out to files the pos vocab and the letter vocab
with open('let_vocab.txt', 'w', encoding='utf8') as f:
    for let, id in let_vocab.get_c2i().items():
        f.write(str(id) + ' : ' + let + '\n')
with open('pos_vocab.txt', 'w', encoding='utf8') as f:
    for pos, id in pos_vocab.get_c2i().items():
        f.write(str(id) + ' : ' + pos + '\n')


# to save on memory space, we will clear out all_data from memory
all_data = None

# create the model and all it's parameters
model = Model()

# create the word encoders (an encoder for the chars for the bilstm, and an encoder for the prev-pos lstm)
pos_enc = WordEncoder("posenc", EMBED_DIM, model, pos_vocab)
let_enc = WordEncoder("letenc", EMBED_DIM, model, let_vocab)

# the BiLSTM for all the chars, take input of embed dim, and output of the hidden_dim minus the embed_dim because we will concatenate
# with output from a separate bilstm of just the word
bilstm = BILSTMTransducer(BILSTM_LAYERS, EMBED_DIM, HIDDEN_DIM, model)

# a prev-pos lstm. The mlp's will take this as input as well
prev_pos_lstm = LSTMBuilder(BILSTM_LAYERS, EMBED_DIM, EMBED_DIM, model)

# now the class mlp, it will take input of 2*HIDDEN_DIM (A concatenate of the before and after the word) + EMBED_DIM from the prev-pos
# output of 2, unknown\talmud
class_mlp = MLP(model, "classmlp", 2*HIDDEN_DIM + EMBED_DIM, HIDDEN_DIM, 2)
# pos mlp, same input but output the size of pos_vocab
pos_mlp = MLP(model, 'posmlp', 2*HIDDEN_DIM + EMBED_DIM, HIDDEN_DIM, pos_vocab.size())

# the trainer
trainer = AdamTrainer(model)

# if we are loading in a model
if filename_to_load:
    model.load(filename_to_load)
run_network_on_validation(START_EPOCH - 1)

# train!
for epoch in range(START_EPOCH, 100):
    last_loss, last_pos_prec, last_class_prec = 0.0, 0.0, 0.0
    total_loss, total_pos_prec, total_class_prec = 0.0, 0.0, 0.0
    total_pos_items = 0
    
    # shuffle the train data
    random.shuffle(train_data)
    
    items_seen = 0
    # iterate
    for daf in train_data:
        # calculate the loss & prec
        loss, class_prec, pos_prec = CalculateLossForDaf(daf, fValidation=False)
        
        # forward propagate
        total_loss += loss.value() / len(daf)
        # back propagate
        loss.backward()
        trainer.update()
        
        # increment the prec variable
        if not pos_prec is None:
            total_pos_prec += pos_prec
            total_pos_items += 1

        total_class_prec += class_prec
        
        items_seen += 1
        # breakpoint?
        breakpoint = 50
        if items_seen % breakpoint == 0:    
            last_loss = total_loss / breakpoint
            last_pos_prec = total_pos_prec / total_pos_items * 100
            last_class_prec = total_class_prec / breakpoint * 100
            
            log_message ("Paras processed: " + str(items_seen) + ", loss: " + str(last_loss) + ', pos_prec: ' + str(last_pos_prec) + ', class_prec: ' + str(last_class_prec))
            
            total_loss, total_pos_prec, total_class_prec = 0.0, 0.0, 0.0
            total_pos_items = 0
            
    log_message ('Finished epoch ' + str(epoch))
    val_class_prec, val_pos_prec = run_network_on_validation(epoch)
    
    filename_to_save = 'postagger_model_embdim' + str(EMBED_DIM) + '_hiddim' + str(HIDDEN_DIM) + '_lyr' + sLAYERS + '_e' + str(epoch)
    filename_to_save += '_trainloss' +  str(last_loss) + '_trainprec' + str(last_pos_prec) + '_valprec' + str(val_pos_prec) + '.model'
    model.save(filename_to_save)
