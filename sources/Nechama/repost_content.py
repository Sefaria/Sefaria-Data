#encoding=utf-8

import django
django.setup()
from sefaria.model import *
from sefaria.system.database import db
import re
from sources.local_settings import *
from sources.functions import post_sheet, http_request
import unicodecsv as csv

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

def delete_asterisks(txt):
    """
    deletes asterisks from the text since it is in the margins
    :param txt: text
    :return: text clean of asterisks
    """
    return re.sub(u'\*', '', txt)

def check_for_sheet_linking(format_source, compile, content_source):
    for match in re.finditer(compile, format_source):
        if not match.group('text2'):
            continue
        content_source = re.sub(re.sub(u'(\(|\))', u'', match.group('text2')), re.sub(u'(\(|\))', u'', match.group('aref')), content_source)
    return content_source

def check_for_section_title(source, compile):
    if re.search(u'153', source['en']):
        return source['en']
    if re.search(compile, source['he']):
        strip_html = re.sub(u'<.*?>', u'', source['en'])
        new_source = u'<table><tbody><tr><td><big><b>' + strip_html + u'</b></big></tbody></td></tr></table>'
        return new_source
    return source['en']

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
    section_title_pattern = re.compile(u'<table><tbody><tr><td><big>')

    k = 0
    if copy_as_is:
        format_sheet['sources'] = content_sheet['sources']

    format_sources = format_sheet['sources'] #sorted(format_sheet['sources'], key=lambda x:x['node'])
    for j, s in enumerate(content_sheet['sources']): #enumerate(sorted(content_sheet['sources'], key=lambda x:x['node'])):
        try:
            i = j+k
            if i >= len(format_sources):
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
                    # print u"node {} after {} looks wrong".format(s['node'], i)
                    continue
            if 'outsideBiText' in s.keys():
                if not s['outsideBiText']['he']:
                    continue
                format_sources[i]['outsideBiText']['he'] = check_for_sheet_linking(format_sources[i]['outsideBiText']['he'], linking_pattern, s['outsideBiText']['he'])
                format_sources[i]['outsideBiText']['en'] = s['outsideBiText']['en']
                format_sources[i]['outsideBiText']['en'] = check_for_section_title(s['outsideBiText'], section_title_pattern)
                if hasattr(format_sources[i], 'options') and hasattr(format_sources[i]['options'], 'sourcePrefix'):
                    format_sources[i]['outsideBiText']['he'] = delete_asterisks(format_sources[i]['outsideBiText']['he'])
                    format_sources[i]['outsideBiText']['en'] = delete_asterisks(format_sources[i]['outsideBiText']['en'])
            elif 'outsideText' in s.keys():
                format_sources[i]['outsideText']['he'] = check_for_sheet_linking(format_sources[i]['outsideText']['he'], linking_pattern, s['outsideText']['he'])
            elif 'text' in s.keys():
                format_sources[i]['text']['he'] = check_for_sheet_linking(format_sources[i]['text']['he'], linking_pattern, s['text']['he'])
                format_sources[i]['text']['en'] = s['text']['en']
                format_sources[i]['ref'] = s['ref']
                format_sources[i]['heRef'] = Ref(s['ref']).he_normal()

        except KeyError:
            # print u"node {} after {} looks wrong".format(s['node'], i)
            # format_sources[i]['KeyError']
            with open(u"sheet_{}.csv".format(format_sheet['id']), 'w') as fcsv:
                writer = csv.DictWriter(fcsv, [u'fromat {}'.format(format_sheet['id']), u'content {}'.format(content_sheet['id'])])
                writer.writeheader()
                row = []
                for i, s in enumerate(content_sheet['sources']):
                    if 'outsideBiText' in s.keys():
                        row.append({u'fromat {}'.format(format_sheet['id']):'outsideBiText'})
                        # writer.writerow({u'fromat {}'.format(format_sheet['id']):'outsideBiText'})
                    else:
                        row.append({u'fromat {}'.format(format_sheet['id']):'text'})
                        # writer.writerow({u'fromat {}'.format(format_sheet['id']):'text'})

                for i, f in enumerate(format_sources):
                    if i>=len(row):
                        break
                    if 'outsideBiText' in f.keys():
                        row[i][u'content {}'.format(content_sheet['id'])] = 'outsideBiText'
                        # writer.writerow({u'content {}'.format(content_sheet['id']):'outsideBiText'})
                    else:
                        row[i][u'content {}'.format(content_sheet['id'])] = 'text'
                        # writer.writerow({u'content {}'.format(content_sheet['id']): 'text'})
                writer.writerows(row)
            raise KeyError('something went wrong')
    format_sheet['tags'].append('Merged')
    return format_sheet

