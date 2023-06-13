import django
django.setup()
from sefaria.model import *
import re
"""
http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002691623

Same link, new syntax:

['http://rosetta.nli.org.il/delivery/DeliveryManagerServlet?dps_pid=IE13133653',
 'http://web.nli.org.il/sites/nlis/he/Song/Pages/Song.aspx?SongID=717#3,138,2253,486',
 'http://aleph.nli.org.il:80/F/?func=direct&doc_number=000077860&local_base=RMB01',
 'http://aleph.nli.org.il:80/F/?func=direct&doc_number=000109739&local_base=MBI01',
 'http://aleph.nli.org.il:80/F/?func=direct&doc_number=000309285&local_base=MBI01']
"""
import re
vs = VersionSet({"versionTitle": {"$regex": 'nli\.org.*?\?'}})
for c, v in enumerate(vs):
    if 'nli.org' in v.versionSource:
        end = v.versionSource.split("?")[-1]
        if not end.startswith("http"):
            num = re.search(".*?(NNL.{1,})&?", end)
            if num:
                v.versionSource = f'https://www.nli.org.il/he/books/{num.group(1)}'
                #v.save()
            else:
                print(f"PROBLEM WITH {v.versionSource}")
        else:
            print("OTHER PROBLEM")

# print(starts)
# print(ends)
