from collections import defaultdict
import re, json, csv, srsly
from tqdm import tqdm
import django
django.setup()
from sefaria.model import *
from functools import reduce
from research.prodigy.prodigy_package.db_manager import MongoProdigyDBManager
from research.prodigy.prodigy_package.recipes import load_model
from research.prodigy.functions import custom_tokenizer_factory

def dh_filter(span_text, span):
    return re.search(r"\u05d3(?:\"|''|\u05f4|\u05f3\u05f3)\u05d4", span_text) is not None

def paren_at_end_filter(span_text, span):
    return re.search(r"[\)\]]$", span_text) is not None

def make_csv_by_filter(input_collection, output_file, filter_func):
    rows = []
    my_db = MongoProdigyDBManager('blah')
    max_token_len = 0
    for doc in getattr(my_db.db, input_collection).find({}):
        for span in doc['spans']:
            span_text = doc['text'][span['start']:span['end']]
            is_relevant = filter_func(span_text, span)
            if not is_relevant:
                continue
            for is_text in (True, False):
                temp_row = {
                    "Text": span_text if is_text else '',
                    "Ref": doc['meta']['Ref'],
                }
                token_len = span['token_end'] - span['token_start'] + 1
                if token_len > max_token_len:
                    max_token_len = token_len
                for i, itoken in enumerate(range(span['token_start'], span['token_end']+1)):
                    token = doc['tokens'][itoken]
                    temp_row[f'Token {i}'] = token['text'] if is_text else f'{token["start"]}|{token["end"]}|{token["id"]}'
                rows += [temp_row]
    with open(output_file, 'w') as fout:
        c = csv.DictWriter(fout, ['Ref', 'Text'] + [f'Token {i}' for i in range(max_token_len)])
        c.writeheader()
        c.writerows(rows)

def modify_data_based_on_csv(in_file, input_collection, output_collection):
    my_db = MongoProdigyDBManager(output_collection)
    docs = getattr(my_db.db, input_collection).find({})
    span_map = defaultdict(list)
    input_keys = set()
    with open(in_file, 'r') as fin:
        rows = csv.DictReader(fin)
        for text_row in rows:
            num_row = next(rows)
            start, end, token_start = num_row["Token 0"].split('|')
            token_end = token_start
            key = f'{text_row["Ref"]}|{text_row["Text"]}|{start}|{token_start}'
            icol = 0
            while True:
                col_data = num_row.get(f'Token {icol}', None)
                if col_data is None or len(col_data) == 0:
                    break
                
                _, end, token_end = col_data.split('|')
                icol += 1
            span_map[key] += [(start, end, token_start, token_end)]
            input_keys.add(key)
    used_keys = set()
    getattr(my_db.db, output_collection).delete_many({})
    for doc in docs:
        for span in doc['spans']:
            full_text = doc['text'][span['start']:span['end']]
            key = f'{doc["meta"]["Ref"]}|{full_text}|{span["start"]}|{span["token_start"]}'
            span_list = span_map[key]
            if len(span_list) == 1:
                start, end, token_start, token_end = span_list[0]
                span['start'] = int(start)
                span['end'] = int(end)
                span['token_start'] = int(token_start)
                span['token_end'] = int(token_end)
                used_keys.add(key)
        getattr(my_db.db, output_collection).insert_one(doc)
    for key in input_keys:
        if key not in used_keys:
            print("unused", key)

def move_binary_output_to_own_collection():
   my_db = MongoProdigyDBManager('blah')
   binary_output = list(my_db.db.examples2_output.find({"_view_id": "ner"}))
   my_db.db.examples2_binary.insert_many(binary_output)

def get_all_sequence_match_inds(seq, words):
    seq_str = "$$$".join(seq)
    word_str = "$$$".join(words)
    match_inds = []
    match_start_char = 0
    while True:
        try:
            start_char = seq_str.index(word_str, match_start_char)
            if start_char > 0:
                # safe to add $$$ to force beginning of word match
                # TODO too lazy to deal with end of word. not relevant right now.
                start_char = seq_str.index("$$$" + word_str, match_start_char)
                start_char += 3
            match_start_char = start_char + len(word_str)
            start_ind = seq_str[:start_char].count("$$$")
            end_ind = start_ind + len(words)
            match_inds += [(start_ind, end_ind)]
        except ValueError:
            break
    return match_inds


