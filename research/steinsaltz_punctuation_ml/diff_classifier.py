import django, json, csv, re, sklearn, sys, fasttext, random, pickle

django.setup()
from functools import reduce
import numpy as np
from tqdm import tqdm
from collections import defaultdict
import tensorflow as tf
import tensorview as tv
from tensorflow import keras
from tensorflow.keras.callbacks import Callback
from tensorflow.keras import preprocessing, datasets, layers, models, optimizers, losses, metrics, callbacks, initializers, backend, constraints
from tensorflow.python.platform import gfile
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_curve, auc
import matplotlib.pyplot as plt
from sefaria.model import *
from sefaria.utils.hebrew import strip_cantillation

# from this answer: https://github.com/tensorflow/tensorflow/issues/24496#issuecomment-464909727
from tensorflow.compat.v1 import ConfigProto
from tensorflow.compat.v1 import InteractiveSession
config = ConfigProto()
config.gpu_options.allow_growth = True
session = InteractiveSession(config=config)

N_EPOCHS = 50
EMBEDDING_SIZE = 170
BATCH_SIZE = 512
DATA = "/home/nss/sefaria/data/research/steinsaltz_punctuation_ml/data"
MODEL_LOC = "/home/nss/sefaria/data/research/steinsaltz_punctuation_ml/models"
TEST_SIZE = 0.2
RANDOM_STATE = 42

def get_pred_array(y, class_idx):
    return y['has_diff'][:, :, class_idx].flatten()

class RocCallback(Callback):
    def __init__(self, training_data, validation_data, desired_tprs, wait_num=1, class_idx=0):
        super().__init__()
        self.class_idx = class_idx
        self.desired_tprs = desired_tprs
        self.x = training_data[0]
        self.true_labels = self.get_pred_array(training_data[1])
        self.x_val = validation_data[0]
        self.true_labels_val = self.get_pred_array(validation_data[1])
        self.wait_num = wait_num

    def get_pred_array(self, y):
        return get_pred_array(y, self.class_idx)

    def on_epoch_end(self, epoch, logs=None):
        if epoch % self.wait_num != 0: return
        #y_pred_train = self.model.predict(self.x)
        #fpr, tpr, threshold = roc_curve(self.true_labels, self.get_pred_array(y_pred_train))
        y_pred_val = self.model.predict(self.x_val, batch_size=BATCH_SIZE)
        fpr_val, tpr_val, threshold = roc_curve(self.true_labels_val, self.get_pred_array(y_pred_val))
        #roc_auc = auc(fpr, tpr)
        roc_auc_val = auc(fpr_val, tpr_val)

        # plot
        #plt.title(f'ROC for epoch {epoch}')
        #plt.plot(fpr, tpr, 'b', label=f'AUC = {roc_auc}')
        #plt.plot(fpr_val, tpr_val, 'm', label=f'VAL AUC = {roc_auc_val}')
        # TODO too much to plot threholds on plot...
        # for i, thresh in enumerate(threshold):
        #     plt.annotate(round(thresh, 4), (fpr_val[i], tpr_val[i]))
        # plt.legend(loc='lower right')
        # plt.plot([0, 1], [0, 1], 'r--')
        # plt.xlim([0, 1])
        # plt.ylim([0, 1])
        # plt.ylabel('True Positive Rate')
        # plt.xlabel('False Positive Rate')
        # plt.show()

        desired_tprs = self.desired_tprs[:]
        print()
        for temp_tpr, temp_fpr, thresh in zip(tpr_val, fpr_val, threshold):
            if temp_tpr > desired_tprs[0]:
                print(f'TPR: {round(temp_tpr, 4)} FPR: {round(temp_fpr, 4)} THRESH: {thresh}')
                desired_tprs.pop(0)
                if len(desired_tprs) == 0: break

