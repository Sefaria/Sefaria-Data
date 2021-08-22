from bs4 import BeautifulSoup, Tag
import csv
import re
import bleach
text_dict = {}
html_set = set()
file = "LeadershipintheWilderness 07 draft 07 balanced.html"
with open(file, 'r') as f:
	soup = BeautifulSoup(f)
	footnotes_text = soup.find_all(class_="Footnote-Text")
	footnotes_sup = soup.find_all(class_="footnote-refe _idGenCharOverride-1")
	zipped = zip(footnotes_sup, footnotes_text)
	for i, zipped_tuple in enumerate(zipped):
		sup, text = zipped_tuple
		sup.string = sup.text.strip()
		assert text.text.startswith(sup.text+".\t")
		i_tag = '<sup>{}</sup><i class="footnote">{}</i>'.format(sup.text, text.text.replace(sup.text+".\t", ""))
		sup.string = i_tag
	chapters = soup.find_all(class_="Chapter-Style")[1:]
	for p in chapters:
		title = p.text
		p = p.next_sibling
		while not isinstance(p, Tag):
			p = p.next_sibling

		if isinstance(p, Tag) and p.get("class", "") == ["Chapter-Title"]:
			title += ": {}".format(p.text)
			p = p.next_sibling
			if not isinstance(p, Tag):
				p = p.next_sibling


		text_dict[title] = []
		found_notes = False
		while p and p.get("class", "") != ["Chapter-Style"]:
			if isinstance(p, Tag) and p.get("class", "") != ["Footnote-Text"]:
				if p.text.strip() == "Notes":
					found_notes = True
				if not found_notes:
					orig_p = p
					if p.name == "ul":
						p_arr += [subp for subp in p.contents if isinstance(subp, Tag) and subp.name in ["p", "li"]]
					elif p.name == "table":
						p = p.find("td")
						orig_p_arr = [subp for subp in p.contents if isinstance(subp, Tag) and subp.name in ["p", "ul"]]
						p_arr = []
						for p in orig_p_arr:
							if p.name == "ul":
								p_arr += [subp for subp in p.contents if isinstance(subp, Tag) and subp.name in ["p", "li"]]
							else:
								p_arr.append(p)
					elif p.name == "p":
						p_arr = [p]
						orig_p = p
					else:
						p = p.next_sibling
						p_arr = []
						orig_p = p
					for p in p_arr:
						assert p.name in ["p", "li"]
						p_text = str(p)
						p_text = re.sub('<span class="(it-text|_80-italic)">(.*?)</span>', '<i>\g<2></i>', p_text)
						p_text = re.sub('<span class="it-text-bold">(.*?)</span>', '<b>\g<1></b>', p_text)
						if "class" in p.attrs and "sub-" in p["class"][0]:
							p_text = "<b>"+p_text+"</b>"
						p_text = p_text.replace("&lt;", "<").replace("&gt;", ">").replace('<li class="bullet-first">', "• ").replace('<li class="bullets">', '<br/>• ')
						p_text = bleach.clean(p_text, strip=True, tags=["b", "i", "sup"], attributes=["class"])
						text_dict[title].append(p_text)
			p = p.next_sibling if len(p_arr) <= 1 else orig_p.next_sibling
			p_arr = []
			while p and not isinstance(p, Tag):
				p = p.next_sibling

with open("{}.csv".format(file.split()[0]), 'w') as f:
	writer = csv.writer(f)
	for title in text_dict:
		for i, p in enumerate(text_dict[title]):
			writer.writerow(["{} {}".format(title, i+1), p])

print(html_set)