# -*- coding: utf-8 -*-
import django
django.setup()

from sefaria.model import *

PersonRelationshipTypeSet().delete()

prt = PersonRelationshipType({"key": "student"})
prt.set_forward_name("Learned From", "en")
prt.set_forward_name("רבותיו", "he")
prt.set_reverse_name("Taught", "en")
prt.set_reverse_name("תלמידיו", "he")
prt.save()

prt = PersonRelationshipType({"key": "child"})
prt.set_forward_name("Child of", "en")
prt.set_forward_name("בנו של", "he")
prt.set_reverse_name("Parent of", "en")
prt.set_reverse_name("אביו של", "he")
prt.save()

prt = PersonRelationshipType({"key": "childinlaw"})
prt.set_forward_name("Son in Law of", "en")
prt.set_forward_name("חתנו של", "he")
prt.set_reverse_name("Father in Law of", "en")
prt.set_reverse_name("מחותנו של", "he")
prt.save()

prt = PersonRelationshipType({"key": "grandchild"})
prt.set_forward_name("Grandchild of", "en")
prt.set_forward_name("נכדו של", "he")
prt.set_reverse_name("Grandparent of", "en")
prt.set_reverse_name("סבו של", "he")
prt.save()

prt = PersonRelationshipType({"key": "member"})
prt.set_forward_name("From the School of", "en")
prt.set_forward_name("שייך לחוגו של", "he")
prt.set_reverse_name("Influenced", "en")
prt.set_reverse_name("חברים", "he")
prt.save()

prt = PersonRelationshipType({"key": "correspondent"})
prt.set_forward_name("Corresponded with", "en")
prt.set_forward_name("התכתב עם", "he")
prt.set_reverse_name("Corresponded with", "en")
prt.set_reverse_name("התכתב עם", "he")
prt.save()

prt = PersonRelationshipType({"key": "opposed"})
prt.set_forward_name("Opposed", "en")
prt.set_forward_name("התנגד ל", "he")
prt.set_reverse_name("Was Opposed by", "en")
prt.set_reverse_name("התנגד ל", "he") #todo: better transx
prt.save()

prt = PersonRelationshipType({"key": "cousin"})
prt.set_forward_name("Cousin of", "en")
prt.set_forward_name("בן דודו של", "he")
prt.set_reverse_name("Cousin of", "en")
prt.set_reverse_name("בן דודו של", "he")
prt.save()
