#encoding=utf-8
import sys
from sources.Shulchan_Arukh.ShulchanArukh import *
from sources.functions import *
from bs4.element import *

filename = u"../../txt_files/Orach_Chaim/part_1/eshel_3 volumes with simanim.txt"

root = Root('../../Orach_Chaim.xml')
commentaries = root.get_commentaries()
eshel = commentaries.get_commentary_by_title("Eshel Avraham")
if eshel is None:
    eshel = commentaries.add_commentary("Eshel Avraham", u"אשל אברהם")

base = root.get_base_text()

eshel.remove_volume(1)
with codecs.open(filename, 'r',
                 'utf-8') as infile:
    volume = eshel.add_volume(infile.read(), 1)
assert isinstance(volume, Volume)

volume.mark_simanim(u'@00([\u05d0-\u05ea]{1,4})')
volume.validate_simanim(complete=False)
errors =[]

errors += volume.mark_seifim(u'@22([\u05d0-\u05ea]{1,3})', cyclical=True)
volume.validate_seifim()

errors += volume.format_text('@11|@44', '@33|@55', 'dh')
match = 0
not_match = 0
total = 0
simanim_w_probs = {}
for i in range(3):
    b_vol = base.get_volume(i + 1)

    assert isinstance(b_vol, Volume)
    volume.set_rid_on_seifim(cyclical=True)
    eshel_mark = u"@88" if i < 2 else u"@99"
    xrefs = b_vol.Tag.find_all(lambda x: x.name == 'xref' and re.search(eshel_mark, x.text) is not None)
    for xref in xrefs:
        rid = xref.attrs['id']
        siman = rid.split("-")[2].replace("si", "")
        seifim = volume.Tag.find_all(lambda x: x.name == "seif" and x.attrs['rid'] == rid)
        assert len(seifim) == 1
        seif_text = seifim[0].text
        next_sibling = ""
        word_after_i_tag = xref.next_sibling
        while not isinstance(word_after_i_tag, NavigableString) or word_after_i_tag.replace(" ", "") == "":
            if word_after_i_tag.next_sibling:
                word_after_i_tag = word_after_i_tag.next_sibling
            else:
                break
        if find_almost_identical(seif_text.split(" ")[0], [word_after_i_tag.strip().split(" ")[0]], ratio=0.7):
            match += 1
        else:
            if siman not in simanim_w_probs.keys():
                simanim_w_probs[siman] = []
            simanim_w_probs[siman].append((seif_text, word_after_i_tag))



    if len(sys.argv) == 2 and sys.argv[1] == "--run":
        errors += root.populate_comment_store()
        errors += b_vol.validate_all_xrefs_matched(lambda x: x.name == 'xref' and re.search(eshel_mark, x.text) is not None, base="Orach Chaim", commentary="Eshel Avraham", simanim_only=True)


for i in errors:
    print i

# for siman in sorted(simanim_w_probs.keys()):
#     probs_arr = simanim_w_probs[siman]
#     print "SIMAN {}\n".format(siman)
#     for eshel, base in probs_arr:
#         print u"Eshel:{}\n".format(eshel)
#         print u"Orach Chaim:{}\n".format(base)
#         print
#     print

root.export()




