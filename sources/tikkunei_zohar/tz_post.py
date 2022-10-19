import django
django.setup()

from sefaria.tracker import modify_bulk_text
from sefaria.model import Ref, VersionSet, Version
from sources.functions import post_text, post_index, add_term, add_category,post_link
from tz_parse import *
from sefaria.model.schema import *
from sources.local_settings import SEFARIA_SERVER, API_KEY, UID
from collections import defaultdict


# from collections import OrderedDict

def get_index():
    schema = JaggedArrayNode()
    titles = [
        {
            "text": "Tikkunei haZohar",
            "lang": "en"
        },
        {
            "text": "תקוני הזוהר",
            "lang": "he"
        },
        {
            "text": "תיקוני הזוהר",
            "lang": "he"
        },
        {
            "text": "תיקון",
            "lang": "he"
        },
        {
            "text": "תקו''ז תיקון",
            "lang": "he"
        },
        {
            "text": "תקו\"ז",
            "lang": "he"
        },
        {
            "text": "תקון",
            "lang": "he"
        },
        {
            "text": "תיקוני זוהר",
            "lang": "he"
        },
        {
            "text": "תקוני זהר",
            "lang": "he"
        },
        {
            "text": "תקוני זוהר",
            "lang": "he"
        },
        {
            "text": "תקו״ז",
            "lang": "he"
        },
        {
            "text": "תקו”ז",
            "lang": "he"
        },
        {
            "text": "תקוני הזהר",
            "lang": "he",
            "primary": True
        },
        {
            "text": "Tikkunei Zohar",
            "lang": "en",
            "primary": True
        }
    ]

    for title in titles:
        schema.add_title(title["text"], title["lang"], title["primary"] if "primary" in title else False)

    schema.key = 'Tikkunei Zohar'
    schema.depth = 2
    schema.addressTypes = ["Talmud", "Integer"]
    schema.sectionNames = ["Daf", "Paragraph"]
    schema.validate()
    index_dict = {
        'title': 'Tikkunei Zohar',
        'categories': ['Kabbalah', 'Zohar'],
        'schema': schema.serialize(),  # This line converts the schema into json
        'collective_title': 'Tikkunei Zohar'
    }
    print(index_dict)
    return index_dict


def get_mappings():
    parsers = [HtmlTzParser("vol2.html", 2, language="bi")]
    # parsers = [HtmlTzParser("vol2.html", 2), DocsTzParser("vol3.docx", 3), DocsTzParser("vol4.docx", 4), DocsTzParser("vol5.docx", 5)]
    # parsers = [DocsTzParser("vol4.docx", 4)]
    # parsers = [DocsTzParser("vol4.docx", 4), DocsTzParser("vol5.docx", 5)]
    mappings = defaultdict()
    mappings['Tikkunei Zohar'] = {}
    for i, parser in enumerate(parsers):
        if i > 0:
            parser.tikkun = parsers[i-1].tikkun
        parser.read_file()
        for paragraph in parser.paragraphs:
            ref = Ref('Tikkunei Zohar ' + paragraph.daf.name + ' ' + str(paragraph.paragraph_number+1))
            print(ref)
            mappings[ref.index.title][str(ref)] = paragraph.get_words()

    return mappings

def get_version():
    cur_version = VersionSet({'title': 'Tikkunei Zohar', 'versionTitle': 'Solomon Tikkunei Zohar'})
    if cur_version.count() > 0:
        cur_version.delete()
    text_version = Version({
        'versionTitle': 'Solomon Tikkunei Zohar',
        'versionSource': '',
        "title": "Tikkunei Zohar",
        "chapter": [],
        "language": "en",
        "digitizedBySefaria": True,
        "license": "Public Domain",
        "status": "locked"
    })
    return text_version


def get_node():
    node = ArrayMapNode()
    node.depth = 2
    node.include_previews = True
    node.addressTypes = ['']
    return node


def get_version_for_post(map, item):
    version = {
        'versionTitle': 'Solomon Tikkunei Zohar',
        'versionSource': '',
        "title": "Tikkunei Zohar",
        # "chapter": [],
        "language": "en",
        "digitizedBySefaria": True,
        "license": "Public Domain",
        "status": "locked",
        "text": map["Tikkunei Zohar"][item]
    }
    return version

def post_version():
    map = get_mappings()
    # node = get_node()
    for item in map['Tikkunei Zohar']:
        version = get_version_for_post(map, item)
        post_text(item, version, server=SEFARIA_SERVER, weak_network=True)
    # modify_bulk_text(user=UID, version=version,text_map=map['Tikkunei Zohar'], skip_links=True, count_after=False)
    print("hi")

def post_tz():
    index_dict = get_index()
    add_term('Tikkunei Zohar', u'תקוני הזהר', server=SEFARIA_SERVER)
    post_index(index_dict, server=SEFARIA_SERVER)


# post_tz()
# create_version()
# post_version()
# post_text(text_version)
post_tz()
post_version()