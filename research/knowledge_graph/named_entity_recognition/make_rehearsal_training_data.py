"""
Makes training data based on current model to
prevent model from "catastrophic forgetting"!
See: https://explosion.ai/blog/pseudo-rehearsal-catastrophic-forgetting
"""
import random
import srsly
import spacy
import re
import django
django.setup()
from pathlib import Path
from functools import partial
from tqdm import tqdm
from unidecode import unidecode
from sefaria.model import *
from spacy.gold import GoldParse
from spacy.util import minibatch, compounding

TRAIN_DATA = list(filter(lambda x: len(x[0]) > 0, srsly.read_jsonl('training/naive_training.jsonl')))


def read_raw_data(nlp, jsonl_loc):
    for text in srsly.read_jsonl(jsonl_loc):
        if text.strip():
            doc = nlp.make_doc(text)
            yield doc


def read_gold_data(nlp, gold_loc):
    docs = []
    golds = []
    for json_obj in srsly.read_jsonl(gold_loc):
        doc = nlp.make_doc(json_obj["text"])
        ents = [(ent["start"], ent["end"], ent["label"]) for ent in json_obj["spans"]]
        gold = GoldParse(doc, entities=ents)
        docs.append(doc)
        golds.append(gold)
    return list(zip(docs, golds))


def normalize_text(lang, text):
    text = TextChunk._strip_itags(text)
    text = re.sub('<[^>]+>', ' ', text)
    if lang == 'en':
        text = unidecode(text)
        text = re.sub('\([^)]+\)', ' ', text)
        text = re.sub('\[[^\]]+\]', ' ', text)
    text = ' '.join(text.split())
    return text


def make_raw_data(jsonl_loc):
    categories = ['Tanakh', 'Mishnah']
    books = ['Midrash Tanchuma', 'Pirkei DeRabbi Eliezer', 'Sifra', 'Sifrei Bamidbar', 'Sifrei Devarim',
             'Mishneh Torah, Foundations of the Torah', 'Mishneh Torah, Human Dispositions',
             'Mishneh Torah, Reading the Shema', 'Mishneh Torah, Sabbath', 'Avot D\'Rabbi Natan',
             'Guide for the Perplexed', 'Nineteen Letters', 'Collected Responsa in Wartime',
             'Contemporary Halakhic Problems, Vol I', 'Contemporary Halakhic Problems, Vol II',
             'Contemporary Halakhic Problems, Vol III', 'Contemporary Halakhic Problems, Vol IV', 'Depths of Yonah',
             'Likutei Moharan', 'Kedushat Levi', 'Messilat Yesharim', 'Orchot Tzadikim', 'Shemirat HaLashon']
    for cat in categories:
        books += library.get_indexes_in_category(cat)
    data = []
    for b in tqdm(books):
        i = library.get_index(b)
        default_en = None
        for v in i.versionSet():
            if v.language == 'en':
                default_en = v
                break
        if default_en is None:
            continue

        def action(data, temp_text, tref, heTref, self):
            data += [normalize_text('en', temp_text)]
        default_en.walk_thru_contents(partial(action, data))
    srsly.write_jsonl(jsonl_loc, data)


def convert_training_to_displacy(jsonl_loc):
    out = []
    for text, tags in srsly.read_jsonl(jsonl_loc):
        out += [{
            'text': text,
            'ents': sorted([{'start': s, 'end': e, 'label': l} for s, e, l in tags['entities']], key=lambda x: x['start'])
        }]
    srsly.write_jsonl(jsonl_loc + '.displacy', out)


def display_displacy(jsonl_loc):
    jsonl_data = list(filter(lambda x: len(x['text']) > 0, srsly.read_jsonl(jsonl_loc)))
    spacy.displacy.serve(jsonl_data, style='ent', manual=True)


def main(model_name, unlabelled_loc, output_dir):
    n_iter = 9
    dropout = 0.2
    batch_size = 4
    nlp = spacy.load(model_name)
    print("Loaded model '%s'" % model_name)
    raw_docs = list(read_raw_data(nlp, unlabelled_loc))
    optimizer = nlp.resume_training()
    # Avoid use of Adam when resuming training. I don't understand this well
    # yet, but I'm getting weird results from Adam. Try commenting out the
    # nlp.update(), and using Adam -- you'll find the models drift apart.
    # I guess Adam is losing precision, introducing gradient noise?
    optimizer.alpha = 0.1
    optimizer.b1 = 0.0
    optimizer.b2 = 0.0

    # get names of other pipes to disable them during training
    pipe_exceptions = ["ner", "trf_wordpiecer", "trf_tok2vec"]
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe not in pipe_exceptions]
    sizes = compounding(1.0, 4.0, 1.001)
    with nlp.disable_pipes(*other_pipes):
        for itn in tqdm(range(n_iter), total=n_iter):
            random.shuffle(TRAIN_DATA)
            random.shuffle(raw_docs)
            losses = {}
            r_losses = {}
            # batch up the examples using spaCy's minibatch
            raw_batches = minibatch(raw_docs, size=batch_size)
            for batch in minibatch(TRAIN_DATA, size=sizes):
                docs, golds = zip(*batch)
                nlp.update(docs, golds, sgd=optimizer, drop=dropout, losses=losses)
                try:
                    raw_batch = list(next(raw_batches))
                except StopIteration:
                    break
                nlp.rehearse(raw_batch, sgd=optimizer, losses=r_losses)
            print("Losses", losses)
            print("R. Losses", r_losses)
    # save model to output directory
    if output_dir is not None:
        output_dir = Path(output_dir)
        if not output_dir.exists():
            output_dir.mkdir()
        nlp.to_disk(output_dir)
        print("Saved model to", output_dir)


if __name__ == "__main__":
    # make_raw_data('training/raw_rehearsal_data.jsonl')
    # main("en_core_web_lg", "training/raw_rehearsal_data.jsonl", "models/talmud_ner")
    pass
