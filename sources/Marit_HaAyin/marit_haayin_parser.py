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
FILE = u"Marit_HaAyin.txt"
VERSION_TITLE = u"Marit HaAyin, Jerusalem 1960"
VERSION_SOURCE = u"http://beta.nli.org.il/he/books/NNL_ALEPH001139211/NLI"

dh3 = {}
mesechtot = {}

sedarim = ["Seder Nashim", "Seder Moed", "Seder Nashim", "Seder Nezikin", "Seder Nezikin", "Seder Nashim",
           "Seder Nezikin", "Seder Moed", "Seder Moed", "Seder Moed", "Seder Nezikin", "Seder Nashim",
           "Seder Moed", "Seder Kodashim", "Seder Moed", "Seder Nashim", "Seder Nezikin", "Seder Tahorot",
           "Seder Kodashim", "Seder Nashim", "Seder Kodashim", "Seder Moed", "Seder Kodashim", "Seder Zeraim",
           "Seder Kodashim", "Seder Kodashim", "Seder Moed", "Seder Nezikin", "Seder Moed", "Seder Kodashim",
           "Seder Nezikin", "Seder Nashim", "Seder Nezikin", "Seder Kodashim", "Seder Moed", "Seder Kodashim",
           "Seder Moed"]

def parse(filename):
    dapim = []
    diburrei_hamatchil = []
    curr_mesechet = -1

    daf_marker = re.compile(u'(\[(.*) (.*),(.*)\])')
    first_parag_marker1 = re.compile(u'@11(.*?)@5')
    other_parag_marker = re.compile(u'@11(.*?)@33')
    midl_bold_marker = re.compile(u'(.*?)@66(.*?)@5(.*)')

    first_daf = True
    dibur_hamatchil = ""
    check = True
    daf_index = 0
    time = 0
    test1 = 0
    test2 = 0
    test3 = 0
    dh = []
    dh2 = {}

    with codecs.open(filename, 'r', 'utf-8') as f:
        for line in f:
            if u"@00" in line: # if new mesechet
                curr_mesechet += 1
                if curr_mesechet:
                    dh2[daf_index] = dh[:]
                    diburrei_hamatchil.append(re.sub(u' +', u' ', dibur_hamatchil))
                    dapim.append(diburrei_hamatchil)
                    test1 += 1
                    mesechtot[mesechet_name] = dapim[:]
                    dh3[mesechet_name] = dict(dh2)
                    dh2 = {}
                    dapim = []
                    dh = []
                    diburrei_hamatchil = []
                    prev_daf_index = 0
                    daf_index = 0
                    first_daf = True
                trash, mesechet_name = line.split(u"מסכת")
                mesechet_name = mesechet_name.strip()
                continue

            daf_match = daf_marker.search(line)
            if daf_match: # if new daf
                if not first_daf:
                    dh2[daf_index] = dh[:]
                    dh = []
                    diburrei_hamatchil.append(re.sub(u' +', u' ', dibur_hamatchil))
                    dapim.append(diburrei_hamatchil)
                    test2 += 1
                    diburrei_hamatchil = []
                first_daf = False
                daf = daf_match.group(3)
                amud = daf_match.group(4)

                try:
                    daf_num = getGematria(daf)
                    amud_num = getGematria(amud)
                    prev_daf_index = daf_index
                    daf_index = daf_num*2 + amud_num - 2
                except:
                    print "There was an issue with gematria"
                finally:
                    for i in range(daf_index - prev_daf_index - 1):
                        dapim.append([])
                        test3 += 1

            # each line is a new paragraph/bold
            parag_match = first_parag_marker1.search(line)
            if parag_match:  # new paragraph from 11 to 5
                if u"@66" in parag_match.group(0): # if there's a 66 in the middle (the 11 to 5 is fake)
                    parag_match = other_parag_marker.search(parag_match.group(0))
                    bold = parag_match.group(1).rstrip()  # 11@ to 33@
                    line = u"<br>" + u"<b>" + bold + u"</b>" + line[parag_match.end():]
                    check = False
                else:  # confirmed paragraph from 11 to 5
                    if dibur_hamatchil and not daf_match:
                        diburrei_hamatchil.append(re.sub(u' +', u' ', dibur_hamatchil))
                    dibur_hamatchil = parag_match.group(1).rstrip().replace(u"@33", u"")  # 11@ to 5@
                    dh.append(re.sub(u' +', u' ', dibur_hamatchil))
                    dibur_hamatchil = u"<b>" + dibur_hamatchil + u"</b>"
            else:  # new paragraph from 11 to 33
                parag_match = other_parag_marker.search(line)
                bold = parag_match.group(1).rstrip()  # 11@ to 33@
                line = u"<br>" + u"<b>" + bold + u"</b>" + line[parag_match.end():]
                check = False
                time += 1

            if check:
                line = line[parag_match.end():]
            check = True

            bold_match = midl_bold_marker.search(line)
            while bold_match:  # if bold in middle of paragraph
                line = bold_match.group(1) + u"<b>" + bold_match.group(2) + u"</b>" + bold_match.group(3)
                bold_match = midl_bold_marker.search(line)
            dibur_hamatchil += u" " + line.rstrip()

        dh2[daf_index] = dh[:]
        dh3[mesechet_name] = dict(dh2)
        dapim.append(diburrei_hamatchil)
        mesechtot[mesechet_name] = dapim[:]

    return mesechtot


