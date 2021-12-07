import django
django.setup()
from data_utilities.XML_to_JaggedArray import XML_to_JaggedArray
from sefaria.helper.schema import *
from sources.functions import *
import bleach

def reorder_modify(text):
    return bleach.clean(text, strip=True)

def tester(x):
    #Chapter 1.
    return x.tag == "p" and re.search("Chapters? \d+.{,30}\.", x.text)

if __name__ == "__main__":
    #add_term("Preface", u"פתח דבר", "pseudo_toc_categories", "http://localhost:8000")
    #create_schema("Responsa to Chaplains", u"משהו", ["Halakhah"])
    post_info = {}
    post_info["language"] = "en"
    post_info["server"] = SEFARIA_SERVER
    allowed_tags = ["book", "intro", "bibl", "part", "chapter", "p", "ftnote", "title", "ol", "footnotes", "appendix", "h1"]
    allowed_attributes = ["id"]
    p = re.compile("\d+a?\.")

    post_info["versionTitle"] = "The Early Prophets"
    post_info["versionSource"] = "http://www.sefaria.org"
    title = "The Early Prophets"
    file_name = "The_Early_Prophets.xml"
    lines = open(file_name, 'r', errors='ignore').read()
    parser = XML_to_JaggedArray(title, lines, allowed_tags, allowed_attributes, post_info, change_name=True,
                                titled=True, print_bool=True)
    parser.set_funcs(reorder_modify=reorder_modify, reorder_test=tester)
    parser.run()