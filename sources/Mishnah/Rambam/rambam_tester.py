# -*- coding: utf-8 -*-

import os
from sefaria.model import *

tractates = library.get_indexes_in_category('Mishnah')


def standardize_files(identifyer):
    """
    Convert filenames to a standardized english format
    :param identifyer: tag to identify first word in filename
    """

    for book in tractates:

        # derive file name
        hebrew = Ref(book).he_book().replace(u'משנה', identifyer)
        he_file = u'{}.txt'.format(hebrew)
        en_file = '{}.txt'.format(book.replace('Mishnah','Rambam'))

        # check if file exists
        if os.path.isfile(he_file):
            print 'fixing {}'.format(en_file)
            os.rename(he_file, en_file)


def file_exists():
    """
    go through rambam files and check what's there and what isn't.
    """

    for book in tractates:

        rambam = book.replace('Mishnah', 'Rambam')
        if not os.path.isfile('{}.txt'.format(rambam)):
            print 'missing {}'.format(rambam)
