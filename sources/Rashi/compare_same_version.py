from sefaria.model import *
import  sys
import re
file = open("comparing.txt","w")
title = str(sys.argv[1])
vers = str(sys.argv[2])
try:
    vers2 = str(sys.argv[3])
except Exception as e:
    print "out of range"
if 'vers2' not in locals():
    vers2 = vers

print vers
v_english = Version().load({"title": title, "versionTitle": vers , "language": "en"}).get_content()
v_hebrew = Version().load({"title": title, "versionTitle": vers2 , "language": "he"}).get_content()
eng= []
for j, perek in enumerate(v_english):
    for i, pasuk in enumerate(perek):
        for m,dibbur in enumerate(pasuk):
            if len(pasuk) > 0:
                #ans = str(j+1) + "," + str(i + 1) + "," + str(m + 1)
                ans = j + 1, "," , i + 1, "," , m + 1
                eng.append(ans)
heb = []
for k , perek in enumerate(v_hebrew):
    for l, pasuk in enumerate(perek):
        for p, dibbur in enumerate(pasuk):
            if len(pasuk) > 0:
                #ans = str(k + 1) + "," + str(l + 1) + "," + str( p + 1)
                ans = k + 1,"," ,l+1, "," ,p + 1
                heb.append(ans)
comparison =  sorted(set(heb).difference(set(eng)))
print len(comparison)
for item in comparison:
    it = re.sub("\,\s\'\,\'","",str(item))
    it =re.sub(ur"[\(\)]", "", it)
    perek = re.split("\,", it)[0]
    pasuk = re.split("\,", it)[1]
    dibur = re.split("\,", it)[2]
    file.write("www.sefaria.org/" + title + "." + str(perek).strip() + "." + str(pasuk).strip() + "." + str(dibur).strip() + "\n")
