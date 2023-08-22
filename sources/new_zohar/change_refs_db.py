import json
import csv
import re
import django
django.setup()
from sefaria.model import *
from sefaria.system.database import db
from sefaria.settings import USE_VARNISH, MULTISERVER_ENABLED
from sefaria.system.multiserver.coordinator import server_coordinator
from sefaria.system.varnish.wrapper import invalidate_all
from sefaria.system.exceptions import InputError
from pymongo import ReplaceOne, DeleteOne

MISSINGS, FOUND = [], []
X=set()
REFS = set()

ALL_SEGMENTS = {}

def get_segments(ref):
    global ALL_SEGMENTS
    try:
        return ALL_SEGMENTS[ref]
    except KeyError:
        ALL_SEGMENTS[ref] = ref.all_segment_refs()
        return ALL_SEGMENTS[ref]

def act_on_collection(col, callback, query={}, active=False):
    print(f'starting hande {col} collection')
    col = getattr(db, col)
    docs = col.find(query)
    requests = []
    for doc in docs:
        req = callback(col, doc, active)
        if active:
            if req:
                requests.append(req)
            if len(requests) > 1000:
                print('bulk write')
                col.bulk_write(requests, ordered=False)
                requests = []
    if active and requests:
        col.bulk_write(requests, ordered=False)

with open('map_old_to_new-new.json') as fp:
    MAP = json.load(fp)
    MAP = {k.replace(' old', ''): v for k, v in MAP.items()}
def get_segment_ref(ref):
    try:
        return MAP[ref]
    except KeyError:
        return

def find_segment_ref(ref):
    if isinstance(ref, Ref):
        ref = ref.normal()
    new = get_segment_ref(ref)
    if not new and len(Ref(ref).text('he').text) < 27 and Ref(ref).next_segment_ref():
        new = get_segment_ref(Ref(ref).next_segment_ref().normal())
    return new

def new_ref(old_ref):
    if old_ref == 'Zohar 3:300a:2-3':
        return "Zohar, Ha'Azinu 17:252"
    if old_ref == 'Zohar 3:300a:6':
        return "Zohar, Ha'Azinu 17:256"
    try:
        Ref(old_ref)
    except InputError:
        return
    seg = find_segment_ref(old_ref)
    if seg:
        return seg
    if not get_segments(Ref(old_ref)):
        return
    fref = get_segments(Ref(old_ref))[0]
    lref = get_segments(Ref(old_ref))[-1]
    first, last = find_segment_ref(fref), find_segment_ref(lref)

    if first and last:
        return old_ref #for running before the new one is live
        try:
            first, last = get_segments(Ref(first))[0], get_segments(Ref(last))[-1]
        except IndexError:
            print(f'no segments to {first} or {last}')
            return
        if first.index_node == last.index_node:
            new = f'{first.normal()}-{last.normal()}'
            try:
                new = Ref(new).normal()
            except:
                print(f'error with trying change {old_ref} to {new}')
            else:
                return new

def change_link(col, link, active=False):
    global MISSINGS, REFS, FOUND
    if link['auto']:
        if active:
            return DeleteOne(link)
        return
    else:
        _id = link.pop('_id')
        for refs in ['refs']:#, 'expandedRefs0', 'expandedRefs1']:
            row = {'col': 'links', 'query': {'$and': []}, 'update': {'$set': {'refs': []}}, '_id': str(_id)}
            for r, ref in enumerate(link[refs]):
                if Ref(ref).index.title == 'Zohar':
                    new = new_ref(ref)
                    row['update']['$set']['refs'].append(new)
                    if new:
                        if refs == 'refs':
                            FOUND.append(row)
                            row['query']['$and'].append({'refs': {'$regex': f'^{new.split(":")[0]}'}})
                        link[refs][r] = new
                    else:
                        MISSINGS.append({'ref': ref, 'collection': col.name, '_id': _id})
                        segments = get_segments(Ref(ref))
                        REFS.update({segments[0], segments[-1]})
                        return
                else:
                    row['query']['$and'].append({'refs': ref})
                    row['update']['$set']['refs'].append(ref)
            # row['update']['$set']['expandedRefs0'] = [x.normal() for x in get_segments(Ref(row['update']['$set']['refs'][0]))]
            # row['update']['$set']['expandedRefs1'] = [x.normal() for x in get_segments(Ref(row['update']['$set']['refs'][1]))]
        if active:
            return ReplaceOne({'_id': _id}, link)

def change_topic(col, topic, active=False):
    global MISSINGS, REFS, FOUND
    _id = topic.pop('_id')
    ref = topic['ref']
    new = new_ref(ref)
    if new:
        FOUND.append({'col': 'topic_links', '_id': str(_id), 'query': {'ref': {'$regex': f'^{new.split(":")[0]}'}, 'toTopic': topic['toTopic'], 'linkType': topic['linkType'], 'dataSource': topic['dataSource']}, 'update': {'$set': {'ref': new}}})#, 'expandedRefs': [r.normal() for r in get_segments(Ref(new))]}}})
        topic['ref'] = new
        if active:
            topic['expandedRefs'] = [r.normal() for r in get_segments(Ref(new))]
    else:
        if ref == 'Zohar 3:275b:6-8':
            return DeleteOne(topic)
        MISSINGS.append({'ref': ref, 'collection': col.name, '_id': _id, 'more': f'https://www.sefaria.org/topics/{topic["toTopic"]}'})
        segments = get_segments(Ref(ref))
        REFS.update({segments[0], segments[-1]})
    if active:
        return ReplaceOne({'_id': _id}, topic)

