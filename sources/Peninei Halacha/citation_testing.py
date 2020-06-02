# -*- coding: utf-8 -*-
import django
django.setup()
from sefaria.model import *
import requests
import regex as re
import csv
import codecs
from sources.functions import post_text
from itertools import zip_longest
from sefaria.utils.hebrew import is_hebrew

SEFARIA_SERVER = "https://topicside.cauldron.sefaria.org"

# Shulchan Arukh
sa_re = re.compile('\([^()]*?(שו"ע)(?!\s*(או"ח|יו"ד|אב"ה|חו"מ|אה"ע))[^()]*?\)')
sa_en_re = re.compile('\([^()]*?(Shulchan Aruch|SA)(?:(?P<vav>\s*(and|,)?)\s*(Rama))?\s+\d+:\d+[^()]*?\)')
mb_re = re.compile('\([^()]*\s+מ"ב\s+[^()]*\)')

def retrieve_segments(title, server=None, lang='he'):
    ind = library.get_index(title)
    sections = ind.all_section_refs()
    segments = []
    for sec in sections:
        if server:
            sec_text_he = requests.get("{}/api/texts/{}?context=0"
                                    .format(server, sec.normal())).json()["he"]
            if lang != 'he':
                sec_text_en = requests.get("{}/api/texts/{}?context=0"
                                           .format(server, sec.normal())).json()["en"]

        else:
            sec_text_he = sec.text('he').text
            sec_text_en = sec.text('en').text
        if lang == 'both':
            sec_text_both = zip_longest(sec_text_he, sec_text_en, fillvalue='')
            segment = (sec, sec_text_both)
        elif lang == 'en':
            segment = (sec, sec_text_en)
        else:
            segment = (sec, sec_text_he)
        segments.append(segment)
    return segments


def SA(sec, jseg, arg_text, string_to_add_after_he='',string_to_add_after_en='', lang='he'):
    rows = []
    subs = []
    row = {}
    # if lang == 'both':
    #     # text = text[0]
    for text in arg_text:
        matchs_he = re.finditer(sa_re, text)
        matchs_en = re.finditer(sa_en_re, text)
        # if len(list(matchs_en)) != len(list(matchs_he)):
        #     print("matches of both languages in SA don't match for seg {}.{}".format(sec, jseg+1))
        matchs = list(matchs_en) + list(matchs_he)
        for match in matchs:
            to_change = match.group()
            new_subd = False
            if re.search('רמ"א', match.group()):
                to_change = re.sub('שו"ע\s*?(?P<vav>ו?)(רמ"א)', 'רמ"א \g<vav>שו"ע', match.group())
                if not re.search(sa_re, to_change):
                    new_sub = to_change
                    new_subd = True
            elif re.search('Rama', match.group()):
                to_change = re.sub('(Shulchan Aruch|SA)(?:(?P<vav>\s*(and|,))?(\s*?Rama))', 'Rama\g<vav> Shulchan Aruch', match.group())
                if not re.search(sa_en_re, to_change):
                    new_sub = to_change
                    new_subd = True
            if not new_subd:
                new_sub = re.sub('שו"ע', 'שו"ע{}'.format(string_to_add_after_he), to_change)
                new_sub = re.sub('Shulchan Aruch', 'Shulchan Aruch{}'.format(string_to_add_after_en), new_sub)
            subs.append((match.group(), new_sub))
            row['ref'] = Ref("{}:{}".format(sec.normal(), jseg + 1)).normal()
            row['old'] = match.group()
            row['new'] = new_sub
            rows.append(row.copy())
    return rows, subs


def MB(sec, jseg, text, string_to_add_after_he='', lang = 'he'):
    rows = []
    rows_en = []
    subs = []
    row = {}
    row_en = {}
    if lang == 'both':
        text_he = text[0]
        text_en = text[1]
    else:
        text_he = text
    matchs = re.finditer(mb_re, text_he)
    if lang == 'both':
        matchs_en = re.finditer('(MB|Mishnah Berurah)', text_en)
        # matchs = list(matchs) + list(matchs_en)
        # if not len(re.findall('(MB|Mishnah Berurah)', text_en)) == len(re.findall(mb_re, text_he)):
        #     print("sec {} heb {} en {}".format(sec, len(matchs_en), len(re.findall(mb_re, text_he))))
        #     return rows, subs
        for match in matchs_en:
            new_sub = re.sub('MB', 'Mishnah Berurah', match.group())
            subs.append((match.group(), new_sub))
            row_en['ref'] = Ref("{}:{}".format(sec.normal(), jseg + 1)).normal()
            row_en['old'] = match.group()
            row_en['new'] = new_sub
            rows.append(row_en.copy())
    for match in matchs:
        new_sub = re.sub('מ"ב', 'משנה ברורה', match.group())
        subs.append((match.group(), new_sub))
        row['ref'] = Ref("{}:{}".format(sec.normal(), jseg + 1)).normal()
        row['old'] = match.group()
        row['new'] = new_sub
        rows.append(row.copy())
        # if lang == 'both':
        #     for match in matchs:
        #         new_sub = re.sub('מ"ב', 'משנה ברורה', match.group())
        #         subs.append((match.group(), new_sub))
        #         row['ref'] = Ref("{}:{}".format(sec.normal(), jseg + 1)).normal()
        #         row['old'] = match.group()
        #         row['new'] = new_sub
        #         rows.append(row.copy())
    return rows, subs


