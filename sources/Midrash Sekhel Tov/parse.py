#encoding=utf-8
import django
django.setup()
from sefaria.model import *
from sources.functions import *
import os
links = []
def create_link(segment_num, **kwargs):
    title = Term().load({"titles.text": kwargs["title"]}).name
    torah_ref = "{} {}:{}".format(title, kwargs["perek"], kwargs["pasuk"])
    comm_ref = "Midrash Sekhel Tov, {}:{}".format(torah_ref, segment_num)
    assert int(segment_num)
    links.append({"refs": [torah_ref, comm_ref], "auto": True, "type": "Commentary", "generated_by": "midrash_sekhel"})
    print comm_ref
    post_link(links[-1])

def add_line(input_line, prev_line, **kwargs):
    lines = input_line.split(":")
    for line in lines:
        line = line.strip()
        try:
            if len(line) > 2:
                text[curr_text][curr_perek][curr_pasuk].append(line+":")
                segment_num = len(text[curr_text][curr_perek][curr_pasuk])
                create_link(segment_num, **kwargs)
        except KeyError as e:
            print curr_text
            assert curr_pasuk == e.message
            print prev_line

root = SchemaNode()
root.add_primary_titles("Midrash Sekhel Tov", u"מדרש שכל טוב")
root.key = "Midrash Sekhel Tov"
for node_title in ["Bereshit", "Shemot", "Vayikra"]:
    node = JaggedArrayNode()
    node.add_shared_term(node_title)
    node.depth = 3
    node.add_structure(["Perek", "Pasuk", "Paragraph"])
    node.key = node_title
    node.validate()
    root.append(node)

root.validate()
indx = {
    "title": root.key,
    "categories": ["Tanakh", "Commentary"],
    "schema": root.serialize()
}
post_index(indx)


file = [f for f in os.listdir(".") if f.endswith(".txt")][0]
text = {}
prev_line = ""
with open(file) as open_file:
    lines = list(open_file)
    for n, line in enumerate(lines):
        line = line.strip()
        pasuk_re = re.search(u"^(.{1,2})\)", line.decode('utf-8'))
        pasuk = None
        if pasuk_re:
            pasuk = pasuk_re.group(1)

        if "@00" in line:
            line = line[line.find("@00")+3:]
            curr_text = line
            text[curr_text] = {}
            prev_pasuk = prev_perek = curr_perek = curr_pasuk = 0
        elif line.startswith("@11"):
            curr_perek = getGematria(line)
            assert curr_perek > prev_perek
            text[curr_text][curr_perek] = {}
            curr_pasuk = 0
        elif line.startswith("@22") or pasuk:
            curr_pasuk = getGematria(pasuk) if pasuk else getGematria(line)
            assert curr_pasuk > prev_pasuk or curr_perek >= prev_perek
            text[curr_text][curr_perek][curr_pasuk] = []
            if line.count(" ") >= 2:
                line = u" ".join(line.decode('utf-8').split()[1:])
                add_line(line, lines[n-1], title=curr_text, perek=curr_perek, pasuk=curr_pasuk)
        elif curr_perek >= 1:
            add_line(line, lines[n-1], title=curr_text, perek=curr_perek, pasuk=curr_pasuk)
        else:
            print "Intro text in {}:".format(curr_text)
            print prev_line
            print line


        prev_perek = curr_perek
        prev_pasuk = curr_pasuk
        prev_line = line

    for title in text.keys():
        en_title = Term().load({"titles.text": title}).name
        ref = "Midrash Sekhel Tov, {}".format(en_title)
        for curr_perek in text[title].keys():
            text[title][curr_perek] = convertDictToArray(text[title][curr_perek])
        text[title] = convertDictToArray(text[title])
        send_text = {
            "language": "he",
            "versionTitle": "Sechel Tob, Berlin 1900-1901",
            "versionSource": "https://beta.nli.org.il/he/books/NNL_ALEPH001725650/NLI",
            "text": text[title]
        }
        #post_text(ref, send_text)
#post_link(links)