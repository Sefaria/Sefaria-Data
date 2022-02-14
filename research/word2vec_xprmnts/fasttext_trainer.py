import django, re, csv, srsly, json
django.setup()
from tqdm import tqdm
import fasttext
from gensim.models import Word2Vec
from gensim.models.word2vec import LineSentence

from sefaria.model import *
from sefaria.utils.hebrew import strip_cantillation
from sefaria.system.exceptions import InputError
DATA_LOC = "/home/nss/sefaria/datasets/text classification"
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
def normalize(s, lang, heavy=False):
    for k, v in unidecode_table.items():
        s = s.replace(k, v)
    s = re.sub(r"\s*<[^>]+>\s*", " ", s)
    s = re.sub(r'־', ' ', s)
    if heavy:
        s = re.sub(r'\([^)]+\)', ' ', s)
        s = re.sub(r'\[[^\]]+\]', ' ', s)
        if lang == 'he':
            s = re.sub(r'[^ \u05d0-\u05ea"\'״׳]', '', s)
        elif lang == 'en':
            s = re.sub(r'[^ a-zA-Z"\'״׳]', ' ', s)

        # remove quotations at beginning and end of words
        s = " ".join(re.sub(r'^["\'״׳]+', "", re.sub(r'["\'״׳]+$', "", word)) for word in s.split()).strip()
    else:
        s = strip_cantillation(s, strip_vowels=True)
    return s

def remove_prefixes(s):
    normalized = ""
    for word in s.split():
        word = re.sub(r"^[^|]+\|", "", word)
        normalized += ' ' + word
    return normalized

class TextWalker:

    def __init__(self, output, lang, max_line_len=None, format='txt', overlap=0):
        self.output = output
        self.lang = lang
        self.max_line_len = max_line_len
        self.format = format
        self.overlap = overlap

    def write_lines(self, text):
        text = normalize(text, self.lang)
        if self.max_line_len is None:
            self.write_text(text)
        else:
            words = text.split()
            for i in range(0, len(words), self.max_line_len - self.overlap):
                line = " ".join(words[i:i + self.max_line_len])
                self.write_text(line)

    def write_text(self, text):
        if self.format == 'jsonl':
            text = json.dumps({"text": text})
        self.output.write(text + '\n')

    def action(self, text, en_tref, he_tref, version):
        self.write_lines(text)

def export_library_as_file(lang, output_prefix, max_line_len=None, format='txt', overlap=0, webpages_text=None):
    vs = VersionSet({"language": lang})
    count = vs.count()
    fname = f"{output_prefix}/all_text_{lang}"
    if max_line_len is not None:
        fname += f"_{max_line_len}_lines"
    fname += f".{format}"
    output = open(fname, "w")
    walker = TextWalker(output, lang, max_line_len=max_line_len, format=format, overlap=overlap)
    for v in tqdm(vs, total=count):
        if v.versionTitle[-5:-3] == ' [':
            print("SKIPPING", v.versionTitle)
            continue 
        try:
            v.walk_thru_contents(walker.action)
        except InputError:
            continue
    if webpages_text is not None:
        with open(webpages_text, 'r') as fin:
            for line in fin:
                walker.write_lines(line)

    output.close()

def export_library_without_prefixes_as_file():
    output = open("all_text_he_no_prefixes_old.txt", "w")
    walker = TextWalker(output, 'he')
    with open(f"{DATA_LOC}/prefix_with_refs.json", "r") as fin:
        j = json.load(fin)
    word_count = 0
    unique_words = set()
    for ref, text in tqdm(j.items(), total=len(j)):
        text = normalize(remove_prefixes(text), 'he')
        if len(text) == 0:
            continue
        word_count += len(text.split())
        for word in text.split():
            unique_words.add(word)
        walker.write_text(text)
    output.close()
    print("Unique words:", len(unique_words))
    print("Total words:", word_count)


class BiWalker:
    def __init__(self, bi_data):
        self.bi_data = bi_data
    def action(self, text, en_tref, he_tref, version):
        if 'en' not in self.bi_data[en_tref]:
            self.bi_data[en_tref]['en'] = ''
        self.bi_data[en_tref]['en'] += normalize(text, 'en') + " "

def export_library_as_csv():
    with open(f"{DATA_LOC}/prefix_with_refs.json", "r") as fin:
        j = json.load(fin)
    from collections import defaultdict
    bi_data = defaultdict(dict)
    for ref, text in tqdm(j.items(), total=len(j)):
        text = normalize(remove_prefixes(text), 'he')
        try:
            oref = Ref(ref)
        except InputError:
            continue
        bi_data[ref]['book'] = oref.index.title
        if len(text) == 0:
            continue
        bi_data[ref]['he'] = text
    vs = VersionSet({"language": 'en'})
    count = vs.count()
    walker = BiWalker(bi_data)
    for v in tqdm(vs, total=count):
        if v.versionTitle[-5:-3] == ' [':
            continue 
        try:
            v.walk_thru_contents(walker.action)
        except InputError:
            continue
    rows = [{"Ref": ref, "He": s.get('he', ''), "En": s.get('en', ''), "Book": s.get('book', '')} for ref, s in bi_data.items() if (len(s.get('en', '')) > 0 or len(s.get('he', '')) > 0)]
    with open(f"{DATA_LOC}/en_and_he_without_prefixes.csv", "w") as fout:
        c = csv.DictWriter(fout, ["Ref", "He", "En", "Book"])
        c.writeheader()
        c.writerows(rows)


