import django
django.setup()
from sefaria.model import *

rambam_paths = [p.full_path[-1] for p in Category().load({"path": ["Halakhah", "Mishneh Torah"]}).get_toc_object().children[1:-1]]
rambam_paths = rambam_paths[:6]
lechem_path = ["Halakhah", "Mishneh Torah", "Commentary", "Lechem Mishneh"]
if Term().load({"name": "Lechem Mishneh"}) is None:
	t = Term()
	t.name = "Lechem Mishneh"
	t.add_primary_titles(t.name, "לחם משנה ב")
	t.save()
	if Category().load({"path": ["Halakhah", "Mishneh Torah", "Commentary", "Lechem Mishneh"]}) is None:
		c = Category()
		c.add_shared_term("Lechem Mishneh")
		c.path = lechem_path
		c.save()
		for rambam_path in rambam_paths:
			new_c = Category()
			new_c.path = lechem_path + [rambam_path]
			new_c.add_shared_term(rambam_path)
			new_c.save()


indices = library.get_indices_by_collective_title("Lehem Mishneh")
for i in indices:
	print(i)
	i = library.get_index(i)
	curr_title = i.title
	new_title = curr_title.replace("Lehem", "Lechem")
	i.set_title(new_title)
	i.collective_title = "Lechem Mishneh"
	assert i.categories[-1] != "Lehem Mishneh" and i.categories[-2] == "Lehem Mishneh"
	i.categories[-2] = "Lechem Mishneh"
	i.save()
	i.versionState().refresh()



c = Category().load({"path": ["Halakhah", "Mishneh Torah", "Commentary", "Lehem Mishneh"]})
if c:
	for child in c.get_toc_object().children:
		Category().load({"path": child.full_path}).delete(force=True)
	c.delete(force=True)
	t = Term().load({"name": "Lehem Mishneh"})
	if t:
		t.delete()
t = Term().load({"name": "Lechem Mishneh"})
t.add_title("לחם משנה", 'he', True, True)
t.save()