# encoding=utf-8

import re
import os
import codecs
from collections import defaultdict
from os.path import dirname as loc
from data_utilities.util import getGematria, Singleton
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
        reference_records[ref_key][u'times-referenced'] += 1
    else:
        siman = next(s for s in book.get_simanim() if s.num == reference_object[u'siman'])
        try:
            seif = next(s for s in siman.get_child() if s.num == reference_object[u'remote-seif'])
        except StopIteration:
            print u'{} {}:{} does not exist'.format(*ref_key)
            return
        num_refs = len(seif.grab_references(u'\*\)?'))
        reference_records[ref_key][u'star-counts'] = num_refs
        reference_records[ref_key][u'times-referenced'] = 1
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
problems = filter(lambda x: x if u'times-referenced' not in x
                  else (x if x[u'times-referenced'] != x[u'star-counts'] else None), suite.record_list)
print len(suite.record_list)
print len(problems)
import json
with codecs.open('nekudat_refs.json', 'wb', 'utf-8') as fp:
    json.dump(problems, fp)

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
for vol_num in range(1, 5):
    print 'vol {}'.format(vol_num)
    nek.remove_volume(vol_num)
    with codecs.open(filenames[vol_num], 'r', 'utf-8') as fp:
        volume = nek.add_volume(fp.read(), vol_num)
    assert isinstance(volume, Volume)
    volume.mark_simanim(u'@22([\u05d0-\u05ea]{1,3})')
    volume.validate_simanim(complete=False)

