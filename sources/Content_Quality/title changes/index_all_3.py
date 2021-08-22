import django
django.setup()
from sefaria.model import *

indices = ["Halacha and Aggadah", "Derech Chaim"]
new_titles = ["Halakhah and Aggadah", "Derekh Chayim"]
all_i = IndexSet()
for i, index in enumerate(indices):
	index = library.get_index(index)
	old_title = index.title
	new_title = index.title.replace(old_title, new_titles[i])
	index.set_title(new_title)
	for t in index.nodes.title_group.titles:
		if t["lang"] == "en" and old_title in t["text"]:
			print("Replacing {}".format(t["text"]))
			t["text"] = t["text"].replace(old_title, new_titles[i])
	index.save()
	index.versionState().refresh()

	for comm in all_i:
		if getattr(comm, "base_text_titles", None) and (old_title in comm.base_text_titles or new_title in comm.base_text_titles):
			print(comm)
			comm.base_text_titles = [new_titles[i]]
			new_title = comm.title.replace(old_title, new_titles[i])
			comm.set_title(new_title)
			for t in comm.nodes.title_group.titles:
				if t["lang"] == "en" and old_title in t["text"]:
					print("Replacing {}".format(t["text"]))
					t["text"] = t["text"].replace(old_title, new_titles[i])
			comm.save()
			comm.versionState().refresh()
library.rebuild(include_toc=True)



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


new = ["Pitchei Teshuva", "Kitzur Baal HaTurim", "Melekhet Shelomoh", "Maharam Schiff"]
orig = ["Pithei Teshuva", "Kitzur Baal Haturim", "Melechet Shlomo", "Maharam Shif"]
for i, cat in enumerate(orig):
	subcats = CategorySet({"path": cat}).array()
	old_term = Term().load({"name": cat})
	t = Term()
	t.name = new[i]
	t.add_primary_titles(new[i], old_term.get_primary_title('he')+" ב")
	t.save()
	for c in subcats:
		if orig[i] in c.lastPath:
			print(c)
			new_c = Category()
			new_c.path = c.path
			new_c.add_shared_term(t.name)
			new_c.lastPath = new_c.path[-1] = new[i]
			new_c.enDesc = getattr(c, "enDesc", "")
			new_c.heDesc = getattr(c, "heDesc", "")
			new_c.enShortDesc = getattr(c, "enShortDesc", "")
			new_c.heShortDesc = getattr(c, "heShortDesc", "")
			new_c.save(override_dependencies=True)
		else:
			continue
	for c in subcats:
		if orig[i] in c.lastPath:
			continue
		c.path = [x.replace(orig[i], new[i]) for x in c.path]
		print(c)
		c.save(override_dependencies=True)

library.rebuild(include_toc=True)

for i, cat in enumerate(orig):
	for book in library.get_indexes_in_category(cat, include_dependant=True):
		book = library.get_index(book)
		book.collective_title = new[i]
		for title in book.nodes.title_group.titles:
			if title["lang"] == "en" and orig[i] in title["text"]:
				print("Replacing {}".format(title["text"]))
				title["text"] = title["text"].replace(orig[i], new[i])
		book.nodes.title_group._primary_title = {}
		orig_title = book.get_title('en')
		new_title = book.get_title('en').replace(orig[i], new[i])
		book.set_title(new_title)
		book.key = new_title
		book.categories = [c.replace(orig[i], new[i]) for c in book.categories]
		book.save()
		book.versionState().refresh()

	subcats = CategorySet({"path": cat}).array()
	for c in subcats:
		if orig[i] not in c.lastPath:
			c.delete(force=True)

	for c in subcats:
		if orig[i] in c.lastPath:
			c.delete(force=True)

	assert len(CategorySet({"path": cat}).array()) == 0

for i, cat in enumerate(orig):
	Term().load({"name": orig[i]}).delete()
	t = Term().load({"name": new[i]})
	temp_title = t.get_primary_title('he')
	he_title = " ".join(temp_title.split()[:-1])
	t.add_title(he_title, 'he', True, True)
	t.remove_title(temp_title, 'he')
	t.save()
	library.rebuild(include_toc=True)
