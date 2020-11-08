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

# global configurations
csv.field_size_limit(sys.maxsize)
# from this answer: https://github.com/tensorflow/tensorflow/issues/24496#issuecomment-464909727
from tensorflow.compat.v1 import ConfigProto
from tensorflow.compat.v1 import InteractiveSession
config = ConfigProto()
config.gpu_options.allow_growth = True
session = InteractiveSession(config=config)

# constants
DATA = "/home/nss/Documents/Forks/Yishai-Sefaria-Project/ML/data/concat_english_prefix_hebrew.csv"
EMBEDDING_HE = "/home/nss/sefaria/datasets/text classification/fasttext_he_no_prefixes_20.bin"
EMBEDDING_EN = "/home/nss/sefaria/datasets/text classification/fasttext_en_no_prefixes_20.bin"
EMBEDDING_LINKS = "/home/nss/sefaria/datasets/text classification/link_embeddings_he.json"

MAX_DOCUMENT_LENGTH = 100
EMBEDDING_SIZE = 20
LINK_EMBEDDING_SIZE = 50
LINK_INPUT_LENGTH = 30
WINDOW_SIZE = EMBEDDING_SIZE
STRIDE = int(WINDOW_SIZE/2)
N_EPOCHS = 150
BATCH_SIZE = 2**11
TEST_SIZE = 0.3
RANDOM_SEED = 613
random.seed(RANDOM_SEED)
# tf2 cnn https://nbviewer.ipython.org/github/tonio73/data-science/blob/master/nlp/C2C_Fasttext-Tensorflow.ipynb

unidecode_table = {
    "ḥ": "h",
    "Ḥ": "H",
    "ă": "a",
    "ǎ": "a",
    "ġ": "g",
    "ḫ": "h",
    "ḳ": "k",
    "Ḳ": "K",
    "ŏ": "o",
    "ṭ": "t",
    "ż": "z",
    "Ż": "Z" ,
    "’": "'",
    '\u05f3': "'",
    "\u05f4": '"',
    "”": '"',
    "“": '"'
}
class CnnClf:
    def __init__(self, model_name, klass_name, embedding_matrix, embedding_size=EMBEDDING_SIZE, input_length=MAX_DOCUMENT_LENGTH):
        self.klass_name = klass_name
        self.model = models.Sequential(name=f'{model_name}-model')
        self.model.add(layers.Embedding(embedding_matrix.shape[0], embedding_size, input_length=input_length, embeddings_initializer=initializers.Constant(embedding_matrix), trainable=False))
        # model.add(layers.Embedding(len(tokenizer.word_index)+1, embedding_size, input_length=MAX_DOCUMENT_LENGTH))  # for trainable embedding layer
        self.model.add(layers.Dropout(0.1))
        self.model.add(layers.Convolution1D(16, kernel_size=4, activation='relu', strides=1, padding='same', kernel_constraint=constraints.MaxNorm(max_value=3)))
        self.model.add(layers.Dropout(0.5))
        self.model.add(layers.Convolution1D(12, kernel_size=8, activation='relu', strides=2, padding='same', kernel_constraint=constraints.MaxNorm(max_value=3)))
        self.model.add(layers.Dropout(0.5))
        self.model.add(layers.Convolution1D(8, kernel_size=16, activation='relu', strides=2, padding='same', kernel_constraint=constraints.MaxNorm(max_value=3)))
        self.model.add(layers.Dropout(0.5))
        self.model.add(layers.Flatten())
        self.model.add(layers.Dense(128, activation='relu', kernel_constraint=constraints.MaxNorm(max_value=3)))
        self.model.add(layers.Dropout(0.5))
        self.model.add(layers.Dense(64, activation='relu', kernel_constraint=constraints.MaxNorm(max_value=3)))
        self.model.add(layers.Dropout(0.5))
        self.model.add(layers.Dense(2, activation='softmax', kernel_constraint=constraints.MaxNorm(max_value=3)))
        self.model.compile(optimizer=optimizers.Adam(), #learning_rate=0.001), 
                    loss=losses.CategoricalCrossentropy(from_logits=False), 
                    metrics=[metrics.CategoricalAccuracy(), metrics.Recall(class_id=0), metrics.Precision(class_id=0)])

    def fit(self, x_train, y_train, **kwargs):
        return self.model.fit(x_train, y_train, callbacks=self.get_callbacks(), **kwargs)

    def evaluate(self, x_test, y_test, **kwargs):
        return self.model.evaluate(x_test, y_test, **kwargs)

    def get_callbacks(self):
        return [
            #keras.callbacks.ModelCheckpoint(filepath= str(c2c_path / 'checkpoints/model_{epoch}'), save_best_only=True, verbose=1),
            tv.train.PlotMetricsOnEpoch(metrics_name=[f'Loss {self.klass_name}', 'Accuracy', 'Recall', 'Precision'], cell_size=(6,4), columns=4, iter_num=N_EPOCHS, wait_num=N_EPOCHS),
        ]

