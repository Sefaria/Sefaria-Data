# encoding=utf-8

import os
from os.path import dirname as loc
from sources.Shulchan_Arukh.ShulchanArukh import *

root_dir = loc(loc(loc(os.path.abspath(__file__))))
xml_loc = os.path.join(root_dir, 'Yoreh_Deah.xml')

filenames = [
    u'txt_files/Yoreh_Deah/part_1/שולחן ערוך יורה דעה חלק א שך.txt',
    u'txt_files/Yoreh_Deah/part_2/שולחן ערוך יורה דעה חלק ב שך.txt',
    u'txt_files/Yoreh_Deah/part_3/שך יורה דעה חלק ג מוכן.txt',
    u'txt_files/Yoreh_Deah/part_4/שך יורה דעה חלק ד.txt',
]

filenames = dict(zip(range(1, 5), [os.path.join(root_dir, f) for f in filenames]))

root = Root(xml_loc)
commentaries = root.get_commentaries()
shach = commentaries.get_commentary_by_title(u"Siftei Kohen")
if shach is None:
    shach = commentaries.add_commentary(u"Siftei Kohen", u"שפתי כהן")

for vol_num in range(1, 5):
    print 'vol {}'.format(vol_num)
    shach.remove_volume(vol_num)
    with codecs.open(filenames[vol_num], 'r', 'utf-8') as fp:
        volume = shach.add_volume(fp.read(), vol_num)
    assert isinstance(volume, Volume)
    volume.mark_simanim(u'@22([\u05d0-\u05ea]{1,3})', specials={
        u'@01': {'name': u'Sfek_Sfeka', 'end': u'@10'},
        u'@02': {'name': u'Sfek_Sfeka_Summary', 'end': u'@20'},
        u'@03': {'name': u'No_Idea_What_This_Is', 'end': u'@30'}
    })
    volume.validate_simanim()
    print "Validating Seifim"
    errors = volume.mark_seifim(u'@11([\u05d0-\u05ea]{1,3})')
    for e in errors:
        print e
    volume.validate_seifim()