if __name__ == "__main__":
    # ssns = [1409, 259, 246, 774, 327, 172, 332, 142, 619, 115, 273, 210, 147, 46, 661, 1405, 204, 27, 118, 1440, 35, 37, 169, 299, 44, 45, 174, 47, 48, 49, 50, 51, 52, 53, 54, 55, 114, 1403, 1404, 1402, 1406, 1407]

    format_map = {1: 152685, 259: 152686, 5: 152687, 774: 152688, 1409: 152719, 172: 152725, 142: 152720, 273: 152690, 147: 152721,
     174: 152726, 27: 152691, 1440: 152723, 35: 152692, 37: 152693, 169: 152724, 299: 152694, 44: 152695, 45: 152696,
     46: 152697, 47: 152698, 48: 152699, 49: 152700, 50: 152701, 51: 152702, 52: 152703, 53: 152704, 54: 152705,
     55: 152706, 246: 152729, 327: 152707, 332: 152708, 204: 152727, 210: 152728, 14: 152689, 1407: 152718, 619: 152709,
     114: 152710, 115: 152711, 118: 152712, 1402: 152713, 1403: 152714, 1404: 152715, 1405: 152716, 1406: 152717,
     661: 152722}

    new_format_map = {1: 152730, 259: 152731, 5: 152732, 774: 152733, 1409: 152764, 172: 152770, 142: 152765, 273: 152735, 147: 152766, 174: 152771, 27: 152736, 1440: 152768, 35: 152737, 37: 152738, 169: 152769, 299: 152739, 44: 152740, 45: 152741, 46: 152742, 47: 152743, 48: 152744, 49: 152745, 50: 152746, 51: 152747, 52: 152748, 53: 152749, 54: 152750, 55: 152751, 246: 152774, 327: 152752, 332: 152753, 204: 152772, 210: 152773, 14: 152734, 1407: 152763, 619: 152754, 114: 152755, 115: 152756, 118: 152757, 1402: 152758, 1403: 152759, 1404: 152760, 1405: 152761, 1406: 152762, 661: 152767}


    content_map = {1: 152685, 259: 151432, 5: 152689, 774: 151948, 1409: 152596, 172: 151346, 142: 152825, 273: 152955, 147: 151322, 174: 151348, 27: 151204, 1440: 152627, 35: 151212, 37: 151214, 169: 151343, 299: 152981, 44: 152728, 45: 152729, 46: 152730, 47: 152731, 48: 152732, 49: 152733, 50: 152734, 51: 152735, 52: 152736, 53: 152737, 54: 152738, 55: 152739, 246: 152928, 327: 151500, 332: 151505, 204: 151378, 210: 152892, 14: 152698, 1407: 152594, 619: 151794, 114: 151289, 115: 151290, 118: 151293, 1402: 152589, 1403: 152590, 1404: 152591, 1405: 152592, 1406: 152593, 661: 151835}

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
            # content_sheet['tags'].append('NOT merged')
            # post_sheet(content_sheet, "http://ravnataf.sandbox.sefaria.org",api_key='sNyyfrHouUbaaNDIbI94Q8hFClFMZrYUGC88X5QNWYk')
            print "didn't merge, updated {}, ssn: {}".format(format_sheet['id'], content_ssn)
            didnt_post.append({'ssn':content_ssn})
    #
    print didnt_post
    # print [dp['ssn'] for dp in didnt_post]
    # print [dp['ravnataf_id'] for dp in didnt_post]
    # print len(didnt_post)
