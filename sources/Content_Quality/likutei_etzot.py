from sources.functions import *
root = SchemaNode()
root.add_primary_titles("Likutei Etzot", "ליקוטי עצות")
root.key = "Likutei Etzot"

nodes = """הקדמה מדפוס ראשון / Introduction to First Edition
הקדמה מדפוס שני / Introduction to Second Edition
אמת ואמונה / Truth and Faith
אנחה / Sighing
אכילה / Eating
הכנסת אורחים / Hospitality
ארץ ישראל / Eretz Israel
ברית / Berit
בנים / Children
בטחון / Trust
בושה / Shame
בגדים / Clothing
גאוה וענוה / Arrogance and Humility
דעת / Knowledge
דיבור / Speech
התבודדות / Hitbodedut
התחזקות / Strengthening
השגות והתנוצצות אלוקות / Divine Attainments
וידוי דברים / Confession
זיכרון / Memory
חקירות וחכמות חיצוניות / Philosophy and Secular Wisdom
חיתון / Marriage
חצות / Midnight
טלטול ונסיעת דרכים / Travel
יראה ועבודה / Fear of God
כעס / Anger
כבוד וגדולה ומנהיגות / Honor
ליצנות / Scoffing
ממון ופרנסה / Money and Livelihood
מחשבות והרהורים / Thoughts
מחלוקת ומריבה / Dispute and Discord
מניעות / Obstacles and Inhibitions
מקווה / Mikveh
מועדי ה' / Moadei Hashem
          שבת / Shabbat
          ראש חודש / Rosh Chodesh
          שלוש רגלים / Three Festivals
          ניסן ופסח / Nisan and Passover
          ספירה ושבועות / Omer and Shavuot
          ימים שבין המצרים / Three Weeks
          אלול / Elul
          ראש השנה / Rosh Hashana
          יום כיפור / Yom Kippur
          סוכות / Sukkot
          חנוכה / Chanukah
          פורים / Purim
נגינה / Music
סבלנות / Patience
עזות / Brazenness
עצה / Advice
עינים / Eyes
פדיון / Redeeming Prisoners
צדיק / Tzadik
צדקה / Charity
ציצית / Tzitzit
קדושה / Sanctity
רצון וכיסופין / Desire and Yearning
רפואה / Healing
שמחה / Happiness
שלום / Peace
תלמוד תורה / Torah Learning
תפילה / Prayer
תוכחה / Discipline
תפילין / Tefillin
תענית / Fasting
תשובה / Repentance
תמימות / Completeness""".splitlines()
prev_node = None
for node in nodes:
    he, en = node.split(" / ")
    new_node = JaggedArrayNode()
    new_node.add_primary_titles(en, he.strip())
    new_node.key = en
    new_node.add_structure(["Paragraph"])
    new_node.validate()
    if he != he.strip():
        prev_node.append(new_node)
    elif prev_node and len(prev_node.children) > 0:
        root.append(new_node)
        prev_node = new_node
    else:
        root.append(new_node)
        prev_node = new_node
root.validate()
indx  = {
    "title": root.key,
    "categories": ["Chasidut", "Breslov"],
    "schema": root.serialize(),
}
post_index(indx)