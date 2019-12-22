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
                temp = " ".join(line.split()[1:])
                assert siman - prev_siman == 1
                mechaber_kereti_dict[siman] = {}
            elif "@11" in line:
                seif = getGematria(line.split()[0])
                line = " ".join(line.split()[1:])
                if temp:
                    line = temp + " " + line
                    temp = ""
                line = line.decode('utf-8')
                line = re.sub(u"\[\S{1,3}\]", u"", line)
                line = re.sub(u"[!*]+\S+", u"", line)
                line = re.sub(u"@\d+\S{1,5}", u"", line)
                line = re.sub(u"\(#\)", u"", line)
                line = re.sub(u" \*", u"", line)
                mechaber_kereti_dict[siman][seif] = line
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
                kereti_text_dict[siman] = {}
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
                kereti_text_dict[siman][seif] = 0
                prev_line = line
                prev_seif = seif
            elif siman in kereti_text_dict and seif in kereti_text_dict[siman]:
                kereti_text_dict[siman][seif] += len(line.split()[1:])
            prev_text_line = line


for siman in mechaber_kereti_dict:
    for seif in mechaber_kereti_dict[siman]:
        mechaber = mechaber_kereti_dict[siman][seif]
        if not "&" in mechaber:
            continue
        mechaber = mechaber.replace("& ", "")
        our_text = TextChunk(Ref("Shulchan Arukh, Yoreh Deah {}:{}".format(siman, seif)), lang='he').text
        our_text = re.sub(u"<.*?>", u" ", our_text)
        our_text = re.sub(u"</.*?>", u" ", our_text)
        while "  " in our_text:
            our_text = our_text.replace("  ", " ")
        while "  " in mechaber:
            mechaber = mechaber.replace("  ", " ")
        our_text = our_text.replace(" .", ".")
        our_text = our_text.strip()
        mechaber = mechaber.strip()
        diff = abs(our_text.count(" ") - mechaber.count(" "))
        if 20 >= diff > 0:
            print "Difference of {} in {}:{}".format(diff, siman, seif)
            print our_text
            print mechaber
            print "***"

