import django
django.setup()
from noam import yield_by_conditions, get_masechet
import csv
from sources.functions import add_term, add_category, post_text, post_index, post_link
from sefaria.model import *

def make_term_and_cat(server):
    he_ter = 'נועם ירושלמי'
    add_term(comm, he_ter, server=server)

    categories = ["Talmud", "Yerushalmi", "Commentary"]
    add_category('Commentary', categories, server=server)
    categories.append(comm)
    add_category(comm, categories, server=server)

def post(mas, com, server, data):
    he_ter = 'נועם ירושלמי'

    categories = ["Talmud", "Yerushalmi", "Commentary"]
    categories.append(comm)
    base_title = f'Jerusalem Talmud {mas}'
    seder = library.get_index(base_title).categories[-1]
    categories.append(seder)
    add_category(categories[-1], categories, server=server)

    title = f'{com} on {mas}'
    he_mas = library.get_index(base_title).get_title('he').replace('תלמוד ירושלמי ', '')
    record = JaggedArrayNode()
    record.add_primary_titles(title, f'{he_ter} על {he_mas}')
    record.add_structure(['Chapter', 'Halakhah', 'Segment', 'Comment'])
    record.addressTypes = ['Perek', 'Halakhah', 'Integer', 'Integer']
    record.toc_zoom = 2
    record.validate()
    index_dict = {'collective_title': com,
                  'title': title,
                  'categories': categories,
                  'schema': record.serialize(),
                  'dependence': 'Commentary',
                  'base_text_titles': [base_title],
                  }
    post_index(index_dict, server=server)

    year = 1863 if seder == 'Zeraim' else 1866 if seder == 'Moed' else 1868 if seder == 'Nashim' else 1869
    text_version = {
        'versionTitle': f'Vilna, {year}',
        'versionSource': "https://www.nli.org.il/he/books/NNL_ALEPH990012024800205171/NLI",
        'language': 'he',
        'text': data,
        'versionNotes': 'This text was digitized and released into the public domain by <a href="http://dicta.org.il">Dicta: The Israel Center for Text Analysis</a>, using a state-of-the-art OCR pipeline leveraging a custom-built transformer-based language model for Rabbinic Hebrew.',
        'versionNotesInHebrew': 'מהדורה דיגיטלית זו, שהותקנה באמצעות כלים של בינה מלאכותית, זמינה לתועלת הציבור באדיבות <a href="http://dicta.org.il">דיקטה: המרכז הישראלי לניתוח טקסטים</a>. הטקסט עבר דיגיטציה באמצעות טכנולוגיה של זיהוי תווים אופטי (OCR pipeline) המבוססת על רשתות עצביות ומודל שפה לעברית רבנית.',
        'license': 'Public Domain'
    }
    post_text(title, text_version, server=server, index_count='on')

server = 'http://localhost:8000'
server = 'https://new-shmuel.cauldron.sefaria.org'
comm = 'Noam Yerushalmi'
make_term_and_cat(server)

with open('Noam Yerushalmi.csv') as fp:
    r = csv.DictReader(fp)
    fieldnames = r.fieldnames
    rows = list(r)
links = []
for bunch in yield_by_conditions(rows, get_masechet, lambda x, y: get_masechet(x) != y):
    mas = get_masechet(bunch[0])
    print(mas)
    text = []
    for row in bunch:
        ref = row['base text ref']
        if ref:
            if text:
                end = len(text[-1][-1][-1])
                if end > 1:
                    links[-1]['refs'][-1] += f'-{end}'
            perek, halakha, seg = ref.split()[-1].split('-')[0].split(':')
            perek, halakha, seg = int(perek), int(halakha), int(seg)
            if len(text) < perek:
                text += [[] for _ in range(perek - len(text))]
            if len(text[-1]) < halakha:
                text[-1] += [[] for _ in range(halakha - len(text[-1]))]
            if len(text[-1][-1]) < seg:
                text[-1][-1] += [[] for _ in range(seg - len(text[-1][-1]))]
            links.append({
                'refs': [ref, f'{comm} on {mas} {perek}:{halakha}:{seg}:1'],
                'auto': True,
                'type': 'commentary',
                'generated_by': 'noam yerushalmi parser'
            })
        text[-1][-1][-1].append(row['text'])
    end = len(text[-1][-1][-1])
    if end > 1:
        links[-1]['refs'][-1] += f'-{end}'
    # post(mas, comm, server, text)

print(len(links))
post_link(links, server, VERBOSE=False)
