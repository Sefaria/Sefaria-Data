# coding=utf-8

from data_utilities.util import he_ord
from sources.Shulchan_Arukh.ShulchanArukh import *


def diagnose_mismatch(siman_from_base, siman_from_beer):
    """

    :param siman_from_base:
    :param siman_from_beer:
    :return:
    """
    # collect all data-labels from seifim in Beer HaGolah
    found = False
    beer_labels = iter([s.Tag['label'] for s in siman_from_beer.get_child()])
    beer_nums = 0
    jump_ahead = False

    # walk through seifim in base text
    for seif in siman_from_base.get_child():
        # in each seif collect refs to Beer HaGolah
        beer_refs = [m.group(1) for m in re.finditer(u'@44([\u05d0-\u05ea])', unicode(seif))]

        # compare letters, if the letters don't match log
        for ref in beer_refs:
            if jump_ahead:
                jump_ahead = False
                continue
            try:
                curr_label = beer_labels.next()
                beer_nums += 1
                if curr_label != ref:
                    print u"Mismatch found in Seif {}. {} in Shulchan Arukh, but {} in Beer HaGolah (comment {})".format(
                        seif.num, ref, curr_label, beer_nums
                    )
                    found = True

                    # Markers are out of sync. We need to advance one to get them back in sync
                    label_num, ref_num = he_ord(curr_label), he_ord(ref)
                    if label_num > ref_num or (label_num - ref_num == -21):
                        jump_ahead = True
                    else:
                        beer_labels.next()
                        beer_nums += 1

            except StopIteration:
                if not found:
                    print "Could not find source of mismatch. Might appear at the end of the Siman."
                print ''
                return

    if not found:
        print "Could not find source of mismatch. Might appear at the end of the Siman."
    print ''
    return



filenames = {
    'part_1': u'/home/jonathan/sefaria/Sefaria-Data/sources/Shulchan_Arukh/txt_files/Even_Haezer/part_1/באר הגולה אבן העזר חלק א.txt',
    'part_2': u'/home/jonathan/sefaria/Sefaria-Data/sources/Shulchan_Arukh/txt_files/Even_Haezer/part_2/שולחן ערוך אבן האזל חלק ב באר הגולה.txt'
}

root = Root('../../Even_HaEzer.xml')
commentaries = root.get_commentaries()
base_text = root.get_base_text()

b_hagolah = commentaries.get_commentary_by_title("Be'er HaGolah")
if b_hagolah is None:
    b_hagolah = commentaries.add_commentary("Be'er HaGolah", u"באר הגולה")

for i in range (1,3):
    print '\nVolume {}'.format(i)
    filename = filenames['part_{}'.format(i)]
    b_hagolah.remove_volume(i)
    with codecs.open(filename, 'r', 'utf-8') as infile:
        volume = b_hagolah.add_volume(infile.read(), i)

    volume.mark_simanim(u'@12([\u05d0-\u05ea]{1,3})', specials={
        u'@13': {'name': u'Halitza', 'end': u'!end!'},
        u'@14': {'name': u'Get', 'end': u'!end!'}
    })

    volume.validate_simanim()

    errors = volume.mark_seifim(u'@11([\u05d0-\u05ea\u2022])', cyclical=True)
    for e in errors:
        print e

    base_volume = base_text.get_volume(i)
    beer_simanim = {s.num: s for s in volume.get_child()}
    issues = 0
    for base_siman in base_volume.get_child():
        beer_siman = beer_simanim.get(base_siman.num, None)

        total_footnotes = len(re.findall(u'@44[\u05d0-\u05ea]', unicode(base_siman)))
        if beer_siman:
            total_comments = len(beer_siman.get_child())
        else:
            total_comments = 0
        if total_footnotes != total_comments:
            print "mismatch in siman {}. {} footnotes and {} comments".format(base_siman.num, total_footnotes, total_comments)
            diagnose_mismatch(base_siman, beer_siman)
            issues += 1
    print '{} issues'.format(issues)
