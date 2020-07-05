import unicodecsv, re
from sefaria.model import *

LEXICON_NAME = "Acronyms"

def create_lexicon():
    l = Lexicon().load({"name": LEXICON_NAME})
    if not l:
        Lexicon({
            "to_language" : "heb",
            "name" : LEXICON_NAME,
            "language" : "heb.mishnaic",
            "source" : "Original Sefaria Compilation",
            "attribution" : "Dicta",
            "text_categories" : []
        }).save()

def create_wordform(data):
    wf = WordForm().load({"form": data['Phrase']})
    if not wf:
        WordForm({"form": data['Phrase'],
                       "lookups": [{"headword": data["Phrase"], "parent_lexicon": LEXICON_NAME}]}).save()


def creat_lexiconentry(data):
    le = LexiconEntry().load({"headword": data["Phrase"], "parent_lexicon": LEXICON_NAME})
    if not le:
        senses = []
        for i in range(1, 24):
            temp_def = data['Alternate #{}'.format(i)]
            temp_def = re.sub(r'\([0-9]+\)','', temp_def)
            temp_def = temp_def.replace('_',' ').strip()
            if len(temp_def) == 0:
                break
            senses += [{
                'definition': temp_def
            }]

        dict_entry = {
            'headword': data['Phrase'],
            'parent_lexicon': LEXICON_NAME,
            'content': {'senses': senses}
        }

        LexiconEntry(dict_entry).save()

def read_source():
    source_path = 'sources/rashei_tevot.csv'
    f = open(source_path, 'rb')
    csv = unicodecsv.DictReader(f)
    for i,row in enumerate(csv):
        if i % 100 == 0:
            print("{}".format(i))
        create_wordform(row)
        creat_lexiconentry(row)


create_lexicon()
read_source()

"""
{
    "_id" : ObjectId("55925f5dfbfba21c01b3ce3c"),
    "to_language" : "eng",
    "name" : "Halachic Terminology",
    "language" : "heb.mishnaic",
    "source" : "Original Sefaria Compilation",
    "attribution" : "Rav Yehoshua Kahan",
    "text_categories" : [
        "Mishnah, Seder Zeraim",
        "Mishnah, Seder Moed",
        "Mishnah, Seder Nashim",
        "Mishnah, Seder Nezikin",
        "Mishnah, Seder Kodashim",
        "Mishnah, Seder Tahorot"
    ]
}

"""