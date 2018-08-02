# encoding=utf-8

import os
from os.path import dirname as loc
from sources.Shulchan_Arukh.ShulchanArukh import *

root_dir = loc(loc(loc(os.path.abspath(__file__))))
xml_loc = os.path.join(root_dir, 'Yoreh_Deah.xml')

filenames = [
    u"txt_files/Yoreh_Deah/part_1/שולחן ערוך יורה דעה חלק א ביאור הגרא.txt",
    u"txt_files/Yoreh_Deah/part_2/שולחן ערוך יורה דעה חלק ב ביאור הגר''א.txt",
    u"txt_files/Yoreh_Deah/part_3/‏‏‏‏‏‏‏‏ביאור הגרא שולחן ערוך יורה דעה חלק ג.txt",
    u"txt_files/Yoreh_Deah/part_4/שולחן ערוך יורה דעה חלק ד ביאור הגרא.txt"
]
filenames = dict(zip(range(1, 5), [os.path.join(root_dir, f) for f in filenames]))

root = Root(xml_loc)
commentaries = root.get_commentaries()
gra = commentaries.get_commentary_by_title(u"Beur HaGra")
assert isinstance(gra, Commentary)

for vol_num in range(1, 5):
    print 'vol {}'.format(vol_num)
    gra.remove_volume(vol_num)
    with codecs.open(filenames[vol_num], 'r', 'utf-8') as fp:
        volume = gra.add_volume(fp.read(), vol_num)
    assert isinstance(volume, Volume)

    volume.mark_simanim(u'@22([\u05d0-\u05ea]{1,3})')
    volume.validate_simanim(complete=False)
    print "Validating Seifim"
    errors = volume.mark_seifim(u'@11\[([\u05d0-\u05ea]{1,3})\]')
    for e in errors:
        print e
    volume.validate_seifim()
    pattern_list = [
        {
            u'name': u'dh',
            u'start': u'@32',
            u'end': u'@33'
        },
        {
            u'name': u'small',
            u'start': u'@77',
            u'end': u'@55'
        }
    ]
    # errors = volume.format_text(u'@32', u'@33', u'dh')
    errors = volume.format_text_multiple(pattern_list)
    for e in errors:
        print e

    volume.set_rid_on_seifim()
    base = root.get_base_text()
    b_vol = base.get_volume(vol_num)
    assert isinstance(b_vol, Volume)
    root.populate_comment_store(verbose=True)
    errors = b_vol.validate_all_xrefs_matched(lambda x: x.name == 'xref' and re.search(u'@99', x.text) is not None)
    for e in errors:
        print e
root.export()