class CnnClfEnsemble:
    def __init__(self, klass_name):
        self.klass_name = klass_name

    def build_model(self, embedding_matrix_dict, tokenizer_dict, embedding_size=EMBEDDING_SIZE, input_length=MAX_DOCUMENT_LENGTH, link_embedding_size=LINK_EMBEDDING_SIZE, link_input_length=LINK_INPUT_LENGTH):
        self.embedding_matrix_dict = embedding_matrix_dict
        self.tokenizer_dict = tokenizer_dict
        he_inputs = keras.Input(shape=(input_length,), name="hebrew")        
        en_inputs = keras.Input(shape=(input_length,), name="english")
        link_inputs = keras.Input(shape=(link_input_length,), name="links")

        he_outputs = self.get_text_model(embedding_matrix_dict["hebrew"], embedding_size, input_length)(he_inputs)
        en_outputs = self.get_text_model(embedding_matrix_dict["english"], embedding_size, input_length)(en_inputs)
        # link_outputs = self.get_link_model(embedding_matrix_dict["links"], link_embedding_size, link_input_length)(link_inputs)
        x = layers.Concatenate()([he_outputs, en_outputs])  # link_outputs
        x = layers.Dense(128, activation='relu', kernel_constraint=constraints.MaxNorm(max_value=3))(x)
        x = layers.Dropout(0.5)(x)
        x = layers.Dense(64, activation='relu', kernel_constraint=constraints.MaxNorm(max_value=3))(x)
        outputs = layers.Dropout(0.5)(x)
        outputs = layers.Dense(2, activation='softmax', kernel_constraint=constraints.MaxNorm(max_value=3))(x)
        self.model = keras.Model(inputs=[he_inputs, en_inputs], outputs=outputs, name=self.klass_name)  # link_inputs
        self.model.compile(optimizer=optimizers.Adam(), #learning_rate=0.001), 
                    loss=losses.CategoricalCrossentropy(from_logits=False), 
                    metrics=[metrics.CategoricalAccuracy(), metrics.Recall(class_id=0), metrics.Precision(class_id=0)])
        # self.model.summary()

    @staticmethod
    def get_link_model(link_embedding_matrix, link_embedding_size, link_input_length):
        inputs = keras.Input(shape=(link_input_length,))
        x = layers.Embedding(link_embedding_matrix.shape[0], link_embedding_size, input_length=link_input_length, embeddings_initializer=initializers.Constant(link_embedding_matrix), trainable=False)(inputs)
        x = layers.Dropout(0.1)(x)
        x = layers.Convolution1D(16, kernel_size=4, activation='relu', strides=1, padding='same', kernel_constraint=constraints.MaxNorm(max_value=3))(x)
        x = layers.Dropout(0.5)(x)
        x = layers.Convolution1D(12, kernel_size=8, activation='relu', strides=2, padding='same', kernel_constraint=constraints.MaxNorm(max_value=3))(x)
        x = layers.Dropout(0.5)(x)
        x = layers.Convolution1D(8, kernel_size=16, activation='relu', strides=2, padding='same', kernel_constraint=constraints.MaxNorm(max_value=3))(x)
        x = layers.Dropout(0.5)(x)
        outputs = layers.Flatten()(x)
        return keras.Model(inputs, outputs)
 
    @staticmethod
    def get_text_model(embedding_matrix, embedding_size=EMBEDDING_SIZE, input_length=MAX_DOCUMENT_LENGTH):
        inputs = keras.Input(shape=(input_length,))
        x = layers.Embedding(embedding_matrix.shape[0], embedding_size, input_length=input_length, embeddings_initializer=initializers.Constant(embedding_matrix), trainable=False)(inputs)
        x = layers.Dropout(0.1)(x)
        x = layers.Convolution1D(16, kernel_size=4, activation='relu', strides=1, padding='same', kernel_constraint=constraints.MaxNorm(max_value=3))(x)
        x = layers.Dropout(0.5)(x)
        x = layers.Convolution1D(12, kernel_size=8, activation='relu', strides=2, padding='same', kernel_constraint=constraints.MaxNorm(max_value=3))(x)
        x = layers.Dropout(0.5)(x)
        x = layers.Convolution1D(8, kernel_size=16, activation='relu', strides=2, padding='same', kernel_constraint=constraints.MaxNorm(max_value=3))(x)
        x = layers.Dropout(0.5)(x)
        outputs = layers.Flatten()(x)
        # outputs = layers.Dense(2, activation='relu', kernel_constraint=constraints.MaxNorm(max_value=3))(x)
        return keras.Model(inputs, outputs)

    def fit(self, x_train, y_train, **kwargs):
        return self.model.fit(x_train, y_train, callbacks=self.get_callbacks(kwargs.get('verbose', 0)), **kwargs)

    def evaluate(self, x_test, y_test, **kwargs):
        return self.model.evaluate(x_test, y_test, **kwargs)

    def save(self, folder):
        # weights
        self.model.save_weights(f'{folder}/{self.klass_name}/{self.klass_name}')
        # embeddings
        matrix_out = {}
        for key, matrix in self.embedding_matrix_dict.items():
            matrix_out[key] = matrix.tolist()
        with open(f'{folder}/{self.klass_name}/{self.klass_name}.embedding', 'w') as fout:
            json.dump(matrix_out, fout, ensure_ascii=False)
        # tokenizer
        with open(f'{folder}/{self.klass_name}/{self.klass_name}.tokenizer', 'wb') as fout:
            pickle.dump(self.tokenizer_dict, fout, protocol=pickle.HIGHEST_PROTOCOL)

    def load(self, folder, embedding_size=EMBEDDING_SIZE, input_length=MAX_DOCUMENT_LENGTH, link_embedding_size=LINK_EMBEDDING_SIZE, link_input_length=LINK_INPUT_LENGTH):
        # embeddings
        with open(f'{folder}/{self.klass_name}/{self.klass_name}.embedding', 'r') as fin:
            matrix_in = json.load(fin)
        self.embedding_matrix_dict = {}
        for key, matrix in matrix_in.items():
            self.embedding_matrix_dict[key] = np.array(matrix)
        # tokenizer
        with open(f'{folder}/{self.klass_name}/{self.klass_name}.tokenizer', 'rb') as fin:
            self.tokenizer_dict = pickle.load(fin)
        # weights
        self.build_model(self.embedding_matrix_dict, self.tokenizer_dict, embedding_size, input_length, link_embedding_size, link_input_length)
        self.model.load_weights(f'{folder}/{self.klass_name}/{self.klass_name}')


    def get_callbacks(self, verbose):
        if verbose == 0:
            return []
        return [
            #keras.callbacks.ModelCheckpoint(filepath= str(c2c_path / 'checkpoints/model_{epoch}'), save_best_only=True, verbose=1),
            tv.train.PlotMetricsOnEpoch(metrics_name=[f'Loss {self.klass_name}', 'Accuracy', 'Recall', 'Precision'], cell_size=(6,4), columns=4, iter_num=N_EPOCHS, wait_num=N_EPOCHS),
        ]

