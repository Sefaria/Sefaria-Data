import django
django.setup()
from sefaria.model import *


new = ["Ma'aneh Lashon Chabad", "Minchat Kenaot", "Derekh HaShem", "Shemonah Kevatzim",
 "Pri HaAretz", "Sefer HaMiddot", "Sha'ar HaEmunah VeYesod HaChasidut",
 "Machberet Menachem", "Sefer HaBachur", "Meshekh Chokhmah", "Tur HaArokh",
 "Likutei Halakhot", "Darkhei HaTalmud"]
orig = ["Maaneh Lashon Chabad", "Minhat Kenaot", "Derech Hashem", "Shmonah Kvatzim",
				"Pri Haaretz", "Sefer HaMidot", "Shaar HaEmunah Ve'Yesod HaChassidut",
				"Mahberet Menachem", "Sefer haBachur", "Meshech Chochma", "Tur HaAroch",
				"Likutei Halachot", "Darchei HaTalmud"]
assert len(orig) == len(new)
for i, index in enumerate(orig):
	try:
		index = library.get_index(index)
		old_title = index.title
		new_title = index.title.replace(old_title, new[i])
		print(new_title)
		index.set_title(new_title)
		for t in index.nodes.title_group.titles:
			if t["lang"] == "en" and old_title in t["text"]:
				print("Replacing {}".format(t["text"]))
				t["text"] = t["text"].replace(old_title, new[i])
		index.save()
	except Exception as e:
		print(e)
library.rebuild(include_toc=True)




