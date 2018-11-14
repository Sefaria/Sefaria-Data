# encoding=utf-8

import re
import os
import codecs
from collections import defaultdict
from os.path import dirname as loc
from data_utilities.util import getGematria, Singleton
from itertools import count
from sources.Shulchan_Arukh.ShulchanArukh import *

root_dir = loc(loc(loc(os.path.abspath(__file__))))
xml_loc = os.path.join(root_dir, 'Yoreh_Deah.xml')
filenames = [
    u'txt_files/Yoreh_Deah/part_1/שולחן ערוך יורה דעה חלק א נקודת הכסף.txt',
    u'txt_files/Yoreh_Deah/part_2/שולחן ערוך יורה דעה חלק ב נקודות הכסף.txt',
    u'txt_files/Yoreh_Deah/part_3/נקודות הכסף שולחן ערוך יורה דעה חלק ג.txt',
    u'txt_files/Yoreh_Deah/part_4/שולחן ערוך יורה דעה חלק ד נקודות הכסף.txt'
]
filenames  = dict(zip(range(1, 5), [os.path.join(root_dir, f) for f in filenames]))
root = Root(xml_loc)


class Tester(object):
    def __call__(self, match):
        self.match = match
        return bool(match)


class ReferenceSuite:

    reference_regex = re.compile(u'''
    ^(?:(\u05e9\u05dd|\u05d4\u05d2\u05d4\u05d4?)\s?)?  # שם
    (\u05d1?(?P<commentator>\u05d8\u05d6|\u05e9\u05da|\u05e9\u05d5?\u05e2)\s?)?  # Shach, Taz, Shulchan Arukh
    (\u05e1(\u05e7\s?|\u05e2\u05d9\u05e3\s)(?P<seif>[\u05d0-\u05ea]{1,3}))?$  # Match the seif
    ''', re.VERBOSE)

    def __init__(self):
        self.record_list = []

    def clear_records(self):
        self.record_list = []

    @staticmethod
    def get_default_reference(siman=None):
        return {
            u'siman': siman,
            u'local-seif': None,
            u'remote-seif': None,
            u'comments-on': u'Turei Zahav'
        }

    @staticmethod
    def get_commentator(match_obj):
        if match_obj is None or match_obj.group(u'commentator') is None:
            return None

        commenator_reg = re.compile(u'(?P<taz>\u05d8\u05d6)|'
                                    u'(?P<shach>\u05e9\u05da)|'
                                    u'(?P<base>\u05e9\u05d5?\u05e2)', re.VERBOSE)
        book_names = {
            u'taz': u'Turei Zahav',
            u'shach': u'Siftei Kohen',
            u'base': u'base'
        }
        commentator = commenator_reg.match(match_obj.group(u'commentator')).lastgroup
        return book_names[commentator]

    def walk_through_file(self, filename):
        """
        Derive and store references from a single file
        :param filename:
        :return:
        """
        tester = Tester()
        previous_reference, seif = None, 0
        with codecs.open(filename, 'r', 'utf-8') as fp:
            lines = fp.readlines()
        for line in lines:
            if tester(re.search(u'@22([\u05d0-\u05ea]{1,3})', line)):
                siman = getGematria(tester.match.group(1))
                seif = 0
                previous_reference = self.get_default_reference(siman)

            if re.match(u'^@00\(', line):
                seif += 1
                reference = {
                    u'siman': siman,
                    u'local-seif': seif,
                    u'remote-seif': None,
                    u'comments-on': None,
                    u'raw-text': line
                }
                stripped = re.sub(u'[^\u05d0-\u05ea ]', u'', line)
                stripped = re.sub(u'^\u05e1\u05d9(?:\u05de\u05df)?\s([\u05d0-\u05ea]{1,3})\s?', u'', stripped)
                ref_match = self.reference_regex.match(stripped)
                if not ref_match:
                    print u"No match found for:"
                    print line
                    continue
                reference[u'comments-on'] = self.get_commentator(ref_match)
                reference[u'remote-seif'] = \
                    None if ref_match.group(u'seif') is None else getGematria(ref_match.group(u'seif'))
                if reference[u'comments-on'] is None:
                    reference[u'comments-on'] = previous_reference[u'comments-on']
                else:
                    previous_reference[u'comments-on'] = reference[u'comments-on']
                if reference[u'remote-seif'] is None:
                    reference[u'remote-seif'] = previous_reference[u'remote-seif']
                else:
                    previous_reference[u'remote-seif'] = reference[u'remote-seif']
                if reference[u'remote-seif'] is None:
                    print u'No remote seif for {} {}'.format(reference[u'siman'], reference[u'local-seif'])
                self.record_list.append(reference)


