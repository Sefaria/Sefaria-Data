# -*- coding: utf8 -*-
__author__ = 'eliav'
from sefaria.model import *
import re


masechet = "Yoma"
masechet_he = ur"יומא"


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
    seder_avoda = JaggedArrayNode()
    seder_avoda.add_title(u"הלכות סדר עבודת יום הכפורים", "he", primary=True)
    seder_avoda.add_title("Hilchot Seder Avodat Yom haKippurim", "en", primary=True)
    seder_avoda.key = "Hilchot Seder Avodat Yom haKippurim"
    seder_avoda.depth = 1
    seder_avoda.sectionNames = ["siman"]
    seder_avoda.addressTypes = ["Integer"]
    kitzur_seder = JaggedArrayNode()
    kitzur_seder.add_title("Seder haavodah bekitzur", "en", primary=True)
    kitzur_seder.add_title(ur"סדר העבודה בקצור מלשון הרא\"ש זצ\"ל", "he", primary = True)
    kitzur_seder.key = "Seder haavodah bekitzur"
    kitzur_seder.depth = 1
    kitzur_seder.sectionNames = ["Siman"]
    kitzur_seder.addressTypes = ["Integer"]
    perek_shmini = JaggedArrayNode()
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
        if ur'סדר עבודה בקצור' in seif:
            print seif

            break
        content = re.split('@66', seif)
        siman = []
        for cont in content:
            #print cont
            if len(re.split('(?:@33|@77)', cont)) > 1:
                cont = "<b>" + re.split('(?:@33|@77)', cont)[0] + "</b>" + re.split('(?:@33|@77)', cont)[1]
            else:
                cont = cont[0]
            siman.append(cont)
        hilchot_seder_haavoda.append(siman)


if __name__ == '__main__':
    text = open_file()
    book_record1()
    parsed = parse_seder_haavoda(text)