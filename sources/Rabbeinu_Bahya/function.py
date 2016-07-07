# -*- coding: utf-8 -*-
import codecs
import regex
from sefaria.model import *
from sources import functions
from data_utilities import util
from sources.Match import match_new
from sources.Match.match import Match
from sefaria.model.schema import AddressTalmud, SchemaNode, JaggedArrayNode
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json
import pdb
import os
import sys
import re
p = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, p)

os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *
from functions import *

hebrew_names = []
english_names = []
bereishit = ['בראשית', 'נח', 'לך-לך', 'וירא', 'חיי שרה', 'תולדות', 'ויצא', 'וישלח', 'וישב', 'מקץ', 'ויגש', 'ויחי']
shemot = ['שמות', 'וארא', 'בא', 'בשלח', 'יתרו', 'משפטים', 'תרומה', 'תצוה', 'כי תשא', 'ויקהל', 'פקודי']
vayikra = ['ויקרא', 'צו', 'שמיני', 'תזריא', 'מצרא', 'אחרי מות', 'קדשים', 'אמור', 'בהר', 'בחקתי']
bamidbar = ['במדבר', 'נשא', 'בהעלתך', 'שלח', 'קרח', 'חקת', 'בלק', 'פינחס', 'מטות', 'מסעי']
devarim = ['דברים', 'ואתחנן', 'עקב', 'ראה', 'שפטים', 'כי תצא', 'כי תבוא', 'נצבים', 'וילך', 'האזינו', 'וזאת הברכה']
hebrew_names.append(bereishit)
hebrew_names.append(shemot)
hebrew_names.append(vayikra)
hebrew_names.append(bamidbar)
hebrew_names.append(devarim)

bereishit_english = ['Bereishit', 'Noah', 'Lech-Lecha', 'Chaya Sarah', 'Toldos', 'Vayetze', 'Vayishlach', 'Vayeishev', 'Miketz', 'Vayigash', 'Vayihi']
shemot_english = ['Shemot', 'Varah', 'Bo', 'Beshalah', 'Yitro', 'Mishpatim', 'Terumah', 'Tizaveh', 'Ki Tisa', 'Vayekel', 'Pikudei']
vayikra_english = ['Vayikra', 'Tzav', 'Shimini', 'Tazria', 'Metzora', 'Ahrei Mot', 'Kedoshim', 'Emor', 'Behar', 'Behukotai']
bamidbar_english = ['Bamidbar', 'Naso', 'Behaloteha', 'Shelah', 'Korah', 'Hukat', 'Balak', 'Pinheas', 'Matos', 'Masai']
devarim_english = ['Devarim', 'Veethanan', 'Ekev', 'Reah', 'Shoftim', 'Ki Taza', 'Ki Tavo', 'Netzavim', 'Vayaleh', 'Hazinu', 'Vzot Habraha']
english_names.append(bereishit_english)
english_names.append(shemot_english)
english_names.append(vayikra_english)
english_names.append(bamidbar_english)
english_names.append(devarim_english)



def create_indices():
    rabbeinu_bahya_book = SchemaNode()
    rabbeinu_bahya_book



def create_jagged_array_node(dictionary):
    intro_node = JaggedArrayNode()
    intro_node.add_title(dictionary['english_title'],"en", primary=True)
    intro_node.add_title(dictionary['hebrew_title'],"he", primary=True)
    intro_node.key = dictionary['english_title']
    intro_node.depth = 1
    intro_node.addressTypes = ["Integer"]
    intro_node.sectionNames = ["Comment"]
    return intro_node



