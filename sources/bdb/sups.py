from pymongo.errors import DocumentTooLarge
import re
import copy
from sefaria.system.database import db

def replace_sups(text):
    if not text:
        return text
    return re.sub('<sup>(.*?</sup> *<i class="footnote)', r'<sup class="footnote-marker">\1', text)


col = db.sheets
doc_ids = [d['_id'] for d in col.find({})]
for idd in doc_ids:
    doc = col.find_one({'_id': idd})
    # if 'id' in doc:
    #     print(doc['id'])
    # else:
    #     print('no id', idd)
    new = copy.deepcopy(doc)
    for source in new['sources']:
        keys = list(source)
        for k in ['node', 'options', 'comment', 'ref', 'heRef', 'media', 'addedBy', 'userLink', 'caption', 'highlighter']:
            if k in keys:
                keys.remove(k)
        if not keys:
            continue
        text = ''
        done = False
        for key in ['text', 'outsideText', 'comment']:
            if key in source:
                if type(source[key]) == str:
                    source[key] = replace_sups(source[key])
                    done = True
                else:
                    text = source[key]
                break
        if done:
            continue
        if text == '':
            if 'outsideBiText' in source:
                text = source['outsideBiText']
            else:
                text = source
        if not text:
            continue
        if type(text) == str:
            type('text is string', source)
        else:
            try:
                text['en'] = replace_sups(text['en'])
                try:
                    text['he'] = replace_sups(text['he'])
                except KeyError:
                    pass
            except KeyError:
                try:
                    text['he'] = replace_sups(text['he'])
                except KeyError:
                    print('problem with source', source)
    if doc['sources'] != new['sources']:
        try:
            col.update_one({'_id': idd}, {'$set': {'sources': new['sources']}})
        except DocumentTooLarge:
            col.delete_one({'_id': idd})
            col.insert_one(new)

def first_type(array):
    for x in array:
        if x:
            return type(x)

def get_segments(text):
    if not text:
        yield []
    elif type(text) == dict:
        yield from get_segments(text.values())
    elif first_type(text) == str:
        yield text
    else:
        for a in text:
            yield from get_segments(a)

print('texts')
col = db.texts
doc_ids = [d['_id'] for d in col.find({})]
for idd in doc_ids:
    doc = col.find_one({'_id': idd})
    new = copy.deepcopy(doc)
    for array in get_segments(new['chapter']):
        for i in range(len(array)):
            new_text = replace_sups(array[i])
            if array[i] != new_text:
                array[i] = new_text
    if doc != new:
        try:
            col.update_one({'_id': idd}, {'$set': {'chapter': new['chapter']}})
        except DocumentTooLarge:
            col.delete_one({'_id': idd})
            col.insert_one(new)

