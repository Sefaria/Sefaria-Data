import MySQLdb
import codecs

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

    teachers = []
    students = []

    cur.execute("select l_sage_id_student from lineage where l_sage_id_teacher={};".format(id))
    rows = cur.fetchall()
    for row in rows:
        students.append(row[0])

    cur.execute("select l_sage_id_teacher from lineage where l_sage_id_student={};".format(id))
    rows = cur.fetchall()
    for row in rows:
        teachers.append(row[0])

    s.update({
        "en_alts" : en_alts,
        "he_alts" : he_alts,
        "teachers": teachers,
        "students": students
    })


f = codecs.open('/tmp/sages.csv', 'w', encoding='utf-8')

f.write(u"|".join([
    "id",
    "title",
    "name",
    "alt names",
    "heb title",
    "heb name",
    "alt heb names",
    "period",
    "j encyclopedia link",
    "wiki link",
    "region",
    "teachers",
    "students"
]) + u"\n")

for id, s in sages.iteritems():
    f.write(u"|".join([unicode(s).strip() for s in [
        unicode(id),
        s["sage_title_en"],
        s["sage_name_en"],
        u", ".join([unicode(x[0]) + u" " + unicode(x[1]) for x in s["en_alts"]]),
        s["sage_title_heb"],
        s["sage_name_heb"],
        u", ".join([unicode(x[0]) + u" " + unicode(x[1]) for x in s["he_alts"]]),
        s["period"],
        s["je_link"],
        s["wp_link"],
        s["region_en"],
        u", ".join([sages[i]["sage_title_en"] + u" " + sages[i]["sage_name_en"] for i in s["teachers"]]),
        u", ".join([sages[i]["sage_title_en"] + u" " + sages[i]["sage_name_en"] for i in s["students"]])
    ]]) + u"\n")

