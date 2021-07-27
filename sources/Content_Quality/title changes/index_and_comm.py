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
		if getattr(comm, "base_text_titles", None) and old_title in comm.base_text_titles:
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