import os
from sources.functions import *
import time
texts = {}
for dir in os.listdir("."):
	if os.path.isdir(dir):
		en, he, category = dir.split(", ")
		category = ["Responsa"] if category == "Responsa" else ["Talmud", "Bavli", "Commentary"]
		pages = {}
		root = JaggedArrayNode()
		root.add_primary_titles(en, he)
		root.add_structure(["Section", "Paragraph"])
		root.key = en
		root.validate()
		indx = {
			"title": en,
			"categories": category,
			"schema": root.serialize()
		}
		#post_index(indx, server="https://germantalmud.cauldron.sefaria.org")
		for f in os.listdir("./"+dir):
			with open("./"+dir+"/"+f, 'r') as open_f:
				assert "-" in f
				page = f.split("-")[-1].replace(".txt", "")
				while page.startswith("0"):
					page = page[1:]
				page = int(page)
				pages[page] = open_f.readlines()

		send_text = {
			"text": convertDictToArray(pages),
			"versionTitle": "Dicta",
			"versionSource": "https://www.sefaria.org",
			"language": "he"
		}
		print("https://germantalmud.cauldron.sefaria.org/"+en.replace(" ", "_"))
		#post_text(en, send_text, server="https://germantalmud.cauldron.sefaria.org")
		time.sleep(1)