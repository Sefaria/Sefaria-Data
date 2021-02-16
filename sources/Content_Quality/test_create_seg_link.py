from sources.functions import *
from sefaria.helper.link import add_links_from_text
from sefaria.model.schema import *
from sefaria.utils.hebrew import *
from sefaria.system.database import ensure_indices
from sefaria.model.tests.ref_catching_test import *
from sefaria.helper.link import rebuild_links_from_text as rebuild
import numpy

assert not Ref("Orot").is_section_level()
assert Ref("Pesach Haggadah, Magid, First Fruits Declaration 2") .all_context_refs() == [Ref('Pesach Haggadah, Magid, First Fruits Declaration 2'), Ref('Pesach Haggadah, Magid, First Fruits Declaration'), Ref('Pesach Haggadah, Magid')]
assert not Ref("Orot").is_segment_level()


print(Ref("Zohar 1:25a-2:27b").he_normal())

print(Ref("Zohar 1:25a-27b").he_normal())


print(Ref("Berakhot 2a-3a").he_normal())
print(Ref("Bava Metzia 20b-21b").he_normal())
print(Ref("Bava Metzia 20a:1-20b:1").he_normal())
print(Ref("Zohar 1-2").he_normal())
print(Ref("Zohar 1:25a-27b").he_normal())

oref = Ref("Zohar 1:25a-27b")
oref.normal()


assert Ref("Shabbat 5b:10-20").overlaps(Ref("Shabbat 5b:18-20"))
assert Ref("Shabbat 15b:5-8").range_list() ==  [Ref('Shabbat 15b:5'), Ref('Shabbat 15b:6'), Ref('Shabbat 15b:7'), Ref('Shabbat 15b:8')]

print(Ref("Shabbat 7-8").normal())
print(Ref("Shabbat 7").normal())
print(Ref("Shabbat 7a-8b"))
print(Ref("Shabbat 7a-8a"))
print(Ref('Shabbat 7b-8b'))
print(Ref('Shabbat 7b-8a'))
Ref("Footnotes_to_Teshuvot_haRashba_part_V").version_list()
print(library.get_refs_in_string("(שו”ע יו”ד קיג:ד)"))
print(library.get_refs_in_string('(שו"ע יו"ד קיג:ד)', citing_only=True))
print(library.get_refs_in_string('(שו״ע יו״ד קיג:ד)'))

full = library.full_title_list('en') + library.full_title_list('he')
citations = library.citing_title_list('en') + library.citing_title_list('he')
print(len(numpy.array(full).tobytes()) * 0.000001)
print(len(numpy.array(citations).tobytes()) * 0.000001)
titles = [t for t in library.citing_title_list("en") + library.citing_title_list("he")]
gershayim = [t for t in titles if '״' in t]
fancy_quotes = [t for t in titles if '”' in t]
regular_quotes = [t for t in titles if '"' in t]
Ref('שו"ע יו"ד קיג:ד')

print(library.get_refs_in_string("Berakhot 7a-b"))
print(library.get_refs_in_string("Berakhot 7a:2-8b:3"))

print(library.get_refs_in_string("Genesis 1:2-3"))
print(library.get_refs_in_string("Genesis 1-Genesis 2"))


library.get_refs_in_string("שבת טו.")

assert Ref("Zohar 2.15a - b").toSections[1] == 30

assert m.Ref('שבת טו. - טז:') == m.Ref("Shabbat 15a-16b")

assert m.Ref('שבת טו א - טז ב') == m.Ref("Shabbat 15a-16b")


#
# assert Ref("Zohar 2.15a - 15b").sections[1] == 29
# assert Ref("Zohar 2.15a - 15b").toSections[1] == 30
assert Ref("Zohar 2.15a - b").sections[1] == 29

print(library.get_refs_in_string("Genesis 1-3"))

Test_find_citation_in_text().test_regex_string_en_array()
#print(library.get_refs_in_string("Genesis/Bereshit 2 -Genesis 2:3"))
#ensure_indices()

print(Ref("Berakhot 3"))

section_patterns = {
        "en": r"(?:(?:(?:[Vv]ol.)|(?:[Vv]olumes?)|(?:[Nn]o.))?\s*)",
        "he": r"""(?:\u05d1?
        (?:\u05db\u05dc\u05dc)
        |(?:\u05e1\u05b4?\u05d9\u05de\u05b8?\u05df\s+)			# Siman spelled out with optional nikud, with a space after
            |(?:\u05e1\u05d9(?:["\u05f4'\u05f3\u2018\u2019](?:['\u05f3\u2018\u2019]|\s+)))		# or Samech, Yued (for 'Siman') maybe followed by a quote of some sort
        )"""
    }

# assert Ref("Zohar 2.15a - 15b").sections[1] == 29
# assert Ref("Zohar 2.15a - 15b").toSections[1] == 30
#print(library.get_refs_in_string("Found in (Berakhot 3a-3b)", "en", citing_only=True))
print(library.get_refs_in_string("Found in (Berakhot 3a-b)", "en", citing_only=True))
print(library.get_refs_in_string("Found in (Berakhot 3a-b)", "en", citing_only=False))

# # print(library.get_refs_in_string("ברכות ב", "he", citing_only=True))
# add_links_from_text(Ref("Genesis 2"), "en", "Hello (Berakhot 3)", 1, 1)
# # Link({"refs": ["Berakhot 2a", "Exodus 2:1"], "generated_by": "steve", "type": "", "auto": True}).save()
# # Link({"refs": ["Genesis 2", "Exodus 2:1"], "generated_by": "steve", "type": "", "auto": True}).save()
