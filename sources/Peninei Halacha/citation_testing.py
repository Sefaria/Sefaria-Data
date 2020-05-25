# -*- coding: utf-8 -*-
import django
django.setup()
from sefaria.model import *
import requests
import regex as re
import csv
import codecs
from sources.functions import post_text

SEFARIA_SERVER = "https://topicside.cauldron.sefaria.org"

# Shulchan Arukh
sa_re = re.compile('\([^()]*?(שו"ע)(?!\s*(או"ח|יו"ד|אב"ה|חו"מ|אה"ע))[^()]*?\)')
mb_re = re.compile('\([^()]*\s+מ"ב\s+[^()]*\)')

def retrieve_segments(title, server=None):
    ind = library.get_index(title)
    sections = ind.all_section_refs()
    segments = []
    for sec in sections:
        if server:
            sec_text = requests.get("{}/api/texts/{}?context=0"
                                    .format(server, sec.normal())).json()["he"]

        else:
            sec_text = sec.text('he').text
        segments.append((sec, sec_text))
    return segments

def SA(sec, jseg, text, string_to_add_before=''):
    rows = []
    subs = []
    row = {}
    matchs = re.finditer(sa_re, text)
    for match in matchs:
        to_change = match.group()
        new_subd = False
        if re.search('רמ"א', match.group()):
            to_change = re.sub('שו"ע\s*?(?P<vav>ו?)(רמ"א)', 'רמ"א \g<vav>שו"ע', match.group())
            if not re.search(sa_re, to_change):
                new_sub = to_change
                new_subd = True
        if not new_subd:
            new_sub = re.sub('שו"ע', 'שו"ע {}'.format(string_to_add_before), to_change)
        subs.append((match.group(), new_sub))
        row['ref'] = Ref("{}:{}".format(sec.normal(), jseg + 1)).normal()
        row['old'] = match.group()
        row['new'] = new_sub
        rows.append(row.copy())
    return rows, subs

def MB(sec, jseg, text, string_to_add_before=''):
    rows = []
    subs = []
    row = {}
    matchs = re.finditer(mb_re, text)
    for match in matchs:
        new_sub = re.sub('מ"ב', 'משנה ברורה', match.group())
        subs.append((match.group(), new_sub))
        row['ref'] = Ref("{}:{}".format(sec.normal(), jseg + 1)).normal()
        row['old'] = match.group()
        row['new'] = new_sub
        rows.append(row.copy())
    return rows, subs


def chnage_text(section_tuples, string_to_add_before ="", post=False, server='local', change='SA'):
    rows = []
    subs = []
    for (sec, sec_text) in section_tuples:
        new_sec_text = []
        for jseg, text in enumerate(sec_text):
            # subs = []
            if change == 'SA':
                changed_rows, changed_subs = SA(sec, jseg, text, string_to_add_before)
            else:  # if change == 'MB':
                changed_rows, changed_subs = MB(sec, jseg, text, string_to_add_before)
            rows.extend(changed_rows)
            subs.extend(changed_subs)
            new_text = text
            for sub in subs:
                new_text = re.sub(sub[0], sub[1], new_text)
                print("{}:{}".format(sec.normal(), jseg+1))
                print(new_text)  # post back to server here
            if post and changed_subs:
                post_to_server(sec, jseg, new_text, server)
            new_sec_text.append(new_text)
        # if post:
        #     post_to_server(sec, -1, new_sec_text, server)
    return rows


def write_to_csv(rows, filename):
    with codecs.open('{}.csv'.format(filename), 'w') as csv_file:
        writer = csv.DictWriter(csv_file, ['ref', 'old', 'new'])  # fieldnames = obj_list[0].keys())
        writer.writeheader()
        writer.writerows(rows)

def post_to_server(sec, jseg, new_text, post = 'local', text_version='', vtitle="Peninei Halakhah, Yeshivat Har Bracha"):
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
        tc = TextChunk(Ref("{}.{}".format(sec.normal(), jseg + 1)), lang='he',
                       vtitle=vtitle)
        tc.text = new_text
        tc.save(force_save=True)

if __name__ == "__main__":
    section_tuples = retrieve_segments('Peninei Halakhah, Prayer')
    rows = chnage_text(section_tuples, string_to_add_before='או"ח', change='MB')
    write_to_csv(rows, '/home/shanee/www/Sefaria-Data/sources/Peninei Halacha/Prayer_MB')
    # post_to_server(Ref(rows[0]['ref']), rows[0]['new'], post='local')