from typing import Callable, Iterator, List

from spacy.util import ensure_path
from research.prodigy.db_manager import MongoProdigyDBManager
import spacy, re, srsly, json, csv
from tqdm import tqdm
from spacy.tokenizer import Tokenizer
from spacy.lang.he import Hebrew
from sklearn.model_selection import train_test_split
from spacy.training import Example
from spacy.language import Language

@spacy.registry.readers("mongo_reader")
def stream_data(db_host: str, db_port: int, collection: str, random_state: int, train_perc: float, corpus_type: str) -> Callable[[Language], Iterator[Example]]:
    my_db = MongoProdigyDBManager(db_host, db_port)
    def generate_stream(nlp):
        data = [d for d in getattr(my_db.db, collection).find({}) if len(d['text']) > 20]
        # make data unique
        data = list({(d['meta']['Ref'], d['text']): d for d in data}.values())
        train_data, test_data = train_test_split(data, random_state=random_state, train_size=train_perc)
        corpus_data = train_data if corpus_type == "train" else test_data
        for raw_example in corpus_data:
            doc = nlp.make_doc(raw_example['text'])
            entities = [(span['start'], span['end'], span['label']) for span in raw_example['spans']]
            example = Example.from_dict(doc, {"entities": entities})
            yield example

    return generate_stream

@spacy.registry.tokenizers("custom_tokenizer")
def custom_tokenizer_factory():
    def custom_tokenizer(nlp):
        tag_re = r'<[^>]+>'
        class_re = r'<[a-z]+ class="[a-z]+">'
        prefix_re = re.compile(rf'''^(?:[\[({{:"'\u05F4\u05F3§\u05c0\u05c3]|{tag_re}|class="[a-zA-Z\-]+">)''')
        suffix_re =  re.compile(rf'''(?:[\])}}.,;:?!"'\u05F4\u05F3\u05c0\u05c3]|{tag_re})$''')
        infix_re = re.compile(rf'''([-~]|{tag_re})''')
        tokenizer = Tokenizer(nlp.vocab, prefix_search=prefix_re.search,
                                    suffix_search=suffix_re.search,
                                    infix_finditer=infix_re.finditer,
                                    token_match=None)
        return tokenizer
    return custom_tokenizer

def make_evaluation_files(evaluation_data, ner_model, output_folder):
    tp,fp,fn,tn = 0,0,0,0
    data_tuples = [(eg.text, eg) for eg in evaluation_data]
    output_json = []
    # see https://spacy.io/api/language#pipe
    for doc, example in tqdm(ner_model.pipe(data_tuples, as_tuples=True)):
        # correct_ents
        ents_x2y = example.get_aligned_spans_x2y(example.reference.ents)
        correct_ents = [(e.start_char, e.end_char, e.label_) for e in ents_x2y]
        # predicted_ents
        ents_x2y = example.get_aligned_spans_x2y(doc.ents)
        predicted_ents = [(e.start_char, e.end_char, e.label_) for e in ents_x2y]
        # false positives
        temp_fp = [ent for ent in predicted_ents if ent not in correct_ents]
        fp += len(temp_fp)
        # true positives
        temp_tp = [ent for ent in predicted_ents if ent in correct_ents]
        tp += len(temp_tp)
        # false negatives
        temp_fn = [ent for ent in correct_ents if ent not in predicted_ents]
        fn += len(temp_fn)
        # true negatives
        temp_tn = [ent for ent in correct_ents if ent in predicted_ents]
        tn += len(temp_tn)
        output_json += [{
            "text": doc.text,
            "tp": [list(ent) for ent in temp_tp],
            "fp": [list(ent) for ent in temp_fp],
            "fn": [list(ent) for ent in temp_fn]
        }]
    
    srsly.write_jsonl(f"{output_folder}/doc_evaluation.jsonl", output_json)
    make_evaluation_html(output_json, output_folder)
    return tp, fp, tn, fn

def wrap_chars(s, chars_to_wrap, get_wrapped_text):
    dummy_char = "█"
    char_list = list(s)
    start_char_to_slug = {}
    for start, end, metadata in chars_to_wrap:
        mention = s[start:end]
        start_char_to_slug[(start, end)] = (mention, metadata)
        char_list[start:end] = list(dummy_char*(end-start))
    dummy_text = "".join(char_list)

    def repl(match):
        try:
            mention, metadata = start_char_to_slug[(match.start(), match.end())]
        except KeyError:
            return match.group()
        return f"""{get_wrapped_text(mention, metadata)}"""
    return re.sub(fr"{dummy_char}+", repl, dummy_text)

