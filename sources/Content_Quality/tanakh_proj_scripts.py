import django
django.setup()
from sefaria.model import *
import csv
with open("English Version Titles - version_titles.csv", 'r') as f:
    rows = list(csv.reader(f))[1:]
    for row in rows:
        print(row)
        vs = VersionSet({"versionTitle": row[0]})
        print(abs(vs.count() - int(row[1])))
        if len(row[2]) > 0:
            for v in vs:
                v.shortVersionTitle = row[2]
                v.save(override_dependencies=True)


bucket = "sefaria-in-text-images"
import os

# g = GoogleStorageManager()
#
# jpgs = [open("../Everett Fox/The Five Books of Moses, by Everett Fox/"+x, 'r') for x in os.listdir("../Everett Fox/The Five Books of Moses, by Everett Fox") if x.endswith("jpg")]
# for i, j in enumerate(jpgs):
#     to_filename = "Fox_Torah_{}.jpg".format(i+1)
#     g.upload_file(j, to_filename, "sefaria-in-text-images")


#
# vtitle = "The Rashi chumash by Rabbi Shraga Silverstein"
# img = "https://images-na.ssl-images-amazon.com/images/I/51UsUBzedUL.jpg"
# url = "https://www.amazon.com/Rashi-Chumash-Bereshith-Shraga-Silverstein/dp/1492863203"
# for title in ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]:
#     vs = VersionSet({"title": title, "versionTitle": vtitle})
#     assert vs.count() == 1
#     v = vs[0]
#     v.purchaseInformationImage = img
#     v.purchaseInformationURL = url
#     v.save()
#
# vtitle = "The Holy Scriptures: A New Translation (JPS 1917)"
# img = "https://live.staticflickr.com/5329/17198899114_63c7a50f7c_c.jpg"
# url = "https://jps.org/books/holy-scriptures-tanakh-1917-edition/"
# for title in ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]:
#     vs = VersionSet({"title": title, "versionTitle": vtitle})
#     assert vs.count() == 1
#     v = vs[0]
#     v.purchaseInformationImage = img
#     v.purchaseInformationURL = url
#     v.save()
