#encoding=utf-8

"""

I may need to write a method that can accept a non-numeric value and then treat it as a numeric value.
So, if it finds the value ".", it would pretend that it found the number immediately after the last location that was
used.
For example, Siman 307 in Sha'arei Teshuva goes <blank> <2> <blank> <16>. The first <blank> would default to 1, the
second <blank> would get the value 3.
This might not work in the general case, as the we would need to maintain that the number we've chosen isn't used later
on. That being said, this idea seems to only be an issue for sparse texts, dense ones would require nesting unmarked
comments inside existing comments. Also, it's because the text is so sparse that nesting becomes a problem.
The following Simanim have an unmarked comment followed by א:
קפט, רו, רצ, תפב, תקלז, תרצא

The method `Seif.mark_mixed_seifim` should handle the parsing describe above.

use the character u'\u2022' for marking 'unmarked' comments
"""

import re
from sources.Shulchan_Arukh.ShulchanArukh import *

filenames = {
    'shaarei_1': u'../../txt_files/Orach_Chaim/part_1/שוע אורח חיים חלק א שערי תשובה.txt',
    'shaarei_2': u'../../txt_files/Orach_Chaim/part_2/שולחן ערוך אורח חיים חלק ב שערי תשובה.txt',
    'shaarei_3': u'../../txt_files/Orach_Chaim/part_3/שולחן ערוך אורח חיים חלק ג שערי תשובה.txt',
}

root = Root('../../Orach_Chaim.xml')
commentaries = root.get_commentaries()
base_text = root.get_base_text()

shaarei = commentaries.get_commentary_by_title("Sha'arei Teshuvah")
if shaarei is None:
    shaarei = commentaries.add_commentary("Sha'arei Teshuvah", u"שערי תשובה")
siman_patterns = dict(zip(range(1,4), [ur'@{}([\u05d0-\u05ea]{{1,4}})'.format(i) for i in [u'00', u'22', u'00']]))
seif_patterns =  dict(zip(range(1,4), [ur'@{}\(([\u05d0-\u05ea\u2022]{{1,2}})\)'.format(i) for i in [u'22', u'11', u'22']]))

def is_numbered(label):
    if re.search(ur'^[\u05d0-\u05ea]{1,2}', label):
        return True
    else:
        return False

for i in range(1, 4):
    print "\nSha'arei Teshuva Vol.{}".format(i)
    filename = filenames['shaarei_{}'.format(i)]
    shaarei.remove_volume(i)
    with codecs.open(filename, 'r', 'utf-8') as infile:
        volume = shaarei.add_volume(infile.read(), i)

    assert isinstance(volume, Volume)
    volume.mark_simanim(siman_patterns[i])
    print "Validating Simanim"
    volume.validate_simanim(complete=False)

    errors = []
    for siman in volume.get_child():
        try:
            siman.mark_mixed_seifim(seif_patterns[i], is_numbered)
        except DuplicateChildError as e:
            errors.append('Siman {}:{}'.format(siman.num, e))
    if len(errors) == 0:
        print 'No Seif errors in vol.{}'.format(i)
    else:
        for e in errors:
            print e

    if i == 2:
        errors = volume.format_text(u'@33', u'@34', u'dh')
    else:
        errors = volume.format_text(u'@11', u'@33', u'dh')
    if len(errors) == 0:
        print 'no formatting errros'
    else:
        for e in errors:
            print e

    volume.set_rid_on_seifim()

    # Those seifim that use a label are "un-numbered", and in the case of Sha'arei Teshuvah, have no mark in the base text
    # The links were compiled externally
    bad_rids = [s['rid'] for s in volume.Tag.find_all('seif', label=True)]
    volume.unlink_seifim(bad_rids)

errors = root.populate_comment_store(verbose=True)
if len(errors) == 0:
    print "Populated commentStore successfully - Sha'arei Teshuvah"

for i in range(1,4):
    b_vol = base_text.get_volume(i)
    errors = b_vol.validate_all_xrefs_matched(lambda x: x.name == 'xref' and re.search(u'@62', x.text) is not None,
                                              base="Orach Chaim", commentary="Sha'arei Teshuvah", simanim_only=False)
    for e in errors:
        print e

root.export()
