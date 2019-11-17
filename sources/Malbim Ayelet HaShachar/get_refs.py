#encoding=utf-8
import django
django.setup()
from sefaria.model import *
from sources.functions import *
import re
from sefaria.system.exceptions import *
links = []
for seg in library.get_index("Malbim Ayelet HaShachar").all_segment_refs():
    malbim_patterns = []
    line = seg.text('he').text
    line = line.replace(u"ס'", u"סימן").replace(u"סי'", u"סימן")
    i = 0
    j = 3
    while j <= len(line.split()):
        three_words = line.split()[i:j]
        if three_words[1] == u"סימן":
            malbim_patterns.append((three_words[0], three_words[2]))
        i += 1
        j += 1

    for parsha, siman in malbim_patterns:
        parsha = parsha.replace("<b>", "").replace("</b>", "")
        parsha = re.sub(u"[\(\)\.\,]", u"", parsha)
        parsha = parsha.replace(u"אחרי", u"אחרי מות").replace(u"בחוקותי", u"בחוקתי").replace(u'בחקותי', u"בחוקתי")
        if parsha == u'שם' or len(parsha) < 3:
            parsha = prev_parsha
        siman_num = getGematria(re.sub(u"[\(\)\.\,]", u"", siman))
        term = Term().load({"titles.text": parsha})
        if parsha.startswith(u"ו") and u"ויקרא" not in parsha:
            parsha = parsha[1:]
        if not term:
            term = Term().load({"titles.text": u"פרשת " + parsha})
        try:
            parsha_name = term.name
            malbim_ref = Ref(u"Malbim on Leviticus, {} {}".format(parsha_name, siman_num))
            link = {"refs": [malbim_ref.as_ranged_segment_ref().normal(), seg.context_ref().as_ranged_segment_ref().normal()], "type": "Commentary",
            "auto": True, "generated_by": "malbim_ayelet_to_leviticus"}
            links.append(link)
        except (InputError, PartialRefInputError, AttributeError) as e:
            print parsha
        prev_parsha = parsha

print(len(links))
post_link(links, server="http://ste.sandbox.sefaria.org")