class BookStore(object):
    __metaclass__ = Singleton

    def __init__(self):
        base = root.get_base_text()
        commentaries = root.get_commentaries()
        taz = commentaries.get_commentary_by_title(u'Turei Zahav')
        shach = commentaries.get_commentary_by_title(u'Siftei Kohen')
        self.lookup = {
            u'base': base,
            u'Turei Zahav': taz,
            u'Siftei Kohen': shach
        }


def check_reference(reference_object, reference_records):
    if reference_object[u'remote-seif'] is None:
        return
    storage = BookStore()
    book = storage.lookup[reference_object[u'comments-on']]
    ref_key = (reference_object[u'comments-on'], reference_object[u'siman'], reference_object[u'remote-seif'])
    if ref_key in reference_records:
        reference_records[ref_key][u'places-referenced'].append(reference_object[u'local-seif'])
    else:
        siman = next(s for s in book.get_simanim() if s.num == reference_object[u'siman'])
        try:
            seif = next(s for s in siman.get_child() if s.num == reference_object[u'remote-seif'])
        except StopIteration:
            print u'{} {}:{} does not exist'.format(*ref_key)
            return
        num_refs = len(seif.grab_references(u'@58\*\)?'))
        if num_refs == 0:
            num_refs = len(seif.grab_references(u'\*\)?'))
        reference_records[ref_key][u'star-counts'] = num_refs
        reference_records[ref_key][u'places-referenced'] = [reference_object[u'local-seif']]
    reference_object.update(reference_records[ref_key])


suite = ReferenceSuite()
store = defaultdict(dict)
for i in range(1, 5):
    print u'vol {}'.format(i)
    suite.walk_through_file(filenames[i])
for r in suite.record_list:
    check_reference(r, store)
for r in suite.record_list:
    my_key = (r[u'comments-on'], r[u'siman'], r[u'remote-seif'])
    try:
        r.update(store[my_key])
    except KeyError:
        continue
map(lambda x: x[1].update({'key': x[0]}), store.items())
store_list = sorted(store.values(), key=lambda x: (x['key'][1], x['key'][2], x['key'][0]))
problems = filter(lambda x: x if u'places-referenced' not in x
                  else (x if len(x[u'places-referenced']) != x[u'star-counts'] else None), suite.record_list)
print len(suite.record_list)
print len(problems)
book_mapping = {(r['siman'], r['local-seif']): r['comments-on'] for r in suite.record_list}
# import json
# with codecs.open('nekudat_refs.json', 'wb', 'utf-8') as fp:
#     json.dump(suite.record_list, fp)

"""
For each reference I now know how many possible references point to said reference in the base text. I need to determine
if each base text reference has the correct number of marks.

A remote ref can be identified by (<book>, <siman>, <remote-seif>). For each remote ref we want:
a) number of times each ref is referenced
b) number of * marks in said remote ref

The problem I have now is mapping remote-refs to the nekudat haKesef locations that referenced them.
I can walk through my reference suite and derive the appropriate key for my reference-store. I can then update each
reference with the contents of each ref-store.

Multiple stars may not be errors. Filter down to those problems that have 0 stars of a bad seif number
"""
commentaries = root.get_commentaries()
nek = commentaries.get_commentary_by_title(u"Nekudat HaKesef")
if nek is None:
    nek = commentaries.add_commentary(u"Nekudat HaKesef", u"נקודת הכסף")


