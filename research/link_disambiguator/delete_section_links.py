import django, unicodecsv
django.setup()

from sefaria.model import *
from sefaria.system.exceptions import InputError

with open("scripts/unambiguous_links.json", "rb") as fin:
    cin = unicodecsv.DictReader(fin)
    count = 0
    for row in cin:
        if count % 1000 == 0:
            print(count)
        count += 1
        try:
            r = Ref(row["Quoting Ref"])
            s = Ref(row["Quoted Ref"])
            t = s.section_ref()
            ls = r.linkset().refs_from(r, as_link=True)
            found_segment, found_section = False, False
            section_link = None
            for l, u in ls:
                if u == s:
                    found_segment = True
                if u == t:
                    found_section = True
                    section_link = l
            if found_segment and found_section:
                section_link.delete()
        except InputError:
            print("{} - {}".format(row["Quoting Ref"], row["Quoted Ref"]))
