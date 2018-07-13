# -*- coding: utf-8 -*-
import sys
import os
# for a script located two directories below this file
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
sys.path.append("/Users/Eytan/Desktop/sefaria/Sefaria-Data/sources")

from local_settings import *
from Likutei_Halachot_parse_text import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
from functions import *
import re
import data_utilities
import codecs
import unicodecsv as csv
from fuzzywuzzy import fuzz

from sources import functions

#this method returns enlish title of closest matching title on our topic table, given a hebrew title and the name of the order its from
def get_english_title(he_title, order):
    #for some reason, fuzzywuzzy doesn't work with הקדמת המחבר so we
    #do that explicitly
    if "הקדמת" in he_title:
        return "Author's Introduction"
    if "‏ארבע‏ ‏פרש" in he_title:
        return "Laws of the Four Festive Torah Portions"
    if "ברכת הריח" in he_title:
        return "Laws of Blessing on Fragrance"
    if "תשעה‏ ‏באב‏" in he_title:
        return "Laws of the Ninth of Av and Other Fast Days"
    if "הלכות ‏שאלה‏" in he_title:
        return "Laws of Borrowing"
    with open("Likutei_Halachot_"+order+".csv", 'rb') as csvfile:
        reader = csv.reader(csvfile)
        title_table = list(reader)
    he_title_list = []
    for row in title_table:
        he_title_list.append(row[0])

    return title_table[get_match_index(he_title,he_title_list)][1]

                       
def get_match_index(byte_term, input_list):
    term = byte_term.decode('utf-8')
    score=-1
    return_index = -1
    for index, item in enumerate(input_list):
        this_score = fuzz.ratio(term, item)
        if this_score>score:
            return_touple = [item, this_score]
            score = this_score
            return_index = index
    return return_index
def main():
    pass

if __name__ == "__main__":
    text = get_parsed_text()

    # create root record
    record = SchemaNode()
    record.add_title('Likutei Halachot', 'en', primary=True, )
    record.add_title(u'ליקוטי הלכות', 'he', primary=True, )
    record.key = 'Likutei Halachot'

    #add introduction node
    intro_node = JaggedArrayNode()
    intro_node.add_title("Author's Introduction", 'en', primary = True)
    intro_node.add_title("הקדמת המחבר", 'he', primary = True)
    intro_node.key = "Author's Introduction"
    intro_node.depth = 1
    intro_node.addressTypes = ['Integer']
    intro_node.sectionNames = ['Paragraph']

    record.append(intro_node)

    # add order nodes
    orders = [ ["Orach Chaim","אורח חיים"],["Yoreh Deah","יורה דעה"],["Even HaEzer","אבן העזר"],["Choshen Mishpat","חושן משפט"]]

    for index, order in enumerate(orders):
        order_node = SchemaNode()
        order_node.add_title(order[0], 'en', primary=True)
        order_node.add_title(order[1], 'he', primary=True)
        order_node.key = order[0]

        #add topic nodes to order node
        for topic in text[index][0]:
            print "INDEX TOPIC: ",topic,get_english_title(topic, order[0])
            topic_node = JaggedArrayNode()
            topic_node.add_title(get_english_title(topic, order[0]), 'en', primary = True)
            topic_node.add_title(topic, 'he', primary = True)
            topic_node.key = get_english_title(topic, order[0])
            topic_node.depth = 3
            topic_node.addressTypes = ['Integer','Integer','Integer']
            topic_node.sectionNames = ['Chapter','Section','Paragraph']

            order_node.append(topic_node)

        record.append(order_node)

    record.validate()
    #enter general work index
    index = {
        "title": "Likutei Halachot",
        "categories": ["Chasidut"],
        "schema": record.serialize()
    }


    post_index(index, weak_network=True)
    main()