class PunctuationClf:

    def __init__(self, vocab_size, embedding_size, input_length) -> None:
        self.vocab_size = vocab_size
        self.embedding_size = embedding_size
        self.input_length = input_length

        inputs = keras.Input((self.input_length,))
        model_head = self.get_model_head()(inputs)
        has_diff_out = self.get_mlp_model(2, 'has_diff')(model_head)
        self.model = keras.Model(inputs=inputs, outputs={
            'has_diff': has_diff_out,
        })
        my_losses = {
            "has_diff": losses.BinaryCrossentropy(from_logits=False),
        }
        my_metrics = {
            "has_diff": [metrics.Recall(), metrics.Precision()],
        }
        self.model.compile(optimizer=optimizers.Adam(), #learning_rate=0.001),
                    loss=my_losses,
                    metrics=my_metrics)
        self.model.summary()

    def get_mlp_model(self, num_classes, name):
        inputs = keras.Input((self.input_length, self.embedding_size))
        x = layers.Dropout(0.5)(inputs)
        x = layers.Dense(128, activation='relu', kernel_constraint=constraints.MaxNorm(max_value=3))(x)
        x = layers.Dropout(0.5)(x)
        x = layers.Dense(64, activation='relu', kernel_constraint=constraints.MaxNorm(max_value=3))(x)
        x = layers.Dropout(0.5)(x)
        x = layers.Dense(32, activation='relu', kernel_constraint=constraints.MaxNorm(max_value=3))(x)
        x = layers.Dropout(0.5)(x)
        outputs = layers.Dense(num_classes, activation='softmax', kernel_constraint=constraints.MaxNorm(max_value=3))(x)
        return keras.Model(inputs, outputs, name=name)

    def get_model_head(self):
        inputs = keras.Input((self.input_length,))
        x = layers.Embedding(self.vocab_size+2, self.embedding_size, input_length=self.input_length, trainable=True, mask_zero=True)(inputs)
        # outputs = layers.LSTM(self.embedding_size, return_sequences=True)(x)
        outputs = layers.Bidirectional(layers.LSTM(int(self.embedding_size/2), return_sequences=True, dropout=0.5, recurrent_dropout=0.5), input_shape=(self.input_length, self.embedding_size))(x)
        return keras.Model(inputs, outputs)

    def fit(self, x_train, y_train, **kwargs):
        return self.model.fit(x_train, y_train, callbacks=self.get_callbacks(x_train, y_train, **kwargs), **kwargs)

    def evaluate(self, x_test, y_test, **kwargs):
        return self.model.evaluate(x_test, y_test, **kwargs)

    def save(self, folder=MODEL_LOC):
        self.model.save_weights(f'{folder}/diff_clf')

    def load(self, folder=MODEL_LOC):
        self.model.load_weights(f'{folder}/diff_clf')

    def get_callbacks(self, x_train, y_train, **kwargs):
        return [
            #keras.callbacks.ModelCheckpoint(filepath= str(c2c_path / 'checkpoints/model_{epoch}'), save_best_only=True, verbose=1),
            tv.train.PlotMetricsOnEpoch(metrics_name=[f'Loss', 'Recall', 'Precision'], cell_size=(6,4), columns=3, iter_num=N_EPOCHS, wait_num=5),
            RocCallback(training_data=(x_train, y_train), validation_data=kwargs.get('validation_data'), class_idx=1, desired_tprs=[0.99,0.999,0.9999,0.99999], wait_num=5)
        ]

class Vocab:

    def __init__(self, init_vocab=None) -> None:
        self.__vocabulary = init_vocab or {}

    def seq_to_int(self, seq):
        for elem in seq:
            if elem not in self.__vocabulary:
                self.__vocabulary[elem] = len(self.__vocabulary)
            yield self.__vocabulary[elem]

    @property
    def size(self):
        return len(self.__vocabulary)

def get_sequenced_text(X, tokenizer):
    X_seq = tokenizer.texts_to_sequences(X)
    return X_seq

def one_hot(index, n_classes):
    vector = [0]*n_classes
    vector[index] = 1
    return vector

def read_data():
    titles = ["Berakhot", "Shabbat", "Eruvin", "Pesachim", "Yoma", "Sukkah"]
    raw_data_by_seg = defaultdict(list)
    Y = []
    all_text = []
    all_refs = []
    for title in titles:
        with open(f"{DATA}/punct_diff/{title}.csv", "r") as fin:
            raw_data = list(csv.DictReader(fin))
        for row in raw_data:
            raw_data_by_seg[row['Ref']] += [row]
        for ref, seg_data in raw_data_by_seg.items():
            line = [re.sub(r'<[^>]+>', '', row['In']) for row in seg_data]
            Y += [[one_hot(0, 2) if row['Tag'] == 'equal' else one_hot(1, 2) for row in seg_data]]
            all_text += [line]
            all_refs += [ref]

    tokenizer = preprocessing.text.Tokenizer(oov_token="<UNK>")
    tokenizer.fit_on_texts(all_text)
    max_doc_len = 0
    X = get_sequenced_text(all_text, tokenizer)
    for temp_x in X:
        if len(temp_x) > max_doc_len:
            max_doc_len = len(temp_x)
    def pad(seq, value=0):
        return preprocessing.sequence.pad_sequences(seq, maxlen=max_doc_len, padding='post', truncating='post', value=value)
    X = pad(X)
    Y = {
        "has_diff": np.asarray(pad(Y, one_hot(0, 2))),
    }
    return X, Y,  len(tokenizer.word_counts), max_doc_len, all_text, all_refs

