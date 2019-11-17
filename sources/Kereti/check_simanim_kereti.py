#encoding=utf-8
import django
django.setup()
from sefaria.model import *
from sources.functions import *
kereti_text_dict = {}
mechaber_kereti_dict = {}
siman = 0
prev_siman = 0
for f in ["Mechaber 1.txt", "Mechaber 2.txt"]:
    with open(f) as file:
        for line in file:
            if "@22" in line:
                siman = getGematria(line.split()[0])
                assert siman - prev_siman == 1
                mechaber_kereti_dict[siman] = 0
            if "&" in line:
                mechaber_kereti_dict[siman] += line.count("&")
            prev_siman = siman

prev_siman = siman = 0
prev_line = ""
report = codecs.open("errors.csv", 'w', encoding='utf-8')
report.write("File name,Previous seif,Current seif,First line of seif\n")
for f in ["Kereti 1.txt", "Kereti 2.txt"]:
    with open(f) as file:
        print f
        for i, line in enumerate(file):
            if "@00" in line:
                siman = getGematria(line.split()[-1])
                assert siman - prev_siman == 1, "{} vs {}".format(line, prev_line)
                kereti_text_dict[siman] = 0
                prev_line = line
                seif = prev_seif = 0
                prev_siman = siman
            elif "@22" in line:
                line = line.replace("יוד", "י")
                seif = getGematria(line)
                if seif - prev_seif != 1:
                    line_to_write = u"{},{},{},{}".format(f, prev_line.decode('utf-8'), line.decode('utf-8'), prev_text_line.decode('utf-8'))
                    line_to_write = line_to_write.replace("\n", "") + "\n"
                    report.write(line_to_write)
                kereti_text_dict[siman] += 1
                prev_line = line
                prev_seif = seif
            prev_text_line = line

print len(kereti_text_dict.keys()) - len(mechaber_kereti_dict.keys())

for dict in [mechaber_kereti_dict, kereti_text_dict]:
    for siman in dict.keys():
        if not siman in mechaber_kereti_dict.keys() or not siman in kereti_text_dict.keys():
            continue
        diff = mechaber_kereti_dict[siman] - kereti_text_dict[siman]
        if diff > 0:
            print "Siman {}: There are {} more & marks in Mechaber than Seifim in Kereti".format(siman, diff)
        elif diff < 0:
            print "Siman {}: There are {} more seifim in Kereti than & marks in Mechaber".format(siman, abs(diff))




