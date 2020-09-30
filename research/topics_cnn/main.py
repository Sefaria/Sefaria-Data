import django, json, csv, re, sklearn, sys, fasttext, random
django.setup()
import numpy as np
from tqdm import tqdm
import tensorflow as tf
import tensorview as tv
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
EMBEDDING = "/home/nss/sefaria/datasets/text classification/fasttext_he_no_prefixes_20.bin"
MAX_DOCUMENT_LENGTH = 100
EMBEDDING_SIZE = 20
WINDOW_SIZE = EMBEDDING_SIZE
STRIDE = int(WINDOW_SIZE/2)
N_EPOCHS = 120
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

class BinaryRelevance:
    def __init__(self, clf_klass, klasses, clf_params=None):
        self.clf_klass = clf_klass
        clf_params = clf_params or {}
        self.clf_params = clf_params
        self.klasses = klasses
        self.models = {}
        self.test_sets = {}
    
    def fit(self, get_dataset_for_klass, **clf_fit_kwargs):
        for iklass, klass in enumerate(self.klasses):
            print("KLASS", klass)
            self.fit_class(iklass, klass, get_dataset_for_klass, **clf_fit_kwargs)

    def fit_class(self, iklass, klass, get_dataset_for_klass, **clf_fit_kwargs):
        X_train, X_test, Y_train, Y_test, embedding_matrix = get_dataset_for_klass(klass)
        self.test_sets[klass] = (X_test, Y_test)
        temp_clf = self.clf_klass(str(iklass), klass, embedding_matrix, **self.clf_params)
        results = temp_clf.fit(X_train, Y_train, validation_data=(X_test, Y_test), **clf_fit_kwargs)
        self.models[klass] = temp_clf

    def evaluate(self, get_dataset_for_klass, **clf_evaluate_kwargs):
        for iklass, klass in enumerate(self.klasses):
            print("KLASS", klass)
            X_test, Y_test = self.test_sets[klass]
            #_, X_test, _, Y_test, _ = get_dataset_for_klass(klass)
            temp_clf = self.models[klass]
            results = temp_clf.evaluate(X_test, Y_test, **clf_evaluate_kwargs)
            print("RESULTS", klass, results)
            # TODO what to do with results?
    
class DataManager:

    def __init__(self, data_file, embedding_file, embedding_size):
        X, Y = self.load_data(data_file)
        self.X = X
        self.Y = Y
        self.embedding_model = fasttext.load_model(embedding_file)
        self.embedding_size = embedding_size
        self.toc_mapping = self.get_toc_mapping()


    def load_data(self, data_file):
        X, Y = [], []
        with open(data_file, "r") as fin:
            c = csv.DictReader(fin)
            for row in c:
                temp_x = DataManager.get_training_x(row)
                temp_y = DataManager.get_training_y(row)
                if not temp_x:
                    continue
                X += [temp_x]
                Y += [temp_y]            
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

    def get_train_test_sets(self, X, Y):
        tokenizer = preprocessing.text.Tokenizer(oov_token="<UNK>")
        tokenizer.fit_on_texts(X)
        embedding_matrix = self.get_embedding_matrix(tokenizer)
        X_seq = tokenizer.texts_to_sequences(X)
        X_seq = preprocessing.sequence.pad_sequences(X_seq, maxlen=MAX_DOCUMENT_LENGTH, padding='post', truncating='post')
        X_train, X_test, Y_train, Y_test = train_test_split(X_seq, np.asarray(Y), test_size=TEST_SIZE)
        return X_train, X_test, Y_train, Y_test, embedding_matrix

    @staticmethod
    def get_training_x(row):
        return DataManager.clean_text(row["He_prefixed"])

    @staticmethod
    def get_training_y(row):
        return row["Topics"].split()

    @staticmethod
    def normalize(s):
        for k, v in unidecode_table.items():
            s = s.replace(k, v)
        s = re.sub(r"<[^>]+>", " ", s)
        s = re.sub(r'־', ' ', s)
        s = re.sub(r'\([^)]+\)', '', s)
        s = re.sub(r'\[[^\]]+\]', '', s)
        s = re.sub(r'[^ \u05d0-\u05ea"\'״׳]', '', s)
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
    def clean_text(s):
        return DataManager.normalize(DataManager.remove_prefixes(s))

    def get_embedding_matrix(self, tokenizer):
        embedding_matrix = np.zeros((len(tokenizer.word_index)+1, self.embedding_size))
        for word, i in tqdm(tokenizer.word_index.items(), desc="Filling in embedding matrix"):
            embedding = self.embedding_model.get_word_vector(word)
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

    def get_super_topics(self):
        return list(self.toc_mapping.keys())


def get_data_for_classes(slug_set, X, Y):
    new_X, new_Y = zip(*list(filter(lambda x: len(set(x[1]) & slug_set) == 1, zip(X, Y))))
    new_Y = [list(set(temp_y) & slug_set)[0] for temp_y in new_Y]
    return new_X, new_Y



if __name__ == "__main__":

    dm = DataManager(DATA, EMBEDDING, EMBEDDING_SIZE)
    print(dm.get_super_topics())
    super_topic_clf = BinaryRelevance(CnnClf, dm.get_super_topics())
    super_topic_clf.fit_class(1, "philosophy", dm.get_dataset_for_super_topic, epochs=N_EPOCHS, verbose=1, batch_size=BATCH_SIZE)
    # super_topic_clf.fit(dm.get_dataset_for_super_topic, epochs=N_EPOCHS, verbose=1, batch_size=BATCH_SIZE)
    # super_topic_clf.evaluate(dm.get_dataset_for_super_topic, batch_size=BATCH_SIZE, verbose=1, return_dict=True)
    # results = cnn.evaluate(X_test, Y_test, batch_size=BATCH_SIZE, verbose=1, return_dict=True)
    # print(super_topic, "Evaluation", str(results))
# CURRENT RESULTS
# for distinguishing b/w moses and abraham
# loss: 0.2545 - categorical_accuracy: 0.8880 - val_loss: 0.3006 - val_categorical_accuracy: 0.8844
# for binary on abraham
# loss: 0.2538 - categorical_accuracy: 0.8906 - val_loss: 0.2883 - val_categorical_accuracy: 0.8946


# Good article on dropout https://machinelearningmastery.com/dropout-for-regularizing-deep-neural-networks/