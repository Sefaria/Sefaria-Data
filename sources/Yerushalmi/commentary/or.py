import django
django.setup()
from sefaria.model import *
#from sources.functions import add_term, add_category

server = 'http://localhost:9000'
#server = 'https://jt4.cauldron.sefaria.org'
ohr = 'Ohr LaYesharim'
hohr = 'אור לישרים'
jt = ' on Jerusalem Talmud'
hjt = ' על תלמוד ירושלמי'
#add_term(ohr, hohr, server=server)
#add_term(ohr+jt, hohr+hjt, server=server)
categories = ["Talmud", "Yerushalmi", "Commentary", ohr+jt]
#add_category(ohr+jt, categories, server=server)
ind = library.get_index(f'{ohr+jt} Berakhot')
ind.categories = categories
ind.dependence = 'Commentary'
ind.base_text_titles = ['Jerusalem Talmud Berakhot']
ind.base_text_mapping = 'one_to_one'
ind.collective_title = ohr
ind.save()
