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
    "AH" : (1560, 2500)
}

rows = cur.fetchall()
TimePeriodSet().delete()

for row in rows:
    period = row[0]
    era = row[2]
    gen = row[3]
    ptype = ''
    primary_name = ''

    if len(period) > 2:
        ptype = "Two Generations"
        primary_name = era + " - " + gen.title()
    elif (period[0] == 'T' or period[0] == 'Z' or period[0] == 'A') and len(period) > 1 and period[1] != "H" and period[1] != 'V':
        ptype = "Generation"
        primary_name = era + " - " + gen.title()
    else:
        ptype = "Era"
        primary_name = era

    range_string = row[4].replace(u"–",u"-")
    tp = TimePeriod({
        "symbol": period,
        "order": float(row[1]),
        "range_string": range_string,
        "type": ptype
    })
    tp.add_name(primary_name, "en", primary=True)

    m = re.match(ur"\s*(\d+)\s*-\s*(\d+)\s*CE", range_string)
    if m:
        tp.start = m.group(1)
        tp.end = m.group(2)
    elif dates.get(tp.symbol):
        d = dates.get(tp.symbol)
        tp.start = d[0]
        tp.end = d[1]
    else:
        print "?? " + row[4]

    tp.save()

t = TimePeriod({
    "symbol": "A",
    "order": 18.5,
    "range_string": "220 - 500 CE",
    "start": 220,
    "end": 500,
    "type": "Era"
})
t.add_name("Amoraim", "en", primary=True)
t.save()
