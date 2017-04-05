__author__ = 'stevenkaplan'

from data_utilities.XML_to_JaggedArray import *
SERVER = "http://ste.sefaria.org"

def cleanNodeName(text, titled=False):
    text = cleanText(text)
    bad_chars = [":", '-', '.']
    bad_chars += re.findall(u"[\u05D0-\u05EA]+", text)
    for bad_char in bad_chars:
        text = text.replace(bad_char, ",")
        " ".join(text.split())
    text = bleach.clean(text, strip=True)
    if titled:
        return text.title()
    return text

def cleanText(text):
    things_to_replace = {
        u'\xa0': u'',
        u'\u015b': u's',
        u'\u2018': u"'",
        u'\u2019': u"'",
        u'\u05f4': u'"',
        u'\u201c': u'"',
        u'\u201d': u'"',
        u'\u1e93': u'z',
        u'\u1e24': u'H'
    }
    for key in things_to_replace:
        text = text.replace(key, things_to_replace[key])
    return text

def create_schema_parts():
    part = None
    root = None
    root_title = ""
    for line in open("structure.txt"):
        line = line.replace("\n", "").replace("\r", "")
        if len(line) == 0:
            continue
        en, he = line.split(" / ")
        en = cleanNodeName(en.decode('utf-8')).strip()
        if line.startswith("Contemporary Halakhic"):
            if part:
                root.append(part)
                part = None
            if root:
                post_index_schema(root, root_title)
            root = SchemaNode()
            root_title = en
            root.add_primary_titles(en, he)
        elif line.startswith("Part I"):
            if part:
                root.append(part)
            part = SchemaNode()
            part.add_primary_titles(en, he)
        elif line.startswith("  "):
            print line
            node = JaggedArrayNode()
            node.add_structure(["Paragraph"])
            node.add_primary_titles(en, he)
            part.append(node)
        elif line.find(" / ") >= 0:
            node = JaggedArrayNode()
            node.add_structure(["Paragraph"])
            node.add_primary_titles(en, he)
            if line.startswith("Appendi") and part:
                root.append(part)
                part = None
            root.append(node)
    post_index_schema(root, root_title)


def post_index_schema(root, title):
    root.validate()
    post_index({
        "schema": root.serialize(),
        "title": title,
        "categories": ["Halakha"]
    }, server=SERVER)

def reorder_modify(text):
    return bleach.clean(text, strip=True)

if __name__ == "__main__":
    #create_schema_parts()
    post_info = {}
    post_info["language"] = "en"
    post_info["server"] = SERVER
    allowed_tags = ["book", "intro", "part", "chapter", "p", "ftnote", "title", "footnotes", "appendix"]
    allowed_attributes = ["id"]
    p = re.compile("\d+a?\.")
    post_info["versionTitle"] = "Contemporary halakhic problems; by J. David Bleich, 1977-2005"
    post_info["versionSource"] = "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001100271"

    for i in [3, 5]:#range(6):
        title = "Contemporary Halakhic Problems, Vol {}".format(i+1)
        file_name = "ContemporaryHalakhicProblems-Vol{}.xml".format(i+1)
        parser = XML_to_JaggedArray(title, file_name, allowed_tags, allowed_attributes, post_info, change_name=True, image_dir="./images")
        parser.set_funcs(reorder_test=lambda x: x.tag == "title" and x.text.find("<bold>") == 0, reorder_modify=reorder_modify)
        parser.run()