class BinaryRelevance:
    def __init__(self, clf_klass, klasses, clf_params=None):
        self.clf_klass = clf_klass
        clf_params = clf_params or {}
        self.clf_params = clf_params
        self.klasses = klasses
        self.models = {}
        self.test_sets = {}
        self.results = {}

    def load_models(self, folder):
        for klass in tqdm(self.klasses, desc="load models"):
            temp_clf = self.clf_klass(klass, **self.clf_params)
            temp_clf.load(folder)
            self.models[klass] = temp_clf
    
    def fit(self, get_dataset_for_klass, **clf_fit_kwargs):
        for iklass, klass in tqdm(enumerate(self.klasses), total=len(self.klasses)):
            self.fit_class(iklass, klass, get_dataset_for_klass, **clf_fit_kwargs)

    def fit_class(self, iklass, klass, get_dataset_for_klass, **clf_fit_kwargs):
        X_train, X_test, Y_train, Y_test, embedding_matrix, tokenizer = get_dataset_for_klass(klass)
        self.test_sets[klass] = (X_test, Y_test)
        temp_clf = self.clf_klass(klass, **self.clf_params)
        temp_clf.build_model(embedding_matrix, tokenizer)
        results = temp_clf.fit(X_train, Y_train, validation_data=(X_test, Y_test), **clf_fit_kwargs)
        temp_clf.save('research/topics_cnn/cnn_models')
        self.models[klass] = temp_clf

    def evaluate(self, get_dataset_for_klass, **clf_evaluate_kwargs):
        for iklass, klass in enumerate(self.klasses):
            X_test, Y_test = self.test_sets[klass]
            #_, X_test, _, Y_test, _ = get_dataset_for_klass(klass)
            temp_clf = self.models[klass]
            results = temp_clf.evaluate(X_test, Y_test, **clf_evaluate_kwargs)
            results['f1'] = 2*(results['precision']*results['recall'])/(results['precision']+results['recall'])
            results['weight'] = X_test.shape[1]
            print("RESULTS", klass, results)
            self.results[klass] = results
        f1_mean = sum([r['f1']*r['weight'] for r in self.results.values()])/sum([r['weight'] for r in self.results.values()])
        recall_mean = sum([r['recall']*r['weight'] for r in self.results.values()])/sum([r['weight'] for r in self.results.values()])
        precision_mean = sum([r['precision']*r['weight'] for r in self.results.values()])/sum([r['weight'] for r in self.results.values()])

        out = {
            'f1_mean': f1_mean,
            'recall_mean': recall_mean,
            'precision_mean': precision_mean,
            'results_by_class': self.results
        }
        with open('research/topics_cnn/cnn_models/results.json', 'w') as fout:
            json.dump(out, fout, ensure_ascii=False, indent=2)

    