def fix_perek():
    db_mng = MongoProdigyDBManager("Copy_of_examples2_output")
    curr_ref = None
    nlp, model_exists = load_model('./research/prodigy/output/ref_tagging_cpu/model-last', ['מקור'])
    tokenizer = custom_tokenizer_factory()(nlp)
    with open("/home/nss/Downloads/fix_perek.txt", "r") as fin:
        for line in fin:
            line=line.strip()
            if curr_ref is None:
                curr_ref = line
            elif len(line) == 0:
                curr_ref = None
            else:
                doc = db_mng.output_collection.find_one({"meta.Ref": curr_ref})
                if doc is None:
                    print("oh no", curr_ref)
                mult_split = line.split('x')
                if len(mult_split) == 1:
                    mult = 1
                else:
                    line, mult = mult_split
                    mult = int(mult)
                words = [t.text for t in tokenizer(line)]
                already_matched_inds = reduce(lambda a, b: a | b, [set(range(span['token_start'], span['token_end'])) for span in doc['spans']], set())
                match_inds = get_all_sequence_match_inds([t['text'] for t in doc['tokens']], words)
                match_inds = list(filter(lambda x: len(set(range(x[0], x[1])) & already_matched_inds) == 0, match_inds))
                if len(match_inds) > mult:
                    print(line, curr_ref, words, mult)
                    continue
                # All checks have passed! Do edit
                for token_start, token_end in match_inds:
                    start_token = next(x for x in doc['tokens'] if x['id'] == token_start)
                    end_token = next(x for x in doc['tokens'] if (x['id'] == token_end-1))
                    doc['spans'] += [{
                        "label": "מקור",
                        "start": start_token['start'],
                        "end": end_token['end'],
                        "token_start": token_start,
                        "token_end": token_end-1  # classic off-by-one...
                    }]
                db_mng.output_collection.update_one({"_id": doc['_id']}, {"$set": {"spans": doc['spans']}})


def fix_ids(in_file, host='localhost', port=27017, collection='silver_output_binary'):
    from pymongo import MongoClient
    from bson import ObjectId
    client = MongoClient(host, port)
    db = getattr(client, 'prodigy')
    with open(in_file, 'r') as fin:
        for line in fin:
            line = line.strip()
            if len(line) == 0: continue
            splitted = line.split()
            _id = splitted[0]
            answer = "reject"
            if len(splitted) > 1 and splitted[1] == "GOOD":            
                answer = "accept"
            doc = getattr(db, collection).find_one({"_id": ObjectId(_id)})
            if doc is None:
                print(f"_id {_id} doesnt exists")
                continue
            if doc['answer'] == answer:
                print(f"_id {_id} already has answer {answer}")
                continue
            doc['answer'] = answer
            getattr(db, collection).replace_one({"_id": ObjectId(_id)}, doc)

def merge_gold_full_into_silver_binary():
    import random
    gold_db = MongoProdigyDBManager("gold_output_full")
    silver_db = MongoProdigyDBManager("silver_output_binary")
    for gold in gold_db.output_collection.find({}):
        gold['_view_id'] = 'ner'
        spans = set()
        for ispan, span in enumerate(gold['spans']):
            binary_gold = gold.copy()
            binary_gold['spans'] = [span]
            if ispan > 0:
                del binary_gold['tokens']
            del binary_gold['_id']
            silver_db.output_collection.insert_one(binary_gold)
            spans.add((span['token_start'], span['token_end']))
        new_spans = []
        while len(new_spans) < len(gold['tokens'])/100:
            if len(gold['tokens']) < 20: break
            rand_token_start = random.choice(range(len(gold['tokens'])-6))
            new_span = (rand_token_start, rand_token_start+random.choice(range(3,6)))
            if new_span in spans or new_span[1] >= len(gold['tokens']): continue
            spans.add(new_span)
            new_spans += [new_span]
            binary_gold = gold.copy()
            start_char = next(x for x in gold['tokens'] if x['id'] == new_span[0])
            end_char = next(x for x in gold['tokens'] if (x['id'] == new_span[1]))
            binary_gold['spans'] = [{
                "start" : start_char['start'], 
                "end" : end_char['end'], 
                "token_start" : new_span[0], 
                "token_end" : new_span[1], 
                "label" : "מקור"
            }]
            del binary_gold['tokens']
            del binary_gold['_id']
            binary_gold['answer'] = 'reject'
            silver_db.output_collection.insert_one(binary_gold)            
if __name__ == "__main__":
    # make_csv_by_filter('examples2_output', 'research/prodigy/output/one_time_output/paren_at_end_list.csv', paren_at_end_filter)
    # modify_data_based_on_csv('/home/nss/Downloads/Dibur Hamatchil Editing - Sheet2.csv', 'examples2_output', 'examples2_output_paren')
    # move_binary_output_to_own_collection()
    # fix_perek()
    # fix_ids("research/prodigy/to_fix.txt")
    merge_gold_full_into_silver_binary()