def change_note(col, note, active=False):
    global MISSINGS, REFS, FOUND
    _id = note.pop('_id')
    new = new_ref(note['ref'])
    if new:
        FOUND.append({'col': 'notes', '_id': str(_id), 'query': {'ref':  {'$regex': f'^{new.split(":")[0]}'}, 'owner': note['owner']}, 'update': {'$set': {'ref' :new}}})
        note['ref'] = new
    else:
        MISSINGS.append({'ref': note['ref'], 'collection': col.name, '_id': _id})
        segments = get_segments(Ref(note['ref']))
        REFS.update({segments[0], segments[-1]})
    if active:
        return ReplaceOne({'_id': _id}, note)

def change_sheet(col, sheet, active=False):
    global MISSINGS, REFS
    _id = sheet.pop('_id')
    old_refs = []
    new_refs = []
    for r, ref in enumerate(sheet['includedRefs']):
        try:
            Ref(ref)
        except:
            continue
        if Ref(ref).index.title == 'Zohar':
            old_refs.append(ref)
            new = new_ref(ref)
            if new:
                sheet['includedRefs'][r] = new
                new_refs.append(new)
            else:
                MISSINGS.append({'ref': ref, 'collection': col.name, '_id': _id, 'more': f'https://www.sefaria.org/sheets/{sheet["id"]}'})
                segments = get_segments(Ref(ref))
                REFS.update({segments[0], segments[-1]})
    for source in sheet['sources']:
        if 'ref' in source:
            try:
                Ref(source['ref'])
            except:
                continue
            if Ref(source['ref']).index.title == 'Zohar':
                old_refs.append(ref)
                new = new_ref(source['ref'])
                if new:
                    source['ref'] = new
                    if active:
                        source['heRef'] = Ref(new).he_normal().replace('זוהר הדור הבא הבא הבא', 'ספר הזהר')
                    new_refs.append(new)
                else:
                    text = ''
                    try:
                        text = source['text']
                        text = text['he']
                        while isinstance(text, list):
                            text = text[0]
                        text = text[:200]
                    except:
                        pass
                    MISSINGS.append({'ref': source['ref'], 'collection': col.name, '_id': _id,
                                     'more': f'https://www.sefaria.org/sheets/{sheet["id"]}', 'text': text})
                    segments = get_segments(Ref(source['ref']))
                    REFS.update({segments[0], segments[-1]})
    if len(old_refs) == len(new_refs):
        if active:
            sheet['expandedRefs'] = [x for x in sheet['expandedRefs'] if not re.search('^Zohar \d', x)] + list(set([r.normal() for ref in new_refs for r in get_segments(Ref(ref))]))
            return ReplaceOne({'_id': _id}, sheet)

def change_webpage(col, wp, active=False):
    _id = wp.pop('_id')
    for refs in ['expandedRefs', 'refs']:
        wp[refs] = [r for r in wp[refs] if not re.search('^Zohar \d', r)]
    if active:
        return ReplaceOne({'_id': _id}, wp)

def change_history(col, his, active=False):
    if active:
        return DeleteOne(his)

def change_user_history(col, uh, active=False):
    _id = uh.pop('_id')
    new = new_ref(uh['ref'])
    if new:
        uh['ref'] = new
        if active:
            uh['context_refs'] = [r.normal() for r in Ref(new).all_context_refs()]
            uh['he_ref'] = Ref(new).he_normal()
        if 'versions' in uh and 'he' in uh['versions'] and uh['versions']['he'] == 'New Torat Emet Zohar':
                uh['versions']['he'] = 'Torat Emet'
        if active:
            return ReplaceOne({'_id': _id}, uh)
    else:
        MISSINGS.append({'ref': uh['ref'], 'collection': col.name, '_id': _id})
        try:
            segments = get_segments(Ref(uh['ref']))
            REFS.update({segments[0], segments[-1]})
        except: #problem with ref. we can skip that
            pass

def change_user_history2(col, uh, active=False):
    _id = uh.pop('_id')
    new = uh['ref'].replace(' TNNNG' '')
    if active:
        uh['context_refs'] = [r.normal() for r in Ref(new).all_context_refs()]
        uh['he_ref'] = Ref(new).he_normal()

def change_ref_data(col, rd, active=False):
    if active:
        return DeleteOne(rd)


if __name__ == '__main__':
    active = False
    act_on_collection('links', change_link, {'refs': {'$regex': '^Zohar \d'}}, active)
    act_on_collection('topic_links', change_topic, {'ref': {'$regex': '^Zohar \d'}}, active)
    act_on_collection('notes', change_note, {'ref': {'$regex': '^Zohar \d'}}, active)
    # act_on_collection('sheets', change_sheet, {'expandedRefs': {'$regex': '^Zohar \d'}}, active)
    # act_on_collection('webpages', change_webpage, {'expandedRefs': {'$regex': '^Zohar \d'}}, active)
    # act_on_collection('history', change_history, {'ref': {'$regex': '^Zohar \d'}}, active)
    # act_on_collection('user_history', change_user_history2, {'ref': {'$regex': '^Zohar TNNNG'}}, active)
    # act_on_collection('ref_data', change_ref_data, {'ref': {'$regex': '^Zohar \d'}}, active)
    # act_on_collection('user_history', change_user_history, {'ref': {'$regex': '^Zohar \d:'}}, active)

    library.rebuild()
    if MULTISERVER_ENABLED:
        server_coordinator.publish_event("library", "rebuild")
    if USE_VARNISH:
        invalidate_all()

    with open('missing_refs.csv', 'w') as fp:
        w = csv.DictWriter(fp, fieldnames=['ref', 'collection', '_id', 'more', 'text'])
        w.writeheader()
        for row in MISSINGS:
            w.writerow(row)
    with open('found.json', 'w') as fp:
        json.dump(FOUND, fp)
    print(len([x for x in REFS if x.text('he').text]))
    print(len(REFS))
