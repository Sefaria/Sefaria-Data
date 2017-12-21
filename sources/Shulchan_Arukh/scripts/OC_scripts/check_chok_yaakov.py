#encoding=utf-8
import sys
from sources.Shulchan_Arukh.ShulchanArukh import *
from sources.functions import UnicodeReader

if __name__ == "__main__":
    f = "Chok Yaakov on Shulchan Arukh, Orach Chayim - he - Maginei Eretz_ Shulchan Aruch Orach Chaim, Lemberg, 1893.csv"
    with open(f) as open_f:
        reader = UnicodeReader(open_f)
        for row in reader:
            if not row[0].startswith("Chok"):
                continue
            ref = row[0]
            comment = row[1]
            if comment.endswith("</b>"):
                ref = ref.replace("Chok Yaakov on Shulchan Arukh, Orach Chayim ", "")
                siman, seif = ref.split(":")
                print "Siman {}, Seif {}".format(siman, seif)