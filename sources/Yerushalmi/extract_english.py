# encoding=utf-8
import django
django.setup()
import os
import bs4
import csv
import json
from itertools import zip_longest
from data_utilities.util import traverse_ja
from sources.Yerushalmi.sefaria_objects import *
from sources.Yerushalmi.text_mapping import create_helper_html
from data_utilities.ParseUtil import ParsedDocument, Description, ParseState
import yutil


"""
loop through xml files
get book elements
lookup title via json
proceed as normal
For each tractate:
 - Ref, English, Hebrew, Mehon-Hebrew (talmud)
 - Chapter, English, (Hebrew, Mehon-Hebrew) (mishna)
"""



def count_talmud_segments(title, vtitle='Guggenheimer'):
    oref = Ref(title)
    ja = oref.text(lang='he', vtitle=vtitle).ja().array()
    count = 0
    for segment in traverse_ja(ja):
        if segment['indices'][2]:
            count += 1
    return count


def get_chapter(tag: bs4.Tag):
    for parent in tag.parents:
        if parent.name == 'chapter':
            return parent['num']
    return None

# Is this the translation of a Mishnah? (This logic doesn't work for Shabbat and Eruvin. We're not sure what logic does.)
def is_mishna(tag: bs4.Tag):
    return 'mishna' in {n.name for n in tag.parents}


def is_ja_talmud(segment):
    return bool(segment['indices'][2])  # first segment of every halakha is a mishna and the index is therefore 0


def is_ja_mishna(segment):
    return not is_ja_mishna(segment)


def get_footnote_map(soup):
    fn_map = {}
    for fn in soup.find_all("fn"):
        id = fn["id"]
        label = fn.label.text
        txt = " ".join([s for s in fn.p.stripped_strings])
        fn_map[id] = {"label": label, "txt": txt}
    return fn_map


def get_text_pairs(soup):
    pairs = []
    source_paras = soup.find_all(lambda tag: tag.name == 'source_para' and 'variant_text_block' not in {n.name for n in tag.parents})
    for source_para in source_paras:
        trans_para = soup.find("trans_para", pararef=source_para["id"])
        pairs += [(
            " ".join([s for s in source_para.stripped_strings]),
            " ".join([s for s in trans_para.stripped_strings])
        )]
    return pairs

with open('guggenheimer_titles.json') as fp:
    titles_to_file_mapping = json.load(fp)
book_mapping = {
    value: key.replace("Jerusalem Talmud", "JTmock") for key, value in titles_to_file_mapping.items()
}
# print(book_mapping)

xml_dir, output_dir = 'GuggenheimerXmls', 'code_output/english_guggenheimer'
xml_files = [x for x in os.listdir(xml_dir) if x.endswith('xml')]
for xml_file in xml_files:
    with open(os.path.join(xml_dir, xml_file)) as fp:
        soup = bs4.BeautifulSoup(fp, 'xml')
    for book in soup.find_all('book'):
        title = book_mapping[book['id']]
        for chapter in book.find_all('chapter'):
            chap_num = int(chapter["num"])
            print(f'{title} {chap_num}')
            fn_map = get_footnote_map(chapter)
            text_pairs = get_text_pairs(chapter)
            pass

        trans_para = book.find_all('trans_para')

        talmud_only, mishna_only = [], []
        for t in trans_para:
            if is_mishna(t):
                mishna_only.append(t)
            else:
                talmud_only.append(t)

        oref = Ref(title)
        gugg_chunk, mehon_chunk = oref.text(lang='he', vtitle='Guggenheimer'), oref.text(lang='he', vtitle='Mehon-Mamre')
        gugg_mishna, gugg_talmud = filter(is_ja_mishna, traverse_ja(gugg_chunk.text)), filter(is_ja_talmud, traverse_ja(gugg_chunk.text))
        mehon_mishna, mehon_talmud = filter(is_ja_mishna, traverse_ja(mehon_chunk.text)), filter(is_ja_talmud, traverse_ja(mehon_chunk.text))
        gugg_talmud = list(gugg_talmud)
        print(title, "Extracted English Segments:", len(talmud_only), "Local Talmud:", len(gugg_talmud))
        talmud_output = []
        for eg, hg, mm in zip_longest(talmud_only, gugg_talmud, mehon_talmud, fillvalue=''):
            try:
                iref = ':'.join([str(x+1) for x in hg['indices']])
            except TypeError:
                iref = 'N/A'
            talmud_output.append({
                'Ref': iref,
                # todo: instead of " ".join, write a method that takes a tag and returns a more desireable result
		'English': ' '.join(eg.text.split()) if isinstance(eg, bs4.Tag) else eg,
                'Hebrew': hg['data'] if isinstance(hg, dict) else hg,
                'Mehon-Mamre': mm['data'] if isinstance(mm, dict) else mm,
            })
        trac_output = os.path.join(output_dir, title.replace(' ', '_'))
        if not os.path.exists(trac_output):
            os.mkdir(trac_output)
        with open(os.path.join(trac_output, 'english_talmud.csv'), 'w') as fp:
            writer = csv.DictWriter(fp, fieldnames=['Ref', 'English', 'Hebrew', 'Mehon-Mamre'])
            writer.writeheader()
            writer.writerows(talmud_output)

        mishnayot_out = []
        last_chapter = 1
        for mishna in mishna_only:
            chapter = get_chapter(mishna)
            if not chapter:
                chapter = last_chapter
            last_chapter = chapter
            mishnayot_out.append({
                'Chapter': chapter,
                'Mishnah': ' '.join(mishna.text.split())
            })
        with open(os.path.join(trac_output, 'english_mishnah.csv'), 'w') as fp:
            writer = csv.DictWriter(fp, fieldnames=['Chapter', 'Mishnah'])
            writer.writeheader()
            writer.writerows(mishnayot_out)


# print(count_talmud_segments('JTmock Berakhot'))
# with open('GuggenheimerXmls/zeraim_berakhot.xml') as fp:
#     soup = bs4.BeautifulSoup(fp, 'xml')
# trans_para = soup.find_all('trans_para')
# print(len(trans_para))
# talmud_only = [t for t in trans_para if not is_mishna(t)]
# mishna_only = [t for t in trans_para if is_mishna(t)]
# print(len(talmud_only))
# r = Ref("JTmock Berakhot")
# t = r.text(lang='he', vtitle='Guggenheimer').text
# local_talmud = [q for q in traverse_ja(t) if q['indices'][2]]
# local_mishna = [q for q in traverse_ja(t) if not q['indices'][2]]
# out = [
#     f'<tr><td>{e}</td><td>{h["data"]}</td></tr>'
#     for e, h in zip(talmud_only, local_talmud)
# ]
# create_helper_html(out, 'e_h_compare.html')
