# encoding=utf-8

import re
import os
import codecs
import django
django.setup()
from sefaria.model import *
from functools import partial
from bs4 import BeautifulSoup
from multiprocessing import Pool
from collections import OrderedDict
from parsing_utilities.util import PlaceHolder
from linking_utilities.dibur_hamatchil_matcher import match_ref
from sources.functions import post_text, post_index, post_link


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
        # if not Term().load({'name': title_reg.search(leaf['text']).group('en')}):
        if not Term().load_by_title(title_reg.search(leaf['text']).group('he')):
            print unicode(leaf)

    return OrderedDict(((title_reg.search(leaf['text']).group('he'), title_reg.search(leaf['text']).group('en'))
                        for leaf in leaf_tags))


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
    my_titles = set(get_node_names().keys())
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


def generate_schema():
    node_names = get_node_names()
    root_node = SchemaNode()
    root_node.add_primary_titles(u"Shem MiShmuel", u"שם משמואל")

    for name in node_names:
        node = JaggedArrayNode()

        shared_title = Term().load_by_title(name)
        if shared_title:
            en_title = shared_title.get_primary_title('en')
            node.add_shared_term(en_title)
            node.key = en_title
        else:
            node.add_primary_titles(node_names[name], name)

        if name == u'הקדמה':
            node.add_structure([u"Paragraph"])
        else:
            node.add_structure([u"Chapter", u"Paragraph"])
        node.validate()
        root_node.append(node)
    root_node.validate()
    return root_node


def upload_text(text_mapping, node_mapping, node_name, server='http://localhost:8000', remove_links=False):
    def cleaner(ja):
        assert isinstance(ja, list)
        for i, item in enumerate(ja):
            if isinstance(item, list):
                cleaner(item)
            elif isinstance(item, basestring):
                ja[i] = re.sub(u'link', u'b', ja[i])
            else:
                raise TypeError
    version = {
        u"versionTitle": u"Sefer Shem Mishmuel, Piotrkow, 1927-1934",
        u"versionSource": u"http://aleph.nli.org.il/F/?func=direct&doc_number=001875809&local_base=NNL01",
        u"language": u"he",
        u"text": text_mapping[node_name]
    }
    if node_name == u'הקדמה':
        version[u'text'] = version[u'text'][0]

    if remove_links:
        cleaner(version[u'text'])
    post_text(u"Shem MiShmuel, {}".format(node_mapping[node_name]), version, server=server, weak_network=True)


def link_shem():
    """
    For this method to work, the text needs to be uploaded to the local database, with escaped <link> tags wrapping
    text that needs to be linked.
    :return:
    """
    def match_template(base_text, base_tokenizer, comments, **kwargs):
        return match_ref(base_text, comments, base_tokenizer, **kwargs)

    def tokenizer(t):
        return re.split(u'[^\u05d0-\u05ea]+', t)

    def extract(t):
        t = re.match(u'^&lt;link&gt;([^&]+)&lt;/link&gt;', t).group(1)
        t = re.split(u" \u05d5\u05d2\u05d5'? ", t)[0]
        t = re.sub(u"\s[\u05d3\u05d4]'\s", u" \u05d9\u05d4\u05d5\u05d4 ", t)
        return t

    possible_link_list = []
    database_index = library.get_index(u'Shem MiShmuel')
    for node in database_index.nodes.children:
        if not hasattr(node, 'sharedTitle'):
            continue
        node_term = Term().load_by_title(node.sharedTitle)
        if not hasattr(node_term, 'ref'):
            continue

        parsha_tc = Ref(node_term.ref).text(lang='he', vtitle=u'Tanach with Text Only')
        matcher = partial(match_template, parsha_tc, tokenizer, dh_extract_method=extract)
        print node.ref().normal()

        for segment in node.ref().all_segment_refs():
            comment_tc = segment.text(lang=u'he', vtitle=u'Sefer Shem Mishmuel, Piotrkow, 1927-1934')
            if re.match(u'^&lt;link&gt;([^&]+)&lt;/link&gt;', comment_tc.text):
                possible_link = matcher(comment_tc)
                possible_link['comment_refs'] = [r.normal() for r in possible_link['comment_refs']]
                possible_link['matches'] = [r.normal() if r else u"None" for r in possible_link['matches']]
                possible_link_list.append(possible_link)
    return possible_link_list


# import json
# with codecs.open('test.json', 'w', 'utf-8') as fp:
#     json.dump(my_links, fp)
destination = 'http://shem.sandbox.sefaria.org'
shem_index = {
    u'title': u'Shem MiShmuel',
    u'categories': [u'Chasidut'],
    u'schema': generate_schema().serialize()
}

my_text = {}
for f in os.listdir(u'.'):
    if re.search(u'\.txt$', f):
        file_text = parse_file(f)
        if any([k in my_text for k in file_text.keys()]):
            raise AssertionError(u"Duplicate")
        my_text.update(file_text)
#
post_index(shem_index, server=destination)
my_node_names = get_node_names()
uploader = partial(upload_text, my_text, my_node_names, server='http://localhost:8000', remove_links=False)
for k in my_node_names.keys():
    uploader(k)
my_links = link_shem()
actual_links = [
    {
        'refs': [m['matches'][0], m['comment_refs'][0]],
        'type': 'allusion',
        'auto': True,
        'generated_by': 'Shem MiShmuel Parser'
    }
    for m in my_links if m['matches'][0] is not None]
uploader = partial(upload_text, my_text, my_node_names, server=destination, remove_links=True)

pool = Pool(5)
pool.map(uploader, my_node_names.keys())
post_link(actual_links, server=destination)


