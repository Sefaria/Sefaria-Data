# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
from sefaria.model import *
from sources.functions import *
from data_utilities.dibur_hamatchil_matcher import *


SERVER = "http://proto.sefaria.org"

def create_schema(en, he):
    root = SchemaNode()
    root.add_primary_titles(en, he)

    intro = JaggedArrayNode()
    intro.add_primary_titles("Introduction", u"הקדמה")
    intro.add_structure(["Paragraph"])

    default_node = JaggedArrayNode()
    default_node.key = "default"
    default_node.default = True
    default_node.add_structure(["Chapter", "Mishna", "Paragraph"])


    root.append(intro)
    root.append(default_node)
    root.validate()

    index = {
        "title": "Magen Avot",
        "dependence": "Commentary",
        "schema": root.serialize(),
        "base_text_titles": ["Pirkei Avot"],
        "collective_title": "Magen Avot",
        "categories": ["Mishnah", "Commentary", "Seder Nezikin"]
    }

    post_index(index, server=SERVER)

def get_text(f):
    current_perek = 0
    text = {}
    dhs = {}
    start = False
    for line in f:
        orig_line = line
        if not start and line.find("@00פרק") == -1:
            continue
        else:
            start = True
        line = line.replace("\n", "").replace("\r", "").decode('utf-8')
        if len(line) < 5:
            continue
        if line.find("@00") >= 0:
            current_perek += 1
            text[current_perek] = []
            dhs[current_perek] = []
            continue

        if line.find("@11") == 0:
            assert line.find("@") != line.rfind("@")
            line = line.replace("@11", "")
            end = line.find("@")
            dhs[current_perek].append(line[0:end])
            line = removeAllTags(line)
            line = u"<b>{}</b>{}".format(line[0:end], line[end:])
            text[current_perek].append(line)
        else:
            line = removeAllTags(line)
            text[current_perek].append(line)
            dhs[current_perek].append(" ".join(line.split(" ")[0:10]))

    return text, dhs

def restructure(text, dhs):
    def base_tokenizer(str):
        str = re.sub(ur"\([^\(\)]+\)", u"", str)
        word_list = re.split(ur"\s+", str)
        word_list = [strip_nekud(w) for w in word_list if w]  # remove empty strings
        return word_list

    results = {}
    new_text = []
    print "start to link"
    for perek in dhs:
        base = TextChunk(Ref("Pirkei Avot {}".format(perek)), lang='he')
        results[perek] = match_ref(base, dhs[perek], base_tokenizer)['matches']
        new_text.append([])
        new_text[perek-1] = []
        highest = -1
        for each in results[perek]:
            if each and each.sections[1] > highest:
                highest = each.sections[1]
        for i in range(highest):
            new_text[perek-1].append([])

        section = 1
        prev_comms = []
        for pos, result in enumerate(results[perek]):
            comm = text[perek][pos]
            if result:
                section = result.sections[1]
                if len(prev_comms) > 0:
                    for prev in prev_comms:
                        new_text[perek-1][section-1].append(prev)
                    prev_comms = []
                new_text[perek-1][section-1].append(comm)
            else:
                prev_comms += [comm]

        make_links(perek, new_text[perek-1])


    return new_text


def make_links(perek_num, text):
    links = []
    for section_count in range(len(text)):
        for comment_count in range(len(text[section_count])):
            pirkei_ref = "Pirkei Avot {}:{}".format(perek_num, section_count+1)
            magen_ref = "Magen Avot {}:{}:{}".format(perek_num, section_count+1, comment_count+1)
            links.append({
                "refs": [
                             pirkei_ref,
                            magen_ref
                        ],
                "type": "commentary",
                "auto": True,
                "generated_by": "Magen Avot"
            })
    post_link(links, server=SERVER)


