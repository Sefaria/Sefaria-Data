#encoding=utf-8

from sources.Shulchan_Arukh.ShulchanArukh import *
def convert_11s(filename):
    new = []
    with open(filename) as f:
        for line in f:
            if len(line) > 15 and not line.startswith("@11") and "@33" in line and not "@22" in line:
                line = "@11" + line
            if len(line) > 15 and line.startswith("@11") and "@33" not in line:
                line = line.replace("@11 ", "").replace("@11", "")
            new.append(line)
    with open(filename, 'w') as f:
        for line in new:
            f.write(line)

root = Root('../../Orach_Chaim.xml')
commentaries = root.get_commentaries()
eshel = commentaries.get_commentary_by_title("Eshel Avraham on Orach Chayim")
if eshel is None:
    eshel = commentaries.add_commentary("Eshel Avraham on Orach Chayim", u"טז על אורח חיים")


filenames = [u"../../txt_files/Orach_Chaim/part_1/שוע אורח חיים חלק א אשל אברהם.txt",
             u"../../txt_files/Orach_Chaim/part_2/שולחן ערוך אורח חיים חלק ב אשל אברהם.txt",
             u"../../txt_files/Orach_Chaim/part_3/שלחן ערוך אורח חיים חלק ג אשל אברהם מושלם.txt"]

base = root.get_base_text()
base.add_titles("Orach Chaim", u"אורח חיים")
base_refs = []
base_indices = [45, 146, 149, 325, 368, 407, 414, 442, 456]
e = open("eshel.txt", 'w')
b = open("base.txt", 'w')
for i in range(3):
    b_vol = base.get_volume(i+1)
    mark = "@88" if i < 2 else "@99"
    for siman in b_vol:
        for seif in siman:
            for char in [match.group(1) for match in seif.grab_references(mark+"(\S+)\]")]:
                base_refs += [char]
                if len(base_refs) in base_indices:
                    print len(base_refs)
                    print u"Orach Chaim Volume {}, Siman {}, Seif {}".format(i+1, numToHeb(siman.num), numToHeb(seif.num))


eshel_markers = []
eshel_indices = [44, 146, 148, 191, 325, 364, 369, 407, 413, 442, 448, 455]

modify = lambda str: str.replace("[", "").replace("]", "").replace("(", "").replace(")", "").decode('utf-8')
for file_n, filename in enumerate(filenames):
    with open(filename) as f:
        base_ref_augmenter = 0
        for line_n, line in enumerate(f):
            for i, char in enumerate([modify(str) for str in re.findall(u"@22(\S+)", line)]):
                len_eshel = len(eshel_markers) + base_ref_augmenter
                eshel_markers += [char]
                if len(eshel_markers) in eshel_indices:
                    print len(eshel_markers)
                    print "Eshel Avraham on Orach Chaim, Volume {}".format(file_n+1)
                    print line

count = 0
for eshel in eshel_markers:
    count += 1
    e.write(eshel.encode('utf-8')+'\n')

print count

for base in base_refs:
    count += 1
    b.write(base.encode('utf-8')+'\n')

print count

e.close()
b.close()

'''


for i, filename in enumerate(filenames):
    eshel.remove_volume(i+1)
    # correct_marks_in_file(filename, u'@00([\u05d0-\u05ea]{1,2})', u'@22([\u05d0-\u05ea]{1,3})')
    with codecs.open(filename, 'r', 'utf-8') as infile:
        volume = eshel.add_volume(infile.read(), i+1)
    assert isinstance(volume, Volume)

    base = root.get_base_text()
    base.add_titles("Orach Chaim", u"אורח חיים")
    b_vol = base.get_volume(i+1)
    #b_vol.mark_references(volume.get_book_id(), u'@88([\u05d0-\u05ea]{1,3})\]', group=1)

    errors = volume.mark_simanim(u'@00([\u05d0-\u05ea]{1,4})') if i == 0 else volume.mark_simanim(u'@22([\u05d0-\u05ea]{1,4})')
    volume.validate_simanim(complete=False)

    errors += volume.mark_seifim(u'@22\(([\u05d0-\u05ea]{1,3})\)') if i == 0 else volume.mark_seifim(u'@11\(([\u05d0-\u05ea]{1,3})\)')
    volume.validate_seifim()

    errors += volume.format_text('@11', '@33', 'dh')

    assert isinstance(b_vol, Volume)
    volume.set_rid_on_seifim()
    print errors

errors += root.populate_comment_store()
errors += b_vol.validate_all_xrefs_matched(lambda x: x.name == 'xref' and re.search(u'@88', x.text) is not None, base="Orach Chaim", commentary="Eshel Avraham on Orach Chaim", simanim_only=True)
for i in errors:
    print i



root.export()
'''