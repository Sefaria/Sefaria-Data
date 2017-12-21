# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
from sources.functions import *
from sefaria.model import *
from data_utilities.XML_to_JaggedArray import XML_to_JaggedArray
from sefaria.helper.schema import *
import bleach

SERVER = "http://draft.sefaria.org"

def get_order():
    chapters = """  - פתיחה / Prelude
  - שער החכמה / On Wisdom
  - שער הענוה / On Humility
  - שער הפרישות / On Abstinence
  - שער הצניעות והבשת / On Modesty and Shame
  - שער הרחקת התאווה / On Self Denial
  - שער הביטחון וייאוש התקווה באדם / On Man's Confidence and Despair
  - שער המתון והסבל / On Deliberation and Endurance
  - שער הספוק / On Sufficiency
  - שער החסד והצדק / On Kindness and Charity
  - שער הרש והשאלה / On Poverty and Asking Help
  - שער השתיקה ועת דבר נכוחה / On Silence and Speaking Opportunely
  - שער האמת / On Truth
  - שער החברים והחברה / On Companionship and Association
  - שער בחינת האוהבים והתנצלותם ומחילתם / On the Testing of Friends, their Indulgence, and Forgiveness
  - שער ההכרה וההנהגה / On Discernment and Manners
  - שער בהסתר הסוד / On Keeping a Secret
  - שער המלך / On Kingship
  - שער הכסילות והגאווה והאיוולת / On Stupidity, Pride, and Folly
  - שער הקנאה / On Jealousy
  - שער החנף ולשון הרע ושכן רע / On Hypocrisy, Slander, and Evil Neighbors
  - שער בקור האוהבים והחולים והכבדים בביקור / On Visiting Friends and the Sick, and on Nuisances in Visiting
  - שער אחרון מהספר והוא חבור המוסרים / Last Chapter of the Book; Collection of Maxims"""
    order_chapters = chapters.splitlines()
    order_chapters = [ch.split(" / ")[1] for ch in order_chapters]
    return order_chapters


def reorder_modify(text):
    return bleach.clean(text, strip=True)

if __name__ == "__main__":
    #add_term("Preface", u"פתח דבר", "pseudo_toc_categories", "http://localhost:8000")
    post_info = {}
    post_info["language"] = "en"
    post_info["server"] = SERVER
    allowed_tags = ["book", "intro", "part", "chapter", "p", "h1", "ftnote", "title", "ol", "footnotes", "appendix"]
    allowed_attributes = ["id"]
    p = re.compile("\d+a?\.")

    post_info["versionTitle"] = "Shekel HaKodesh"
    post_info["versionSource"] = "http://primo.nli.org.il/"
    title = "Shekel HaKodesh"
    file_name = "ShekelHaKodesh.xml"
    chapters = get_order()
    print chapters

    parser = XML_to_JaggedArray(title, file_name, allowed_tags, allowed_attributes, post_info, array_of_names=chapters, print_bool=True, change_name=True, image_dir="./images",
                                titled=True)
    parser.set_funcs(reorder_test=lambda x: x.tag == "h1", reorder_modify=reorder_modify)
    parser.run()