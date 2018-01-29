#encoding=utf-8
import sys
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


root = Root('../../Even_HaEzer.xml')
commentaries = root.get_commentaries()
taz = commentaries.get_commentary_by_title("Turei Zahav")
if taz is None:
    taz = commentaries.add_commentary("Turei Zahav", u"טורי זהב")

a = {}

filenames = [u"../../txt_files/Even_Haezer/part_1/Taz_vol1.txt",
             u"../../txt_files/Even_Haezer/part_2/שולחן ערוך אבן האזל חלק ב טז.txt"]
errors = []
for i, filename in enumerate(filenames):
    taz.remove_volume(i+1)
    # correct_marks_in_file(filename, u'@00([\u05d0-\u05ea]{1,2})', u'@22([\u05d0-\u05ea]{1,3})')
    with codecs.open(filename, 'r', 'utf-8') as infile:
        contents = infile.read()
        volume = taz.add_volume(contents, i+1)
    assert isinstance(volume, Volume)

    base = root.get_base_text()
    b_vol = base.get_volume(i+1)
    #b_vol.mark_references(volume.get_book_id(), u'@77\(([\u05d0-\u05ea]{1,3})\)', group=1)

    volume.mark_simanim(u'@22([\u05d0-\u05ea]{1,4})', specials={u'@00': {'name': u'topic'}})
    volume.validate_simanim(complete=False)

    errors += volume.mark_seifim(u'@11\(([\u05d0-\u05ea]{1,3})\)')
    volume.validate_seifim()

    errors += volume.format_text('', '', 'reg-text')

    volume.render()

    assert isinstance(b_vol, Volume)
    volume.set_rid_on_seifim()
    if len(sys.argv) == 2 and sys.argv[1] == "--run":
        errors += root.populate_comment_store()
        errors += b_vol.validate_all_xrefs_matched(lambda x: x.name == 'xref' and re.search(u'@77', x.text) is not None, base="Orach Chaim", commentary="Turei Zahav", simanim_only=True)


for i in errors:
    print i

root.export()