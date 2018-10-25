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

@99 is very rare. Use for an inline <br>.

Something I need to look out for is the @00 followed immediately by an @22.
Each Section has a header and segments. If I find two consecutive headers, then just combine them (and report).

Following that, just break up the segments. Bold @66-@77, and mark @11-@33 for dh matcher.

The @88 indicates a new node. We want a hashmap from @88 titles to JaggedArrays.

Two methods:
1) Break file into dictionary of @88 titles and text
2) Split text into sections and segments
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


def parse_node_text(input_text):
    full_node, current_section, header = [], [], None
    for line in input_text:
        line = re.sub(u'^\s+|\s+$', u'', line)
        if re.match(u'^(@00|@22)', line):

            # new header, if not first header, check that there are segments in current_section
            if len(current_section) > 0 and header is not None:
                current_section.insert(0, header)
                full_node.append(current_section)
                current_section = []
                header = u'<b>{}</b>'.format(re.sub(u'^(@00|@22)', u'', line))

            # first header
            elif len(current_section) == 0 and header is None:
                header = u'<b>{}</b>'.format(re.sub(u'^(@00|@22)', u'', line))

            # double header
            elif header and len(current_section) == 0:
                header += u'<b>{}</b>'.format(re.sub(u'^(@00|@22)', u'', line))
                header = re.sub(u'</b><b>', u' ', header)

            # This is the case where text went into the segments without any header
            else:
                raise AssertionError(u"Segments added without header")

        else:
            if not header:
                raise AssertionError(u"Tried to add segments without header")
            line = re.sub(u'@66([^@]+)@77', u'<b>\g<1></b>', line)
            line = re.sub(u'@11([^@]+)@33', u'<link>\g<1></link>', line)
            line = re.sub(u'@44([^@]+)@55', u'<big>\g<1></big>', line)
            line = re.sub(u'@99', u'<br>', line)
            current_section.append(line)
    else:
        current_section.insert(0, header)
        full_node.append(current_section)
    return full_node


def parse_file(filename):
    nodes, node_name, current_text = {}, None, []
    with codecs.open(filename, 'r', 'utf-8') as fp:
        lines = fp.readlines()

    for line in lines:
        if re.search(u'^@88', line):
            if current_text:
                nodes[node_name] = parse_node_text(current_text)
                current_text = []
            node_name = re.sub(u'@88(\u05e4\u05e8\u05e9\u05ea\s)?', u'', line)
            node_name = re.sub(u'^\s+|\s+$', u'', node_name)
            if node_name in nodes:
                raise AssertionError(u'{} appears twice in file'.format(node_name))
        else:
            current_text.append(line)
    else:
        nodes[node_name] = parse_node_text(current_text)
    return nodes


my_text = {}
for f in os.listdir(u'.'):
    if re.search(u'\.txt$', f):
        file_text = parse_file(f)
        if any([k in my_text for k in file_text.keys()]):
            raise AssertionError(u"Duplicate")
        my_text.update(file_text)

for k in my_text.keys():
    print k

workflowy_names = {j: i for i, j in enumerate(get_node_names())}
print all([k in workflowy_names for k in my_text.keys()])
my_text = [{key: value} for key, value in my_text.iteritems()]
import json
with codecs.open('test.json', 'w', 'utf-8') as fp:
    json.dump(sorted(my_text, key=lambda x: workflowy_names[x.keys()[0]])[:5], fp)

