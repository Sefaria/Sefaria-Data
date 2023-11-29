import django
django.setup()
from sefaria.helper.text import modify_many_texts_and_make_report

r=modify_many_texts_and_make_report(lambda x: (x.replace("''", '"'), x.count("''")))
with open('geresh.csv', 'wb') as fp:
    fp.write(r)
r=modify_many_texts_and_make_report(lambda x: (x.replace("ײ", 'יי'), x.count("ײ")), {'actualLanguage': {'$ne': 'yi'}})
with open('yud.csv', 'wb') as fp:
    fp.write(r)
