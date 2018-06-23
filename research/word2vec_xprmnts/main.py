# encoding=utf-8

import codecs
import word2vec
from export_library_as_file import export_library_as_file, export_library_as_docs

def get_training_set():
    try:
        with codecs.open("all_of_sefaria.txt", "rb", encoding='utf8') as fin:
            assert isinstance(fin, file)
            return fin.readlines()
    except IOError:
        print "EXPORTING LIBRARY"
        export_library_as_file("all_of_sefaria.txt")
        return get_training_set()


def train_word2phrase():
    word2vec.word2phrase("all_of_sefaria.txt", "word2phrase.bin", verbose=True)


def train_word2vec():
    word2vec.word2vec("word2phrase.bin", "word2vec.bin", verbose=True)


def train_clusters():
    word2vec.word2clusters("word2phrase.bin", "word2vec.bin", 1000, verbose=True)


def train_doc2vec():
    word2vec.doc2vec("all_of_sefaria_docs.txt", "doc2vec.bin", verbose=True, cbow=0)


def get_model(filename, clusters=False):
    if clusters:
        return word2vec.load_clusters(filename)
    else:
        return word2vec.load(filename)



def get_k_similar(model, word, k=10):
    indexes, metrics = model.cosine(word, n=k)
    return model.vocab[indexes]


#export_library_as_file("all_of_sefaria.txt")
#export_library_as_docs("all_of_sefaria_docs.txt")
#train_word2phrase()
#train_word2vec()
#train_clusters()
#train_doc2vec()
model = get_model("word2vec.bin")
for w in model.vocab[:1000]:
    print u"{}: {}".format(w, u', '.join(get_k_similar(model, w).tolist()))