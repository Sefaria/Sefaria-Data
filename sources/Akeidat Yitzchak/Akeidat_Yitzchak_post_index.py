# -*- coding: utf-8 -*-
import sys
import os
# for a script located two directories below this file
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
sys.path.append("/Users/Eytan/Desktop/sefaria/Sefaria-Data/sources")

from local_settings import *

sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
#from sefaria.model import *

from functions import *
import re
import data_utilities
import codecs
from sources import functions


# create index record
record = SchemaNode()
record.add_title('Akeidat Yitzchak', 'en', primary=True, )
record.add_title(u"עקידת יצחק", 'he', primary=True, )
record.key = 'Akeidat Yitzchak'

#books = [ ["Bereishit","בְּרֵאשִׁית"],["Shemot","שִׁמוֹת"],["Vayikra","ויקרא"],["Bəmidbar","במדבר"],["Devarim","דברים"] ]


    book_node = JaggedArrayNode()
    book_node.add_title(book[1],'en',primary=True)
    book_node.add_title(book[2],'en',primary=True)
    book_node.key = book[1]
    book_node.depth = 2
    book_node.addressTypes = ['Integer','Integer']
    book_node.sectionNames = ['Gate','Chapter']

    
