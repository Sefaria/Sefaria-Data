import django
django.setup()
from docx2python import docx2python
from bs4 import BeautifulSoup
from os import walk
from sefaria.model.schema import TitleGroup
import re
from sefaria.model import *
from sefaria.system.exceptions import InputError
from sources.functions import *
from time import sleep

ftnote_counter = 0

class Version:
    def __init__(self, title, vtitle, vsource):
        self.title = title
        self.vtitle = vtitle
        self.vsource = vsource

ner_mitzvah_version = Version("Ner Mitzvah", "Ner Mitzvah, with footnotes and annotations by Rabbi Yehoshua D. Hartman, Machon Yerushalyim, 2012",
                              "https://www.nli.org.il/he/books/NNL_ALEPH002302983/NLI")
derech_chaim_version = Version("Derech Chaim", "Derech Chaim, with footnotes and annotations by Rabbi Yehoshua D. Hartman, Machon Yerushalyim, 2005-2010",
                               "https://www.nli.org.il/he/books/NNL_ALEPH005271216/NLI")
beer_hagolah_version = Version("Be'er HaGolah", "Be'er HaGolah, with footnotes and annotations by Rabbi Yehoshua D. Hartman, Machon Yerushalyim, 2002",
                               "https://www.nli.org.il/he/books/NNL_ALEPH002605581/NLI")
gevurot_hashem_version = Version("Gevurot Hashem", "Gevurot Hashem, with footnotes and annotations by Rabbi Yehoshua D. Hartman, Machon Yerushalyim, 2015-2020",
                                 "https://www.nli.org.il/he/books/NNL_ALEPH003874699/NLI")
ohr_chadash_version = Version("Ohr Chadash", "Ohr Chadash, with footnotes and annotations by Rabbi Yehoshua D. Hartman, Machon Yerushalyim, 2014",
                              "https://www.nli.org.il/he/books/NNL_ALEPH004713598/NLI")
netiv_version = Version("Netivot Olam, Netiv Hatorah", "Netivot Olam, Netiv Hatorah, with footnotes and annotations by Rabbi Yehoshua D. Hartman, Machon Yerushalyim, 2012",
                        "https://www.nli.org.il/he/books/NNL_ALEPH003379908/NLI")
versions = [ner_mitzvah_version, derech_chaim_version, beer_hagolah_version, gevurot_hashem_version, ohr_chadash_version, netiv_version]

def get_footnotes(document):
    text = []
    prev_found_ftnote = False
    ftnotes = list(document.footnotes[0][0][0])
    new_ftnotes = []
    counter = -1
    for ftnote in ftnotes:
        if not ftnote:
            continue
        ftnote = re.sub("&(.*?)\^(.*?)", "<b>\g<1></b>\g<2>", ftnote)
        ftnote = re.sub("@(.*?)\^(.*?)", "<b>\g<1></b>\g<2>", ftnote)
        ftnote = ftnote.replace("<> ", "")
        if ftnote.startswith("footnote"):
            counter += 1
            new_ftnotes.append("")
        elif not ftnote.startswith("%"):
            new_ftnotes[counter] += ftnote + " "
        else:
            counter += 2
            new_ftnotes.append(ftnote)
            new_ftnotes.append("")
    if new_ftnotes[0] == "":
        new_ftnotes = new_ftnotes[1:]
    return new_ftnotes
#
# def process_footnotes(document, file, ftnote_counter):
#     actual_footnotes = {0: []}
#     mishnah = 0
#     prev_mishnah = ""
#     for ftnote in document.footnotes[0][0][0]:
#
#         if start > -1:
#             ftnote_counter += 1
#             actual_footnotes[mishnah].append(str(ftnote_counter) + " " + ftnote[start+2:])
#         else:
#             poss_match = re.search("%.*?\[(.*?)\]", ftnote)
#             if poss_match:
#                 poss_match = poss_match.group(1).replace("משנה", "").replace("המשך", "").replace("משניות", "")
#                 poss_match = re.sub('(פ".*?) ', '', poss_match).split("-")[0].replace('"', "").strip()
#                 if "DH" in file and poss_match.startswith("מ"):
#                     poss_match = poss_match[1:]
#                 poss_mishnah = getGematria(poss_match)
#                 if mishnah >= poss_mishnah:
#                     print("{} {} vs {}".format(file, ftnote, prev_mishnah))
#                 else:
#                     mishnah = poss_mishnah
#                     actual_footnotes[mishnah] = []
#                 prev_mishnah = ftnote
#
#     if len(actual_footnotes.keys()) == 1:
#         actual_footnotes = actual_footnotes[0]
#     else:
#         if len(actual_footnotes[0]) != 0:
#             print(file)
#         actual_footnotes.pop(0)
#         actual_footnotes = convertDictToArray(actual_footnotes)
#     return actual_footnotes, ftnote_counter