def make_evaluation_html(data, output_folder):
    html = """
    <html>
      <head>
        <style>
        body { max-width: 800px; margin-right: auto; margin-left: auto; }
        .doc { line-height: 200%; border-bottom: 2px black solid; padding-bottom: 20px; }
        .tag { padding: 5px; }
        .tp { background-color: greenyellow; border: 5px lightgreen solid; }
        .fp { background-color: pink; border: 5px lightgreen solid; }
        .fn { background-color: greenyellow; border: 5px pink solid; }
        </style>
      </head>
      <body>
    """
    def get_wrapped_text(mention, metadata):
        return f'<span class="{metadata} tag">{mention}</span>'
    for d in data:
        chars_to_wrap  = [(s, e, 'tp') for (s, e, _) in d['tp']]
        chars_to_wrap += [(s, e, 'fp') for (s, e, _) in d['fp']]
        chars_to_wrap += [(s, e, 'fn') for (s, e, _) in d['fn']]
        wrapped_text = wrap_chars(d['text'], chars_to_wrap, get_wrapped_text)
        html += f"""
        <p dir="rtl" class="doc">{wrapped_text}</p>
        """
    html += """
      </body>
    </html>
    """
    with open(f"{output_folder}/doc_evaluation.html", "w") as fout:
        fout.write(html)

def convert_jsonl_to_json(filename):
    j = list(srsly.read_jsonl(filename))
    with open(filename[:-1], 'w') as fout:
        json.dump(j, fout, ensure_ascii=False, indent=2)

def get_window_around_match(start, end, text, window=10):
    before_window, after_window = '', ''

    before_text = text[:start]
    before_window_words = list(filter(lambda x: len(x) > 0, before_text.split()))[-window:]
    before_window = " ".join(before_window_words)

    after_text = text[end:]
    after_window_words = list(filter(lambda x: len(x) > 0, after_text.split()))[:window]
    after_window = " ".join(after_window_words)

    return before_window, after_window

def convert_jsonl_to_csv(filename):
    j = srsly.read_jsonl(filename)
    rows = []
    for d in j:
        algo_guesses = {(s, e) for s, e, _ in (d['fp'] + d['tp'])}
        false_negs = {(s, e) for s, e, _ in d['fn']}
        all_algo_inds = set()
        for start, end in algo_guesses:
            all_algo_inds |= set(range(start, end))
        missed_tags = set()
        for start, end in false_negs:
            temp_inds = set(range(start, end))
            if len(temp_inds & all_algo_inds) == 0:
                missed_tags.add((start, end))
        for algo_missed, temp_data in zip(['n', 'y'], [algo_guesses, missed_tags]):
            for start, end in temp_data:
                before, after = get_window_around_match(start, end, d['text'])
                match = d['text'][start:end]
                rows += [{
                    "Before": before,
                    "After": after,
                    "Citation": match,
                    "Algorithm Missed": algo_missed
                }]

    with open(filename[:-5] + '.csv', 'w') as fout:
        c = csv.DictWriter(fout, ['Type','Correct?', 'Algorithm Missed','After', 'Citation', 'Before'])
        c.writeheader()
        c.writerows(rows)

if __name__ == "__main__":
    # nlp = spacy.load('./research/prodigy/output/ref_tagging_cpu/model-last')
    # data = stream_data('localhost', 27017, 'examples', 613, 0.8, 'test')(nlp)
    # print(make_evaluation_files(data, nlp, './research/prodigy/output/evaluation_results'))
    # convert_jsonl_to_json('./research/prodigy/output/evaluation_results/doc_evaluation.jsonl')
    convert_jsonl_to_csv('./research/prodigy/output/evaluation_results/doc_evaluation.jsonl')
    # spacy.training.offsets_to_biluo_tags(doc, entities)
"""
to run gpu
python -m spacy train ./research/prodigy/configs/ref_tagging.cfg --output ./research/prodigy/output/ref_tagging --code ./research/prodigy/functions.py --gpu-id 0

to run cpu
python -m spacy train ./research/prodigy/configs/ref_tagging_cpu.cfg --output ./research/prodigy/output/ref_tagging_cpu --code ./research/prodigy/functions.py --gpu-id 0
 21    6600        373.19     42.73   57.39   61.05   54.15    0.57
 
debug data
python -m spacy debug data ./research/prodigy/configs/ref_tagging.cfg -c ./research/prodigy/functions.py

pretrain cpu
python -m spacy pretrain ./research/prodigy/configs/ref_tagging_cpu.cfg ./research/prodigy/ref_tagging_cpu --code ./research/prodigy/functions.py --gpu-id 0

convert fasttext vectors
python -m spacy init vectors he "/home/nss/sefaria/datasets/text classification/fasttext_he_no_prefixes_300.vec" "/home/nss/sefaria/datasets/text classification/prodigy/dim300" --verbose

pretrain process
- download latest mongodump
- export to jsonl file. see fasttext_trainer.export_library_as_file
- train fasttext. see fasttext_trainer.train_fasttext
- convert fasttext to .vec file. see fasttext_trainer.convert_fasttext_bin_to_vec
- run "convert fasttext vectors" above
- run "pretrain cpu" above

"""