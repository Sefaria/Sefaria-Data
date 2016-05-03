# -*- coding: utf-8 -*-
"""
A series of sanity checks to be run on the Vilna Edition Mishna texts. Steve and I are both writhing tests,
to avoid merge conflicts down the line, we are keeping our tests separate for now, this may change down
the line.
"""

import os, sys
p = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print p
sys.path.insert(0, p)
from local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
import codecs


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

files_exist()