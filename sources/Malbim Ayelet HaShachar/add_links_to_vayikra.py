#encoding=utf-8
import django
django.setup()
from sefaria.model import *
from sources.functions import *
import re
ls = LinkSet({"$and": [{"refs": {"$regex": "^Malbim on Leviticus"}}, {"refs": {"$regex": "^Malbim Ayelet HaShachar"}}]})

LinkSet({"$and": [{"refs": {"$regex": "^Malbim on Leviticus"}}, {"refs": "Leviticus 10:2"}]})


for l in ls:
    malbim_on_leviticus_ref, malbim_ayelet_ref = (l.refs[0], l.refs[1]) if "Leviticus" in l.refs[0] else (l.refs[1], l.refs[0])
    print malbim_ayelet_ref
    ls_2 = LinkSet({"generated_by": u'sterling_Malbim_linker', "$and": [{"refs": {"$regex": "^Leviticus"}}, {"refs": malbim_on_leviticus_ref}]})
    for l_2 in ls_2:
        leviticus_ref = l_2.refs[0] if l_2.refs[0].startswith("Leviticus") else l_2.refs[1]
        print leviticus_ref
        assert Ref(malbim_ayelet_ref).text('he').text
        assert Ref(leviticus_ref).text('he').text
        new_link = {"refs": [malbim_ayelet_ref, leviticus_ref], "auto": True, "generated_by": "malbim_ayelet_to_leviticus", "type": "Commentary"}
        try:
            Link(new_link).save()
        except:
            print "ERROR"
            print



