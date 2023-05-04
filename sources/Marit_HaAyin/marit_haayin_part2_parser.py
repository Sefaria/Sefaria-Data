# -*- coding: utf-8 -*-
import django
django.setup()
from sefaria.model import *
from sefaria.model.schema import AddressTalmud
from linking_utilities.dibur_hamatchil_matcher import *
from sources.functions import *
import re
import codecs

# SERVER = u"http://localhost:8000"
SERVER = u"http://marithaayin.sandbox.sefaria.org"
FILE = u"Marit_HaAyin_part_2.txt"
VERSION_TITLE = u"Marit HaAyin, Jerusalem 1960"
VERSION_SOURCE = u"http://beta.nli.org.il/he/books/NNL_ALEPH001139211/NLI"

hebNames = [u"משנה שקלים", u"משנה עדיות", u"משנה אבות", u"משנה מדות", u"משנה קינים"]
engNames = [u"Mishnah Shekalim", u"Mishnah Eduyot", u"Pirkei Avot", u"Mishnah Middot", u"Mishnah Kinnim"]
sedarim = [u"Seder Moed", u"Seder Nezikin", u"Seder Nezikin", u"Seder Kodashim", u"Seder Kodashim"]

def parse(filename):
    perek = []
    perakim = []
    diburrei_hamatchil = []
    curr_mesechet = -1
    shekalim = []
    eduyot = []
    avot = []
    middot = []
    kinnim = []
    mesechtot = [shekalim, eduyot, avot, middot, kinnim]
    first_mishnah = True
    mishnah_num = 0
    perek_num = 0
    dibur_hamatchil = ""
    check = True

    mishnah_marker = re.compile(u'(\[(.*) (.*),(.*)\])')
    first_parag_marker1 = re.compile(u'@11(.*?)@5')
    other_parag_marker = re.compile(u'@11(.*?)@33')


    with codecs.open(filename, 'r', 'utf-8') as f:
        for line in f:
            if u"@00" in line: # if new mesechet
                curr_mesechet += 1
                if curr_mesechet:
                    diburrei_hamatchil.append(re.sub(u' +', u' ', dibur_hamatchil))
                    perek.append(diburrei_hamatchil)
                    perakim.append(perek)
                    mesechtot[curr_mesechet-1] = perakim[:]
                    prev_mishnah_num = 0
                    mishnah_num = 0
                    perek_num = 0
                    prev_perek_num = 0
                    perakim = []
                    perek = []
                    diburrei_hamatchil = []
                    first_mishnah = True
                continue

            mishnah_match = mishnah_marker.search(line)
            if mishnah_match: # if new mishnah
                if not first_mishnah:
                    diburrei_hamatchil.append(re.sub(u' +', u' ', dibur_hamatchil))
                    perek.append(diburrei_hamatchil)
                    diburrei_hamatchil = []
                first_mishnah = False
                perek_g = mishnah_match.group(3)
                mishnah_g = mishnah_match.group(4)

                try:
                    prev_mishnah_num = mishnah_num
                    prev_perek_num = perek_num
                    perek_num = getGematria(perek_g)
                    mishnah_num = getGematria(mishnah_g)

                    if perek_num > prev_perek_num and perek:
                        perakim.append(perek)
                        perek = []
                        prev_mishnah_num = 0

                except:
                    print "There was an issue with gematria"
                finally:
                    for i in range(perek_num - prev_perek_num - 1):
                        perakim.append([])
                        prev_mishnah_num = 0
                    for i in range(mishnah_num - prev_mishnah_num - 1):
                        perek.append([])

            # each line is a new paragraph/bold
            parag_match = first_parag_marker1.search(line)
            if parag_match:
                if not mishnah_match:  # new paragraph from 11 to 5
                    diburrei_hamatchil.append(re.sub(u' +', u' ', dibur_hamatchil))
                dibur_hamatchil = parag_match.group(1).rstrip().replace(u"@33", u"")  # 11@ to 5@
                dibur_hamatchil = u"<b>" + dibur_hamatchil + u"</b>"
            else:  # new paragraph from 11 to 33
                parag_match = other_parag_marker.search(line)
                bold = parag_match.group(1).rstrip()  # 11@ to 33@
                line = u"<br>" + u"<b>" + bold + u"</b>" + line[parag_match.end():]
                check = False

            if check:
                line = line[parag_match.end():]
            check = True

            dibur_hamatchil += u" " + line.rstrip()

        diburrei_hamatchil.append(re.sub(u' +', u' ', dibur_hamatchil))
        perek.append(diburrei_hamatchil)
        perakim.append(perek)
        mesechtot[4] = perakim[:]

    return mesechtot


def post_index_to_server(en, he, seder):
    root = JaggedArrayNode()
    comm_en = "Marit HaAyin on {}".format(en)
    comm_he = u"מראית העין על {}".format(he)
    root.add_primary_titles(comm_en, comm_he)
    root.add_structure(["Chapter", "Mishnah", "Comment"], address_types=['Perek', 'Mishnah', 'Integer'])
    root.depth = 3
    root.validate()
    index = {
        "dependence": "Commentary",
        "base_text_titles": [en],
        "base_text_mapping": "many_to_one",
        "title": comm_en,
        "collective_title": "Marit HaAyin",
        "schema": root.serialize(),
        "categories": ["Mishnah", "Commentary", "Marit HaAyin", seder]
    }
    post_index(index, server=SERVER)


def post_text_to_server(text, en):
    send_text = {
        "text": text,
        "versionTitle": VERSION_TITLE,
        "versionSource": VERSION_SOURCE,
        "language": "he"
    }
    post_text("Marit HaAyin on {}".format(en), send_text, server=SERVER)

if __name__ == "__main__":
    texts = parse(FILE)
    #add_term("Marit HaAyin", u"מראית העין")

    # c1 = Category()
    # c1.add_primary_titles("Marit HaAyin", u"מראית העין")
    # c1.path = ["Mishnah", "Commentary", "Marit HaAyin", sedarim[0]]
    # c1.save()
    # c2 = Category()
    # c2.add_primary_titles("Marit HaAyin", u"מראית העין")
    # c2.path = ["Mishnah", "Commentary", "Marit HaAyin", sedarim[1]]
    # c2.save()
    add_category("Marit HaAyin",["Mishnah", "Commentary", "Marit HaAyin"], u"מראית העין")
    add_category(sedarim[0],["Mishnah", "Commentary", "Marit HaAyin", sedarim[0]], u"סדר מועד")
    add_category(sedarim[1],["Mishnah", "Commentary", "Marit HaAyin", sedarim[1]], u"סדר נזיקין")
    add_category(sedarim[3], ["Mishnah", "Commentary", "Marit HaAyin", sedarim[3]], u"סדר קדשים")

    for name in range(5):
        post_index_to_server(engNames[name], hebNames[name], sedarim[name])
        post_text_to_server(texts[name], engNames[name])
