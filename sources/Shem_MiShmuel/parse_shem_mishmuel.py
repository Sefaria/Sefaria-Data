# encoding=utf-8

import re
import os
import codecs
import django
django.setup()
from sefaria.model import *
from functools import partial
from bs4 import BeautifulSoup
from data_utilities.util import PlaceHolder


"""
The workflowy defines a complex schema. What we need to do is parse each file and be able to associate each piece
with it's correct place in the schema. Let's start by getting the structure from the workflowy document, then we'll see
how easy it is to map names found in the files to that.


Still need to check that all nodes from workflowy have corresoponding text. Also should verify that all Parashot exist
in our workflowy.

Need to establish what each mark means. Seems that @00 and @22 indicate headers for new sections, while @66 and @11 
indicate new segments. We need to confirm that @66 and @11 are always followed by @77 and @33 respectively.
Strange marks: @99, @44, @55.

@44 and @55 are emphasis. Probably can swap with an opening and closing <big> tag for emphasis.

@99 is very rare. Use for an inline <br> (wit
"""


def get_node_names():
    filename = "Shem_MiShmuel_Workflowy_Structure.opml"
    with codecs.open(filename, 'r', 'utf-8') as fp:
        soup = BeautifulSoup(fp, 'lxml')
    root_tag = soup.body.outline
    leaf_tags = root_tag.find_all('outline')
    title_reg = re.compile(ur"^(?P<he>[\u05d0-\u05ea\s]+) / (?P<en>[a-z A-Z']+)$")
    for leaf in leaf_tags:
        if not Term().load({'name': title_reg.search(leaf['text']).group('en')}):
            print unicode(leaf)

    return [title_reg.search(leaf['text']).group('he') for leaf in leaf_tags]


def find_parshas_in_files():
    holder = PlaceHolder()
    my_files = [f for f in os.listdir('.') if re.search(u'\.txt$', f)]
    parshas = []
    for f in my_files:
        with codecs.open(f, 'r', 'utf-8') as fp:
            lines = fp.readlines()
        parshas.extend([re.sub(u'^\s+|\s+$', u'', holder.group(1))
                        for line in lines if holder(re.search(u'^@88(.*)$', line))])
    return parshas


def check_mark_balance(filename):
    def reverse_findall(string, expression):
        return len(re.findall(expression, string, re.MULTILINE))

    perfect = True
    print filename
    with codecs.open(filename, 'r', 'utf-8') as fp:
        my_text = fp.read()

    finder = partial(reverse_findall, my_text)
    if not finder(u'^@66') == finder(u'@66') == finder(u'@77') == finder(u'^@66[^@\n]+@77') > 0:
        print u'Problem with @66'
        perfect = False
    if not finder(u'^@11') == finder(u'@11') == finder(u'@33') == finder(u'^@11[^@\n]+@33') > 0:
        print u'Problem with @11'
        perfect = False
    if perfect:
        print "No problems found"
    print ""


# for f in os.listdir(u'.'):
#     if re.search(u'\.txt$', f):
#         check_mark_balance(f)


def check_parashot():
    my_titles = set(get_node_names())
    # for t in my_titles:
    #     print t

    my_parshas = find_parshas_in_files()

    my_parshas = [re.sub(u'^\u05e4\u05e8\u05e9\u05ea\s', u'', p) for p in my_parshas]
    good, bad = [], []
    for p in my_parshas:
        if p in my_titles:
            good.append(p)
        else:
            bad.append(p)

    print "Good Parashot:"
    for g in good:
        print g

    print "\nBad Parashot"
    for b in bad:
        print b

    sefaria_parsha_names = set([t.get_primary_title('he') for t in TermSet({'scheme': 'Parasha'})])
    for i in sefaria_parsha_names.difference(my_titles):
        print i

    for i in my_titles.difference(set(my_parshas)):
        print i


def locate_marks():
    marks_by_file = {}
    for filename in os.listdir(u'.'):
        if not re.search(u'\.txt$', filename):
            continue
        with codecs.open(filename, 'r', 'utf-8') as fp:
            marks_by_file[filename] = set(re.findall(u'@\d\d', fp.read()))

    common_marks = set.intersection(*marks_by_file.values())
    print "Common Marks:"
    for m in common_marks:
        print m
    print ""

    # let's keep track of marks that are not common, but we know what they are:
    known_marks = [
        u'@11',  # start of biblical quote
        u'@33',  # end of biblical quote
    ]
    print "Known Marks:"
    for m in known_marks:
        print m
    print ""

    common_marks.update(known_marks)
    print "Weird marks"
    for filename, value in marks_by_file.items():
        print filename
        weird = value.difference(common_marks)
        for w in weird:
            print w
        print ""


locate_marks()
