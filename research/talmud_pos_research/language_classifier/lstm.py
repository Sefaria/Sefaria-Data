import sys
import random,json,codecs
from collections import defaultdict
from itertools import count

sys.path.append("/Users/nss/cnn/pycnn")
from pycnn import *

training_root = "../../dibur_hamatchil/dh_source_scripts/cal_matcher_output"

word_list = json.load(codecs.open("{}/Berakhot/test_set/test_set_9_11_naive_{}.json".format(training_root,"2b"),encoding='utf8'),encoding='utf-8')["words"]
POS_TAGS = ["N01","N02","N03","N04","N05","V01","V02","V03","V04","V05","V06","V07","V08","V09","V10","V11","V12","A01","A02","A03","A04","A05","n01","n02","n03","n04","n05","P01","P02","P03","P","GN","c","a","I","d","PN","UKN"]

"""
def make_training_set(word_list):
    ts_words = []
    ts_tags = []
    curr_words = []
    curr_tags = []
    vocab = set()
    in_string = False
    for w in word_list:
        if w["class"] == "talmud":
            if not in_string:
                curr_words = []
                curr_tags = []
                curr_words.append("<EOS>")
                curr_tags.append("UKN")
                vocab.add("<EOS>")
                in_string = True
            curr_words.append(w["word"])
            curr_tags.append(w["POS"])
            vocab.add(w["word"])
        else:
            if in_string:
                curr_words.append("<EOS>")
                curr_tags.append("UKN")
                ts_words.append(curr_words)
                ts_tags.append(curr_tags)
                in_string = False
    return (ts_words,ts_tags,list(vocab))
"""
def make_training_set(word_list):
    ts_words = []
    ts_tags = []
    vocab = set()
    in_string = False
    for w in word_list:
        if w["class"] == "talmud":
            if not in_string:
                ts_words.append("<EOS>")
                ts_tags.append("UKN")
                vocab.add("<EOS>")
                in_string = True
            ts_words.append(w["word"])
            ts_tags.append(w["POS"])
            vocab.add(w["word"])
        else:
            if in_string:
                ts_words.append("<EOS>")
                ts_tags.append("UKN")
                in_string = False
    return (ts_words,ts_tags,list(vocab))

def pos2num(pos):
    if pos[0] == 'p':
        pos = "P" + pos[1:]
    return POS_TAGS.index(pos)

def word2num(word,vocab):
    return vocab.index(word)

m = Model()

# add parameters to model
m.add_parameters("W", (40,40))
m.add_parameters("b", 40)
m.add_lookup_parameters("lookup", (500, 40))
print "added"

# create trainer
trainer = SimpleSGDTrainer(m)

# L2 regularization and learning rate parameters can be passed to the trainer:
# alpha = 0.1  # learning rate
# lambda = 0.0001  # regularization
# trainer = SimpleSGDTrainer(m, lam=lambda, e0=alpha)

# function for graph creation
def create_network_return_loss(model, inputs, expected_output, vocab):
    """
    inputs is a list of numbers
    """
    renew_cg()
    W = parameter(model["W"])
    b = parameter(model["b"])
    lookup = model["lookup"]
    #emb_vectors = [lookup[word2num(w,vocab)] for w in inputs]
    #net_input = concatenate(emb_vectors)
    net_input = lookup[word2num(inputs,vocab)]
    net_output = softmax( (W*net_input) + b)
    loss = -log(pick(net_output, pos2num(expected_output)))
    return loss

# function for prediction
def create_network_return_best(model, inputs, vocab):
    """
    inputs is a list of numbers
    """
    renew_cg()
    W = parameter(model["W"])
    b = parameter(model["b"])
    lookup = model["lookup"]
    #emb_vectors = [lookup[i] for i in inputs]
    #net_input = concatenate(emb_vectors)

    output = []
    for w in inputs:
        net_input = lookup[word2num(w,vocab)]
        net_output = softmax( (W*net_input) + b)
        output.append(POS_TAGS[np.argmax(net_output)])
    return output


# train network
def train(m,w,t,v):
    for inp,lbl in zip(w,t):
        print inp, lbl
        loss = create_network_return_loss(m, inp, lbl,v)
        print loss.value() # need to run loss.value() for the forward prop
        loss.backward()
        trainer.update()

#print create_network_return_best(m, [1,2,3])

w, t, v = make_training_set(word_list)
train(m,w,t,v)

o = create_network_return_best(m,w,v)
num_right = 0
for i,to in enumerate(o):
    if to == t[i]:
        num_right += 1

print "ACCURACY: {}".format(1.0*num_right/len(o))