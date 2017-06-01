# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'

from data_utilities.XML_to_JaggedArray import *
SERVER = "https://www.sefaria.org"

def cleanNodeName(text, titled=False):
    text = cleanText(text)
    bad_chars = [":", '-', '.']
    bad_chars += re.findall(u"[\u05D0-\u05EA]+", text)
    for bad_char in bad_chars:
        text = text.replace(bad_char, ",")
        " ".join(text.split())
    text = bleach.clean(text, strip=True)
    if titled:
        return text.title()
    return text

def cleanText(text):
    things_to_replace = {
        u'\xa0': u'',
        u'\u015b': u's',
        u'\u2018': u"'",
        u'\u2019': u"'",
        u'\u05f4': u'"',
        u'\u201c': u'"',
        u'\u201d': u'"',
        u'\u1e93': u'z',
        u'\u1e24': u'H'
    }
    for key in things_to_replace:
        text = text.replace(key, things_to_replace[key])
    return text

def create_schema_parts():
    part = None
    root = None
    root_title = ""
    for line in open("structure.txt"):
        line = line.replace("\n", "").replace("\r", "")
        if len(line) == 0:
            continue
        en, he = line.split(" / ")
        en = cleanNodeName(en.decode('utf-8')).strip()
        if line.startswith("Contemporary Halakhic"):
            if part:
                root.append(part)
                part = None
            if root:
                post_index_schema(root, root_title)
            root = SchemaNode()
            root_title = en
            root.add_primary_titles(en, he)
        elif line.startswith("Part I"):
            if part:
                root.append(part)
            part = SchemaNode()
            part.add_primary_titles(en, he)
        elif line.startswith("  "):
            print line
            node = JaggedArrayNode()
            node.add_structure(["Paragraph"])
            node.add_primary_titles(en, he)
            part.append(node)
        elif line.find(" / ") >= 0:
            node = JaggedArrayNode()
            node.add_structure(["Paragraph"])
            node.add_primary_titles(en, he)
            if line.startswith("Appendi") and part:
                root.append(part)
                part = None
            root.append(node)
    post_index_schema(root, root_title)


def post_index_schema(root, title):
    root.validate()
    post_index({
        "schema": root.serialize(),
        "title": title,
        "categories": ["Modern Works"]
    }, server=SERVER)

def reorder_modify(text):
    return bleach.clean(text, strip=True)

