#encoding=utf-8

import django
django.setup()
from sefaria.system.database import db

#NOTE: this code is based on ssn tag numbers. if we choose to take those tags off while postinf to production we muxt put this info in in a diffrent space
#one space it is already hidden in is in the pdf html link
map_ssn_url = dict()
for ssn in (range(1, 1479)):
    sheets = db.sheets.find({"$and": [{"tags": "Bilingual"}, {"tags": "{}".format(ssn)}]})
    for s in sheets:
        map_ssn_url[ssn]=s['id']
        print ssn, u":", s['id'], u','
        break
print map_ssn_url
print len(map_ssn_url.items())

