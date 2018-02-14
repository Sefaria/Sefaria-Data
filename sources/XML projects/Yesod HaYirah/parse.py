# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
from sources.functions import *
from sefaria.model import *
from data_utilities.XML_to_JaggedArray import XML_to_JaggedArray
from sefaria.helper.schema import *
import bleach

SERVER = "http://draft.sefaria.org"
def get_order():
    order_chapters = """  - פתיחה / Prelude
      - שער היראה / On Fear
      - שערי התפילה והעבודה / On Prayer and Service
      - שער התורה והחכמה / On the Law and Wisdom
      - שער ההכרה / On Appreciation
      - שער הבשת והעזוז / On Shame and Shamelessness
      - שער הגאות והענווה / On Pride and Meekness
      - שער הסבל / On Endurance
      - שער הצניעות / On Humility
      - שער יצר הערווה / On Chastity
      - שער התאווה / On Desire
      - שער ההסתפקות / On Contentment
      - שער החריצות / On Industry
      - שער מעלת השתיקה והדיבור / On Silence and Speech
      - שער העצה והסוד / On Counsel and Secrets
      - שער הכבוד והשררה / On Dignity and Dominion
      - שער המתון והמהירות / On Deliberation and Haste
      - שער הכבדות / On Visiting and Its Abuse
      - שער האהבה והחברה / On Love and Companionship"""
    order_chapters = order_chapters.splitlines()
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
    post_info["versionTitle"] = "Yesod HaYirah"
    post_info["versionSource"] = "http://primo.nli.org.il/"
    title = "Yesod HaYirah"
    file_name = "YesodHayirah.xml"
    chapters = get_order()
    print chapters

    parser = XML_to_JaggedArray(title, file_name, allowed_tags, allowed_attributes, post_info, array_of_names=chapters, print_bool=True, change_name=True, image_dir="./images",
                                titled=True)
    parser.set_funcs(reorder_test=lambda x: x.tag == "h1", reorder_modify=reorder_modify)
    parser.run()