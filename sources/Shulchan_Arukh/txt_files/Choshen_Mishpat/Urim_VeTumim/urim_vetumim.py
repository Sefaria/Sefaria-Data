# encoding=utf-8

import os
import re
import codecs
from collections import Counter
from sources.Shulchan_Arukh.ShulchanArukh import *

txt_files = [
    u'Choshen_Mishpat_1.txt',
    u'Choshen_Mishpat_2.txt',
    u'urim_1.txt',
    u'urim_2.txt',
    u'tumim_1.txt',
    u'tumim_2.txt',
]


def startup(datafile):
    Root.create_skeleton(datafile)
    data_root = Root(datafile)
    data_base = data_root.get_base_text()
    data_base.add_titles(u"Shulchan Arukh, Choshen Mishpat", u"שולחן ערוך חושן משפט")
    data_commentaries = data_root.get_commentaries()
    data_commentaries.add_commentary(u"Urim", u"אורים")
    data_commentaries.add_commentary(u"Tumim", u"תומים")
    return data_root


def check_markers():
    for filename in txt_files:
        with codecs.open(filename, 'r', 'utf-8') as fp:
            txt = fp.read()
        counts = Counter(re.findall(u'@\d{2}', txt))
        print filename
        for code, counts in sorted(counts.items(), key=lambda x: x[1]):
            print u'{}: {}'.format(code, counts)
        print u'\n'


datafilename = u'urim_vetumim.xml'
if not os.path.exists(datafilename):
    root = startup(datafilename)
else:
    root = Root(datafilename)

base, commentaries = root.get_base_text(), root.get_commentaries()
for vol_num, txt_file in zip([1, 2], txt_files[:2]):
    print u"\nWorking on {}".format(txt_file)
    base.remove_volume(vol_num)
    with codecs.open(txt_file, 'r', 'utf-8') as fp:
        volume = base.add_volume(fp.read(), vol_num)
    assert isinstance(volume, Volume)
    volume.mark_simanim(u'@00([\u05d0-\u05ea]{1,3})')
    print u"Validating Simanim"
    volume.validate_simanim()

    errors = volume.mark_seifim(u'@11([\u05d0-\u05ea]{1,3})')
    print "Validating Seifim"
    for e in errors:
        print e
    volume.validate_seifim()

    errors = volume.format_text(u'.^', u'$.', u'ramah')
    for e in errors:
        print e

    volume.mark_references(commentaries.commentary_ids[u"Urim"], u"@55\(([\u05d0-\u05ea]{1,3})\)", group=1)
    volume.mark_references(commentaries.commentary_ids[u"Tumim"], u"@66\(([\u05d0-\u05ea]{1,3})\)", group=1)

urim = commentaries.get_commentary_by_title(u"Urim")
for vol_num, txt_file in zip([1, 2], txt_files[2:4]):
    print u"\nWorking on {}".format(txt_file)
    urim.remove_volume(vol_num)
    with codecs.open(txt_file, 'r', 'utf-8') as fp:
        volume = urim.add_volume(fp.read(), vol_num)
    assert isinstance(volume, Volume)

    volume.mark_simanim(u'@00([\u05d0-\u05ea]{1,3})')
    volume.validate_simanim(complete=False)
    print "Validating Seifim"
    errors = volume.mark_seifim(u'@22\(([\u05d0-\u05ea]{1,3})\)')
    for e in errors:
        print e
    volume.validate_seifim()

    errors = volume.format_text(u'@11', u'@33', u'dh')
    for e in errors:
        print e

    volume.set_rid_on_seifim()
    b_vol = base.get_volume(vol_num)
    assert isinstance(b_vol, Volume)
    root.populate_comment_store(verbose=True)
    errors = b_vol.validate_all_xrefs_matched(lambda x: x.name == 'xref' and re.search(u'@55', x.text) is not None)
    for e in errors:
        print e

tumim = commentaries.get_commentary_by_title(u"Tumim")
for vol_num, txt_file in zip([1, 2], txt_files[4:]):
    print u"\nWorking on {}".format(txt_file)
    tumim.remove_volume(vol_num)
    with codecs.open(txt_file, 'r' ,'utf-8') as fp:
        volume = tumim.add_volume(fp.read(), vol_num)
    assert isinstance(volume, Volume)

    volume.mark_simanim(u'@00([\u05d0-\u05ea]{1,3})')
    volume.validate_simanim(complete=False)
    print "Validating Seifim"
    errors = volume.mark_seifim(u'@22([\u05d0-\u05ea]{1,3})')
    for e in errors:
        print e
    volume.validate_seifim()

    errors = volume.format_text(u'@11', u'@33', u'df')
    for e in errors:
        print e

    volume.set_rid_on_seifim()
    b_vol = base.get_volume(vol_num)
    assert isinstance(b_vol, Volume)
    root.populate_comment_store(verbose=True)
    errors = b_vol.validate_all_xrefs_matched(lambda x: x.name == 'xref' and re.search(u'@66', x.text) is not None)
    for e in errors:
        print e

root.export()
