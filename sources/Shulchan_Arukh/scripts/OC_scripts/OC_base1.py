# encoding=utf-8

import os
from os.path import dirname as loc
from sources.Shulchan_Arukh.ShulchanArukh import *


def markup(volume, root, i=1):
    commentaries = root.get_commentaries()
    volume.mark_references(commentaries.commentary_ids["Turei Zahav"], u'@77\(([\u05d0-\u05ea]{1,3})\)', group=1)
    eshel_mark = u"@88" if i < 3 else u"@99"
    volume.mark_references(commentaries.commentary_ids["Be'er HaGolah"], u'@44([\u05d0-\u05ea\u2022])', group=1, cyclical=True)
    volume.mark_references(commentaries.commentary_ids["Eshel Avraham"], eshel_mark + u'([\u05d0-\u05ea]{1,3})\]', group=1, cyclical=True)
    volume.mark_references(commentaries.commentary_ids["Ateret Zekenim"], u"(\u2666)(?!\))", group=1, cyclical=True)
    if i == 3:
        volume.mark_references(commentaries.commentary_ids["Chok Yaakov"], u"@14(\[[\u05d0-\u05ea]{1,2}\])", group=1)
    volume.mark_references(commentaries.commentary_ids["Sha'arei Teshuvah"], u"@62\(([\u05d0-\u05ea\u2022]{1,3})\)", group=1)
    volume.convert_pattern_to_itag(u"Magen Avraham", u"@55([\u05d0-\u05ea]{1,3})")
    volume.convert_pattern_to_itag(u"Ba'er Hetev", u"@66\(([\u05d0-\u05ea]{1,3})\)")

if __name__ == "__main__":
    root_dir = loc(loc(loc(os.path.abspath(__file__))))
    xml_loc = os.path.join(root_dir, 'Orach_Chaim.xml')
    print root_dir

    if not os.path.exists(xml_loc):
        Root.create_skeleton(xml_loc)

    root = Root(xml_loc)

    base = root.get_base_text()
    filename = os.path.join(root_dir, u'txt_files/Orach_Chaim/part_1/שוע אורח חיים חלק א.txt')

    base.remove_volume(1)
    with codecs.open(filename, 'r', 'utf-8') as infile:
        volume = base.add_volume(infile.read(), 1)
    assert isinstance(volume, Volume)


    volume.mark_simanim(u'@22([\u05d0-\u05ea]{1,3})', specials={u'@00': {'name': u'topic'}})
    print "Validating Simanim"
    volume.validate_simanim()

    bad = volume.mark_seifim(u'@11([\u05d0-\u05ea]{1,3})', specials={u'@23': {'name': u'title'}})
    print 'Validating Seifim'
    for i in bad:
        print i
    volume.validate_seifim()






    codes = [ur'@77', ur'@66', ur'@55']
    patterns = [ur'@77\(({})\)', ur'@66\(({})\)', ur'@55({})']
    patterns = [i.format(ur'[\u05d0-\u05ea]{1,3}') for i in patterns]


    '''
    אשל אברהם:
    ur'@88([\u05d0-\u05ea])\]'
    '''

    # for pattern in patterns:
    #     correct_marks_in_file(filename, u'@22', pattern)
    # correct_marks_in_file(filename, u'@22', ur'@44([\u05d0-\u05ea])', error_finder=out_of_order_he_letters)


    volume.validate_references(ur'@44([\u05d0-\u05ea])', u'@44', key_callback=he_ord)
    for pattern, code in zip(patterns, codes):
        volume.validate_references(pattern, code)

    errors = volume.format_text('@33', '@34', 'ramah')
    for i in errors:
        print i


    markup(volume, root)

    root.export()

