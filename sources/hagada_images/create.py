import csv
import django
django.setup()
from sefaria.model.manuscript import Manuscript, ManuscriptPage
from sefaria.system.exceptions import DuplicateRecordError
from pymongo.errors import DuplicateKeyError

with open('table.csv', newline='') as fp:
    data = list(csv.DictReader(fp))

for row in data:
    row = {k: v.strip() for k, v in row.items()}

    m = Manuscript()
    m.source = row['url']
    m.description = ''
    m.he_description = ''
    if row['Title']:
        m.title = f"{row['Title']} ({row['Place']}, {row['Year']})".replace(' Ca.', ' ca.')
        m.he_title = f"{row['heb_title']} ({row['heb_place']}, {row['Year']})"
    else:
        m.title = f"{row['Place']}, {row['Year']}"
        m.he_title = f"{row['heb_place']}, {row['Year']}"
    if row['heb_title'] == 'הגדת שיק':
        m.license = 'CC-BY-SA'
    try:
        m.save()
    except (DuplicateKeyError, DuplicateRecordError):
        pass
    m = Manuscript().load({'title': m.title})

    mp = ManuscriptPage()
    file = row['filename']
    mp.image_url = f'https://manuscripts.sefaria.org/arbaa-banim/{file}.jpg'
    mp.thumbnail_url = f'https://manuscripts.sefaria.org/arbaa-banim/{file}_thumbnail.jpg'
    mp.contained_refs = ['Pesach Haggadah, Magid, The Four Sons 1-5']
    mp.manuscript_slug = m.slug
    mp.page_id = m.title
    if row['Series']:
        mp.page_id += f" {row['Series']}"
    mp.set_expanded_refs()
    mp.validate()
    try:
        mp.save()
    except (DuplicateKeyError, DuplicateRecordError):
        pass