def parse_body(document, title, ftnotes, start_at=0):
    body = document.body[0][0][0]
    new_body = []
    last_ftnote_found = 0
    first_ftnote_found = False
    first_ftnote = 0
    for comment in body:
        if not comment:
            continue
        finds = list(re.finditer("----footnote(\d+)----", comment))
        comment = re.sub("#(.*?)=(.*?)", "<b>\g<1></b>\g<2>", comment)
        comment = re.sub("@(.*?)\^(.*?)", "<b>\g<1></b>\g<2>", comment)
        comment = re.sub("&(.*?)\^(.*?)", "<b>\g<1></b>\g<2>", comment)
        comment = re.sub("\s(\S{,15})\^\s", " <b>\g<1></b> ", comment).replace("<b>\\", "<b>")
        for match in finds:
            full_text = match.group(0)
            digit = match.group(1)
            actual_digit = int(digit)
            if not first_ftnote_found:
                first_ftnote_found = True
                first_ftnote = actual_digit
            num_for_tag = start_at + actual_digit - first_ftnote + 1
            i_tag = """<i data-commentator="Footnotes and Annotations" data-label="{}"></i>""".format(num_for_tag)
            last_ftnote_found = num_for_tag
            assert len(comment.split(full_text)) is 2
            comment = comment.replace(full_text, i_tag)
        new_body.append(comment)
    return new_body, last_ftnote_found


def process_depth_3(depth_2_arr, file):
    mishnayot = {1: []}
    mishnah = 1
    prev_mishnah = (None, 0)
    for n, line in enumerate(depth_2_arr):
        if not line.strip():
            continue
        poss_match = re.search("%.*?\[(.*?)\]", line)
        if poss_match:
            poss_match = poss_match.group(1).replace("משנה", "").replace("המשך", "").replace("משניות", "")
            poss_match = re.sub('(פ".*?) ', '', poss_match).split("-")[0].replace('"', "").strip()
            if (file.startswith("Derech Chaim") or file.startswith("Well")) and poss_match.startswith("מ"):
                poss_match = poss_match[1:]
            mishnah = getGematria(poss_match)
            prev_mishnah_num = prev_mishnah[1]
            if n > 0 and ((mishnah - prev_mishnah_num) < 0 or (mishnah - prev_mishnah_num) > 10):
                print("{}: {} {}\n".format(file, line, prev_mishnah[0]))
                mishnah = prev_mishnah[1]
            elif mishnah not in mishnayot:
                mishnayot[mishnah] = []
            prev_mishnah = (line, mishnah)
        else:
            mishnayot[mishnah].append(line)
    return convertDictToArray(mishnayot)


