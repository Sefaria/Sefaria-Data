__author__ = 'eliav'
from sefaria.model import *
import re

masechet = "Yoma"
masechet_he = "יומא"


def open_file():
    with open("source/Rosh_on_%s.txt" % masechet, 'r') as filep:
        file_text = filep.read()
      #  print file_text.decode('utf-8','ignore')
        ucd_text = unicode(file_text, 'utf-8', errors='ignore').strip()
        print masechet_he
        return ucd_text

def book_record1():
    b = u"Rosh on %s" % masechet
    a = u" פסקי הראש על " + masechet_he
    root = SchemaNode()
    root.add_title(b, "en", primary=True)
    root.add_title(a, "he", primary=True)
    root.key = b
    seder_avoda = SchemaNode()
    seder_avoda.add_title(u"הלכות סדר עבודת יום הכפורים", "he", primary=True)
    seder_avoda.add_title("Hilchot Seder Avodat Yom haKippurim", "en", primary=True)
    seder_avoda.key = "Hilchot Seder Avodat Yom haKippurim"
    perek_shmini = JaggedArrayNode()
    #perek_shmini.add_title(u"פרק שמיני", "he", primary=True)
    #perek_shmini.add_title("Perek Shmini", "en", primary=True)
    perek_shmini.default = True
    perek_shmini.depth = 2
    perek_shmini.sectionNames = [ "Halacha","Siman"]
    perek_shmini.addressTypes = ["Integer", "Integer"]
    perek_shmini.key = "default"
    root.append(seder_avoda)
    root.append(perek_shmini)
    root.validate()
    indx = {
    "title": b,
    "categories": ["Other","Rosh"],
    "schema": root.serialize()
    }
    Index(indx).save()


def parse_seder_haavoda(text):
    hilchot_seder_haavoda = []
    cut = re.split("@00",text)
    seder_haavoda = cut[0]
    seifim = re.split('@22', seder_haavoda)
    for seif in seifim:
        content = re.split('@66', seif)
        for cont in content:
            siman = []
            if len(re.split('@33', cont))>1:
                cont = "<b>" + cont[0] + "</b>" + cont[1]
            else:
                cont = content
            siman.append(cont)
        hilchot_seder_haavoda.append(content)

    print len(hilchot_seder_haavoda)