#encoding=utf-8
import sys
from sources.Shulchan_Arukh.ShulchanArukh import *

filenames = [u"../../txt_files/Orach_Chaim/part_3/שלחן ערוך אורח חיים חלק ג עטרת זקנים מושלם.txt",
            u"../../txt_files/Orach_Chaim/part_2/שולחן ערוך אורח חיים חלק ב עטרת זקנים.txt",
            u"../../txt_files/Orach_Chaim/part_1/שוע אורח חיים חלק א ‏עטרת זקנים1.txt"][::-1]

new_lines = {}
for filename in filenames:
    new_lines[filename] = []
    f = open(filename)
    prev_line = ""
    prev_line_44 = None
    lines = [line.decode('utf-8') for line in list(f) if line != "\n"]
    for i, line in enumerate(lines):
        line = line.replace("\r", "")
        orig_line = line
        if line.startswith("@22") or line.startswith("@00"):
            new_lines[filename].append(line.replace(u"@22", u"@00").replace(u"סי' ", u""))
        elif line.startswith("@44"):
            if prev_line.startswith("@11"):
                new_lines[filename][-1] += "!br!"+line.replace(u"@44", u"")
                prev_line_44 = None
        elif line.startswith("@11") or len(line) > 15:
            assert "@11" in line
            line = line.replace("@11", "").replace("@33", "")
            new_lines[filename].append(u"@22\u2666\n")
            if prev_line_44:
                new_lines[filename][-1] = new_lines[filename][-1]+"!br!"+line
                prev_line_44 = None
            else:
                new_lines[filename].append(line)
        prev_line = orig_line

    f.close()


root = Root('../../Orach_Chaim.xml')
commentaries = root.get_commentaries()
commentary = commentaries.get_commentary_by_title("Ateret Zekenim")
if commentary is None:
    commentary = commentaries.add_commentary("Ateret Zekenim", u"עטרת זקנים")

base = root.get_base_text()
errors = []
for i, filename in enumerate(filenames):
    commentary.remove_volume(i + 1)
    text = u"".join(new_lines[filename])
    volume = commentary.add_volume(text, i + 1)
    assert isinstance(volume, Volume)

    volume.mark_simanim(u'@00(.{1,6})')
    volume.validate_simanim(complete=False)

    errors += volume.mark_seifim(u'@22(.{1,6})', cyclical=True)
    volume.validate_seifim()

    errors += volume.format_text(start_special='', end_special='', name=u"reg-text")


    b_vol = base.get_volume(i + 1)

    assert isinstance(b_vol, Volume)
    volume.set_rid_on_seifim(cyclical=True)
    if len(sys.argv) == 2 and sys.argv[1] == "--run":
        errors += root.populate_comment_store()
        errors += b_vol.validate_all_xrefs_matched(lambda x: x.name == 'xref' and re.search(u"(\u2666)(?!\))", x.text) is not None, base="Orach Chaim", commentary="Ateret Zekenim", simanim_only=True)

errors = set(errors)
#sort_func = lambda x: int(x.split("Orach Chaim, Siman ")[1].split(":")[0])
errors = sorted(errors)
for i in errors:
    print i

root.export()
