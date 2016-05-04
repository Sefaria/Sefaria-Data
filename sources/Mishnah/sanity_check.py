# -*- coding: utf-8 -*-
import pdb
import os
import sys
import re
import codecs
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
sys.path.insert(0, '../Match/')
from match import Match
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *
from functions import *
import glob

sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud


#checked Mishnayot for Pereks being in order and within each perek each comment is in order
#checked Boaz for Pereks being in order but DID NOT check that each comment within each perek is in order

#dont_count=['פ"', 'פרק ', 'בבא','פ', 'מעשר', 'פתח']

count=0
for file in glob.glob(u"*.txt"):
    file = file.replace(u"\u200f", u"")
    if file.split(" ")[0] == u"בועז":
        count += 1
        print file
        in_order(file, tag="@00", dont_count=['פ"', 'פרק ', 'בבא','פ', 'מעשר', 'פתח'])


def files_exist():
    """
    Looks through the directory to ensure all files that should be there do exist. It will also take care
    of naming conventions - i.e. it will mark a file as missing if it's named in an unpredictable manner.
    """

    # get a list of all tractates
    tractates = library.get_indexes_in_category('Mishnah')
    missing = codecs.open('missing_tractates.txt', 'w', 'utf-8')

    for tractate in tractates:
        ref = Ref(tractate)
        name = ref.he_book()
        terms = [u'משניות', u'יכין', u'בועז']

        for term in terms:
            file_name = u'{}.txt'.format(name.replace(u'משנה', term))
            if not os.path.isfile(file_name):
                missing.write(u'{}\n'.format(file_name))

    missing.close()
