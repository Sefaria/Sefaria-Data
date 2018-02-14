#encoding=utf-8
from sources.Shulchan_Arukh.ShulchanArukh import *
import sys


filename = "../../txt_files/Orach_Chaim/part_3/שלחן ערוך אורח חיים חלק ג חק יעקב מושלם.txt"
if __name__ == "__main__":
    with codecs.open(filename) as f:
        lines = f.read().splitlines()
    new_lines = []
    prev_seif = 0
    started = False
    siman = 1
    new_lines.append(u"@00א")
    for line_n, line in enumerate(lines):
        if line.startswith("@22"):
            seif = getGematria(line)
            if not started:
                started = True
            elif started and seif < prev_seif:
                siman += 1
                new_lines.append(u"@00{}".format(numToHeb(siman+428)))
            if seif == prev_seif:
                print "Seif repeated: {}".format(seif)
                print prev_line
                print line
            prev_seif = getGematria(line)
        new_lines.append(line.decode('utf-8'))
        prev_line = line

    new_file = "/".join(filename.split("/")[0:-1]) + "/hok_yaakov.txt"
    with codecs.open(new_file, 'w', encoding='utf-8') as f:
        for line in new_lines:
            f.write(line+"\n")