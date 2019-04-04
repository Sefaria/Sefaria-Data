#encoding=utf-8

import django
django.setup()
from sefaria.system.database import db

# NOTE: this code is based on ssn tag numbers. if we choose to take those tags off while posting to production
# we must put this info in in a different space
# one space it is already hidden in is in the pdf html link

#based on tags
map_ssn_url = dict()
for ssn in (range(1, 1479)):
    # sheets = db.sheets.find({"$and": [{"$or": [{"tags": "Bilingual"}, {"tags": "Hebrew Sheet"}]}, {"tags": "{}".format(ssn)}]})
    # sheets = db.sheets.find({"$and": [{"tags": "Bilingual"}, {"tags": "{}".format(ssn)}]})
    sheets = db.sheets.find({"$and": [{"group":"גיליונות נחמה"}, { "tags": "Edited" }, {"tags":"{}".format(ssn)}]})
    # sheets = db.sheets.find({"tags":"{}".format(ssn)})
    for s in sheets.sort("dateCreated", -1):
        # if sheets.count_documents() >1:
        #     print s['dateCreated']
        if ssn in map_ssn_url.keys():
            print "double: {}".format(ssn)
            continue
        else:
            map_ssn_url[ssn]=s['id']
print map_ssn_url
print len(map_ssn_url.items())


# based on ssn pramter
from sefaria.system.database import db
map_ssn_id = dict()
ssn_sheets = db.sheets.find({ "ssn": {"$exists": "true" } })
for s in ssn_sheets:
    map_ssn_id[s['ssn']]=s['id']
print map_ssn_id