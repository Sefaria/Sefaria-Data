import django, json, csv, re, sklearn, sys, fasttext, random, pickle

django.setup()
from functools import reduce
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

N_EPOCHS = 150
EMBEDDING_SIZE = 128
BATCH_SIZE = 1024
DATA = "/home/nss/sefaria/data/research/steinsaltz_punctuation_ml/data"
TEST_SIZE = 0.2
RANDOM_STATE = 42

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

class AddToFirstCol(keras.layers.Layer):

    def call(self, inputs, *args, **kwargs):
        new_col, input = inputs
        new_col = tf.expand_dims(new_col, -1)
        return tf.concat([new_col, input[:, :, 1:]], axis=-1)

class RepeatFeatureLayer(keras.layers.Layer):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.n = kwargs['n']

    def call(self, inputs, *args, **kwargs):
        tile_multiple = tf.constant([1, 1, self.n])
        expanded = tf.expand_dims(inputs, -1)
        return tf.tile(expanded, tile_multiple)

class FlipLRLayer(keras.layers.Layer):
    def call(self, inputs, *args, **kwargs):
        return tf.reverse(inputs, tf.constant([-1]))

class ArgmaxLayer(keras.layers.Layer):
    def call(self, inputs, *args, **kwargs):
        return tf.cast(tf.argmax(inputs, -1), tf.float32)

class PunctuationClf:

    def __init__(self, vocab_size, embedding_size, input_length, n_punct_classes) -> None:
        self.vocab_size = vocab_size
        self.embedding_size = embedding_size
        self.input_length = input_length

        inputs = keras.Input((self.input_length,))
        model_head = self.get_model_head()(inputs)
        has_punct_out = self.get_mlp_model(2, 'has_p')(model_head)
        punct_out = self.get_mlp_model(n_punct_classes, 'p')(model_head)
        # punct_mask = self.get_punct_mask(n_punct_classes, 'p')({'has_p': has_punct_out, 'p_inter': punct_out})
        start_quote_out = self.get_mlp_model(2, 'sq')(model_head)
        end_quote_out = self.get_mlp_model(2, 'eq')(model_head)
        dash_out = self.get_mlp_model(2, 'd')(model_head)
        self.model = keras.Model(inputs=inputs, outputs={
            'has_p': has_punct_out,
            'p': punct_out,
            'sq': start_quote_out,
            'eq': end_quote_out,
            'd': dash_out,
        })
        my_losses = {
            "has_p": losses.BinaryCrossentropy(from_logits=False),
            "p": losses.CategoricalCrossentropy(from_logits=False),
            "sq": losses.BinaryCrossentropy(from_logits=False),
            "eq": losses.BinaryCrossentropy(from_logits=False),
            "d": losses.BinaryCrossentropy(from_logits=False),
        }
        my_metrics = {
            "has_p": [metrics.Recall(class_id=1), metrics.Precision(class_id=1)],
            "p": [metrics.Recall(class_id=1), metrics.Precision(class_id=1)],
            "sq": [metrics.Recall(class_id=1), metrics.Precision(class_id=1)],
            "eq": [metrics.Recall(class_id=1), metrics.Precision(class_id=1)],
            "d": [metrics.Recall(class_id=1), metrics.Precision(class_id=1)],
        }
        self.model.compile(optimizer=optimizers.Adam(), #learning_rate=0.001), 
                    loss=my_losses, 
                    metrics=my_metrics)
        self.model.summary()
    
    def get_mlp_model(self, num_classes, name):
        inputs = keras.Input((self.input_length, self.embedding_size))
        x = layers.Dropout(0.5)(inputs)
        #x = layers.Dense(128, activation='relu', kernel_constraint=constraints.MaxNorm(max_value=3))(x)
        #x = layers.Dropout(0.5)(x)
        x = layers.Dense(64, activation='relu', kernel_constraint=constraints.MaxNorm(max_value=3))(x)
        x = layers.Dropout(0.5)(x)
        x = layers.Dense(32, activation='relu', kernel_constraint=constraints.MaxNorm(max_value=3))(x)
        x = layers.Dropout(0.5)(x)
        outputs = layers.Dense(num_classes, activation='softmax', kernel_constraint=constraints.MaxNorm(max_value=3))(x)
        return keras.Model(inputs, outputs, name=name)

    def get_punct_mask(self, n_punct_classes, name):
        has_punct_input = keras.Input((self.input_length, 2), name='has_p')
        punct_input = keras.Input((self.input_length, n_punct_classes), name='p_inter')
        has_punct_argmax = ArgmaxLayer()(has_punct_input)
        inv_has_punct_argmax = ArgmaxLayer()(FlipLRLayer()(has_punct_input))
        has_punct_mask = RepeatFeatureLayer(n=n_punct_classes)(has_punct_argmax)
        masked = keras.layers.Multiply()([has_punct_mask, punct_input])
        masked = AddToFirstCol()([inv_has_punct_argmax, masked])
        return keras.Model({'has_p': has_punct_input, 'p_inter': punct_input}, masked, name=name)

    def get_model_head(self):
        inputs = keras.Input((self.input_length,))
        x = layers.Embedding(self.vocab_size+2, self.embedding_size, input_length=self.input_length, trainable=True)(inputs)
        # self.model.add(layers.LSTM(128, return_sequences=True))
        outputs = layers.Bidirectional(layers.LSTM(64, return_sequences=True, dropout=0.5, recurrent_dropout=0.5), input_shape=(self.input_length, self.embedding_size))(x)
        return keras.Model(inputs, outputs)
    
    def fit(self, x_train, y_train, **kwargs):
        return self.model.fit(x_train, y_train, callbacks=self.get_callbacks(), **kwargs)

    def evaluate(self, x_test, y_test, **kwargs):
        return self.model.evaluate(x_test, y_test, **kwargs)

    def get_callbacks(self):
        return [
            #keras.callbacks.ModelCheckpoint(filepath= str(c2c_path / 'checkpoints/model_{epoch}'), save_best_only=True, verbose=1),
            #tv.train.PlotMetricsOnEpoch(metrics_name=[f'Loss', 'Accuracy', 'Recall', 'Precision'], cell_size=(6,4), columns=4, iter_num=N_EPOCHS, wait_num=N_EPOCHS),
        ]

