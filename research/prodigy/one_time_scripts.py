from collections import defaultdict
import re, json, csv, srsly
from tqdm import tqdm
import django
django.setup()
from sefaria.model import *
from research.prodigy.db_manager import MongoProdigyDBManager

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
if __name__ == "__main__":
    # make_csv_by_filter('examples2_output', 'research/prodigy/output/one_time_output/paren_at_end_list.csv', paren_at_end_filter)
    modify_data_based_on_csv('/home/nss/Downloads/Dibur Hamatchil Editing - Sheet2.csv', 'examples2_output', 'examples2_output_paren')