def create_new_indices():
    #Be'er HaGolah and Ner Mitzvah and Derech Chaim
    def derech():
        root = SchemaNode()
        root.add_primary_titles("Derech Chaim", "דרך חיים")
        root.key = "Derech Chaim"
        intro = create_intro()
        kol_mishnah = create_new_node_derech_chaim()
        default = JaggedArrayNode()
        default.default = True
        default.key = "default"
        default.add_structure(["Chapter", "Mishnah", "Paragraph"])
        root.append(intro)
        root.append(kol_mishnah)
        root.append(default)
        root.validate()
        # post_index({"title": "Derech Chaim", "schema": root.serialize(), "categories": ["Mishnah", "Commentary"],
        #             "dependence": "Commentary", "base_text_titles": ["Pirkei Avot"], "base_text_mapping": ""})
    def beer():
        root = SchemaNode()
        root.add_primary_titles("Be'er HaGolah", 'באר הגולה')
        root.key = "Be'er HaGolah"
        intro = JaggedArrayNode()
        intro.add_primary_titles("Introduction to Be'er HaGolah", "הקדמה")
        intro.add_structure(["Paragraph"])
        intro.key = "Introduction"
        root.append(intro)
        for i in range(7):
            well = JaggedArrayNode()
            well.add_primary_titles("Well {}".format(i+1), "באר {}".format(numToHeb(i+1)))
            well.add_structure(["Mishnah", "Paragraph"])
            well.key = "Well {}".format(i+1)
            root.append(well)
        root.validate()
        post_index({"title": "Be'er HaGolah", "schema": root.serialize(), "categories": ["Philosophy", "Maharal"]})
    def ner_mitzvah():
        alt_toc_dict = {}
        with open("Ner Mitzvah.csv") as f:
            for row in csv.reader(f):
                if row[0].startswith("Ner Mitzvah"):
                    if row[2]:
                        he, en = row[2], row[3]
                        ref = row[0]
                        alt_toc_dict[(en, he)] = ref
        root = SchemaNode()
        root.add_primary_titles("Ner Mitzvah", "נר מצוה")
        vol = JaggedArrayNode()
        vol.add_primary_titles("Volume I", "חלק א")
        vol.add_structure(["Paragraph"])
        vol.key = "Volume I"
        vol2 = JaggedArrayNode()
        vol2.add_primary_titles("Volume II", "חלק ב")
        vol2.add_structure(["Paragraph"])
        vol2.key = "Volume II"
        root.append(vol)
        root.append(vol2)
        #Index({"title": "Ner Mitzvah", "schema": root.serialize(), "categories": ["Philosophy", "Maharal"]}).save()
        alt_struct = SchemaNode()
        alt_struct.add_shared_term("Topic")
        for tuple, ref in alt_toc_dict.items():
            child = ArrayMapNode()
            child.add_primary_titles(tuple[0], tuple[1])
            child.refs = []
            child.wholeRef = ref
            child.depth = 0
            child.validate()
            alt_struct.append(child)
        alt_struct.key = "Topic"
        alt_struct.validate()
        post_index({"title": "Ner Mitzvah", "schema": root.serialize(), "categories": ["Philosophy", "Maharal"],
                    "alt_structs": {"Topic": {"nodes": alt_struct.serialize()["nodes"]}}})
        print()
        # for tuple in alt_struct_nodes:
        #     he, en = tuple
        #     child_node = ArrayMapNode()
        #     child_node.add_primary_titles(en, he)
        #     child_node.depth = 0
        #     child_node.refs = []
        #     child_node.wholeRef = ""
        #     parsha_node.append(child_node)
        #     parsha_node.validate()
        #     nodes.append(parsha_node.serialize())
        #index["alt_structs"] = {"Parasha": {"nodes": nodes}}

    # beer()
    # derech()
    ner_mitzvah()

def create_new_node_derech_chaim():
    new_node_en, new_node_he = "Kol Yisrael; The Opening Mishna / משנת 'כל ישראל'".split(" / ")
    node = JaggedArrayNode()
    node.add_primary_titles(new_node_en, new_node_he)
    node.key = new_node_en
    node.add_structure(["Paragraph"])
    node.validate()
    return node

def create_footnotes_indices(title):
    if title == ".":
        return
    title = title.split("/")[1]
    index = library.get_index(title)
    contents = get_index_api("Ner Mitzvah", server=SEFARIA_SERVER) if title == 'נר מצוה' else index.contents(v2=True)
    if title != 'נר מצוה':
        return
    title = index.get_title('en')
    en_full_title = "Footnotes and Annotations on {}".format(title)
    he_title = index.get_title('he')
    he_full_title = "הערות ומקורות ל{}".format(he_title)
    term = Term().load({"name": "Footnotes and Annotations"})
    contents["heTitle"] = he_title
    contents = alter_contents(contents, en_full_title, term)
    if title == "Derech Chaim":
        contents["schema"]["nodes"][0] = create_intro().serialize()
        chapters = contents["schema"]["nodes"][1]
        contents["schema"]["nodes"][1] = create_new_node_derech_chaim().serialize()
        contents["schema"]["nodes"] += [chapters]
    elif title == "Be'er HaGolah":
        for n, node in enumerate(contents["schema"]["nodes"]):
            if n > 0:
                node["depth"] = 2
                node["addressTypes"] = ["Integer"] * 2
                node["sectionNames"] = ["Chapter", "Paragraph"]
    contents["categories"] = ["Philosophy", "Maharal", "Commentary"]
    if title == "Ohr Chadash":
        node = contents["schema"]["nodes"][2]
        node["depth"] = 3
        node["addressTypes"] = ["Integer"] * 3
        node["sectionNames"] = ["Chapter", "Verse", "Paragraph"]

    if title == "Derech Chaim":
        contents["categories"] = ["Mishnah", "Commentary"]
    contents["dependence"] = "Commentary"
    contents["base_text_titles"] = [title]
    post_index(contents)


