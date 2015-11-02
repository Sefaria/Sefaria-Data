from sefaria.model import *
import  sys
import re
title = str(sys.argv[1])
vers = str(sys.argv[2])

v_english = Version().load({"title": title, "versionTitle": vers , "language": "en"}).get_content()
v_hebrew = Version().load({"title": title, "versionTitle": vers , "language": "he"}).get_content()
eng= []
for j, perek in enumerate(v_english):
    for i, pasuk in enumerate(perek):
        if len(pasuk) > 0:
            ans = str(j+1) + "," + str(i + 1)
            eng.append(ans)
heb = []
for k , perek in enumerate(v_hebrew):
    for l, pasuk in enumerate(perek):
        if len(pasuk) > 0:
            ans = str(k + 1) + "," + str(l + 1)
            heb.append(ans)
comparison =  sorted(set(heb).difference(set(eng)))
print comparison

