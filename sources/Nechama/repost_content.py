#encoding=utf-8

import django
django.setup()
from sefaria.model import *
from sefaria.system.database import db
import re
from sources.local_settings import *
from sources.functions import post_sheet, http_request

# mapping of the post server
mapping = {1409: 21, 259: 22, 774: 23, 44: 24, 142: 25, 147: 26, 174: 27, 27: 28, 1440: 29, 35: 30, 37: 31, 169: 32, 172: 33, 45: 34, 46: 35, 47: 36, 48: 37, 49: 38, 50: 39, 51: 40, 52: 41, 53: 42, 54: 43, 55: 44, 246: 45, 327: 46, 332: 47, 204: 48, 1407: 49, 619: 50, 114: 51, 115: 52, 118: 53, 1402: 54, 1403: 55, 1404: 56, 1405: 57, 1406: 58, 661: 59
           }



def get_sheet(server, api_key, sheet_id = None, sheet_ssn = None):
    try:
        assert sheet_id or sheet_ssn
    except AssertionError:
        print " you must supply an id or ssn to get a sheet"
        return
    if sheet_ssn:
        sheet_id = mapping[int(sheet_ssn)]

    url = server + "/api/sheets/{}".format(sheet_id)
    got = http_request(url, body={"apikey": api_key}, method="GET")
    return got

def get_ssn(sheet=None, sheet_id=None):
    ssn = None
    # sheet_id: use mapping id_ssn on the correct server
    # if sheet_id:
    #     get_mapping[sheet_id]
    # sheet: use tags to get the ssn
    if sheet:
        if sheet['ssn']:
            ssn = sheet['ssn']
        else:
            for tag in sheet[u'tags']:
                if isinstance(tag, int):
                    ssn = tag
                    break
                elif tag.isdigit():
                    ssn = tag
                    break
    return ssn

def check_for_sheet_linking(format_source, compile, content_source):
    for match in re.finditer(compile, format_source):
        if not match.group('text2'):
            continue
        content_source = re.sub(re.sub(u'(\(|\))', u'', match.group('text2')), re.sub(u'(\(|\))', u'', match.group('aref')), content_source)
    return content_source


def merge(content_sheet, format_sheet, copy_as_is = False):
    """
    Goes over the sources and change only the text but not the options and formatting
    NOTE: Sheets must be of the same format bilingual or Hebrew only!
    :param content_sheet: the sheet we want the content from
    :param format_sheet: the newset posted sheet with the correct format
    :return: merged sheet to be reposted
    """
    # linking_pattern = re.compile(u'(?P<text1>.*?)(?P<aref><a.*?/sheets/(?P<id>\d+).*?>(?P<text2>.*?)</a>)(?P<text3>.*?)')
    linking_pattern = re.compile(u'(?P<aref><a.*?/.+?>(?P<text2>.*?)</a>)')
    k = 0
    if copy_as_is:
        format_sheet['sources'] = content_sheet['sources']
    format_sources = format_sheet['sources'] #sorted(format_sheet['sources'], key=lambda x:x['node'])
    for j, s in enumerate(content_sheet['sources']): #enumerate(sorted(content_sheet['sources'], key=lambda x:x['node'])):
        i = j+k
        if i>=len(format_sources):
            break
        if not s['node'] or not format_sources[i]['node']:
            k += 1
            continue
        if i < len(format_sources) and format_sources[i]['node'] != s['node']:
            if abs(int(format_sources[i]['node'])-int(s['node'])) < 2:
                k += 1
                i = j + k
            else:
                format_sources[i] = s
                continue
        if 'outsideBiText' in s.keys():
            if not s['outsideBiText']['he']:
                continue
            format_sources[i]['outsideBiText']['he'] = check_for_sheet_linking(format_sources[i]['outsideBiText']['he'], linking_pattern, s['outsideBiText']['he'])
            format_sources[i]['outsideBiText']['en'] = s['outsideBiText']['en']
        elif 'outsideText' in s.keys():
            format_sources[i]['outsideText']['he'] = check_for_sheet_linking(format_sources[i]['outsideText']['he'], linking_pattern, s['outsideText']['he'])
        elif 'text' in s.keys():
            format_sources[i]['text']['he'] = check_for_sheet_linking(format_sources[i]['text']['he'], linking_pattern, s['text']['he'])
            format_sources[i]['text']['en'] = s['text']['en']
            format_sources[i]['ref'] = s['ref']
            format_sources[i]['heRef'] = s['heRef']


    format_sheet['tags'].append('merged')
    return format_sheet