def alter_schema(schema, new_index_title, new_index_he_title):
    schema["key"] = schema["title"] = new_index_title
    schema["heTitle"] = new_index_he_title
    title_group = TitleGroup()
    title_group.add_title(new_index_title, 'en', primary=True)
    title_group.add_title(new_index_he_title, 'he', primary=True)
    title_group.validate()
    schema["titles"] = title_group.titles
    return schema

def copy_keys(contents):
    keys_to_copy = ["base_text_titles", "base_text_mapping", "dependence", "addressTypes", "sectionNames", "depth"]
    new_contents = {key: contents[key] for key in contents if key in keys_to_copy}
    if "base_text_titles" in new_contents:
        base_text_titles = contents["base_text_titles"]
        new_contents["base_text_titles"] = [x['en'] for x in base_text_titles]
    return new_contents


def alter_contents(new_contents, new_index_title, book_term):
    new_contents["title"] = new_index_title

    new_heTerm = book_term.titles[0]["text"] if book_term.titles[0]["lang"] == "he" else book_term.titles[1]["text"]
    new_enTerm = book_term.titles[0]["text"] if book_term.titles[0]["lang"] == "en" else book_term.titles[1]["text"]
    old_heTerm = new_contents["heTitle"].split(" על ")[0]
    old_enTerm = new_contents["title"]

    new_contents["heTitle"] = new_index_he_title = "{} על {}".format(new_heTerm, old_heTerm)
    new_contents["collective_title"] = new_enTerm

    new_contents["schema"] = alter_schema(new_contents["schema"], new_index_title, new_index_he_title)

    new_contents["categories"] = [cat.replace(old_enTerm, new_enTerm) for cat in new_contents["categories"]]
    new_contents["titleVariants"] = []
    new_contents["heTitleVariants"] = []

    return new_contents

def get_intro(title, key):
    if key.startswith("Second") and title.startswith("Ohr"):
        return "Second Introduction to Ohr Chadash"
    if title.startswith("Netivot"):
        intro = "{} to Netivot Olam".format(key)
    elif title.startswith("Derech Chaim"):
        intro = key
    elif title.startswith("Be'er"):
        intro = "{} to Be'er HaGolah".format(key)
    else:
        intro = "{} to {}".format(key, title)
    return intro




def post_derech_chaim(nodes, version):
    nodes.pop("Introduction")
    nodes["Footnotes"].pop("Introduction")
    footnotes = nodes["Footnotes"]
    nodes.pop("Footnotes")
    ref_and_text = [("Footnotes and Annotations on Derech Chaim", footnotes),
                    ("Derech Chaim", nodes)]
    for ref, text in ref_and_text:
        if ref.startswith("Foot"):
            continue
        nodes = []
        for n, node in text.items():
            if isinstance(n, str) and n.startswith("Kol Yisrael"):
                send_text = {"versionTitle": version.vtitle,
                             "versionSource": version.vsource,
                             "text": insert_count(node, 0),
                             "language": "he"}
                print(len(str(send_text["text"])))
                post_text("{}, Kol Yisrael; The Opening Mishna".format(ref), send_text)
            else:
                node = process_depth_3(node, "Derech Chaim {}".format(n))
                nodes.append(node)
        for n, ch in enumerate(nodes):
            nodes[n] = [el for el in nodes[n] if el]
            count = 0
            for m, mishnah in enumerate(nodes[n]):
                nodes[n][m] = [el for el in nodes[n][m] if el]
            for m, mishnah in enumerate(nodes[n]):
                if ref.startswith("Footnotes"):
                    nodes[n][m] = insert_count(mishnah, start_at=count)
                    count += len(mishnah)
                if n+1 == 6:
                    send_text = {"versionTitle": version.vtitle,
                             "versionSource": version.vsource,
                             "text": mishnah,
                             "language": "he"}
                    post_text("{} {}:{}".format(ref, n+1, m+1), send_text)
            if n+1 < 6:
                send_text = {"versionTitle": version.vtitle,
                             "versionSource": version.vsource,
                             "text": nodes[n],
                             "language": "he"}
                print(len(str(send_text["text"])))
                post_text("{} {}".format(ref, n+1), send_text)
    return nodes


