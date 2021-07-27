import django
django.setup()
from sefaria.model import *

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
	he_title = " ".join(t.get_primary_title('he').split()[:-1])
	t.add_title(he_title, 'he', True, True)
	t.save()
	library.rebuild(include_toc=True)


