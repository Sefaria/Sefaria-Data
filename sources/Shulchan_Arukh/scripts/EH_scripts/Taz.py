#encoding=utf-8
import sys
from sources.Shulchan_Arukh.ShulchanArukh import *
from EH_base import move_special_section

def convert(filename):
    new = []
    siman = 0
    with open(filename) as f:
        for i, line in enumerate(f):
            if line.startswith("$"):
                siman += 1
                if len(line.split(" ")) > 3: # this line should be a special tag
                    new.append("@00")
                    new.append(line)
                else:
                    line = line.replace("  ", " ")
                    line = line.replace("$סימן ", "@22").replace("$סי' ", "@22").replace("$סי ", "@22")
                    line = line.replace("$", "@22").replace("\n", "").replace("\r", "")
                    new.append(line)
            elif line.startswith("@") and not "@00" in line:
                line = line.replace("@", "@11")
                seif, line = line.split(" ")[0], " ".join(line.split(" ")[1:])
                new.append(seif)
                new.append("@12"+line)
            else:
                new.append(line)
    new_file = open("Taz_1_new.txt", 'w')
    new_file.writelines(new)
    new_file.close()
    return new


def insert_dh(contents):
    #logic is this:when word in after_dh_arr appears, replace it with itself
    # if word is Culay,
    after_dh_arr = [u"בטור", u"פירוש", u"פי'"]
    new = []
    for line_n, line in enumerate(contents):
        try:
            line = line.decode('utf-8')
        except:
            pass
        if line.startswith("@11") and len(line) > 6:
            found = False
            first_6_words = line.split(" ")[0:6]
            for word in after_dh_arr:
                if word in first_6_words:
                    pos = line.find(word)
                    dh = line[0:pos]
                    line = u"{}@33{}".format(dh, line[pos:])
                    found = True
                    break
            if not found:
                if u"כו'" in first_6_words:
                    pos = line.find(u"כו'")
                    dh = line[0:pos+6]
                    line = u"{}@33{}".format(dh, line[pos+6:])
                elif u"." in u" ".join(first_6_words):
                    pos = line.find(u".")
                    dh = line[0:pos+1]
                    line = u"{}@33{}".format(dh, line[pos+1:])

        new.append(line.replace("\n", "").replace("\r", ""))
    return "\n".join(new)



root = Root('../../Even_HaEzer.xml')
commentaries = root.get_commentaries()
taz = commentaries.get_commentary_by_title("Turei Zahav")
if taz is None:
    taz = commentaries.add_commentary("Turei Zahav", u"טורי זהב")

a = {}

filenames = [u"../../txt_files/Even_Haezer/part_1/Taz_vol1.txt",
             u"../../txt_files/Even_Haezer/part_2/Taz 2_with_12s.txt"]
errors, volume = [], None
for i, filename in enumerate(filenames):
    taz.remove_volume(i+1)
    if i == 0:
        contents = convert(filename)
        contents = insert_dh(contents)
        volume = taz.add_volume(contents, i+1)
    elif i == 1:
        # correct_marks_in_file(filename, u'@00([\u05d0-\u05ea]{1,2})', u'@22([\u05d0-\u05ea]{1,3})')
        with codecs.open(filename, 'r', 'utf-8') as infile:
            contents = infile.read()
            contents = insert_dh(contents.splitlines())
        volume = taz.add_volume(contents, i+1)
    assert isinstance(volume, Volume)

    base = root.get_base_text()
    b_vol = base.get_volume(i+1)
    #b_vol.mark_references(volume.get_book_id(), u'@77\(([\u05d0-\u05ea]{1,3})\)', group=1)

    volume.mark_simanim(u'@22([\u05d0-\u05ea]{1,4})', specials={u'@00': {'name': u'topic'},
                                                                u'@14': {'name': u'Get', 'end': u'!end!'},
                                                                u'@15': {'name': u'ShmotAnashim', 'end': u'!end!'}})
    volume.validate_simanim(complete=False)
    errors = volume.mark_seifim(u'@11([\u05d0-\u05ea]{1,3})')
    volume.validate_seifim()
    for e in errors:
        print e

    errors = volume.format_text('@12', '@33', 'dh')
    for e in errors:
        print e

    volume.render()

    assert isinstance(b_vol, Volume)
    volume.set_rid_on_seifim()
    root.populate_comment_store(verbose=False)
    errors = b_vol.validate_all_xrefs_matched(lambda x: x.name == 'xref' and re.search(u'@91', x.text) is not None)

    for e in errors:
        print e


get_sec = move_special_section(taz, u'Turei Zahav, Seder HaGet', u'טורי זהב, סדר הגט', u'Get')
get_sec.mark_seifim(u'@11([\u05d0-\u05ea]{1,3})', enforce_order=True)
get_sec.validate_seifim()
get_sec.format_text(u'', u'', u'reg-text')
get_sec.set_rid_on_seifim(root.get_commentary_id(u"Seder HaGet"), get_sec.get_parent().get_book_id())

names_sec = move_special_section(taz, u"Turei Zahav, Shemot Anashim V'Nashim", u'טורי זהב, שמות אנשים ונשים ', u'ShmotAnashim')
names_sec.mark_seifim(u'@11([\u05d0-\u05ea]{1,3})', enforce_order=True)
names_sec.validate_seifim()
names_sec.format_text(u'', u'', u'reg-text')
for seif in names_sec.get_child():
    assert isinstance(seif, Seif)
    seif.Tag['rid'] = 'no-link'

root.export()