class DataManager:

    def __init__(self, data_file, get_training_x=None, get_training_y=None):
        self.get_training_x = get_training_x or self.get_training_x_default
        self.get_training_y = get_training_y or self.get_training_y_default
        self.topic_counts = defaultdict(int)
        X, Y = self.load_data(data_file)
        self.X = X
        self.Y = Y
        self.toc_mapping = self.get_toc_mapping()

    def load_embeddings(self, embedding_file_he, embedding_file_en, embedding_file_links=None, embedding_size=None, link_embedding_size=None):
        self.embedding_model_he = fasttext.load_model(embedding_file_he)
        self.embedding_model_en = fasttext.load_model(embedding_file_en)
        if embedding_file_links is not None:
            with open(embedding_file_links, "r") as fin:
                self.embedding_model_links = {x['ref'].replace(" ", "_"): x['embedding'] for x in json.load(fin)}
            
        self.embedding_size = embedding_size
        self.link_embedding_size = link_embedding_size

    def load_data(self, data_file):
        X, Y = [], []
        with open(data_file, "r") as fin:
            c = csv.DictReader(fin)
            for row in c:
                temp_x = self.get_training_x(row)
                temp_y = self.get_training_y(row)
                if not temp_x:
                    continue
                X += [temp_x]
                Y += [temp_y]
                for y in temp_y:
                    self.topic_counts[y] += 1         
        return X, Y

    def get_binary_dataset_for_slug_set(self, slug_set, neg_pos_ratio):
        pos_X = [x for x, y in filter(lambda a: len(set(a[1]) & slug_set) > 0, zip(self.X, self.Y))]
        neg_X = [x for x, y in filter(lambda a: len(set(a[1]) & slug_set) == 0, zip(self.X, self.Y))]
        random.shuffle(neg_X)
        if neg_pos_ratio is not None:
            neg_X = neg_X[:len(pos_X)*neg_pos_ratio]
        pos_Y = [[1,0]]*len(pos_X)
        neg_Y = [[0,1]]*len(neg_X)

        X = pos_X + neg_X
        Y = pos_Y + neg_Y
        return X, Y

    @staticmethod
    def get_sequenced_text(X, max_len=MAX_DOCUMENT_LENGTH, minimal_tokenization=False, pretrained_tokenizer=None):
        if pretrained_tokenizer is None:
            if minimal_tokenization:
                tokenizer = preprocessing.text.Tokenizer(oov_token="<UNK>", filters='', lower=False)
            else:
                tokenizer = preprocessing.text.Tokenizer(oov_token="<UNK>")
            tokenizer.fit_on_texts(X)
        else:
            tokenizer = pretrained_tokenizer
        X_seq = tokenizer.texts_to_sequences(X)
        X_seq = preprocessing.sequence.pad_sequences(X_seq, maxlen=max_len, padding='post', truncating='post')
        return tokenizer, X_seq
 
    def get_train_test_sets(self, X, Y, data_type, random_state):
        tokenizer, X_seq = self.get_sequenced_text(X, LINK_INPUT_LENGTH if data_type == "links" else MAX_DOCUMENT_LENGTH, minimal_tokenization=data_type == "links")
        embedding_matrix = self.get_embedding_matrix(tokenizer, data_type)
        X_train, X_test, Y_train, Y_test = train_test_split(X_seq, np.asarray(Y), test_size=TEST_SIZE, random_state=random_state)
        return X_train, X_test, Y_train, Y_test, embedding_matrix, tokenizer

    @staticmethod
    def get_training_x_default(row):
        return {"hebrew": DataManager.clean_text(row["He_prefixed"], 'he'), "english": DataManager.clean_text(row["En"], 'en'), "links": row["Links"].replace(" ", "_").replace("|||", " ")}

    @staticmethod
    def get_training_y_default(row):
        return row["Topics"].split()

    @staticmethod
    def normalize(s, lang):
        for k, v in unidecode_table.items():
            s = s.replace(k, v)
        s = re.sub(r"<[^>]+>", " ", s)
        s = re.sub(r'־', ' ', s)
        s = re.sub(r'\([^)]+\)', ' ', s)
        s = re.sub(r'\[[^\]]+\]', ' ', s)
        if lang == 'he':
            s = re.sub(r'[^ \u05d0-\u05ea"\'״׳]', '', s)
        elif lang == 'en':
            s = re.sub(r'[^ a-zA-Z"\'״׳]', ' ', s)

        # remove are parenthetical text
        s = " ".join(re.sub(r'^["\'״׳]+', "", re.sub(r'["\'״׳]+$', "", word)) for word in s.split()).strip()
        return s

    @staticmethod
    def remove_prefixes(s):
        normalized = ""
        for word in s.split():
            word = re.sub(r"^[^|]+\|", "", word)
            normalized += ' ' + word
        return normalized

    @staticmethod
    def clean_text(s, lang):
        if lang == 'he':
            s = DataManager.remove_prefixes(s)
        return DataManager.normalize(s, lang)

    def get_embedding_matrix(self, tokenizer, data_type):
        embedding_model = getattr(self, f"embedding_model_{data_type}")
        embedding_matrix = np.zeros((len(tokenizer.word_index)+1, self.link_embedding_size if data_type == "links" else self.embedding_size))
        num_unknown = 0
        for word, i in tokenizer.word_index.items():
            if word == '<UNK>':
                num_unknown += 1
            if data_type == "links":
                embedding = embedding_model.get(word, np.zeros((self.link_embedding_size,)))
            else:
                embedding = embedding_model.get_word_vector(word)
            embedding_matrix[i] = embedding
        return embedding_matrix

    @staticmethod
    def get_toc_mapping():
        LAW_SLUG = 'laws'

        roots = TopicSet({"isTopLevelDisplay": True}).array()
        sub_laws = Topic.init(LAW_SLUG).topics_by_link_type_recursively(linkType='displays-under', max_depth=1)
        roots += sub_laws
        toc_mapping = {}
        for root in roots:
            if root.slug == LAW_SLUG:
                continue
            children = root.topics_by_link_type_recursively(linkType='displays-under')
            if len(children) == 1:  # just itself
                continue
            toc_mapping[root.slug] = list(set([child.slug for child in children]))
        return toc_mapping

    def get_dataset_for_super_topic(self, super_topic):
        sub_topics = self.toc_mapping[super_topic]
        X, Y = self.get_binary_dataset_for_slug_set(set(sub_topics), 4)
        return self.get_train_test_sets(X, Y)

    def get_ensemble_dataset_for_super_topic(self, super_topic):
        sub_topics = self.toc_mapping[super_topic]
        X, Y = self.get_binary_dataset_for_slug_set(set(sub_topics), 4)
        return self.get_ensemble_dataset(X, Y)

    def get_ensemble_dataset_for_sub_topic(self, sub_topic):
        X, Y = self.get_binary_dataset_for_slug_set({sub_topic}, 4)
        return self.get_ensemble_dataset(X, Y)

    def get_ensemble_dataset(self, X, Y):
        random_state = RANDOM_SEED
        X_train_he, X_test_he, Y_train, Y_test, embedding_matrix_he, tokenizer_he = self.get_train_test_sets([x["hebrew"] for x in X], Y, "he", random_state)
        X_train_en, X_test_en, Y_train, Y_test, embedding_matrix_en, tokenizer_en = self.get_train_test_sets([x["english"] for x in X], Y, "en", random_state)
        X_train_links, X_test_links, Y_train, Y_test, embedding_matrix_links, tokenizer_links = self.get_train_test_sets([x["links"] for x in X], Y, "links", random_state)
        return (
            {"hebrew": X_train_he, "english": X_train_en, "links": X_train_links},
            {"hebrew": X_test_he, "english": X_test_en, "links": X_test_links},
            Y_train, Y_test,
            {"hebrew": embedding_matrix_he, "english": embedding_matrix_en, "links": embedding_matrix_links},
            {"hebrew": tokenizer_he, "english": tokenizer_en, "links": tokenizer_links}
        )

    def get_super_topics(self):
        return list(self.toc_mapping.keys())

    def get_sub_topics(self, super_topic):
        return self.toc_mapping[super_topic]

    def get_topics_above_count(self, count):
        return [x[0] for x in filter(lambda x: x[1] >= count, self.topic_counts.items())]

    @staticmethod
    def get_ensemble_input_for_inference(X_he, X_en, clf):
        _, X_he_seq = DataManager.get_sequenced_text(X_he, pretrained_tokenizer=clf.tokenizer_dict['hebrew'])
        _, X_en_seq = DataManager.get_sequenced_text(X_en, pretrained_tokenizer=clf.tokenizer_dict['english'])
        return {"hebrew": X_he_seq, "english": X_en_seq}