if __name__ == "__main__":
    simanim_arr = u"""סימן א. בענין אשה שיש לה שבר סמוך למקורה ואינה יכולה להטהר לבעלה
סימן ב. תשובת הגאון מהור"ר איצק שפירא אב"ד דמדינות פיהם
סימן ג. תשובה מן בני הרב מהר"ט אב"ד באוטיץ וגליל ברוין
סימן ד. אשה שמצאה קרטין אדומים וגם אם יש לסמוך ארופאים
סימן ה. אשה שישבה על המשבר ולא ילדה אם טהורה לבעלה
סימן ו. בשר יבש שנמצא עליו כמו מילבי"ן
סימן ז. סופר שאמר שכתב חק תוכות בספר תורה
סימן ח. אם חולה שאין בו סכנה מותר לשתות סתם יינם
סימן ט. אם חייב לקיים שילוח הקן בקן שבחצירו
סימן י. התפלל תפילת מוסף עם הציבור ומסופק אם התפלל שחרית או מוסף
סימן יא. אם מותר להניח מקום השמות פנוי ואחר כך לכתוב על פי סוד
סימן יב. סופר שכתב אות י' משם הוי"ה ולא הניח כמלא אות קטנה
סימן יג. אם יש קפידא במשודכת שמתו שני חתניה
סימן יד. חתן שקיבל עליו להשתדל חזקת יישוב ואין ביכלתו מאחר שציוה שלא לפרסם השידוך
סימן טו. אשה שמצאה דם במי רגליה ולא לפניו ולא לאחריו
סימן טז. קושיא אחת בחושן משפט סימן קצ"ה וגם על נוסח השבעת כתובה
סימן יז. תשובה להרב המופלא הנ"ל
סימן יח. חזר השואל וחיזק דבריו ועוד קושיא על אבה"ע סימן פ"ו שסותר לחו"מ סימן צ"ט
סימן יט. השגות על תשובתו
סימן כ. אם מותר לקרות שם ילד על שם אחיו שמת
סימן כא. אם מת המלך אם כל ישראל מחוייבין להתעסק עמו
סימן כב. בענין עגונה שנשרף בעלה
סימן כג. בענין עגונה שנטבע בעלה מן הרב דק"ק ווירמיישא
סימן כד. תשובה להרב הנ"ל
סימן כה. תשובת הגאון המפורסם מהור"ר יחזקאל אב"ד דק"ק פראג יע"א בעסק הנ"ל
סימן כו. השגות על דברי הגאון אב"ד דק"ק פראג בקצרה
סימן כז. מן בני הגאון מהור"ר טיאה על ענין הנ"ל
סימן כח. תשובה והשגה לבני הרב הנ"ל
סימן כט. הורה תשובה לאשה שנמצא בנה מת אצלה במטה
סימן ל. קושיא על הרא"ש בפסחים ובחולין בענין פלוגתא דחזקיה ורבי אבהו
סימן לא. בשם א-לקים נדבקה יו"ד תחתונה ונראה כחק תוכות
סימן לב. בשם קודש נכתבה אות אחת חציה על המטלית וחציה על היריעה
סימן לג. בענין קניית רשות מן השררה ואם לעשות מזוזה בקאפנעט <small>(חדר קטן)</small>
סימן לד. סופר שהאריך במזוזה ד' של אחד וע"י כן נכנסה ל' מן שורה שניה לתוך חלל הד'
סימן לה. לברר הדין אם כתב וחתם ונתן הגט בלילה אם יש להכשיר
סימן לו. מי שנסע אחיו ולא נודע איה איפה הוא האיך לתקן שלא תהיה אשתו זקוקה ליבום
סימן לז. בירור הדין מה שאמרו אם נשאת לא תצא, אם נשאת ולא נבעלה מה דינו
סימן לח. היתר לאכול גריני קערנר שנמצאו בהם תולעים
סימן לט. מי שמת בתוך החג אם שמיני עצרת עולה לז' ימים למנין שלשים""".splitlines()
    nodes = []
    for count, siman in enumerate(simanim_arr):
        finds = re.findall(u"<small>.*?</small>", siman)
        if finds:
            siman = siman.replace(finds[0], "")
        node = ArrayMapNode()
        node.add_primary_titles("Siman {}".format(count+1), siman)
        node.depth = 0
        node.wholeRef = "Torat Netanel {}".format(count+1)
        node.refs = []
        nodes.append(node.serialize())

    #index = get_index_api("Torat Netanel", server="http://proto.sefaria.org")
    #index['alt_structs'] = {"Simanim": {"nodes": nodes}}
    #post_index(index, server="http://proto.sefaria.org")

    create_schema_parts()
    post_info = {}
    post_info["language"] = "en"
    post_info["server"] = SERVER
    allowed_tags = ["book", "table", "intro", "ol", "h1", "h2", "h3", "h4", "h5", "part", "chapter", "p", "ftnote", "title", "footnotes", "appendix"]
    allowed_attributes = ["id"]
    p = re.compile("\d+a?\.")
    post_info["versionTitle"] = "Contemporary halakhic problems; by J. David Bleich, 1977-2005"
    post_info["versionSource"] = "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001100271"

    for i in range(6): #range(6):
        title = "Contemporary Halakhic Problems, Vol {}".format(i+1)
        file_name = "ContemporaryHalakhicProblems-Vol{}.xml".format(i+1)
        parser = XML_to_JaggedArray(title, file_name, allowed_tags, allowed_attributes, post_info, change_name=True, image_dir="./images")
        parser.set_funcs(reorder_test=lambda x: x.tag == "title" and x.text.find("<bold>") == 0, reorder_modify=reorder_modify)
        parser.run()