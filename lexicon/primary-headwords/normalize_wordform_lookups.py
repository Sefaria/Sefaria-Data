# -*- coding: utf-8 -*-

import django
django.setup()
from sefaria.model import *


wfset = WordFormSet()
for wf in wfset:
    changed = False
    for l in wf.lookups:
        if "lexicon" in l:
            l["parent_lexicon"] = l["lexicon"]
            del l["lexicon"]
            changed = True
    if changed:
        wf.save()