def get_data_for_classes(slug_set, X, Y):
    new_X, new_Y = zip(*list(filter(lambda x: len(set(x[1]) & slug_set) == 1, zip(X, Y))))
    new_Y = [list(set(temp_y) & slug_set)[0] for temp_y in new_Y]
    return new_X, new_Y


def get_data_for_classes_ensemble(slug_set, X, Y):
    new_X, new_Y = zip(*list(filter(lambda x: len(set(x[1]) & slug_set) == 1, zip(X, Y))))
    new_Y = [list(set(temp_y) & slug_set)[0] for temp_y in new_Y]
    return new_X, new_Y



if __name__ == "__main__":

    # dm = DataManager(DATA, EMBEDDING, EMBEDDING_SIZE)
    # print(dm.get_super_topics())
    # super_topic_clf = BinaryRelevance(CnnClf, dm.get_super_topics())
    # super_topic_clf.fit_class(1, "philosophy", dm.get_dataset_for_super_topic, epochs=N_EPOCHS, verbose=1, batch_size=BATCH_SIZE)

    # ensemble
    dm = DataManager(DATA)
    dm.load_embeddings(EMBEDDING_HE, EMBEDDING_EN, EMBEDDING_LINKS, EMBEDDING_SIZE, LINK_EMBEDDING_SIZE)


    # super_topic_clf = BinaryRelevance(CnnClfEnsemble, dm.get_super_topics())
    # super_topic_clf.fit_class(1, "biblical-figures", dm.get_ensemble_dataset_for_super_topic, epochs=N_EPOCHS, verbose=1, batch_size=BATCH_SIZE)
    
    all_topic_clf = BinaryRelevance(CnnClfEnsemble, dm.get_topics_above_count(100))
    # all_topic_clf.load_models('research/topics_cnn/cnn_models')
    all_topic_clf.fit(dm.get_ensemble_dataset_for_sub_topic, epochs=N_EPOCHS, verbose=0, batch_size=BATCH_SIZE)
    all_topic_clf.evaluate(dm.get_ensemble_dataset_for_sub_topic, verbose=0, batch_size=BATCH_SIZE, return_dict=True)


    # sub_topic_clf.fit_class(1, "abraham", dm.get_ensemble_dataset_for_sub_topic, epochs=N_EPOCHS, verbose=1, batch_size=BATCH_SIZE)


    # super_topic_clf.fit(dm.get_dataset_for_super_topic, epochs=N_EPOCHS, verbose=1, batch_size=BATCH_SIZE)
    # super_topic_clf.evaluate(dm.get_dataset_for_super_topic, batch_size=BATCH_SIZE, verbose=1, return_dict=True)
    # results = cnn.evaluate(X_test, Y_test, batch_size=BATCH_SIZE, verbose=1, return_dict=True)
    # print(super_topic, "Evaluation", str(results))
# CURRENT RESULTS
# for distinguishing b/w moses and abraham
# loss: 0.2545 - categorical_accuracy: 0.8880 - val_loss: 0.3006 - val_categorical_accuracy: 0.8844
# for binary on abraham
# loss: 0.2538 - categorical_accuracy: 0.8906 - val_loss: 0.2883 - val_categorical_accuracy: 0.8946
# 11/10/20 for binary moses
#  loss: 0.2675 - categorical_accuracy: 0.8774 - recall: 0.6000 - precision: 0.7378 - val_loss: 0.2956 - val_categorical_accuracy: 0.8668 - val_recall: 0.6912 - val_precision: 0.6599
# 11/10/20 for binary abraham
# loss: 0.2360 - categorical_accuracy: 0.9052 - recall: 0.6716 - precision: 0.8061 - val_loss: 0.2738 - val_categorical_accuracy: 0.8800 - val_recall: 0.6583 - val_precision: 0.7532
# Good article on dropout https://machinelearningmastery.com/dropout-for-regularizing-deep-neural-networks/