def export_links_as_file():
    ls = LinkSet().array()
    output = open("all_links.txt", "w")
    for l in tqdm(ls):
        try:
            Ref(l.refs[0])
        except InputError:
            continue
        try:
            Ref(l.refs[1])
        except InputError:
            continue
        if len(l.expandedRefs0) * len(l.expandedRefs1) > 300:
            print("SKIPPING", l.refs[0], l.refs[1])
            continue
        for ll in l.expandedRefs0:
            for mm in l.expandedRefs1:
                output.write(f"{ll}|||{mm}\n")
    # ls = None
    # for i in tqdm(library.all_index_records()):
    #     refs = i.all_segment_refs()
    #     for i in range(len(refs)-1):
    #         ref1, ref2 = refs[i:i+2]
    #         output.write(f"{ref1.normal()}|||{ref2.normal()}\n")

    output.close()

def export_responsa_as_file():
    import os
    with open('/home/nss/sefaria/datasets/general/responsa-all.txt', 'w') as fout:
        for root, dirs, files in os.walk("/home/nss/sefaria/datasets/general/responsa"):
            for name in files:
                fin = open(os.path.join(root, name), 'r')
                for line in fin:
                    if len(line.strip()) == 0 or line.startswith('### '):
                        continue
                    fout.write(line)
                fin.close()


def train_fasttext(lang, dim=100, external_file=None):
    print("FASTTEXT", dim)
    if external_file is not None:
        train_file = external_file
    else:
        train_file = "/home/nss/sefaria/datasets/general/all_text_he.txt" if lang == "he" else "/home/nss/sefaria/datasets/general/all_text_en.txt"
    model = fasttext.train_unsupervised(train_file, dim=dim, epoch=10)
    model.save_model(f"{DATA_LOC}/fasttext_{lang}_no_prefixes_{dim}.bin")

def convert_fasttext_bin_to_vec(in_path, out_path):
    # original BIN model loading
    f = fasttext.load_model(in_path)

    # get all words from model
    words = f.get_words()

    with open(out_path, 'w') as file_out:
        
        # the first line must contain number of total words and vector dimension
        file_out.write(str(len(words)) + " " + str(f.get_dimension()) + "\n")

        # line by line, you append vectors to VEC file
        for w in tqdm(words):
            v = f.get_word_vector(w)
            vstr = ""
            for vi in v:
                vstr += " " + str(vi)
            try:
                file_out.write(w + vstr+'\n')
            except:
                pass


def train_fasttext_links():
    train_file = "all_links.txt"
    model = fasttext.train_unsupervised(train_file, dim=10, epoch=10)
    model.save_model(f"{DATA_LOC}/fasttext_links.bin")

def train_word2vec(lang, dim=100):
    print("WORD2VEC", dim)
    train_file = "all_text_he_no_prefixes.txt" if lang == "he" else "all_text_en.txt"

    model = Word2Vec(LineSentence(train_file), size=dim, window=5, min_count=7, workers=12, sg=1, iter=10)
    model.save(f"{DATA_LOC}/word2vec_{lang}_no_prefixes_{dim}.bin")

def train_word2vec_links():
    train_file = "all_links.txt"
    model = Word2Vec(LineSentence(train_file), size=10, window=5, min_count=7, workers=12, sg=1, iter=10)
    model.save(f"{DATA_LOC}/word2vec_links.bin")

def train_custom_link_embedding_thingy():
    import networkx as nx
    from tqdm import tqdm
    G = nx.Graph()
    node_int_mapping = {}
    edges = []
    with open("all_links.txt", "r") as fin:
        for line in fin:
            refs = line.strip().split()
            for ref in refs:
                if ref not in node_int_mapping:
                    node_int_mapping[ref] = len(node_int_mapping)
                edges += [refs]
    for node, int_node in tqdm(node_int_mapping.items(), total=len(node_int_mapping)):
        G.add_node(int_node)
    for edge in tqdm(edges):
        G.add_edge(node_int_mapping[edge[0]], node_int_mapping[edge[1]])
    spl = dict(nx.all_pairs_shortest_path_length(G, 2))

if __name__ == "__main__":
    #export_library_as_file('he', '/home/nss/sefaria/datasets/general', max_line_len=512, overlap=50, webpages_text='/home/nss/sefaria/datasets/general/all_text_webpages_he.txt')
    #export_library_as_file('he', '/home/nss/sefaria/datasets/general', max_line_len=512, overlap=50, format='jsonl', webpages_text='/home/nss/sefaria/datasets/general/all_text_webpages_he.txt')  # for spacy pretraining
    # export_library_without_prefixes_as_file()
    # export_links_as_file()
    # train_word2vec_links()
    # train_word2vec('en', dim=20)
    # export_library_as_csv()
    #train_fasttext('he', dim=300, external_file='/home/nss/sefaria/datasets/general/all_text_he_512_lines.txt')
    convert_fasttext_bin_to_vec("/home/nss/sefaria/datasets/text classification/fasttext_he_no_prefixes_300.bin", "/home/nss/sefaria/datasets/text classification/fasttext_he_no_prefixes_300.vec")
    # train_fasttext('', dim=100, external_file='/home/nss/sefaria/datasets/general/responsa-all.txt')
    # export_responsa_as_file()
# TODO
# compare word2vec, glove, elmo
# elmo: https://github.com/allenai/bilm-tf this seems to be updated https://github.com/ltgoslo/simple_elmo_training

# graphsage implementation and tutorial: https://towardsdatascience.com/using-graphsage-to-learn-paper-embeddings-in-cora-a94bb1e9dc9d