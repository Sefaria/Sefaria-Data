import django
django.setup()

import csv
from sefaria.model import *
from sefaria.tracker import modify_bulk_text

if __name__ == '__main__':

    superuser_id = 1
    ref_dict = {}

    #delete version if already exits:
    cur_version = VersionSet({'title': 'Kuzari',
                              'versionTitle': "Kuzari in Arabic, trans. Nabih Bashir, Al-Kamel Verlag, 2012 [ar]"})
    if cur_version.count() > 0:
        cur_version.delete()


    #pase csv into fictionary of refs:
    with open('kuzari aligned.csv', newline='') as csvfile:
        r = csv.reader(csvfile, delimiter=',')

        title = ""
        paragraph_num = 1
        for row in r:
            if row[0] == '':
                ref = title + ":" + str(paragraph_num)
                ref_dict[ref] = row[2]
                paragraph_num += 1
            else:
                paragraph_num = 1
                title = row[0]
                ref = title + ":" + str(paragraph_num)
                ref_dict[ref] = row[2]
                paragraph_num += 1



    #create new version:
    index = library.get_index("Kuzari")

    chapter = index.nodes.create_skeleton()
    new_version = Version({"versionTitle": "Kuzari in Arabic, trans. Nabih Bashir, Al-Kamel Verlag, 2012 [ar]",
                               "versionSource": "'https://korenpub.com/collections/the-noe-edition-koren-talmud-bavli-1'",
                               "title": "Kuzari",
                               "chapter": chapter,
                               "language": "he",
                               "digitizedBySefaria": True,
                               "license": "CC-BY",
                               "status": "locked"
                               })

modify_bulk_text(superuser_id, new_version, ref_dict)
print("finished update")




