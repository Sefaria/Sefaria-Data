from typing import Callable, Iterator, List
from spacy.util import ensure_path
import spacy, re, srsly, json, csv
from tqdm import tqdm
from spacy.tokenizer import Tokenizer
from spacy.lang.he import Hebrew
from sklearn.model_selection import train_test_split
from spacy.training import Example
from spacy.language import Language

try:
    from research.prodigy.db_manager import MongoProdigyDBManager
except ImportError:
    # remote
    from db_manager import MongoProdigyDBManager


@spacy.registry.readers("mongo_reader")
def stream_data(db_host: str, db_port: int, input_collection: str, output_collection: str, random_state: int, train_perc: float, corpus_type: str, min_len: int) -> Callable[[Language], Iterator[Example]]:
    my_db = MongoProdigyDBManager(output_collection, db_host, db_port)
    def generate_stream(nlp):
        data = [d for d in getattr(my_db.db, input_collection).find({}) if len(d['text']) > min_len]
        # make data unique
        data = list({(tuple(sorted(d['meta'].items(), key=lambda x: x[0])), d['text']): d for d in data}.values())
        print("Num examples", len(data))
        if random_state == -1:
            train_data, test_data = (data, []) if corpus_type == "train" else ([], data)
        else:
            train_data, test_data = train_test_split(data, random_state=random_state, train_size=train_perc)
        corpus_data = train_data if corpus_type == "train" else test_data
        for raw_example in corpus_data:
            doc = nlp.make_doc(raw_example['text'])
            doc.user_data = raw_example['meta']
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
            "fn": [list(ent) for ent in temp_fn],
            "ref": example.predicted.user_data['Ref']
        }]
    
    srsly.write_jsonl(f"{output_folder}/doc_evaluation.jsonl", output_json)
    make_evaluation_html(output_json, output_folder, 'doc_evaluation.html')
    return tp, fp, tn, fn

def export_tagged_data_as_html(tagged_data, output_folder):
    output_json = []
    for example in tagged_data:
        ents_x2y = example.get_aligned_spans_x2y(example.reference.ents)
        output_json += [{
            "text": example.text,
            "tp": [[span.start_char, span.end_char, span.label_] for span in ents_x2y],
            "fp": [],
            "fn": [],
            "ref": example.predicted.user_data['Ref']
        }]
    make_evaluation_html(output_json, output_folder, 'doc_export.html')

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

def wrap_chars_with_overlaps(s, chars_to_wrap, get_wrapped_text):
    chars_to_wrap.sort(key=lambda x: (x[0],x[0]-x[1]))
    for i, (start, end, metadata) in enumerate(chars_to_wrap):
        wrapped_text, start_added, end_added = get_wrapped_text(s[start:end], metadata)
        s = s[:start] + wrapped_text + s[end:]
        for j, (start2, end2, metadata2) in enumerate(chars_to_wrap[i+1:]):
            if start2 > end:
                start2 += end_added
            start2 += start_added
            if end2 > end:
                end2 += end_added
            end2 += start_added
            chars_to_wrap[i+j+1] = (start2, end2, metadata2)
    return s

def make_evaluation_html(data, output_folder, output_filename):
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
        .label { font-weight: bold; font-size: 75%; color: #666; padding-right: 5px; }
        </style>
      </head>
      <body>
    """
    def get_wrapped_text(mention, metadata):
        start = f'<span class="{metadata["true condition"]} tag">'
        end = f'<span class="label">{metadata["label"]}</span></span>'
        return f'{start}{mention}{end}', len(start), len(end)
    for i, d in enumerate(data):
        chars_to_wrap  = [(s, e, {"label": l, "true condition": 'tp'}) for (s, e, l) in d['tp']]
        chars_to_wrap += [(s, e, {"label": l, "true condition": 'fp'}) for (s, e, l) in d['fp']]
        chars_to_wrap += [(s, e, {"label": l, "true condition": 'fn'}) for (s, e, l) in d['fn']]
        wrapped_text = wrap_chars_with_overlaps(d['text'], chars_to_wrap, get_wrapped_text)
        html += f"""
        <p class="ref">{i}) {d['ref']}</p>
        <p dir="rtl" class="doc">{wrapped_text}</p>
        """
    html += """
      </body>
    </html>
    """
    with open(f"{output_folder}/{output_filename}", "w") as fout:
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
    nlp = spacy.load('./research/prodigy/output/sub_citation/model-best')
    data = stream_data('localhost', 27017, 'gilyon_sub_citation_output', 'gilyon_input', 613, 0.8, 'test', 0)(nlp)
    print(make_evaluation_files(data, nlp, './research/prodigy/output/evaluation_results'))

    # data = stream_data('localhost', 27017, 'gilyon_sub_citation_output', 'gilyon_input', -1, 1.0, 'train', 0)(nlp)
    # export_tagged_data_as_html(data, './research/prodigy/output/evaluation_results')
    convert_jsonl_to_json('./research/prodigy/output/evaluation_results/doc_evaluation.jsonl')
    # convert_jsonl_to_csv('./research/prodigy/output/evaluation_results/doc_evaluation.jsonl')
    # spacy.training.offsets_to_biluo_tags(doc, entities)
"""
to run gpu
python -m spacy train ./research/prodigy/configs/ref_tagging.cfg --output ./research/prodigy/output/ref_tagging --code ./research/prodigy/functions.py --gpu-id 0

to run cpu
python -m spacy train ./research/prodigy/configs/ref_tagging_cpu.cfg --output ./research/prodigy/output/ref_tagging_cpu --code ./research/prodigy/functions.py --gpu-id 0
600 segments
 69    5000          0.36      0.03   71.26   72.94   69.66    0.71 (0.71, 0.66)
0.71

to train sub citation
python -m spacy train ./research/prodigy/configs/sub_citation.cfg --output ./research/prodigy/output/sub_citation --code ./research/prodigy/functions.py --gpu-id 0

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