def post_index_to_server(en, he, curr_seder):
    root = JaggedArrayNode()
    comm_en = "Marit HaAyin on {}".format(en)
    comm_he = u"מראית העין על {}".format(he)
    root.add_primary_titles(comm_en, comm_he)
    root.add_structure(["Daf", "Line"], address_types=['Talmud', 'Integer'])
    root.validate()
    index = {
        "dependence": "Commentary",
        "base_text_titles": [en],
        "title": comm_en,
        "collective_title": "Marit HaAyin",
        "schema": root.serialize(),
        "categories": ["Talmud", "Bavli", "Commentary", "Marit HaAyin", sedarim[curr_seder]]
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


def post_links_to_server(name, eng_name, data):
    links = []
    amud = 1
    dh_count = 0
    not_match1 = 0
    match2 = 0
    contained = False
    full_words = ""
    dh_out_of_order = set()
    no_match = set()

    for comments in data:
        if comments:
            base = TextChunk(Ref("{} {}".format(eng_name, AddressTalmud.toStr('en', amud))), lang='he')
            n = len("".join(base.text).split())/2
            results = match_ref(base, dh3[name][amud], base_tokenizer=lambda x: x.split(), boundaryFlexibility=n)
            for match_n, match in enumerate(results["matches"]):
                if match:
                    m = "Marit HaAyin on {} {}:{}".format(eng_name, AddressTalmud.toStr("en", amud), match_n + 1)
                    link = {"refs": [match.normal(), m], "generated_by": "Marit HaAyin on {}".format(eng_name),
                            "auto": True,
                            "type": "Commentary"}
                    try:
                        if dh3[name][amud][match_n] not in full_words:
                            links.append(link)
                            full_words += dh3[name][amud][match_n]
                    except:
                        print "Index error"
                else:
                    not_match1 += 1
                    amud2 = amud
                    if amud % 2:
                        amud2 += 1
                    else:
                        amud2 -= 1
                    try:
                        base = TextChunk(Ref("{} {}".format(eng_name, AddressTalmud.toStr('en', amud2))), lang='he')
                        n = len("".join(base.text).split()) / 2
                        results = match_ref(base, dh3[name][amud], base_tokenizer=lambda x: x.split(), boundaryFlexibility=n)
                    except:
                        print "last amud"
                    for match_n, match in enumerate(results["matches"]):
                        if match:
                            m = "Marit HaAyin on {} {}:{}".format(eng_name, AddressTalmud.toStr("en", amud2),
                                                                  match_n + 1)
                            link = {"refs": [match.normal(), m], "generated_by": "Marit HaAyin on {}".format(eng_name),
                                    "auto": True,
                                    "type": "Commentary"}
                            if dh3[name][amud][match_n] not in full_words:
                                links.append(link)
                                full_words += dh3[name][amud][match_n]
                                match2 += 1
                                temp = mesechtot[name][amud-1][match_n]
                                mesechtot[name][amud2-1].append(temp)
                                mesechtot[name][amud-1].remove(temp)

                                temp2 = dh3[name][amud][match_n]
                                try:
                                    dh3[name][amud2].append(temp2)
                                except:
                                    dh3[name][amud2] = [temp2]
                                dh3[name][amud].remove(temp2)
                                dh_out_of_order.add(amud)

                        else:

                            base = TextChunk(Ref("{} {}".format(eng_name, AddressTalmud.toStr('en', amud))), lang='he')
                            n = len("".join(base.text).split()) / 2
                            results = match_ref(base, dh3[name][amud], base_tokenizer=lambda x: x.split(), daf_skips=5, rashi_skips=5, overall=5, boundaryFlexibility=n)

                            for match_n, match in enumerate(results["matches"]):
                                if match:
                                    m = "Marit HaAyin on {} {}:{}".format(eng_name, AddressTalmud.toStr("en", amud),
                                                                          match_n + 1)
                                    link = {"refs": [match.normal(), m],
                                            "generated_by": "Marit HaAyin on {}".format(eng_name),
                                            "auto": True,
                                            "type": "Commentary"}
                                    if dh3[name][amud][match_n] not in full_words:
                                        links.append(link)
                                        full_words += dh3[name][amud][match_n]
                                        match2 += 1
                                else:
                                    no_match.add(amud)


            dh_count += 1
        amud += 1

    print "For {}: Matches out of order: {}\n" \
          "            No matches found: {}".format(eng_name, dh_out_of_order, no_match)
    post_link(links, server=SERVER)


if __name__ == "__main__":
    reached = False
    texts = parse(FILE)
    add_term("Marit HaAyin", u"מראית העין")
    #
    add_category("Marit HaAyin",["Talmud", "Bavli", "Commentary", "Marit HaAyin"], u"מראית העין")
    for seder in list(set(sedarim)):
        heb_name = library.get_term(seder).get_primary_title('he')
        add_category(seder, ["Talmud", "Bavli", "Commentary", "Marit HaAyin", seder], heb_name)

    count = 0
    for name, data in texts.items():
        eng_name = library.get_index(name).get_title('en')
        post_index_to_server(eng_name, name, count)
        post_text_to_server(data, eng_name)
        post_links_to_server(name, eng_name, data)
        count += 1
