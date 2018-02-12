#encoding=utf-8

from sources.Shulchan_Arukh.ShulchanArukh import *

filenames = {
    'part_1': u'../../txt_files/Orach_Chaim/part_1/שוע אורח חיים חלק א באר הגולה.txt',
    'part_2': u'../../txt_files/Orach_Chaim/part_2/באר הגולה אורח חיים חלק ב בעבודה עברתי אותיות רצוף.txt',
    'part_3': u'../../txt_files/Orach_Chaim/part_3/שלחן ערוך אורח חיים חלק ג באר הגולה מושלם.txt'
}

root = Root('../../Orach_Chaim.xml')
commentaries = root.get_commentaries()
base_text = root.get_base_text()

b_hagolah = commentaries.get_commentary_by_title("Be'er HaGolah")
if b_hagolah is None:
    b_hagolah = commentaries.add_commentary("Be'er HaGolah", u"באר הגולה")

for i in range(1, 4):
    print '\nVolume {}'.format(i)
    filename = filenames['part_{}'.format(i)]
    b_hagolah.remove_volume(i)
    with codecs.open(filename, 'r', 'utf-8') as infile:
        volume = b_hagolah.add_volume(infile.read(), i)

    assert isinstance(volume, Volume)
    volume.mark_simanim(u'@12([\u05d0-\u05ea]{1,4})')
    print "Validating Simanim"
    volume.validate_simanim()
    errors = []

    errors += volume.mark_seifim(u'@11([\u05d0-\u05ea\u2022])', cyclical=True)
    print errors

    # base_volume = base_text.get_volume(i)
    # for base_siman, baer_siman in zip(base_volume.get_child(), volume.get_child()):
    #     assert base_siman.num == baer_siman.num
    #
    #     total_footnotes = len(re.findall(u'@44[\u05d0-\u05ea]', unicode(base_siman)))
    #     total_comments = len(baer_siman.get_child())
    #     if total_footnotes != total_comments:
    #         print "mismatch in siman {}. {} footnotes and {} comments".format(baer_siman.num, total_footnotes, total_comments)
    volume.format_text(u'$^', u'$^', u'dh')
    volume.set_rid_on_seifim(cyclical=True)

errors = root.populate_comment_store(verbose=True)
for e in errors:
    print e
for i in range(1,4):
    b_vol = base_text.get_volume(i)
    assert isinstance(b_vol, Volume)
    errors= b_vol.validate_all_xrefs_matched(lambda x: x.name=='xref' and re.search(u'@44', x.text) is not None,
                                               base="Orach Chaim", commentary="Be'er HaGolah", simanim_only=False)
    for e in errors:
        print e


root.export()