if __name__ == "__main__":
    # ssns = [1409, 259, 246, 774, 327, 172, 332, 142, 619, 115, 273, 210, 147, 46, 661, 1405, 204, 27, 118, 1440, 35, 37, 169, 299, 44, 45, 174, 47, 48, 49, 50, 51, 52, 53, 54, 55, 114, 1403, 1404, 1402, 1406, 1407]

    format_map = {1403: 154151}  # {1409: 1460, 259: 1461, 774: 1463, 44: 1484, 142: 1467, 273: 1470, 147: 1472, 174: 1486, 27: 1477, 1440: 1479,
     # 35: 1480, 37: 1481, 169: 1482, 299: 1483, 172: 1465, 45: 1485, 46: 1473, 47: 1487, 48: 1488, 49: 1489, 50: 1490,
     # 51: 1491, 52: 1492, 53: 1493, 54: 1494, 55: 1495, 246: 1462, 327: 1464, 332: 1466, 204: 1476, 210: 1471,
     # 1407: 1501, 619: 1468, 114: 1496, 115: 1469, 118: 1478, 1402: 1499, 1403: 1497, 1404: 1498, 1405: 1475, 1406: 1500,
     # 661: 1474}

    content_map = {1403: 152590}  # {1409: 152596, 259: 151432, 774: 151948, 44: 152728, 142: 152825, 273: 152955, 147: 151322, 174: 151348, 27: 151204, 1440: 152627, 35: 151212, 37: 151214, 169: 151343, 299: 152981, 172: 151346, 45: 152729, 46: 152730, 47: 152731, 48: 152732, 49: 152733, 50: 152734, 51: 152735, 52: 152736, 53: 152737, 54: 152738, 55: 152739, 246: 152928, 327: 151500, 332: 151505, 204: 151378, 210: 152892, 1407: 152594, 619: 151794, 114: 151289, 115: 151290, 118: 151293, 1402: 152589, 1403: 152590, 1404: 152591, 1405: 152592, 1406: 152593, 661: 151835}

    sheet_id_get = content_map.values()
    didnt_post = []
    # for sheet_id in sheet_id_get: #range(154147,154186):
    for sheet_tuple in content_map.items():
        content_sheet = get_sheet("http://qaNechama.sandbox.sefaria.org", 'Un1uRLng7ZwTo0mCvBMI5r8McwbwoEgtuptEQM92FIw', sheet_id=sheet_tuple[1])
        # content_ssn = get_ssn(sheet=content_sheet)
        content_ssn = sheet_tuple[0]
        format_id = format_map[content_ssn]
        # format_sheet_curser = db.sheets.find({"id":format_id})
        format_sheet = get_sheet("http://ravnataf.sandbox.sefaria.org", 'sNyyfrHouUbaaNDIbI94Q8hFClFMZrYUGC88X5QNWYk', sheet_id=format_id)
        # for format_sheet in format_sheet_curser:
            # sanity check
            # assert [int(tag) for tag in content_sheet['tags'] if unicode(tag).isdigit()]== [int(tag) for tag in format_sheet['tags'] if unicode(tag).isdigit()]
        assert 'Bilingual' in format_sheet['tags']
        try:
            merged_sheet = merge(content_sheet, format_sheet, copy_as_is = False)
            # ssns.append(content_ssn)
            del merged_sheet['_id']
            merged_sheet['tags'].append('Edited')
            # merged_sheet['id'] = sheet_id
            merged_sheet['id'] = format_id
            # db.sheets.update({'_id': format_sheet["_id"]}, merged_sheet)
            print "updated {}, ssn: {}".format(merged_sheet['id'], content_ssn)
            response = post_sheet(merged_sheet, "http://ravnataf.sandbox.sefaria.org", api_key='sNyyfrHouUbaaNDIbI94Q8hFClFMZrYUGC88X5QNWYk')
            if not isinstance(response, dict):
                with open(u"nopost.html", 'a') as f:
                    writer = f.write(response)
        except KeyError:
            del content_sheet['_id']
            content_sheet['id'] = format_sheet['id']
            db.sheets.update({'_id': format_sheet["_id"]}, content_sheet)
            print "didn't merge, updated {}, ssn: {}".format(format_sheet['id'], content_ssn)
            didnt_post.append({'ssn':content_ssn})
    #
    print didnt_post
    # print [dp['ssn'] for dp in didnt_post]
    # print [dp['ravnataf_id'] for dp in didnt_post]
    # print len(didnt_post)
