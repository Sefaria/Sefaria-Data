#encoding=utf-8
import django
django.setup()
from sefaria.model import *
from sources.functions import *
import re
from sefaria.system.exceptions import *
links = []
for seg in library.get_index("Malbim Ayelet HaShachar").all_segment_refs():
    line = seg.text('he').text
    malbim_patterns = re.findall(u"[\,\(\s]+(\S+)\sס.{1,4}\s(\S+)\s?[\)\,]+", line)
    for parsha, siman in malbim_patterns:
        parsha = re.sub(u"[\(\)\.\,]", u"", parsha)
        parsha = parsha.replace(u"אחרי", u"אחרי מות")
        siman_num = getGematria(re.sub(u"[\(\)\.\,]", u"", siman))
        term = Term().load({"titles.text": parsha})
        if parsha.startswith(u"ו") and u"ויקרא" not in parsha:
            parsha = parsha[1:]
        if not term:
            term = Term().load({"titles.text": u"פרשת " + parsha})
        try:
            parsha_name = term.name
            malbim_ref = u"Malbim on Leviticus, {} {}".format(parsha_name, siman_num)
            assert Ref(malbim_ref)
            link = {"refs": [malbim_ref, seg.normal()], "type": "Commentary",
            "auto": True, "generated_by": "malbim_ayelet_to_leviticus"}
            links.append(link)
        except (InputError, PartialRefInputError, AttributeError) as e:
            print "Failed to retrieve proper links in {}".format(malbim_ref)

print(len(links))
post_link(links, server="http://ste.sandbox.sefaria.org")