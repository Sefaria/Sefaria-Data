import django
django.setup()
from sefaria.model import *
from sefaria.system.database import db
import csv
from datetime import datetime
from sefaria.utils.calendars import get_parasha
from sefaria.utils.hebrew import *
from sefaria.system.exceptions import BookNameError

class TanakhRow(object):
    __slots__ = "date", "ref", "displayValue", "heDisplayValue"

    def __init__(self, date, title, start, end):
        self.date = date
        if title == "Parasha":
            parasha = get_parasha(datetime.strptime(self.date, "%d/%m/%Y"))
            self.displayValue = parasha["parasha"]
            try:
                self.heDisplayValue = Term().load({"name": self.displayValue.replace("-", " ")}).get_primary_title('he')
            except AttributeError as e:
                parts = self.displayValue.split("-")
                self.heDisplayValue = []
                for part in parts:
                    self.heDisplayValue.append(Term().load({"name": part}).get_primary_title('he'))
                self.heDisplayValue = "-".join(self.heDisplayValue)
            start = Ref(parasha["aliyot"][0]).starting_ref()
            for aliyah in range(1, 8):
                next_aliyah = Ref(parasha["aliyot"][aliyah]).starting_ref()
                prev_aliyah_last_ref = Ref(parasha["aliyot"][aliyah-1]).ending_ref()
                if prev_aliyah_last_ref.next_segment_ref() != next_aliyah:
                    self.ref = start.to(prev_aliyah_last_ref).normal()
                    break
            assert len(self.ref) > 0
        else:
            start = Ref(start)
            end = Ref(end)
            index, sec = " ".join(title.split()[:-1]), title.split()[-1]
            if "." in sec:
                self.displayValue = "{} Seder {}".format(index, sec)
                sec_1 = encode_small_hebrew_numeral(int(sec.split(".")[0]))
                sec_2 = encode_small_hebrew_numeral(int(sec.split(".")[1]))
                sec = "{}.{}".format(sec_1, sec_2)
            else:
                self.displayValue = "{} Seder {}".format(index, sec)
                sec = encode_small_hebrew_numeral(int(sec))
            try:
                index = library.get_index(index).get_title('he')
            except BookNameError as e:
                replace_titles = {"Chronicles": "דברי הימים", "Kings": "מלכים", "Samuel": "שמואל"}
                for en_title in replace_titles:
                    index = index.replace(en_title, replace_titles[en_title])
            self.heDisplayValue = "{} סדר {}".format(index, sec)
            self.ref = configure_refs(start, end)[0]



def configure_refs(r1, r2):
    """
    :param Ref r1:
    :param Ref r2:
    :return:
    """
    if r1.book == r2.book:
        return [r1.to(r2).normal()]

    next_chap = book_end = r1
    while next_chap:
        book_end = next_chap
        next_chap = next_chap.next_section_ref()

    prev_chap = book_start = r2
    while prev_chap:
        book_start = prev_chap
        prev_chap = prev_chap.prev_section_ref()

    return [r1.to(book_end).normal(), book_start.to(r2).normal()]


rows = []
with open("Tanach_Yomi_Sedarim_Calendar_-_updated.csv") as fp:
    for r in csv.reader(fp):
        try:
            rows.append(TanakhRow(*r))
        except Exception as e:
            break
print(len(rows))
entries = [
    {
        "date": datetime.strptime(row.date, "%d/%m/%Y"),
        "ref": row.ref,
        "displayValue": row.displayValue,
        "heDisplayValue": row.heDisplayValue
    }
    for row in rows
]
collection = db.tanakh_yomi
db.drop_collection(collection)
for entry in entries:
    collection.insert_one(entry)
collection.create_index("date")