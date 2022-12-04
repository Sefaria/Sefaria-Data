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

MISSINGS = []
X=set()
REFS = set()

def act_on_collection(col, callback, query={}):
    col = getattr(db, col)
    docs = col.find(query)
    for doc in docs:
        callback(col, doc)

with open('map_old_to_new.json') as fp:
    MAP = json.load(fp)
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
    if Ref(old_ref).all_segment_refs() == [Ref(old_ref)]:
        return find_segment_ref(old_ref)
    fref = Ref(old_ref).all_segment_refs()[0]
    lref = Ref(old_ref).all_segment_refs()[-1]
    first, last = find_segment_ref(fref), find_segment_ref(lref)

    if first and last:
        first, last = Ref(first).all_segment_refs()[0], Ref(last).all_segment_refs()[-1]
        if first.index_node == last.index_node:
            new = f'{first.normal()}-{last.normal()}'
            try:
                new = Ref(new).normal()
            except:
                print(f'error with trying change {old_ref} to {new}')
            else:
                return new

def change_link(col, link):
    global MISSINGS, REFS
    if link['auto']:
        # col.delete_one(link)
        return
    else:
        _id = link.pop('_id')
        for refs in ['refs', 'expandedRefs0', 'expandedRefs1']:
            for r, ref in enumerate(link[refs]):
                if Ref(ref).index.title == 'Zohar':
                    new = new_ref(ref)
                    if new:
                        link[refs][r] = new
                    else:
                        MISSINGS.append({'ref': ref, 'collection': col.name, '_id': _id})
                        segments = Ref(ref).all_segment_refs()
                        REFS.update({segments[0], segments[-1]})
        # col.replace_one({'_id': _id}, link)

def change_topic(col, topic):
    global MISSINGS, REFS
    _id = topic.pop('_id')
    ref = topic['ref']
    new = new_ref(ref)
    if new:
        topic['ref'] = new
        topic['expandedRefs'] = [r.normal() for r in Ref(new).all_segment_refs()]
    else:
        MISSINGS.append({'ref': ref, 'collection': col.name, '_id': _id, 'more': f'https://www.sefaria.org/topics/{topic["toTopic"]}'})
        segments = Ref(ref).all_segment_refs()
        REFS.update({segments[0], segments[-1]})
    # col.replace_one({'_id': _id}, topic)

def change_note(col, note):
    global MISSINGS, REFS
    _id = note.pop('_id')
    new = new_ref(note['ref'])
    if new:
        note['ref'] = new
    else:
        MISSINGS.append({'ref': note['ref'], 'collection': col.name, '_id': _id})
        segments = Ref(note['ref']).all_segment_refs()
        REFS.update({segments[0], segments[-1]})
    # col.replace_one({'_id': _id}, note)

def change_sheet(col, sheet):
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
                segments = Ref(ref).all_segment_refs()
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
                    source['heRef'] = Ref(new).he_normal()
                    new_refs.append(new)
                else:
                    MISSINGS.append({'ref': source['ref'], 'collection': col.name, '_id': _id,
                                     'more': f'https://www.sefaria.org/sheets/{sheet["id"]}'})
                    segments = Ref(source['ref']).all_segment_refs()
                    REFS.update({segments[0], segments[-1]})
    if len(old_refs) == len(new_refs):
        sheet['expandedRefs'] = [x for x in sheet['expandedRefs'] if not re.search('^Zohar \d', x)] + list(set([r.normal() for ref in new_refs for r in Ref(ref).all_segment_refs()]))
        # col.replace_one({'_id': _id}, sheet)

def change_webpage(col, wp):
    _id = wp.pop('_id')
    for refs in ['expandedRefs', 'refs']:
        wp[refs] = [r for r in wp[refs] if not re.search('^Zohar \d', r)]
    # col.replace_one({'_id': _id}, wp)

def change_history(_, his):
    # col.delete_one(his)
    pass

def change_user_history(col, uh):
    _id = uh.pop('_id')
    new = new_ref(uh['ref'])
    if new:
        uh['ref'] = new
        uh['context_refs'] = [r.normal() for r in Ref(new).all_context_refs()]
        uh['he_ref'] = Ref(new).he_normal()
        if 'he' in uh['versions'] and uh['versions']['he'] == 'New Torat Emet Zohar':
                uh['versions']['he'] = 'Torat Emet'
        # col.replace_one({'_id': _id}, uh)
    else:
        MISSINGS.append({'ref': uh['ref'], 'collection': col.name, '_id': _id})
        segments = Ref(uh['ref']).all_segment_refs()
        REFS.update({segments[0], segments[-1]})

def change_ref_data(_, rd):
    # col.delete_one(rd)
    pass


if __name__ == '__main__':
    act_on_collection('links', change_link, {'refs': {'$regex': '^Zohar \d'}})
    act_on_collection('topic_links', change_topic, {'ref': {'$regex': '^Zohar \d'}})
    act_on_collection('notes', change_note, {'ref': {'$regex': '^Zohar \d'}})
    act_on_collection('sheets', change_sheet, {'expandedRefs': {'$regex': '^Zohar \d'}})
    act_on_collection('webpages', change_webpage, {'expandedRefs': {'$regex': '^Zohar \d'}})
    act_on_collection('history', change_history, {'ref': {'$regex': '^Zohar \d'}})
    act_on_collection('user_history', change_user_history, {'ref': {'$regex': '^Zohar \d'}})
    act_on_collection('ref_data', change_ref_data, {'ref': {'$regex': '^Zohar \d'}})

    library.rebuild()
    if MULTISERVER_ENABLED:
        server_coordinator.publish_event("library", "rebuild")
    if USE_VARNISH:
        invalidate_all()

    with open('missing refs.csv', 'w') as fp:
        w = csv.DictWriter(fp, fieldnames=['ref', 'collection', '_id', 'more'])
        w.writeheader()
        for row in MISSINGS:
            w.writerow(row)
    print(len([x for x in REFS if x.text('he').text]))
    print(len(REFS))
