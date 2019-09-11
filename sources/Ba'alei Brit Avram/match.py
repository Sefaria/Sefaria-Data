#encoding=utf-8
import django
django.setup()
from sefaria.model import *
from sources.functions import *
from sefaria.system.exceptions import InputError
from sefaria.export import import_versions_from_stream
import csv
# with open("Ba_alei_Brit_Avram_-_Vilna.csv") as f:
#     import_versions_from_stream(f, [1], 1)
def base_tokenizer(str):
    return str.split()

def dh_extract_method(str):
    if str.find("</b>") > str.find("<b>") >= 0:
        str = str[str.find("<b>")+3:str.find("</b>")]
        str = u" ".join(str.split(u"וגו")[0].split()[0:9])
        return str
    else:
        return ""

VersionState("Ba'alei Brit Avram").refresh()
sections = library.get_index("Ba'alei Brit Avram").all_section_refs()
base_ref = {}
links = []
for sec in sections:
    try:
        parasha = Ref("Parashat "+sec.normal().split(", ")[1])
        links += match_ref_interface(parasha.normal(), sec.normal(), sec.text('he').text, base_tokenizer, dh_extract_method)
    except InputError as e:
        print e.message
post_link(links)
print len(links)