#encoding=utf-8
import django
django.setup()
from sources.functions import *
from sefaria.model import *

def create_index():
    root = SchemaNode()
    root.add_primary_titles("Responsa of Remah", u"שות רמה")
    root.key = "remah"
    intro = JaggedArrayNode()
    intro.add_shared_term("Introduction")
    intro.add_structure(["Paragraph"])
    intro.key = "intro"
    root.append(intro)
    index = JaggedArrayNode()
    index.add_primary_titles("Index", u"לוח המפתחות")
    index.add_structure(["Paragraph"])
    root.append(index)
    default = JaggedArrayNode()
    default.default = True
    default.key = "default"
    default.add_structure(["Siman", "Paragraph"])
    root.append(default)
    root.validate()
    i = {
        "title": "Responsa of Remah",
        "schema": root.serialize(),
        "categories": ["Halakhah"]
    }
    post_index(i, server=SEFARIA_SERVER)


def parse_intro(file):
    intro = []
    with open(file) as f:
        for line in f:
            line = removeAllTags(line)
            intro.append(line)
    return intro

def parse_index(file):
    section = ""
    lines = []
    with open(file) as f:
        for n, line in enumerate(f):
            if line.startswith("@22"):
                section = removeAllTags(line)
            elif line.startswith("@32"):
                lines.append("<b>{}</b> {}".format(section, removeAllTags(line)))
                section = ""
            else:
                line = line.replace("@23", "<b>").replace("@32", "</b>")
    return lines

def parse_default(file):
    section = 0
    lines = {}
    with open(file) as f:
        file_lines = list(f)
        for n, line in enumerate(file_lines):
            if "@22" in line:
                new_section = getGematria(line)
                assert new_section > section
                section = new_section
                lines[section] = []
            else:
                line = removeAllTags(line)
                lines[section].append(line)
    return convertDictToArray(lines)

if __name__ == "__main__":
    create_index()
    intro = parse_intro("intro.txt")
    index = parse_index("index.txt")
    default = parse_default("text.txt")
    tuples = [(", Introduction", intro), (", Index", index), ("", default)]
    for ref, text in tuples:
        send_text = {
            "text": text,
            "language": "he",
            "versionTitle": "Sheelot uTeshuvut Remah, Warsaw, 1883",
            "versionSource": "http://aleph.nli.org.il:80/F/?func=direct&doc_number=000109739&local_base=MBI01"
        }
        print "Responsa of Remah{}".format(ref)
        post_text("Responsa of Remah{}".format(ref), send_text, SEFARIA_SERVER)