def get_train_test():
    X, Y, vocab_size, max_doc_len, all_text, all_refs = read_data()
    Y_train, Y_test = {}, {}
    for key, temp_Y in Y.items():
        X_train, X_test, temp_Y_train, temp_Y_test = train_test_split(X, temp_Y, test_size=TEST_SIZE, random_state=RANDOM_STATE)
        Y_train[key] = temp_Y_train
        Y_test[key] = temp_Y_test
    return X_train, X_test, Y_train, Y_test, vocab_size, max_doc_len, all_text, all_refs

def train_test():
    X_train, X_test, Y_train, Y_test, vocab_size, max_doc_len, all_text, all_refs = get_train_test()
    clf = PunctuationClf(vocab_size, EMBEDDING_SIZE, max_doc_len)
    clf.fit(X_train, Y_train, epochs=N_EPOCHS, batch_size=BATCH_SIZE, validation_data=((X_test, Y_test)))
    clf.evaluate(X_test, Y_test)
    clf.save()

def calc_stats_on_saved_model():
    X_train, X_test, Y_train, Y_test, vocab_size, max_doc_len, all_text, all_refs = get_train_test()
    _, test_text, _, test_refs = train_test_split(all_text, all_refs, test_size=TEST_SIZE, random_state=RANDOM_STATE)
    clf = PunctuationClf(vocab_size, EMBEDDING_SIZE, max_doc_len)
    clf.load()
    # roc_callback = RocCallback((X_train, Y_train), (X_test, Y_test), desired_tprs=[0.99, 0.999], class_idx=1)
    # roc_callback.model = clf.model
    # roc_callback.on_epoch_end(1)

    true_labels = get_pred_array(Y_test, 1)
    pred_labels = get_pred_array(clf.model.predict(X_test, batch_size=BATCH_SIZE), 1)
    count = 0
    threshs = [0.5, 0.4, 0.3, 0.2, 0.1]
    acc_dict = {
        key: [0]*len(threshs) for key in ['tp', 'fp', 'tn', 'fn']
    }
    for i, (t, p) in enumerate(zip(true_labels, pred_labels)):
        for ithresh, thresh in enumerate(threshs):
            dec = 1 if p > thresh else 0
            if t == 1 and dec == 1:
                acc_dict['tp'][ithresh] += 1
            elif t == 1 and dec == 0:
                acc_dict['fn'][ithresh] += 1
            elif t == 0 and dec == 0:
                acc_dict['tn'][ithresh] += 1
            elif t == 0 and dec == 1:
                acc_dict['fp'][ithresh] += 1
        # if dec == t: continue
        # iseg = i // max_doc_len
        # itok = i % max_doc_len
        #if itok >= len(test_text[iseg]): continue  # padding
        # count += 1
        #if count > 100: break
        # seg = test_text[iseg][:]
        # seg[itok] = f"*{seg[itok]}*"
        # print()
        # print(f"Ref: {test_refs[iseg]} - {iseg}:{itok}")
        # print(f"Token with error: {seg[itok]} Is Correct: {not bool(t)} Pred: {not bool(dec)} {round(p, 4)}")
        # print(f"Context: {'|'.join(seg[max(itok-5, 0):itok+6])}")
    for ithresh, thresh in enumerate(threshs):
        tp = acc_dict['tp'][ithresh]
        fp = acc_dict['fp'][ithresh]
        fn = acc_dict['fn'][ithresh]
        print(f'Thresh: {thresh} Precision: {round(tp/(tp+fp), 3)} Recall: {round(tp/(tp+fn), 3)}')

if __name__ == "__main__":
    # train_test()
    calc_stats_on_saved_model()
"""
TODO
- examples of incorrect predictions
- CNN -> LSTM -> MLP to predict punctuation

Results
loss: 0.0042 - recall: 0.9662 - precision: 0.9768 was this training??
val_loss: 0.0032 - val_recall: 0.9602 - val_precision: 0.9711
"""