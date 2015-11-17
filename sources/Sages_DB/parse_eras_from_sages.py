# -*- coding: utf-8 -*-


import MySQLdb
import codecs
from sefaria.model.time import TimePeriod, TimePeriodSet
import re

db = MySQLdb.connect(user="root", db="sages", charset='utf8')
cur = db.cursor()

sages = {}

cur.execute("""
  select period_symbol, period_seq, period_era, period_generation, period_dates
  from periods
  """)

dates= {
    "Z1" : (-180, -140),
    "Z2" : (-140, -100),
    "Z3" : (-100, -60),
    "Z4" : (-60, -30),
    "Z5" : (-30, 20),
    "T" : (20, 220),
    "GN" : (540, 1040),
    "RI" : (1040, 1560),
    "AH" : (1560, 1938)
}

era_lookup = {
 "Acharonim" : u"אחרונים",
 "Amoraim" : u"אמוראים",
 "Avot" : u"אבות",
 "Former Prophets" : u"נביאים ראשונים",
 "Geonim" : u"גאונים",
 "Great Assembly" : u"כנסת הגדולה",
 "Latter Prophets" : u"נביאים אחרונים",
 "Moshe Rabbeinu" : u"משה רבנו",
 "pre-Tannaic" : u"טרום התנאיתי",
 "Rishonim" : u"ראשונים",
 "Savoraim" : u"סבוראים",
 "Tannaim" : u"תנאים",
 "Tannaim/Amoraim" : u"תנאים / אמוראים",
 "Zugot" : u"זוגות",
}

generation_lookup = {
    "eighth generation": u"דור שמיני",
    "fifth and sixth generations": u"דורות חמישי ושישי",
    "fifth generation": u"דור חמישי",
    "first and second generations": u"דורות ראשון ושני",
    "first generation": u"דור ראשון",
    "fourth and fifth generations": u"דורות רביעי וחמישי",
    "fourth generation": u"דור רביעי",
    "second and third generations": u"דורות שני ושלישי",
    "second generation": u"דור שני",
    "seventh generation": u"דור שביעי",
    "sixth and seventh generations": u"דורות שישית ושביעי",
    "sixth generation": u"דור שישי",
    "third and fourth generations": u"דור שלישי ורביעי",
    "third generation": u"דור שלישי",
    "unknown generation": u"דור לא ידוע",
    "transition": u"דור מעבר"
}
rows = cur.fetchall()
TimePeriodSet().delete()

for row in rows:
    period = row[0]
    era = row[2]
    gen = row[3]
    ptype = ''
    primary_name = ''
    hebrew_name = u''

    if len(period) > 2:
        ptype = "Two Generations"
        primary_name = era + " - " + gen.title()
        hebrew_name = era_lookup[era] + u" - " + generation_lookup[gen]
    elif (period[0] == 'T' or period[0] == 'Z' or period[0] == 'A') and len(period) > 1 and period[1] != "H" and period[1] != 'V':
        ptype = "Generation"
        primary_name = era + " - " + gen.title()
        hebrew_name = era_lookup[era] + u" - " + generation_lookup[gen]
    else:
        ptype = "Era"
        primary_name = era
        hebrew_name = era_lookup[era]

    range_string = row[4].replace(u"–",u"-")
    tp = TimePeriod({
        "symbol": period,
        "order": float(row[1]),
        "range_string": range_string,
        "type": ptype,
        "startIsApprox": True,
        "endIsApprox": True
    })
    tp.add_name(primary_name, "en", primary=True)
    tp.add_name(hebrew_name, "he", primary=True)

    m = re.match(ur"\s*(\d+)\s*-\s*(\d+)\s*CE", range_string)
    if dates.get(tp.symbol):
        d = dates.get(tp.symbol)
        tp.start = int(d[0])
        tp.end = int(d[1])
    elif m:
        tp.start = int(m.group(1))
        tp.end = int(m.group(2))
    else:
        print "?? " + row[4]

    tp.save()

t = TimePeriod({
    "symbol": "A",
    "order": 18.5,
    "range_string": "220 - 500 CE",
    "start": 220,
    "end": 500,
    "type": "Era",
    "startIsApprox": True,
    "endIsApprox": True
})
t.add_name("Amoraim", "en", primary=True)
t.add_name(u"אמוראים", "he", primary=True)
t.save()


t = TimePeriod({
    "symbol": "CO",
    "order": 31,
    "range_string": "1939 CE - ",
    "start": 1939,
    "end": 2015,
    "type": "Era",
    "startIsApprox": True,
    "endIsApprox": True
})
t.add_name("Contemporary", "en", primary=True)
t.add_name(u"בני דורנו", "he", primary=True)
t.save()