def post(text):
    send_text = {
        "text": text,
        "language": "he",
        "versionTitle": "Magen Avot, Leipzig 1855",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001277746"
    }
    post_text("Magen Avot", send_text, server=SERVER)
    intro=u"""הרב המחבר זלה"ה
בשם ה' אל עולם
ומצא חן ושכל טוב בעיני אלהים ואדם:
אמר שמעון בה"ר צמח זלה"ה בפתיחת ספרינו זה אשר קראנוהו מגן אבות כתבנו כי עיקר כונתינו היה לפרש מסכת אבות ותחילת המחשבה היא סוף המעשה. והנה זאת המסכתא היא יקרה מאד כי היא המביאה האדם אל השלימות. ולזה אמרו רז"ל בפרק המניח את הכד האי מאן רבעי למהוי חסידא ליקיים מילי דאבות. ואין לנו מעלה יותר גדולה מהחסידות וכבר אמרו חז"ל בראשון מע"ז חסידות מביאה לידי רוח הקדש שנאמר אז דברת בחזון לחסידיך והאומר ענוה גדולה מכולן החסידות גם כן מביאה לידי ענוה. ואע"פי שאמרו ז"ל גם כן האי מאן דבעי למהוי חסידא ליקיים מילי דנזיקין וכן אמרו ליקיים מילי דברכות זאת המסכתא יש לה יתר שאת על ברכות ונזיקין. כי ידוע הוא שהמעלה הגדולה אשר אין אחריה מעלה היא שיהיה האדם טוב לשמים וטוב לבריות וזהו שנאמר ומצא חן ושכל טוב בעיני אלהים ואדם. ואמרו ז"ל בפרק ראשון מקדושין אמרו לצדיק כי טוב כי פרי מעלליהם יאכלו וכי יש צדיק טוב ויש צדיק שאינו טוב אלא טוב לשמים וטוב לבריות זהו צדיק שהוא טוב טוב לשמים ואינו טוב לבריות זהו צדיק שאינו טוב ועל ידי מסכת ברכות האדם הוא טוב לשמים שיהיה שם שמים שגור בפיו בכל שעה על ידי קריאת שמע בברכותיה ותפלה וברכות השבח וההודאה וברכות המצות וברכות הנהנין ועל זה נאמר שויתי ה' לנגדי תמיד כי מימיני בל אמוט כלומר כמו שאין אדם שוכח יד ימינו כלל אבל היא מזומנת לו לכל צרכיו כן ראוי לאדם לשום שם שמים לנגדו תמיד. ואמרו רז"ל בפרק שואל אל תפנו אל מדעתכם וזהו תועלת המגיע ממסכת ברכות המביאה לידי חסידות. ועל ידי מסכת נזיקין הנחלקת לשלשה חלקים הנקראים תלתא בבי הוא טוב לבריות שישמור האדם מלהזיק לבריות ושיעשה גדרים לעצמו שלא יהיה שום אדם ניזוק ממנו אפילו בסיבה רחוקה ובגרמא כמו שהיו חסידים הראשונים מצניעין קוצותיהן וזכוכיותיהן בתוך שדותיהן ומעמיקין להם שלשה טפחים כדי שלא תעלם המחרישה וזהו התועלת המגיע ממסכת נזיקין המביאה לידי חסידות. וזאת המסכתא היא כוללת שתי התועליות יחד שהמקיים אותם הוא טוב לשמים וטוב לבריות כמו שיתבאר מדבריה ולזה סדרוה בסדר נזיקין. כי אחרי שסדרו מס' ברכות בסדר זרעים הקודם לשאר הסדרים וזה לשני טעמים האחד כי זאת המסכתא ראוי להקדימה לשאר מסכתות כי היא הקודמת לשאר מעשים לקרות קריאת שמע ולהתפלל בתחילת היום. והשני כי כל סדר זרעים צריך לברכה כהפרשת תרומה ומעשרות וחלה ובכורים וסידרו מסכת נזיקין בסדר הראוי לה על כן באותו סדר עצמו סידרו מסכת זו הכוללת בתועלתה לשתי המסכתות האלה שהם ברכות ונזיקין:
ועוד יש טעם אחר למה סדרוה בזה הסדר לפי שיש בסדר הזה מסכת סנהדרין וכל החכמים הנזכרים בזאת המסכתא עד רבן יוחנן בן זכאי היו מסנהדרין וגם החכמים שהיו אחר החורבן היו מהסנהדרין כמו ששנינו אמר שמעון בן עזאי מקובל אני מפי שבעים ושנים זקנים ביום שהושיבו רבי אלעזר בן עזריה בישיבה בראשון מזבחים ובמסכת ידים אע"פ שלא היו דנין דיני נפשות ארבעים שנה קודם חורבן הבית כמו שנזכר בראשון מע"ז ובסנהדרין פרק היו בודקין. ויש בזאת המסכתא אזהרות ומוסרים אל הדיינין. וראוי שיהיו אחרי מסכת סנהדרין הקודמת לזאת המסכתא בשתי מסכתות המדברת במינוי הדיינין ותחילת המסכתא הוא הוו מתונין בדין והיא אזהרה לדיינין. ולא נמצאת לזאת המסכתא גמרא לא ירושלמית ולא בבלית לפי שאינה מדברת בדין מהדינין אבל יש קצת משניות נזכרות במקומות מהתלמוד ומהמדרשות. וכן לא נמצאת לה ברייתא ולא תוספתא כי אם אבות דרבי נתן כי רבינו הקדוש שחיבר המשנה ורבי נתן היו סוף התנאים כמו שנזכר בפרק השוכר את הפועלים והיו דברי רבינו הקדוש יותר קצרים מדברי רבי נתן על כן נזכרו במשנה ליופי סדורם ולצחות לשונם:
ונהגו לקרות מסכתא זו בבתי כנסיות ובבתי מדרשות אחר תפלת המנחה בקיץ שהימים ארוכים למשוך לב עמי הארץ לתורה. יש מקומות מפסח ועד העצרת ויש מקומות אחר העצרת וכן מנהגינו במקומותינו כי ראוי לסמוך קריאתה לזמן מתן הורה או מלפניו או מלאחריו. ולזה ראינו לפרשה כמו שפירשנו ספר איוב בספר שקראנוהו אוהב משפט עם הקדמת פרקים בהשגחה. ופירשנו האזהרות בספר שקראנוהו זוהר הרקיע והרחבנו בו איך ראוי שימנו המצות והוא ספר חמוד מאד וכבר נתפשטו שני ספרים אלו כי כמו שנהגו לקרות ספר איוב והאזהרות כל אחד בזמנו כך נהגו לקרות מסכתא זו בין שני זמנים אלה. וכמו שהועלנו התלמידים בפירוש איוב ואזהרות ראינו להועילם בפירוש זאת המסכתא להשאיר אחרינו ברכת מנחה לתלמידים. וכבר הקדמנו בספר הזה שלשה הלקים וזה הוא החלק הרביע אשר קראנוהו חלק ה' עמו לפי שנהגו להתחיל כל ישראל יש להם חלק והרוצה לכתוב אותו נפרד הרשות בידו:
ונהגו הסופרים לכתוב מסכתא זו בסדור תפלות ודלגו קצת משניות ולא ידענו למה אלא שראו לקצר שלא להטריח והכל נפרש בעזרת האל ית'. והנה שמנו לפנינו פירוש רבינו שלמה ז"ל אשר לא היה כמוהו מפרש לשונות על כוונת אומרם. ופירוש רבינו משה ז"ל אשר לא נמצא כמוהו מקרב הדברים אל המושכל. ופירוש רבינו יונה החסיד ז"ל אשר לא קם כמוהו מדבר ביראת ה' למשוך לבות בני האדם לדרכי החסידות. וגם הוא ז"ל, הזכיר פירושים מרבינו מאיר הלוי ז"ל מטליטלה הנודע בשם אבו אל עאפיה ואחר אלו הפירושים עם מה שאנו מוסיפין נפך משלנו בהרחבת ביאור בראיות מדברי חכמים ודרך סברתינו אין לחפש אחר פרושים אחרים כי הם מספיקים להבין הלשונות על כוונת אומרם ושיקבלם השכל ושיגיע האדם אל התכלית המכוונת בזאת המסכתא. ונקראת זאת המסכתא מסבת אבות לפי שנזכרים בה אבות הקבלה ושמה האמיתי הוא משנת חסידים כי זה הוא המכוון ממנה להפליג במעשה הטוב יותר מהמצווה בו וזהו ענין החסידות כמו שנפרש בעזרת האל וזה החלי בעזרת שד"י:"""
    send_text = {
        "text": [intro],
        "language": "he",
        "versionTitle": "Magen Avot, Leipzig 1855",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001277746"
    }
    post_text("Magen Avot, Introduction", send_text, server=SERVER)



if __name__ == "__main__":
    post_term({
        "name": "Magen Avot",
        "scheme": "commentary_works",
        "titles":
        [{
         "lang": "en",
         "text": "Magen Avot",
            "primary": True,
        },
        {
            "lang": "he",
            "text": u"מגן אבות",
            "primary": True
        }
        ]
    }, server=SERVER)
    create_schema("Magen Avot", u"מגן אבות")
    text, dhs = get_text(open("magen avot.txt"))
    text = restructure(text, dhs)
    post(text)