def post_beer_hagolah(nodes, version):
    title = "Be'er HaGolah"
    footnotes = nodes["Footnotes"]
    nodes.pop("Footnotes")
    ref_and_text = [("Footnotes and Annotations on {}".format(title), footnotes),
                    (title, nodes)]
    for ref, text in ref_and_text:
        for well_num in text:
            count = 0
            well = "Well {}".format(well_num)
            node = process_depth_3(text[well_num], well)
            for m, mishnah in enumerate(node):
                if ref.startswith("Footnotes"):
                    node[m] = insert_count(mishnah, start_at=count)
                    count += len(mishnah)
            send_text = {"versionTitle": version.vtitle,
                         "versionSource": version.vsource,
                         "text": node,
                         "language": "he"}
            post_text("{}, {}".format(ref, well), send_text, index_count="on")

def insert_count(ftnote_text, start_at=0):
    for n, line in enumerate(ftnote_text):
        ftnote_text[n] = "({}) {}".format(n+1+start_at, line)
    return ftnote_text


def process_esther_links(links, text):
    def post_links_esther(links):
        links = [{"refs": link, "generated_by": "Esther_to_Ohr_Chadash", "type": "Commentary",
                  "auto": True} for link in links]
        post_link(links)
    prev = ""
    len_links = len(links)
    for l, link in enumerate(reversed(links)):
        esther, ohr = link
        if esther == prev:
            start_ref = Ref(link[1].replace("Ohr Chadash", "Rashi on Genesis"))
            end_ref = Ref(links[len_links-l][1]).starting_ref()
            end_ref_sections = end_ref.sections
            end_ref_prev = end_ref.prev_segment_ref()
            assert end_ref_prev.sections[:-1] == end_ref_sections[:-1]
            link[1] = start_ref.to(end_ref_prev).normal()
        else:
            perek, pasuk = Ref(esther).sections
            para = len(text[perek][pasuk])
            link[1] = link[1].replace("Ohr Chadash", "Rashi on Genesis")
            link[1] = Ref(link[1]).to(Ref("Rashi on Genesis {}:{}:{}".format(perek, pasuk, para))).normal()
        prev = esther
    post_links_esther([[link[0], link[1].replace("Rashi on Genesis", "Ohr Chadash")] for link in links])

def post_ohr_chadash(nodes):
    ftnotes = nodes.pop("Footnotes")
    text = {1: {1: []}}
    ftnotes_text = {1: {1: []}}
    found_prev = False
    esther_links = []
    verses = []
    pasuk = 1
    for ch, node in nodes.items():
        perek = ch
        pasuk = 1
        num_ftnotes_already = 0
        if perek not in text:
            text[perek] = {}
            ftnotes_text[perek] = {}
        if pasuk not in text[perek]:
            text[perek][pasuk] = []
            ftnotes_text[perek][pasuk] = []
        curr_esther_link = "{}:{}:1".format(perek, pasuk)
        ftnotes_ch = ftnotes[ch]
        for i, para in enumerate(node):
            dh = re.search('^<b>"(.*?)</b>.{,15}\((.*?)\)', para)
            if dh:
                verse = dh.group(2)
                try:
                    verse = verse.replace('למעלה ', '').replace('להלן ', '')
                    if re.search("^.{1,2}, .{1,2}$", verse):
                        verse = "אסתר " + verse
                    ref = Ref(verse)
                    is_esther = ref.index.title == "Esther"
                    poss_perek = ref.sections[0]
                    poss_pasuk = ref.sections[1] if len(ref.sections) > 1 else 0
                    if is_esther:
                        verses.append(verse)
                    if is_esther and poss_perek > perek:
                        assert poss_perek == perek + 1
                        perek = poss_perek
                        pasuk = poss_pasuk if poss_pasuk > 0 else pasuk
                    elif is_esther and poss_perek == perek:
                        if poss_pasuk < pasuk or poss_pasuk == 0:
                            print("{} before {}".format(verses[-2], verses[-1]))
                            pasuk = poss_pasuk
                            continue
                        pasuk = poss_pasuk
                except InputError as e:
                    if verse.startswith("פסוק") and len(verse.split()) == 2:
                        poss_pasuk = getGematria(verse.split()[-1])
                        if poss_pasuk > pasuk:
                            pasuk = poss_pasuk
                dh = dh.group(1)
                if perek not in text:
                    text[perek] = {}
                    ftnotes_text[perek] = {}
                if pasuk not in text[perek]:
                    text[perek][pasuk] = []
                    ftnotes_text[perek][pasuk] = []

                curr_esther_link = "{}:{}:{}".format(perek, pasuk, len(text[perek][pasuk]) + 1)
                orig = Ref("Rashi on Genesis {}".format(curr_esther_link))
                new = Ref("Rashi on Genesis {}:{}:{}".format(perek, pasuk, len(text[perek][pasuk]) + 1))

                ohr_chadash = orig.to(new).normal() if pasuk == int(curr_esther_link.split(":")[1]) else new.normal()
                ohr_chadash = ohr_chadash.replace("Rashi on Genesis", "Ohr Chadash")
                esther_links.append(["Esther {}:{}".format(perek, pasuk), ohr_chadash])

            soup = BeautifulSoup(para)
            i_tags = soup.find_all("i")
            ftnotes_in_para = [ftnotes_ch[int(el.attrs["data-label"])-1] for el in i_tags]



            for i_tag in i_tags:
                num_ftnotes_already += 1
                para = para.replace(i_tag.attrs["data-label"], str(num_ftnotes_already))
            text[perek][pasuk].append(para)
            for ftnote in ftnotes_in_para:
                ftnotes_text[perek][pasuk].append(ftnote)

    esther_links = process_esther_links(esther_links, text)
    for perek in text:
        text[perek] = convertDictToArray(text[perek])
        count = 0
        for pasuk in ftnotes_text[perek]:
            ftnotes_text[perek][pasuk] = insert_count(ftnotes_text[perek][pasuk], count)
            count += len(ftnotes_text[perek][pasuk])
        ftnotes_text[perek] = convertDictToArray(ftnotes_text[perek])
    text = convertDictToArray(text)
    ftnotes_text = convertDictToArray(ftnotes_text)
    return text, ftnotes_text

