from sources.functions import *
from collections import Counter
import re
# t = Term()
# t.name = "First Essay"
# t.add_primary_titles(t.name, "מאמר א")
# t.save()
# t = Term()
# t.name = "Second Essay"
# t.add_primary_titles(t.name, "מאמר ב")
# t.save()
# t = Term()
# t.name = "Third Essay"
# t.add_primary_titles(t.name, "מאמר ג")
# t.save()
library.get_index("Genesis").contents()
link = {"refs": ["Leviticus 1:1", "Job 1:1-10:1"], "auto": True, "displayedText": {"en": "First Essay", "he": "מאמר א"},
		"versions": [{"title": "Tanakh: The Holy Scriptures, published by JPS", "language": 'en'}, {"title": "ALL", "language": None}], "type": "essay"}
Link(link).save()
link = {"refs": ["Leviticus 1:1", "Job 3"], "auto": True, "displayedText": {"en": "Second Essay", "he": "מאמר ב"},
		"versions": [{"title": "Tanakh: The Holy Scriptures, published by JPS", "language": 'en'}, {"title": "NONE", "language": None}], "type": "essay"}
Link(link).save()
link = {"refs": ["Leviticus 1:1", "Job 3:2-4"], "auto": True, "displayedText": {"en": "Third Essay", "he": "מאמר ג"},
		"versions": [{"title": "Tanakh: The Holy Scriptures, published by JPS", "language": 'en'}, {"title": "Tanakh: The Holy Scriptures, published by JPS", "language": "en"}], "type": "essay"}
Link(link).save()
category = "Prophets"
start_or_end_space = Counter()
double_spaces = Counter()
space_after_tag = Counter()
space_before_and_after_tag = Counter()
examples = {0: [], 1: [], 2: [], 3: []}

def add_to_examples(seg, vtitle, lang, which_one):
	if len(examples[which_one]) < 20:
		examples[which_one].append("{} {} {}".format(seg.normal(), vtitle, lang))

#for i in library.get_indexes_in_category(category, include_dependant=True):
for i in ["Radak on Isaiah", "Ibn Ezra on Isaiah", "Abarbanel on Isaiah"]:
	if " on " in i:
		print(i)
		i = library.get_index(i)
		for v in i.versionSet():
			for seg in i.all_segment_refs():
				tc = TextChunk(seg, vtitle=v.versionTitle, lang=v.language)
				which_one = 0
				if tc.text.startswith(" ") or tc.text.endswith(" ") or tc.text.endswith("\n"):
					start_or_end_space[i.title] += 1
					tc.text = tc.text.strip()
					add_to_examples(seg, v.versionTitle, v.language, which_one)

				which_one += 1
				while "  " in tc.text:
					double_spaces[i.title] += 1
					tc.text = tc.text.replace("  ", " ")
					add_to_examples(seg, v.versionTitle, v.language, which_one)

				which_one += 1
				starting = re.search("^(<[/a-zA-Z0-9\"\']{1,}>) ", tc.text)
				if starting:  # "<b> hello"
					space_after_tag[i.title] += 1
					text_after_tag = tc.text.replace(starting.group(0), "", 1)
					tag = starting.group(1)
					tc.text = tag + text_after_tag
					add_to_examples(seg, v.versionTitle, v.language, which_one)

				which_one += 1
				middle = re.search(" (<[/a-zA-Z0-9\"\']{1,}>) ", tc.text)
				if middle:  # "hello <b> there"
					space_before_and_after_tag[i.title] += 1
					tag = middle.group(1)
					tc.text = tc.text.replace(" {} ".format(tag), " {}".format(tag))
					add_to_examples(seg, v.versionTitle, v.language, which_one)
				tc.save(force_save=True)


which_one = 0
print("Starting or ending space examples")
for i in examples[which_one]:
	print(i)
print(start_or_end_space.most_common(20))

which_one = 1
print("Double spaces in middle of text examples")
for i in examples[which_one]:
	print(i)
print(double_spaces.most_common(20))

which_one = 2
print("Space after tag examples")
for i in examples[which_one]:
	print(i)
print(space_after_tag.most_common(20))


which_one = 3
print("Space before and after tag examples")
for i in examples[which_one]:
	print(i)
print(space_before_and_after_tag.most_common(20))