u"""
I need to be able to mark certain stars as Kesef unique. What I'll do is scan a targeted remote-seif and look for the
unique identifier. If it's found, then only the advanced regex will be used, otherwise, we'll just look for "regular"
stars.
The unique mark will be @58*. Any seif with that mark will only be able to identify stars preceded by an @58

Properly marking itags:
I need to be able to hand a list of local-seif values, and mark xrefs accordingly. I can't assume that two marks in a
remote-seif necessarily get mapped to two consecutive seifim  *worth checking*.
Start by compiling the list of local-seifim for each remote-seif. If there are no jumps, I can call seif.mark_references
and set the found parameter to 1 less than the first local-seif.
If there are jumps, I'll need to implement a new `mark_references` method that accepts a list.
Also, I'll need to make sure to unwrap all nekudat xrefs before running this method.
"""


def mark_remote_xref(reference):
    book_name, siman_num, remote_seif_num = reference['key']
    book = BookStore().lookup[book_name]
    siman = next(s for s in book.get_simanim() if s.num == siman_num)
    seif = next(s for s in siman.get_child() if s.num == remote_seif_num)
    if len(seif.grab_references(u'@58\*\)?')) >= 1:
        mark_regex = u'@58\*\)?'
    else:
        mark_regex = u'\*\)?'
    local_seifim = iter(reference['places-referenced'])

    def repl(s):
        if re.match(u'^@', s.group()):
            mark = s.group()
        else:
            mark = u'@58{}'.format(s.group())
        return u'<xref id="b{}-c{}-si{}-ord{}">{}</xref>'.format(
            getattr(book, 'id', 0), nek.id, siman_num, next(local_seifim), mark)

    for text_element in seif.get_child():
        for xref in text_element.Tag.find_all(lambda x: x.name == 'xref' and re.search(mark_regex, x.text) is not None):
            xref.unwrap()
        tagged = re.sub(mark_regex, repl, unicode(text_element))
        new_tag = BeautifulSoup(tagged, 'xml').find(text_element.Tag.name)
        text_element.Tag.replace_with(new_tag)
        text_element.Tag = new_tag


for reference in store_list:
    mark_remote_xref(reference)

u"""
As far a marking rids for Seifim, I just need to know which book it's going out to. 
For giving numbers to seifim, I need to just count. The mark_seifim method expects to pass group 1 of a regex match
to a method. For this, create an infinte iterator and a function that calls `next` on that iterator. Said function
should accept any number of parameters and chuck 'em. 
Maybe I can just make this a "cyclical" seif, with some random label
"""

my_book_store = BookStore()
for vol_num in range(1, 5):
    print 'vol {}'.format(vol_num)
    nek.remove_volume(vol_num)
    with codecs.open(filenames[vol_num], 'r', 'utf-8') as fp:
        volume = nek.add_volume(fp.read(), vol_num)
    assert isinstance(volume, Volume)
    volume.mark_simanim(u'@22([\u05d0-\u05ea]{1,3})')
    volume.validate_simanim(complete=False)
    print "Validating Seifim"
    errors = volume.mark_seifim(u'^@00\(()', cyclical=True)
    for e in errors:
        print e
    volume.validate_seifim()
    errors = volume.format_text(u'@11', u'@33', u'dh')
    for e in errors:
        print e
    for siman in volume.get_child():
        for seif in siman.get_child():
            try:
                base_id = getattr(my_book_store.lookup[book_mapping[(siman.num, seif.num)]], u'id', 0)
                seif.set_rid(base_id, nek.id, siman.num)
            except KeyError:
                seif.Tag[u'rid'] = 'no-link'

root.populate_comment_store(verbose=True)
for book in my_book_store.lookup.values():
    for vol_num in range(1, 5):
        volume = book.get_volume(vol_num)
        assert isinstance(volume, Volume)
        errors = volume.validate_all_xrefs_matched(lambda x: x.name == 'xref' and re.search(u'@58', x.text) is not None)
        for e in errors:
            print e

seifim = [seif for siman in nek.get_simanim() for seif in siman.get_child()]
map(lambda x: x.Tag.attrs.update({u'label': u'\u266f'}), seifim)
root.export()

