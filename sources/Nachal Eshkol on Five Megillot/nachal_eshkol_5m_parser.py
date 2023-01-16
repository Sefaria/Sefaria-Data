# -*- coding: utf-8 -*-
import django
django.setup()
from sefaria.model import *
from linking_utilities.dibur_hamatchil_matcher import *
from sources.functions import *
import re
import unicodecsv as csv
import codecs

SERVER = u"http://nachaleshkol.sandbox.sefaria.org/"
# SERVER = u"http://localhost:8000"
FILE = u"Nachal_Eshkol_on_Five_Megillot.csv"
VERSION_TITLE = u"Nachal Eshkol al Hamesh Megilot, Warsaw, 1889"
VERSION_SOURCE = u"http://beta.nli.org.il/he/books/NNL_ALEPH001156901/NLI"

hebNames = [u"שיר השירים", u"אסתר", u"רות", u"איכה", u"קהלת"]
engNames = [u"Song of Songs", u"Esther", u"Ruth", u"Lamentations", u"Ecclesiastes"]


def parse(filename):
    shir_hashirim = []
    esther = []
    rut = []
    eicha = []
    kohelet = []

    megillot = [shir_hashirim, esther, rut, eicha, kohelet]
    curr_megillah = -1
    perek = []
    pasuk = []
    curr_perek = 0
    prev_pasuk_num = 0
    pasuk_marker = re.compile(u'(\(.{1,3}?\))')
    bolder = re.compile(u'(\A.*?\.)')
    first_line = True
    first = True

    with codecs.open(filename, 'r', 'utf-8') as f:
        for line in f:
            if u"$" in line: # if new megillah
                # if not first_line:
                #     megillot[curr_megillah].insert(curr_perek, perek[:])
                new_megillah = True
                curr_megillah += 1
                megillah_name, line = line.rstrip().split(u"$")
                curr_perek = 0

            line = line.replace(u',', u'')
            line = line[1:-1]
            line = line.replace(u':"', u':')

            match = pasuk_marker.search(line)
            if match: # if new pasuk
                pasuk = []
                pasuk_letters = (match.group(0))[1:-1]
                line = line[match.end():]

                try:
                    pasuk_num = getGematria(pasuk_letters)

                    if (curr_megillah == 0 and prev_pasuk_num == 6 and pasuk_num == 8) and first:
                        prev_pasuk_num = 150
                        first = False

                    if pasuk_num <= prev_pasuk_num:  # if new perek
                        if new_megillah and curr_megillah:
                            megillot[curr_megillah-1].append(perek[:])
                            new_megillah = False
                        elif new_megillah or not first_line:
                            megillot[curr_megillah].insert(curr_perek, perek[:])
                        curr_perek += 1
                        perek = []
                        prev_pasuk_num = 0

                finally:
                    if not first_line:
                        dibur_hamatchil = bolder.match(line)
                        line = u'<b>' + dibur_hamatchil.group(0) + u'</b>' + line[dibur_hamatchil.end():]
                    pasuk.append(line.replace("\"\"", "\""))
                    for i in range(pasuk_num - prev_pasuk_num - 1):
                        perek.append([])
                    perek.append(pasuk[:])  # (perek[something].append(pasuk[:])...)
                    prev_pasuk_num = pasuk_num
            else: # if not new pasuk
                if not first_line:
                    dibur_hamatchil = bolder.match(line)
                    line = u'<b>' + dibur_hamatchil.group(0) + u'</b>' + line[dibur_hamatchil.end():]
                perek.remove(pasuk)
                pasuk.append(line.replace("\"\"", "\""))
                perek.append(pasuk[:])
            first_line = False

    megillot[curr_megillah].insert(curr_perek, perek[:])
    return megillot


def post_index_to_server(en, he):
    root = JaggedArrayNode()
    comm_en = "Nachal Eshkol on {}".format(en)
    comm_he = u"נחל אשכול על {}".format(he)
    root.add_primary_titles(comm_en, comm_he)
    root.add_structure(["Chapter", "Verse", "Paragraph"])
    root.toc_zoom = 2
    root.validate()
    index = {
        "dependence": "Commentary",
        "base_text_titles": [en],
        "base_text_mapping": "many_to_one",
        "title": comm_en,
        "collective_title": "Nachal Eshkol",
        "schema": root.serialize(),
        "categories": ["Tanakh", "Commentary", "Nachal Eshkol"]
    }
    post_index(index, server=SERVER)


def post_text_to_server(text, en):
    send_text = {
        "text": text,
        "versionTitle": VERSION_TITLE,
        "versionSource": VERSION_SOURCE,
        "language": "he"
    }
    post_text("Nachal Eshkol on {}".format(en), send_text, server=SERVER)


if __name__ == "__main__":
    texts = parse(FILE)
    add_term("Nachal Eshkol", u"נחל אשכול")

    # c = Category()
    # c.add_primary_titles("Nachal Eshkol", u"נחל אשכול")
    # c.path = ["Tanakh", "Commentary", "Nachal Eshkol"]
    # c.save()

    add_category("Nachal Eshkol",["Tanakh", "Commentary", "Nachal Eshkol"], u"נחל אשכול")

    for name in range(5):
        post_index_to_server(engNames[name], hebNames[name])
        post_text_to_server(texts[name], engNames[name])