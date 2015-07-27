# -*- coding: utf-8 -*-

import MySQLdb
from sefaria.model import *

PersonSet().delete()
PersonRelationshipSet().delete()
PersonRelationshipTypeSet().delete()

prt = PersonRelationshipType({"key": "student"})
prt.set_forward_name(u"Learned From", "en")
prt.set_forward_name(u"רבותיו", "he")
prt.set_reverse_name(u"Taught", "en")
prt.set_reverse_name(u"תלמידיו", "he")
prt.save()

db = MySQLdb.connect(user="root", db="sages", charset='utf8')
cur = db.cursor()

sages = {}

cur.execute("""
  select sage_id, sage_name_heb, sage_title_heb, sage_title_en, sage_name_en, sp_period_symbol, art_je, art_wiki, sr_region_name_heb, region_name_en
  from sages
  left outer join sage_period on sage_id=sp_sage_id
  left outer join articles on sage_id=a_sage_id
  left outer join sage_region on sage_id=sr_sage_id
  left outer join regions on sr_region_name_heb=region_name_heb
""")
rows = cur.fetchall()

for row in rows:
    sages[row[0]] = {
        "id": row[0],
        "sage_name_heb": row[1],
        "sage_title_heb": row[2],
        "sage_title_en": row[3],
        "sage_name_en": row[4],
        "period": row[5],
        "je_link": row[6],
        "wp_link": row[7],
        "region_he": row[8],
        "region_en": row[9],
    }

for id, s in sages.iteritems():
    en_alts = []
    cur.execute("select alt_title_en, alt_name_en from alt_name_en where ane_sage_id={} ".format(id))
    rows = cur.fetchall()
    for row in rows:
        en_alts.append(row)

    he_alts = []
    cur.execute("select alt_title_heb, alt_name_heb from alt_name_heb where anh_sage_id={};".format(id))
    rows = cur.fetchall()
    for row in rows:
        he_alts.append(row)

    s.update({
        "en_alts" : en_alts,
        "he_alts" : he_alts
    })


for id, s in sages.iteritems():
    p = Person({})
    p.key = s["sage_title_en"] + u" " + s["sage_name_en"]
    p.name_group.add_title(s["sage_title_en"] + u" " + s["sage_name_en"], "en", primary=True)
    p.name_group.add_title(s["sage_title_heb"] + u" " + s["sage_name_heb"], "he", primary=True)
    for x in s["en_alts"]:
        p.name_group.add_title(x, "en")
    for x in s["he_alts"]:
        p.name_group.add_title(x, "he")
    tp = TimePeriod().load({"symbol": s["period"]})
    if tp.type == "Generation" or tp.type == "Two Generations":
        p.generation = s["period"]
    elif tp.type == "Era":
        p.era = s["period"]
    p.enWikiLink = s["wp_link"]
    p.jeLink = s["je_link"]
    p.sex = "M"
    p.save()



cur.execute("select l_sage_id_student, l_sage_id_teacher from lineage")
rows = cur.fetchall()
for row in rows:
    PersonRelationship({
        "type": "student",
        "from_key": sages[row[0]]["sage_title_en"] + u" " + sages[row[0]]["sage_name_en"],
        "to_key":  sages[row[1]]["sage_title_en"] + u" " + sages[row[1]]["sage_name_en"]
    }).save()