def post(text):
    for title, nodes in text.items():
        title = title.replace("Netivot Olam", "Netivot Olam, Netiv Hatorah")
        print(title)
        version = [v for v in versions if v.title == title][0]
        intro_nodes = [node for node in nodes.keys() if isinstance(node, str) and "Introduction" in node]
        for intro_node in intro_nodes:
            intro = get_intro(title, intro_node)
            send_text = {"versionTitle": version.vtitle,
                         "versionSource": version.vsource,
                         "text": nodes[intro_node],
                         "language": "he"}

            intro_title = "Netivot Olam" if title.startswith("Netivot Olam") else title
            post_text(intro_title + ", {}".format(intro), send_text, index_count="on")
            nodes["Footnotes"][intro_node] = insert_count(nodes["Footnotes"][intro_node], 0)
            send_text = {"versionTitle": version.vtitle,
                         "versionSource": version.vsource,
                         "text": nodes["Footnotes"][intro_node],
                         "language": "he"}
            post_text("Footnotes and Annotations on {}, {}".format(intro_title, intro), send_text, index_count="on")
            nodes.pop(intro_node)
            nodes["Footnotes"].pop(intro_node)
        if title == "Be'er HaGolah":
            post_beer_hagolah(nodes, version)
        elif title == "Derech Chaim":
            post_derech_chaim(nodes, version)
        elif title == "Ohr Chadash":
            body, footnotes = post_ohr_chadash(nodes)
            for i, ch in enumerate(footnotes):
                send_text = {"versionTitle": version.vtitle,
                         "versionSource": version.vsource,
                         "text": ch,
                         "language": "he"}
                post_text("Footnotes and Annotations on Ohr Chadash {}".format(i+1), send_text)
            for i, ch in enumerate(body):
                send_text = {"versionTitle": version.vtitle,
                             "versionSource": version.vsource,
                             "text": ch,
                             "language": "he"}
                post_text("Ohr Chadash {}".format(i+1), send_text)
        elif title.startswith("Ner"):
            footnotes = nodes["Footnotes"]
            nodes.pop("Footnotes")
            for node in ["Volume I", "Volume II"]:
                send_text = {"versionTitle": version.vtitle,
                             "versionSource": version.vsource,
                             "text": nodes[node],
                             "language": "he"}
                post_text("Ner Mitzvah, {}".format(node), send_text, index_count="on")
            for n, footnote_ch in footnotes.items():
                footnotes[n] = [el for el in footnote_ch if el]
                send_text = {"versionTitle": version.vtitle,
                             "versionSource": version.vsource,
                                 "text": insert_count(footnotes[n]),
                                 "language": "he"}
                ref = "Footnotes and Annotations on {}, {}".format(title, n)
                post_text(ref, send_text, index_count="on")

        else:
            footnotes = nodes["Footnotes"]
            nodes.pop("Footnotes")
            body = convertDictToArray(nodes)
            ftnotes = convertDictToArray(footnotes)
            send_text = {"versionTitle": version.vtitle,
                         "versionSource": version.vsource,
                         "text": ftnotes,
                         "language": "he"}
            #post_text("Footnotes and Annotations on {}".format(title), send_text, index_count="on", server="https://www.sefaria.org")

            for n, footnote_ch in footnotes.items():
                footnotes[n] = [el for el in footnote_ch if el]
                send_text = {"versionTitle": version.vtitle,
                             "versionSource": version.vsource,
                                 "text": insert_count(footnotes[n]),
                                 "language": "he"}
                try:
                    if int(n) > 46:
                        ref = "Footnotes and Annotations on {} {}".format(title, n)
                        post_text(ref, send_text, index_count="off", server="https://www.sefaria.org")
                        sleep(20)
                except Exception as e:
                    print("CANT post {}: {}".format(title, e))
            send_text = {"versionTitle": version.vtitle,
                         "versionSource": version.vsource,
                         "text": body,
                         "language": "he"}
            #post_text(title, send_text, index_count="on")