def chnage_text(section_tuples, string_to_add_after_he="", string_to_add_after_en='', post=False, server='local', change='SA', lang='he'):
    rows = []
    subs = []
    for (sec, sec_text) in section_tuples:
        new_sec_text = []
        for jseg, text in enumerate(sec_text):
            # subs = []
            if change == 'SA' or change == 'all':
                changed_rows, changed_subs = SA(sec, jseg, text, string_to_add_after_he, string_to_add_after_en, lang=lang)
            if change == 'MB':
                changed_rows, changed_subs = MB(sec, jseg, text, lang=lang)
            rows.extend(changed_rows)
            subs.extend(changed_subs)
            new_text = text_substitution(text, subs)
            # for lang_text in text:
            #     new_text_lang = lang_text
            #     for sub in changed_subs:
            #         new_text_lang = re.sub(sub[0], sub[1], new_text_lang)
            #         print("{}:{}".format(sec.normal(), jseg+1))
            #         print(new_text_lang)  # post back to server here
            #     new_text.append(new_text_lang)
            if change == 'all':
                changed_rows, changed_subs = MB(sec, jseg, new_text, string_to_add_after_he, lang=lang)
                rows.extend(changed_rows)
                new_text = text_substitution(new_text, changed_subs)
                # for sub in changed_subs:
                #     new_text = re.sub(sub[0], sub[1], new_text)
                #     print("{}:{}".format(sec.normal(), jseg + 1))
                #     print(new_text)  # post back to server here
            if changed_subs:
                print("{}:{}".format(sec.normal(), jseg+1))
                print(new_text)
                if post:
                    post_to_server(sec, jseg, new_text, server)
            new_sec_text.append(new_text)
        # if post:
        #     post_to_server(sec, -1, new_sec_text, server)
    return rows


def text_substitution(text, subs):
    new_text = []
    for lang_text in text:
        new_text_lang = lang_text
        for sub in subs:
            new_text_lang = re.sub(sub[0], sub[1], new_text_lang)
            # print("{}:{}".format(sec.normal(), jseg + 1))
            # print(new_text_lang)  # post back to server here
        new_text.append(new_text_lang)
    return new_text


def write_to_csv(rows, filename):
    with codecs.open('{}.csv'.format(filename), 'w') as csv_file:
        writer = csv.DictWriter(csv_file, ['ref', 'old', 'new'])  # fieldnames = obj_list[0].keys())
        writer.writeheader()
        writer.writerows(rows)

def post_to_server(sec, jseg, new_text, post = 'local', vtitle_he="Peninei Halakhah, Yeshivat Har Bracha", vtitle_en = "Peninei Halakhah, English ed. Yeshivat Har Bracha"):
    if post == 'server':  # from local settings
        topost = {
            'versionTitle': "Peninei Halakhah, Yeshivat Har Bracha",
            'versionSource': "https://ph.yhb.org.il",
            'language': 'he',
            'text': new_text
        }
        post_ref = "{}.{}".format(sec.normal(), jseg + 1) if jseg + 1 else "{}".format(sec.normal())
        post_text(post_ref, topost) #  server=SEFARIA_SERVER
    elif post == 'local':
        for t in new_text:
            lang = "he" if is_hebrew(t) else "en"
            vtitle = vtitle_he if lang == 'he' else vtitle_en
            tc = TextChunk(Ref("{}.{}".format(sec.normal(), jseg + 1)), lang=lang,
                           vtitle=vtitle)
            tc.text = t
            tc.save(force_save=True)

def find_SA_appearances(ind):
    for r in ind.all_segment_refs():
        tc = r.text('en').text
        for match in re.findall('\([^()]*(Shulchan Aruch)[^()]*\)', tc):
            print(r.normal())
            print(match)


if __name__ == "__main__":
    book = 'Prayer'
    lang = 'both'
    section_tuples = retrieve_segments('Peninei Halakhah, {}'.format(book), lang=lang)
    rows = chnage_text(section_tuples, string_to_add_after_he=' או"ח', string_to_add_after_en=', Orach Chaim', change='all', lang=lang, post=True)
    write_to_csv(rows, '/home/shanee/www/Sefaria-Data/sources/Peninei Halacha/{}_all_test'.format(book))
    # post_to_server(Ref(rows[0]['ref']), rows[0]['new'], post='local')