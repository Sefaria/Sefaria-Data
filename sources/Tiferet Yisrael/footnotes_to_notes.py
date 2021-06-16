import django
django.setup()
from sefaria.model import *
new_name = """פירושים והערות מהרב יהושע הרטמן \ Notes by R Yehoshua Hartman"""
he_term, en_term = new_name.split(" \ ")
t = Term()
t.name = en_term
t.add_primary_titles(t.name, he_term)
if Term().load({"name": t.name}) is None:
	t.save()
for i in library.get_indices_by_collective_title("Footnotes and Annotations"):
	print(i)
	i = library.get_index(i)
	i.collective_title = en_term
	orig_en, orig_he = i.title, i.get_title('he')
	new_he = orig_he.replace("הערות ומקורות", he_term)
	new_en = orig_en.replace("Footnotes and Annotations", en_term)
	print(new_en)
	print(new_he)
	i.set_title(new_he, 'he')
	i.set_title(new_en, 'en')
	i.save()

ls = LinkSet({"refs": {"$regex": "^Notes by R Yehoshua Hartman"}})
count = 0
for l in ls:
	if getattr(l, "inline_reference", False):
		count += 1
		if count % 500 == 0:
			print(count)
		l.inline_reference = "Notes by R Yehoshua Hartman"
		l.save()