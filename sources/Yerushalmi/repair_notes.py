# executed from CLI

import re

mesechtot = ["Avodah Zarah", "Bava Batra", "Bava Kamma", "Bava Metzia", "Beitzah", "Berakhot", "Bikkurim",
             "Chagigah", "Challah", "Demai", "Eruvin", "Gittin", "Horayot", "Ketubot", "Kiddushin", "Kilayim",
             "Maaser Sheni", "Maasrot", "Makkot", "Megillah", "Moed Katan", "Nazir", "Nedarim", "Niddah", "Orlah",
             "Peah", "Pesachim", "Rosh Hashanah", "Sanhedrin", "Shabbat", "Shekalim", "Sheviit", "Shevuot", "Sotah",
             "Sukkah", "Taanit", "Terumot", "Yevamot", "Yoma"]
jtindxes = ["JTmock " + x for x in mesechtot]
g_version = "Guggenheimer"


def replace_footnote(instring):
    return re.sub(r'([^"0-9])(\d+)([^"0-9])', r'\1<i data-commentator="Guggenheimer Notes" data-order="\2"></i>\3', instring)


def replace_folio(instring):
    return re.sub(r"\s*\(fol[. ]*([0-9abcd]*)[^)]*\)\s*", r' <i data-overlay="Venice Pages" data-value="\1"></i>', instring)


def replace_line_marker(instring):
    return re.sub(r"\s*\(([^)]*line[^)]*)\)\s*", r' <i data-overlay="Venice Lines" data-value="\1"></i>', instring)


for index in jtindxes:
    base_ref = Ref(index)          # text is depth 3.
    all_halachot = [halacha for perek in base_ref.all_subrefs() for halacha in perek.all_subrefs()]
    for halacha in all_halachot:
        tc = TextChunk(halacha, vtitle=g_version, lang="he")
        new  = [replace_footnote(replace_folio(replace_line_marker(t))) for t in tc.text]
        # tc.text = new
        # tc.save()
