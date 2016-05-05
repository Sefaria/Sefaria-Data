# -*- coding: utf-8 -*-
import pdb
import os
import sys
import re
import codecs
p = os.path.abspath(__file__)
sys.path.insert(0, p)
import sources
sys.path.insert(0, '../Match/')
from sources.Match import match
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from sources.local_settings import *
from sources.functions import *
import glob
sys.path.insert(0, SEFARIA_PROJECT_PATH)
from data_utilities.sanity_checks import Tag
from sefaria.model import *



def check_mishna_order():
    #checked Mishnayot for Pereks being in order and within each perek each comment is in order
    #checked Boaz for Pereks being in order but DID NOT check that each comment within each perek is in order

    # dont_count=['פ"', 'פרק ', 'בבא','פ', 'מעשר', 'פתח']

    count=0
    for file in glob.glob(u"*.txt"):
        file = file.replace(u"\u200f", u"")
        if file.split(" ")[0] == u"משניות":
            count += 1
            print file
            in_order(file, tag="@22", reset_tag="@00", increment_by=1)


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


def compare_tags_to_comments(main_tag, commentary_tag, output):
    """
    Check that their the number of comments in a commentary match the number of tags in the main text.
    Outputs errors to a file. main_tag and commentary_tag should have members added called segment_tag
    which indicate the beginning of a new section (chapter, verse, etc.).

    :param main_tag: A Tag object associated with the main text
    :param commentary_tag: Tag associated with the commentary.
    :param output: output file for results.
    """

    text_tags = main_tag.count_tags_by_segment(main_tag.segment_tag)
    comment_tags = commentary_tag.count_tags_by_segment(commentary_tag.segment_tag)

    perfect = True

    if len(text_tags) != len(comment_tags):
        output.write(u'Major alignment mismatch between {} and {}\n'.format(main_tag.name, commentary_tag.name))
        return

    for index, appearances in enumerate(text_tags):
        if appearances != comment_tags[index]:
            output.write(u'Tag mismatch {} and {} segment {}\n'.format(main_tag.name, commentary_tag.name, index+1))
            perfect = False

    if perfect:
        output.write(u'Perfect alignment {} and {}\n'.format(main_tag.name, commentary_tag.name))

