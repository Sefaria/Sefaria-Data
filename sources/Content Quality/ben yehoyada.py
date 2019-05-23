import django
django.setup()
import csv
from sefaria.model import *
from sefaria.model.schema import AddressTalmud
from sources.functions import *
from collections import Counter
if __name__ == "__main__":
    dappim = Counter()
    new_csv = ""
    with open("Ben_Yeh.csv") as f:
        # reader = csv.reader(f)
        for row in f:
            ref, text = row.split(",", 1)
            print ref
            if "Introduction" not in row:
                daf = getGematria(ref)*2
                if "." in ref:
                    daf -= 1
                daf = AddressTalmud.toStr("en", daf)
                dappim[daf] += 1
                ref = "Ben Yehoyada on Berakhot {}:{}".format(daf, dappim[daf])

            new_csv += ref+","+text+"\n"
    with open("Ben_Yeh2.csv", 'w') as f:
        f.write(new_csv)


