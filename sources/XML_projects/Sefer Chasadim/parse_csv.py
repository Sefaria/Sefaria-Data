import csv
import re
intro = []
text = []
found_re = False
with open("Sefer Chasidim.csv", 'r') as f:
    for row in csv.reader(f):
        m = re.search("^(\d+). ", row[1])
        if m:
            found_re = True
        if not found_re:
            intro.append(row[1])
        elif m:
            text.append(row[1].replace(m.group(0), ""))
        else:
            text[-1] += "<br/>"+row[1]

with open("Sefer Chasidim by Siman.csv", 'w') as f:
    writer = csv.writer(f)
    for l, line in enumerate(intro):
        writer.writerow(["Sefer Chasidim, Introduction {}".format(l+1), line])
    for l, line in enumerate(text):
        writer.writerow(["Sefer Chasidim {}".format(l + 1), line])
