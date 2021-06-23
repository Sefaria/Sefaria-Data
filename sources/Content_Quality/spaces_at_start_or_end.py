from sources.functions import *
for i in library.get_indexes_in_category("Torah", include_dependant=True):
	if " on " in i:
		i = library.get_index(i)
		for v in i.versionSet():
			for seg in i.all_segment_refs():
				tc = TextChunk(seg, vtitle=v.versionTitle, lang=v.language)

				if tc.text.startswith(" ") or tc.text.endswith(" ") or tc.text.endswith("\n"):
					print("in {}, stripping start and end".format(seg))
					tc.text = tc.text.strip()

				if "  " in tc.text:
					print("in {}, replacing double spaces".format(seg))
					tc.text = tc.text.replace("  ", " ")

				starting = re.search("^(<[a-zA-Z0-9\"\']{1,}>)? ", tc.text)
				if starting: # "<b> hello"
					for pos in starting.regs:
						print("start of {}".format(seg))
						print(tc.text[pos[0]:pos[1]+3])


				middle = re.search(" <[a-zA-Z0-9\"\']{1,}> ", tc.text)
				if middle: # "hello <b> there"
					for pos in middle.regs:
						print("middle of {}".format(seg))
						print(tc.text[pos[0]:pos[1]])

