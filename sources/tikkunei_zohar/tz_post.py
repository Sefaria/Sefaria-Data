import django
django.setup()

from sources.functions import post_text, post_index, add_term, add_category,post_link
from tz_parse import *
from sefaria.model.schema import *
from sources.local_settings import SEFARIA_SERVER, API_KEY


from collections import OrderedDict



def post_tz():
    schema = JaggedArrayNode()
    titles = [
            {
                "text" : "Tikkunei haZohar",
                "lang" : "en"
            },
            {
                "text" : "תקוני הזוהר",
                "lang" : "he"
            },
            {
                "text" : "תיקוני הזוהר",
                "lang" : "he"
            },
            {
                "text" : "תיקון",
                "lang" : "he"
            },
            {
                "text" : "תקו''ז תיקון",
                "lang" : "he"
            },
            {
                "text" : "תקו\"ז",
                "lang" : "he"
            },
            {
                "text" : "תקון",
                "lang" : "he"
            },
            {
                "text" : "תיקוני זוהר",
                "lang" : "he"
            },
            {
                "text" : "תקוני זהר",
                "lang" : "he"
            },
            {
                "text" : "תקוני זוהר",
                "lang" : "he"
            },
            {
                "text" : "תקו״ז",
                "lang" : "he"
            },
            {
                "text" : "תקו”ז",
                "lang" : "he"
            },
            {
                "text" : "תקוני הזהר",
                "lang" : "he",
                "primary" : True
            },
            {
                "text" : "Tikkunei Zohar",
                "lang" : "en",
                "primary" : True
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
    add_term('Tikkunei Zohar', u'תקוני הזהר', server=SEFARIA_SERVER)
    post_index(index_dict, server=SEFARIA_SERVER)
    print("hi")

    text_version = {
        'versionTitle': 'Solomon Tikkunei Zohar',
        'versionSource': '',
        'language': 'en',
        'text': ja_tosefta
    }

post_tz()
post_text(text_version)