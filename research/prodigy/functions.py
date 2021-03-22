from typing import Callable, Iterator, List
from research.prodigy.db_manager import MongoProdigyDBManager
import spacy, re
from spacy.tokenizer import Tokenizer
from spacy.lang.he import Hebrew
from sklearn.model_selection import train_test_split
from spacy.training import Example
from spacy.language import Language

@spacy.registry.readers("mongo_reader")
def stream_data(db_host: str, db_port: int, collection: str, random_state: int, train_perc: float, corpus_type: str) -> Callable[[Language], Iterator[Example]]:
    my_db = MongoProdigyDBManager(db_host, db_port)
    def generate_stream(nlp):
        data = list(getattr(my_db.db, collection).find({}))
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

if __name__ == "__main__":
    nlp = Hebrew()
    text = "והא לית ליה טהרה במקוה - תימה דבסוף כיצד הרגל (ב\"ק דף כה:)"
    entities = [(47, 57, 'מקור')]
    tokenizer = custom_tokenizer(nlp)
    tokens = tokenizer(text)
    for i in range(len(tokens)):
        print(tokens[i])
    # spacy.training.offsets_to_biluo_tags(doc, entities)
"""
to run
python -m spacy train ./research/prodigy/configs/ref_tagging.cfg --output ./research/prodigy/output/ref_tagging --code ./research/prodigy/functions.py --gpu-id 0

debug data
python -m spacy debug data ./research/prodigy/configs/ref_tagging.cfg -c ./research/prodigy/functions.py

pretrain cpu
python -m spacy pretrain ./research/prodigy/configs/ref_tagging_cpu.cfg ./research/prodigy/ref_tagging_cpu --code ./research/prodigy/functions.py
"""