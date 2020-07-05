#encoding=utf-8

import django
django.setup()
from sefaria.system.database import db
import re
from sources.functions import *
#
GET_SERVER = "https://www.sefaria.org"
POST_SERVER = "https://www.sefaria.org"
# GET_SERVER = "http://nechama.sandbox.sefaria.org"
# POST_SERVER = "http://nechama.sandbox.sefaria.org"

delete_data_ref_info = True
compile_seg2ref = re.compile(u'<.*?(?P<add_to>class="refLink"\s*href="/(?P<sheet>sheets/)?(?P<ref>.*?)").*?>')

def get_sheets_from_get_server(list_get_sheet_ids, get_server_address):
    got_sheets = []
    for id in list_get_sheet_ids:
        url = get_server_address + "/api/sheets/{}".format(id)
        got = http_request(url, body={"apikey": API_KEY}, method="GET")
        got_sheets.append(got)
    return got_sheets

def add_all_ref_link(sheet_sources):
    for s in sheet_sources:
        if 'outsideText' in s.keys():
            s['outsideText'] = change_texts(s['outsideText'])
            # for match in re.finditer(compile_seg2ref, s['outsideText']):
                # if re.search(u'data-ref', match.group()):
                #     continue
                # s['outsideText'] = add_ref_link(s['outsideText'], match)
        elif 'outsideBiText' in s.keys():
            s['outsideBiText']['he'] = change_texts(s['outsideBiText']['he'])
            s['outsideBiText']['en'] = change_texts(s['outsideBiText']['en'])
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
            if delete_data_ref_info:
                return delete_ref_link(text)
        else:
            text = add_ref_link(text, match)
    if re.search(u'162386', text):
        print u"Found 162386 in sheet"
    return text


def add_ref_link(text, match):
    if match.group(u'sheet'):
        add = u' data-ref="sheet.{}"'.format(match.group('ref'))
    else:
        add = u' data-ref="{}"'.format(match.group('ref'))
    new_text = re.sub(match.group('add_to'), match.group('add_to') + add, text)
    return new_text


def delete_ref_link(text):
    to_delete = re.compile(u'<.*?(?P<delete>data-ref=[^\s]*?\s).*?>')
    for match in re.finditer(to_delete, text):
        if match:
            text = re.sub(match.group('delete'), u'', text)
    return text

if __name__ == "__main__":
    ids = [160572]  # [162107]
    sheets = get_sheets_from_get_server(ids, GET_SERVER)
    # query = {"group": u"גיליונות נחמה"}
    query = {"id": ids[0]}
    # sheets = db.sheets.find(query) #({"id":ids[0]})
    cnt =0
    for sheet in sheets:
        sheet_id = sheet['id']
        # if sheet_id == 160781:
        #     continue
        print sheet_id
        cnt +=1
        with_data_ref = add_all_ref_link(sheet['sources'])
        sheet['sources'] = with_data_ref
        del sheet['_id']
        post_sheet(sheet, POST_SERVER)
        # db.sheets.replace_one({"id": sheet_id}, sheet)
    print u"changed {} sheets".format(cnt)