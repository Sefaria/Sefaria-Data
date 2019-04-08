#encoding=utf-8
import django
django.setup()
from sefaria.model import *
from sources.functions import *


def create_index():
    root = SchemaNode()
    root.key = "IbnEzraOnEccelesiastes"
    root.add_primary_titles("Ibn Ezra on Ecclesiastes", u"אבן עזרא על קהלת")

    intro = JaggedArrayNode()
    intro.add_shared_term("Introduction")
    intro.add_structure(["Paragraph"])
    intro.key = "intro"

    default = JaggedArrayNode()
    default.default = True
    default.key = "default"
    default.add_structure(["Chapter", "Verse", "Paragraph"])
    root.append(intro)
    root.append(default)
    root.validate()
    post_index({
        "title": "Ibn Ezra on Ecclesiastes",
        "schema": root.serialize(),
        "dependence": "Commentary",
        "base_text_titles": ["Ecclesiastes"],
        "base_text_mapping": "many_to_one",
        "categories": ["Tanakh", "Commentary", "Ibn Ezra", "Writings"],
        "collective_title": "Ibn Ezra"
    }, server=SEFARIA_SERVER)


if __name__ == "__main__":
    text = {}
    create_index()
    with open("kohelet.tsv") as f:
        lines = list(f)
        perek = 0
        for line_n, line in enumerate(lines):
            line = line.replace("\t\t", "\t")
            try:
                poss_perek, pasuk, comment = line.split("\t")
                if poss_perek:
                    poss_perek = poss_perek.replace("פרק ", "")
                    if perek:
                        text[perek] = convertDictToArray(text[perek])
                    perek = getGematria(poss_perek)
                    assert perek < 50
                    text[perek] = {}
                if pasuk not in text[perek]:
                    pasuk = getGematria(pasuk)
                    assert pasuk < 50
                    text[perek][pasuk] = []
                text[perek][pasuk].append(comment)
            except ValueError: #this is the case where there is just a comment with no perek or pasuk marked
                text[perek][pasuk].append(line)

    text[perek] = convertDictToArray(text[perek])

    send_text = {
        "language": "he",
        "versionTitle": "Wikisource",
        "versionSource": "https://he.wikisource.org/wiki/%D7%90%D7%91%D7%9F_%D7%A2%D7%96%D7%A8%D7%90_%D7%A2%D7%9C_%D7%A7%D7%94%D7%9C%D7%AA",
        "text": convertDictToArray(text)
    }
    post_text("Ibn Ezra on Ecclesiastes", send_text, server=SEFARIA_SERVER, index_count="on")
    intro = ["""בשם אשר לו הממשלת אחל לפרש קהלת:""",
"""אורח חיים למעלה למשכיל למען סור משאול מטה כי כאשר יתאוה האורח שנשבה לשוב אל ארץ מולדתו להיות עם משפחתו כי כן תכסף הרוח המשכלת להאחז במעלות הגבוהות עד עלותה אל מערכות אלהים חיים שאינמו שוכני בתי חומר כי הגויות נמשלות לבתים ובעפר יסודם וכענין די מדרהון עם בשרא לא איתוהי וזה יהיה אם תתלבן הרוח ותתקדש מטומאות תאוות הגויות המגואלות המטנפות הקודש להתערב בשאול מטה ותשיב אל לבה לדעת יסודה ולראות סודה בעיני החכמה שלא תכהינה והרחוק כקרוב לפניה והלילה כיום אז תהי נתכנת לדעת קשט אמרי אמת ויהיו מחוקקין עליה שלא ימחו בהפרדה מעל גויתה כי המכתב מכתב אלהים הוא כי למען הראותה הובאה הנה על כן נכלאה במסגר עד עת קץ וכל זה להועיל ולהטיב לה ואם סבלה עמל שנים במספר כן תנוס ותשמח עולמי עדי עד בלי קץ כי כל מעשה יפרד והיה לארבעה ראשים טוב כולו או טוב רובו ורע בקצהו או רע כולו או רע רובו וטוב בקצהו והחלק הראשון הוא מנת בני אלהים והחלק השני הם החיים אשר על פני האדמה והשנים הנשארים נעדרים לא יתכן המנאם כי לא יעשה ה׳ אלהים דבר כי אם טוב כי הכל לעולם טוב הוא וכן כתוב וירא אלהים את כל אשר עשה והנה טוב מאד ואם היה שם רע היה בקצהו כי בעבור רע מעט אין בדרך החכמה העליונה למנוע טוב רב ושורש הרע מחסרון המקבל ואם אין לנו יכולת לדמות מעשה אלהים כי אם אל מעשיו בעבור היות הכל מעשיו הנה ראינו ילבינו הבגדים השטוחים לשמש ויחשכו פני הכובס והלא הפועל אחד יוצא מפועל אחד לכן ישתנו הפועלים בעבור השתנות תולדת המקבלים ומחשבות בני אדם משתנות כפי תולדת גוייה וגוייה והשתנות התולדות בעבור השתנות המערכות העליונות ומקום השמש והמקבל כחה והמדינות והדתים והמאכלים ומי יוכל לספר אותם וכל דרך איש זך בעיניו ויער ה׳ אלהי ישראל את רוח שלמה ידידו לבאר דברי חפץ ולהורות הדרך הישרה כי כל מעשה שיעשה נוצר לא יעמוד כי כל הנברים ילאו לברוא עצם שהוא שורש או להכחידו עד שיהיה נעדר רק כל מעשיהם דמות ותמונה ומקרה להפקיד מחובר ולאבר נפרד ולהניע נח ולהניח נע על כן מעשה בני האדם תהו וריק כי אם יראת ה׳ ולא יוכל איש להשיג אל מעלת יראתו עד עלותו בסולם החכמה ויבנה ויכונן בתבונה:"""]

    send_text["text"] = intro
    post_text("Ibn Ezra on Ecclesiastes, Introduction", send_text, server=SEFARIA_SERVER, index_count="on")