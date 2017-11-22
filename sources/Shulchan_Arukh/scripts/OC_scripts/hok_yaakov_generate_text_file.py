#encoding=utf-8
from sources.Shulchan_Arukh.ShulchanArukh import *
import sys


filename = "../../txt_files/Orach_Chaim/part_3/שלחן ערוך אורח חיים חלק ג חק יעקב מושלם.txt"
if __name__ == "__main__":
    with codecs.open(filename) as f:
        lines = f.read()
    new_lines = []
    prev_seif = 0
    for line_n, line in enumerate(lines):
        if line.startswith("@22"):
            seif = getGematria(line)
            if seif
        elif line.startswith("@11"):
            new_lines.append(line)
        else:
            print