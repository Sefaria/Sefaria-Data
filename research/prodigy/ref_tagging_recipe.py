import prodigy, srsly, spacy, re
from spacy.tokenizer import Tokenizer
from spacy.lang.en import English
from spacy.lang.he import Hebrew
from spacy.util import minibatch, compounding
from prodigy.components.sorters import prefer_uncertain
from prodigy.components.preprocess import add_tokens, split_sentences
from db_manager import MongoProdigyDBManager
from pathlib import Path

# LABELS = ["פשוט", "שם", "דיבור המתחיל"]
LABELS = ['פשוט']

def custom_tokenizer(nlp):
    tag_re = r'<[^>]+>'
    class_re = r'<[a-z]+ class="[a-z]+">'
    prefix_re = re.compile(rf'''^(?:[\[({{:"'\u05F4\u05F3§\u05c0\u05c3]|{tag_re}|class="[a-zA-Z\-]+">)''')
    suffix_re =  re.compile(rf'''(?:[\])}}.,;:?!"'\u05F4\u05F3\u05c0\u05c3]|{tag_re})$''')
    infix_re = re.compile(rf'''([-~]|{tag_re})''')
    return Tokenizer(nlp.vocab, prefix_search=prefix_re.search,
                                suffix_search=suffix_re.search,
                                infix_finditer=infix_re.finditer,
                                token_match=None)

def test_tokenizer(nlp):

    test_text = Ref("Peninei Halakhah, Family 1:6:2").text('he').text
    tokenizer = custom_tokenizer(nlp)
    tokens = tokenizer(test_text)
    for t in tokens[-90:-70]:
        print(t)

def import_file_to_collection(input_file, collection, db_host='localhost', db_port=27017):
    my_db = MongoProdigyDBManager(db_host, db_port)
    stream = srsly.read_jsonl(input_file)
    getattr(my_db.db, collection).delete_many({})
    getattr(my_db.db, collection).insert_many(stream)

def load_model(model_dir):
    model_exists = True
    try:
        nlp = spacy.load(model_dir)
    except OSError:
        model_exists = False
        nlp = Hebrew()
    if "sentencizer" not in nlp.pipe_names:
        sentencizer = nlp.create_pipe("sentencizer")
        nlp.add_pipe(sentencizer)
    if "ner" not in nlp.pipe_names:
        ner = nlp.create_pipe("ner")
        nlp.add_pipe(ner, last=True)
    else:
        ner = nlp.get_pipe("ner")
    for label in LABELS:
        ner.add_label(label)
    if not model_exists:
        nlp.begin_training()
    # nlp.tokenizer = custom_tokenizer(nlp)
    return nlp, model_exists

def save_model(nlp, model_dir):
    model_dir = Path(model_dir)
    if not model_dir.exists():
        model_dir.mkdir()
    nlp.to_disk(model_dir)

def train_model(nlp, annotations, model_dir):
    batches = minibatch(annotations, size=compounding(4.0, 32.0, 1.001))
    for batch in batches:        
        texts = [eg["text"] for eg in batch]
        ents_list = [[(span["start"], span["end"], span["label"]) for span in eg.get("spans", [])] for eg in batch]
        annots = [{"entities": ents} for ents in ents_list]
        losses = {}
        nlp.update(texts, annots, losses=losses)  # TODO add drop=0.5
    save_model(nlp, model_dir)
    return losses

def add_model_predictions(nlp, stream):
    """
    Return new generator that wraps stream
    add model predictions to each example of stream
    """
    for example in stream:
        pred_doc = nlp(example['text'])
        pred_spans = [{"start": pred_doc[ent.start].idx, "end": pred_doc[ent.end-1].idx+len(pred_doc[ent.end-1]), "label": ent.label_} for ent in pred_doc.ents]
        example['spans'] = pred_spans
        yield example

def score_stream(nlp, stream):
    ner = nlp.get_pipe("ner")
    for example in stream:
        docs = nlp(example['text'])
        score = ner.predict(docs)
        yield (score[0], example)

@prodigy.recipe(
    "ref-tagging-recipe",
    dataset=("Dataset to save answers to", "positional", None, str),
    input_collection=("Mongo collection to input data from", "positional", None, str),
    model_dir=("Spacy model location", "positional", None, str),
    view_id=("Annotation interface", "option", "v", str),
    db_host=("Mongo host", "option", None, str),
    db_port=("Mongo port", "option", None, int),
)
def my_custom_recipe(dataset, input_collection, model_dir, view_id="text", db_host="localhost", db_port=27017):
    my_db = MongoProdigyDBManager(db_host, db_port)
    nlp, model_exists = load_model(model_dir)
    if not model_exists:
        temp_stream = getattr(my_db.db, input_collection).find({}, {"_id": 0})
        train_model(nlp, temp_stream, model_dir)
    stream = getattr(my_db.db, input_collection).find({}, {"_id": 0})
    stream = split_sentences(nlp, stream, min_length=200)
    stream = add_model_predictions(nlp, stream)
    stream = add_tokens(nlp, stream, skip=True)


    def update(annotations):
        prev_annotations = my_db.db.examples.find({}, {"_id": 0}).limit(1000).sort([("_id", -1)])
        all_annotations = list(prev_annotations) + list(annotations)
        losses = train_model(nlp, all_annotations, model_dir)
        return losses.get('ner', None)

    def progress(ctrl, update_return_value):
        return update_return_value
        #return ctrl.session_annotated / getattr(my_db.db, input_collection).count_documents({})

    return {
        "db": my_db,
        "dataset": dataset,
        "view_id": view_id,
        "stream": stream,
        "progress": progress,
        "update": update,
        "config": {
            "labels": LABELS,
            "global_css": """
                [data-prodigy-view-id='ner_manual'] .prodigy-content {
                    direction: rtl;
                    text-align: right;
                }
            """
        }
    }

if __name__ == "__main__":
    # test_tokenizer(nlp)
    import_file_to_collection('research/prodigy/data/test_input.jsonl', 'test_input')
"""
command to run
prodigy ref-tagging-recipe ref_tagging test_input research/prodigy/models/ref_tagging --view-id ner_manual -db-host localhost -db-port 27017 -F research/prodigy/ref_tagging_recipe.py
"""

"""
TODO
use on_load to update model with existing annotations? why would I do that?
use split_sentences preprocessor instead of manually splitting sentences first
use prefer_uncertain to prioritize uncertain

^^^ trying to use prefer_uncertain but gettting 
    score = ner.predict(example)
TypeError: Argument 'doc' has incorrect type (expected spacy.tokens.doc.Doc, got str)

way to find rare labels
https://support.prodi.gy/t/best-way-to-annotate-rare-labels-for-classification/1113

way to train spacy model using beam search to get confidence scores for entities
https://github.com/explosion/spaCy/issues/5915
"""