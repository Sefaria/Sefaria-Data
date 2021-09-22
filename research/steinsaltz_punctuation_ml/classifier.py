import django, json, csv, re, sklearn, sys, fasttext, random, pickle

django.setup()
import numpy as np
from tqdm import tqdm
from collections import defaultdict
import tensorflow as tf
import tensorview as tv
from tensorflow import keras
from tensorflow.keras import preprocessing, datasets, layers, models, optimizers, losses, metrics, callbacks, initializers, backend, constraints
from tensorflow.python.platform import gfile
from sklearn.model_selection import train_test_split
from sefaria.model import *
from sefaria.utils.hebrew import strip_cantillation

# from this answer: https://github.com/tensorflow/tensorflow/issues/24496#issuecomment-464909727
from tensorflow.compat.v1 import ConfigProto
from tensorflow.compat.v1 import InteractiveSession
config = ConfigProto()
config.gpu_options.allow_growth = True
session = InteractiveSession(config=config)

N_EPOCHS = 50
EMBEDDING_SIZE = 256
BATCH_SIZE = 2048
DATA = "/home/nss/sefaria/data/research/steinsaltz_punctuation_ml/data"

class HasPunctuationClf:

    def __init__(self, vocab_size, embedding_size, input_length) -> None:
        self.model = models.Sequential(name="has-punctuation")
        self.model.add(layers.Embedding(vocab_size+2, embedding_size, input_length=input_length, trainable=True))
        # self.model.add(layers.LSTM(128, return_sequences=True))
        self.model.add(layers.Bidirectional(layers.LSTM(128, return_sequences=True), input_shape=(input_length, embedding_size)))
        self.model.add(layers.Dense(128, activation='relu'))
        self.model.add(layers.Dense(64, activation='relu'))
        self.model.add(layers.Dense(2, activation='softmax'))
        self.model.compile(optimizer=optimizers.Adam(), #learning_rate=0.001), 
                    loss=losses.CategoricalCrossentropy(from_logits=False), 
                    metrics=[metrics.CategoricalAccuracy(), metrics.Recall(class_id=1), metrics.Precision(class_id=1)])
    
    def fit(self, x_train, y_train, **kwargs):
        return self.model.fit(x_train, y_train, callbacks=self.get_callbacks(), **kwargs)

    def evaluate(self, x_test, y_test, **kwargs):
        return self.model.evaluate(x_test, y_test, **kwargs)

    def get_callbacks(self):
        return [
            #keras.callbacks.ModelCheckpoint(filepath= str(c2c_path / 'checkpoints/model_{epoch}'), save_best_only=True, verbose=1),
            tv.train.PlotMetricsOnEpoch(metrics_name=[f'Loss', 'Accuracy', 'Recall', 'Precision'], cell_size=(6,4), columns=4, iter_num=N_EPOCHS, wait_num=N_EPOCHS),
        ]

def get_sequenced_text(X, tokenizer):
    X_seq = tokenizer.texts_to_sequences(X)
    return X_seq

def read_data():
    with open(f"{DATA}/dataset.csv", "r") as fin:
        raw_data = list(csv.DictReader(fin))
    raw_data_by_seg = defaultdict(list)
    data_by_seg = []
    for row in raw_data:
        raw_data_by_seg[row['Ref']] += [row]
    all_he_text = []
    for seg_data in raw_data_by_seg.values():
        line = " ".join(re.sub(r'<[^>]+>', '', row['Word']) for row in seg_data)
        data_by_seg += [{
            "text": line,
            "has_punct_Y": [[1, 0] if len(row['Punctuation']) == 0 else [0, 1] for row in seg_data],
        }]
        all_he_text += [line]
    X, Y = [], []
    tokenizer = preprocessing.text.Tokenizer(oov_token="<UNK>")
    tokenizer.fit_on_texts(all_he_text)
    max_doc_len = 0
    X = get_sequenced_text(all_he_text, tokenizer)
    for temp_x in X:
        if len(temp_x) > max_doc_len:
            max_doc_len = len(temp_x)
    print('max len', max_doc_len)
    for data in data_by_seg:
        Y += [data['has_punct_Y']]
    
    X = preprocessing.sequence.pad_sequences(X, maxlen=max_doc_len, padding='post', truncating='post')
    Y = preprocessing.sequence.pad_sequences(Y, maxlen=max_doc_len, padding='post', truncating='post', value=[1, 0])
    Y = np.asarray(Y)
    return X, Y, len(tokenizer.word_counts), max_doc_len

def train_has_punct():
    X, Y, vocab_size, max_doc_len = read_data()
    clf = HasPunctuationClf(vocab_size, EMBEDDING_SIZE, max_doc_len)
    clf.fit(X, Y, epochs=N_EPOCHS, batch_size=BATCH_SIZE)

if __name__ == "__main__":
    train_has_punct()