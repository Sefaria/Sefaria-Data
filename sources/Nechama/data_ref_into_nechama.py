#encoding=utf-8

import django
django.setup()
from sefaria.system.database import db
import re

# GET_SERVER = "http://steinsaltz.sandbox.sefaria.org"
# POST_SERVER = "http://steinsaltz.sandbox.sefaria.org"
compile_seg2ref = re.compile(u'<.*?(?P<add_to>class="refLink"\s*href="/(?P<ref>.*?)").*?>')


def add_all_ref_link(sheet_sources):
    for s in sheet_sources:
        if 'outsideText' in s.keys():
            s['outsideText'] = change_texts(s['outsideText'])
            # for match in re.finditer(compile_seg2ref, s['outsideText']):
                # if re.search(u'data-ref', match.group()):
                #     continue
                # s['outsideText'] = add_ref_link(s['outsideText'], match)
        elif 'outsideBiText' in s.keys():
            s['outsideBiText']['he'] = change_texts(s['outsideText']['he'])
            s['outsideBiText']['en'] = change_texts(s['outsideText']['en'])
            # for match in re.finditer(compile_seg2ref, s['outsideBiText']['he']):
            #     if re.search(u'data-ref', match.group()):
            #         continue
            #     s['outsideText']['he'] = add_ref_link(s['outsideBiText']['he'], match)
        elif 'text' in s.keys():
            s['text']['he'] = change_texts(s['text']['he'])
            s['text']['en'] = change_texts(s['text']['en'])

    return sheet_sources


def change_texts(text):
    for match in re.finditer(compile_seg2ref, text):
        if re.search(u'data-ref', match.group()):
            continue
        text = add_ref_link(text, match)
    return text


def add_ref_link(text, match):
    new_text = re.sub(match.group('add_to'), match.group('add_to') + u' data-ref="{}"'.format(match.group('ref')), text)
    return new_text


if __name__ == "__main__":
    ids = [162071]
    # sheets = get_sheets_from_get_server(ids, GET_SERVER)
    sheets = db.sheets.find({"id":ids[0]})
    for sheet in sheets:
        sheet_id= sheet['id']
        print sheet_id
        with_data_ref = add_all_ref_link(sheet['sources'])
        sheet['sources'] = with_data_ref
        # post_sheet(sheet, POST_SERVER)
        db.sheets.replace_one({"id": sheet_id}, sheet)