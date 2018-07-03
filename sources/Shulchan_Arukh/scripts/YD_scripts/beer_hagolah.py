# encoding=utf-8

import os
from data_utilities.util import numToHeb, getGematria
from os.path import dirname as loc
from sources.Shulchan_Arukh.ShulchanArukh import *

root_dir = loc(loc(loc(os.path.abspath(__file__))))
xml_loc = os.path.join(root_dir, 'Yoreh_Deah.xml')

filenames = [
    u"txt_files/Yoreh_Deah/part_1/שולחן ערוך יורה דעה חלק א באר הגולה.txt",
    u"txt_files/Yoreh_Deah/part_2/באר הגולה שולחן ערוך יורה דעה ב.txt",
    u"txt_files/Yoreh_Deah/part_3/‏‏‏‏באר הגולה שולחן ערוך יורה דעה חלק ג.txt",
    u"txt_files/Yoreh_Deah/part_4/‏‏שולחן ערוך יורה דעה חלק ד באר הגולה.txt"
]
filenames = [os.path.join(root_dir, f) for f in filenames]
start_simanim = {1: 1, 3: 112, 4: 203}


def fix_file(filepath, start_siman, test_mode=False):
    output_list = []
    with codecs.open(filepath, 'r', 'utf-8') as fp:
        lines = fp.readlines()
    counter = 0
    for line in lines:
        match = re.match(u'^@11([\u05d0-\u05ea]{1,3})$', line)
        if match and getGematria(match.group(1)) == 1:
            output_list.append(u'@00{}\n'.format(numToHeb(counter + start_siman)))
            counter += 1
        output_list.append(line)
    if test_mode:
        filepath = re.sub(ur'\.txt$', u'_test.txt', filepath)
    with codecs.open(filepath, 'w', 'utf-8') as fp:
        fp.writelines(output_list)


# fix_file(filenames[0], start_simanim[1])
# fix_file(filenames[2], start_simanim[3])
# fix_file(filenames[3], start_simanim[4])

filenames = dict(zip(range(1, 5), filenames))
root = Root(xml_loc)
commentaries = root.get_commentaries()
beer = commentaries.get_commentary_by_title(u"Be'er HaGolah")
assert beer is not None

for vol_num in range(1, 5):
    print 'vol {}'.format(vol_num)
    beer.remove_volume(vol_num)
    with codecs.open(filenames[vol_num], 'r', 'utf-8') as fp:
        volume = beer.add_volume(fp.read(), vol_num)
    assert isinstance(volume, Volume)
    volume.mark_simanim(u'@00([\u05d0-\u05ea]{1,3})')
    volume.validate_simanim()
    print "Validating Seifim"
    errors = volume.mark_seifim(u'@11([\u05d0-\u05ea]{1,3})')
    for e in errors:
        print e
    volume.validate_seifim()
    errors = volume.format_text(u'$^', u'.^', u'dh')
    for e in errors:
        print e
