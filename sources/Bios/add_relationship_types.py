# -*- coding: utf-8 -*-

from sefaria.model import *

"""
This one gets added in ../Sages_DB/parse_sages_to_mongo.py

prt = PersonRelationshipType({"key": "student"})
prt.set_forward_name(u"Learned From", "en")
prt.set_forward_name(u"רבותיו", "he")
prt.set_reverse_name(u"Taught", "en")
prt.set_reverse_name(u"תלמידיו", "he")
prt.save()
"""

prt = PersonRelationshipType({"key": "child"})
prt.set_forward_name(u"Child of", "en")
prt.set_forward_name(u"ילד של", "he")
prt.set_reverse_name(u"Parent of", "en")
prt.set_reverse_name(u"הורה של", "he")
prt.save()

prt = PersonRelationshipType({"key": "childinlaw"})
prt.set_forward_name(u"Son in Law of", "en")
prt.set_forward_name(u"חתנו של", "he")
prt.set_reverse_name(u"Father in Law of", "en")
prt.set_reverse_name(u"מחותן של", "he")
prt.save()

prt = PersonRelationshipType({"key": "grandchild"})
prt.set_forward_name(u"Grandchild of", "en")
prt.set_forward_name(u"נכד של", "he")
prt.set_reverse_name(u"Grandparent of", "en")
prt.set_reverse_name(u"הסב של", "he")
prt.save()

prt = PersonRelationshipType({"key": "member"})
prt.set_forward_name(u"From the School of", "en")
prt.set_forward_name(u"מבית הספר של", "he")
prt.set_reverse_name(u"Members", "en")
prt.set_reverse_name(u"חברים", "he")
prt.save()

prt = PersonRelationshipType({"key": "correspondent"})
prt.set_forward_name(u"Corresponded with", "en")
prt.set_forward_name(u"התכתב עם", "he")
prt.set_reverse_name(u"Corresponded with", "en")
prt.set_reverse_name(u"התכתב עם", "he")
prt.save()

prt = PersonRelationshipType({"key": "opposed"})
prt.set_forward_name(u"Opposed", "en")
prt.set_forward_name(u"התנגד ל", "he")
prt.set_reverse_name(u"Was Opposed by", "en")
prt.set_reverse_name(u"התנגד ל", "he") #todo: better transx
prt.save()

prt = PersonRelationshipType({"key": "cousin"})
prt.set_forward_name(u"Cousin of", "en")
prt.set_forward_name(u"בן דודו של", "he")
prt.set_reverse_name(u"Cousin of", "en")
prt.set_reverse_name(u"בן דודו של", "he")
prt.save()
