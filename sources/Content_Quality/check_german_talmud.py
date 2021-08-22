from sources.functions import *

titles = library.get_indexes_in_category("Bavli")
for t in titles:
	found = False
	for v in library.get_index(t).versionSet():
		if "[de]" in v.versionTitle:
			found = True
			if len(str(v.contents()["chapter"])) < 2000:
				print(t)
				print(v)
