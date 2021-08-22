from sources.functions import *


for i in ["Derekh Chayim", "Ohr Chadash"]+library.get_indexes_in_category("Maharal"):
	vtitle = ""
	i = library.get_index(i)

	for v in i.versionSet():
		if "footnotes and annotations" in v.versionTitle:
			vtitle = v.versionTitle

	if vtitle != "":
		refs = i.all_segment_refs()
		for ref in refs:
			tc = TextChunk(ref, lang='he', vtitle=vtitle)
			if "Footnotes and Annotations" in tc.text:
				print(ref)
				tc.text = tc.text.replace("Footnotes and Annotations", "Notes by Rabbi Yehoshua Hartman")
				tc.save(force_save=True)
