from sources.functions import *




bad_refs = {"opensiddur": ["Psalms 107-150", "Psalms 1-41", "Psalms 90-106",
			"Psalms 42-72", "Psalms 73-89", "Psalms 19:13", "Psalms 90:17"],
			"yeshiva.co": ["Genesis 24:2-9", "Proverbs 23:5"],
			"jewishstandard": ["Leviticus 20:13"],
			"kabbalahoftime": ["Psalms 139-141", "Psalms 89", "Psalms 16-18", "Psalms 139:1"]}

for regex in bad_refs:
	print(regex)
	for ref in bad_refs[regex]:
		print(ref)
		ws = WebPageSet({"refs": ref, "url": {"$regex": regex}})
		print(ws.count())
		ws.delete()
