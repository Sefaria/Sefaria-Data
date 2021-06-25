mesechtot = ["Avodah Zarah", "Bava Batra", "Bava Kamma", "Bava Metzia", "Beitzah", "Berakhot", "Bikkurim",
             "Chagigah", "Challah", "Demai", "Eruvin", "Gittin", "Horayot", "Ketubot", "Kiddushin", "Kilayim",
             "Maaser Sheni", "Maasrot", "Makkot", "Megillah", "Moed Katan", "Nazir", "Nedarim", "Niddah", "Orlah",
             "Peah", "Pesachim", "Rosh Hashanah", "Sanhedrin", "Shabbat", "Shekalim", "Sheviit", "Shevuot", "Sotah",
             "Sukkah", "Taanit", "Terumot", "Yevamot", "Yoma"]
jtindxes = ["JTmock " + x for x in mesechtot]
g_version = "Guggenheimer"

for index in jtindxes:
    base_ref = Ref(index)          # text is depth 3.
    all_halachot = [halacha for perek in base_ref.all_subrefs() for halacha in perek.all_subrefs()]
    for halacha in all_halachot:
        tc = TextChunk(halacha, vtitle=g_version, lang="he")
        if any([not a for a in tc.text]):
            print(f"Collapsing {halacha.normal()}")
            tc.text = [a for a in tc.text if a]
            tc.save()