def one_hot(index, n_classes):
    vector = [0]*n_classes
    vector[index] = 1
    return vector

def get_sequenced_text(X, tokenizer):
    X_seq = tokenizer.texts_to_sequences(X)
    return X_seq

def read_data():
    punct_vocab = Vocab({"": 0})  # make sure empty string is zero so it matches padded values
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
            "has_p": [one_hot(0, 2) if len(row['Punctuation']) == 0 else one_hot(1, 2) for row in seg_data],
            "p": list(punct_vocab.seq_to_int(row['Punctuation'] for row in seg_data)),
            "sq": [one_hot(0, 2) if row['Pre-quote'] == 'False' else one_hot(1, 2) for row in seg_data],
            "eq": [one_hot(0, 2) if row['Post-quote'] == 'False' else one_hot(1, 2) for row in seg_data],
            "d": [one_hot(0, 2) if row['Dash'] == 'False' else one_hot(1, 2) for row in seg_data],
        }]
        all_he_text += [line]

    tokenizer = preprocessing.text.Tokenizer(oov_token="<UNK>")
    tokenizer.fit_on_texts(all_he_text)
    max_doc_len = 0
    X = get_sequenced_text(all_he_text, tokenizer)
    for temp_x in X:
        if len(temp_x) > max_doc_len:
            max_doc_len = len(temp_x)
    def pad(seq, value=0):
        return preprocessing.sequence.pad_sequences(seq, maxlen=max_doc_len, padding='post', truncating='post', value=value)
    X = pad(X)
    Y = {
        'has_p': np.asarray(pad([x['has_p'] for x in data_by_seg], one_hot(0, 2))),
        'p': np.asarray(pad([[one_hot(x, punct_vocab.size) for x in seg_data['p']] for seg_data in data_by_seg], one_hot(0, punct_vocab.size))),
        'sq': np.asarray(pad([x['sq'] for x in data_by_seg], one_hot(0, 2))),
        'eq': np.asarray(pad([x['eq'] for x in data_by_seg], one_hot(0, 2))),
        'd': np.asarray(pad([x['d'] for x in data_by_seg], one_hot(0, 2))),
    }
    return X, Y, len(tokenizer.word_counts), max_doc_len, punct_vocab

def train_test():
    X, Y, vocab_size, max_doc_len, punct_vocab = read_data()
    Y_train, Y_test = {}, {}
    for key, temp_Y in Y.items():
        X_train, X_test, temp_Y_train, temp_Y_test = train_test_split(X, temp_Y, test_size=TEST_SIZE, random_state=RANDOM_STATE)
        Y_train[key] = temp_Y_train
        Y_test[key] = temp_Y_test
    clf = PunctuationClf(vocab_size, EMBEDDING_SIZE, max_doc_len, punct_vocab.size)
    clf.fit(X_train, Y_train, epochs=N_EPOCHS, batch_size=BATCH_SIZE)
    clf.evaluate(X_test, Y_test)

if __name__ == "__main__":
    train_test()