def get_match(header, prev_beer_match, prev_match):
    if header.find('הקדמ') >= 0 or header.find("פתיחה") >= 0:
        curr_node = "Introduction"
        if curr_node in text[index.title]:
            curr_node = "Second Introduction"
        if curr_node in text[index.title]:
            curr_node = "Third Introduction"
        return curr_node, prev_beer_match
    else:
        match = None
        p_match = re.search('פ.{,1}"\S', header)
        perek_match = re.search('פרק\s(.*?)\s', header)
        beer_match = re.search('באר\s(.*?)\s', header)
        if p_match:
            match = getGematria(p_match.group(0)[1:])
        elif perek_match:
            match = getGematria(perek_match.group(1))
        elif beer_match:
            if not prev_beer_match:
                match = 2
            elif beer_match.group(0) != prev_beer_match.group(0):
                match = prev_match + 1
            else:
                match = prev_match
            prev_beer_match = beer_match
        elif header == 'דרך חיים ס"פ ו, עמוד ד   ':
            match = prev_match
        elif header == '		משנת "כל ישראל", עמוד ד':
            match = "Kol Yisrael; The Opening Mishna"
        elif header == '		נר מצוה ב, עמוד סח':
            match = "Volume II"
        elif header == '		נר מצוה, עמוד ג				':
            match = "Volume I"
        else:
            match = 1
        return match, prev_beer_match

if __name__ == "__main__":
    t = Term()
    t.name = "Footnotes and Annotations"
    t.add_primary_titles("Footnotes and Annotations", "הערות ומקורות")
    try:
        t.save()
    except:
        pass
    create_new_indices()
    f = []
    path = "."
    prev_match = None
    prev_beer_match = None
    prev_body = []
    last_ftnote_found = 0
    text = {}
    for (dirpath, dirnames, filenames) in walk(path):
        filenames = [file for file in filenames if file.endswith(".docx") and not "~$" in file]
        filenames = sorted(filenames, key=lambda f: int(re.search("\d+", f).group(0)))
        create_footnotes_indices(dirpath)
        counter = 0
        for f in filenames:
            if "GH" not in f:
                continue
            docx_file = dirpath+"/"+f
            index = library.get_index(dirpath.split("/")[1])
            if not index.title in text:
                text[index.title] = {"Footnotes": {}}
            document = docx2python(docx_file)
            ftnotes = get_footnotes(document)
            header = document.header[0][0][0][0]

            match, prev_beer_match = get_match(header, prev_beer_match, prev_match)
            if match not in text[index.title]:
                text[index.title][match] = []
                text[index.title]["Footnotes"][match] = []
                last_ftnote_found = 0


            body, last_ftnote_found = parse_body(document, index, ftnotes, last_ftnote_found)
            text[index.title][match] += body
            text[index.title]["Footnotes"][match] += ftnotes
            prev_match = match
            prev_body = body
    post(text)