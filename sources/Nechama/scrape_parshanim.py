#encoding=utf-8

import django
django.setup()

import requests
from bs4 import BeautifulSoup, element
import unicodecsv as csv
import codecs

dict_list = []
for i in range(1, 257):
    url = u'http://www.nechama.org.il/commentatorsPopup/{}.html'.format(i)
    r = requests.get(url,)
    data = r.content
    content = BeautifulSoup(data, "lxml")
    title = content.find(attrs={'id': 'contentTop'}).get_text()
    text = content.find(attrs={'id': 'contentBody'}).get_text()
    dict_list.append({u'number':i, u'name':title, u'text':text})

with open('parshanim.csv', 'w') as csv_file:
    writer = csv.DictWriter(csv_file, [u'number', u'name', u'text'])
    writer.writeheader()
    writer.writerows(dict_list)


print "done"
