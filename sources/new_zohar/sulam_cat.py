import django
django.setup()
from sefaria.model import *
from sefaria.helper.category import create_category, move_index_into

ari = Category().load({'path': ['Kabbalah', 'Arizal and Chaim Vital']})
ari.order = 35
ari.save()

name = 'Baal HaSulam'
path = ['Kabbalah', name]
create_category(path, 40, name, 'בעל הסולם')
for title in ["Baal HaSulam's Introduction to Zohar", "Baal HaSulam's Preface to Zohar", "Introduction to Sulam Commentary",
              'Peticha LeChokhmat HaKabbalah', 'Kuntres Matan Torah', 'Sulam on Zohar']:
    move_index_into(title, path)

