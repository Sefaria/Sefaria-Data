from bs4 import BeautifulSoup, Tag
import csv
text_dict = {}
with open("Return 14 draft 14 balanced.html", 'r') as f:
	soup = BeautifulSoup(f)
	footnotes_text = soup.find_all(class_="Endnotes")
	footnotes_sup = soup.find_all(class_="footnote-refe _idGenCharOverride-1")
	zipped = zip(footnotes_sup, footnotes_text)
	for i, zipped_tuple in enumerate(zipped):
		print(i)
		sup, text = zipped_tuple
		assert text.text.startswith(sup.text+".\t")
		i_tag = '<sup>{}</sup><i class="footnotes">{}</i>'.format(sup.text, text.text.replace(sup.text+".\t", ""))
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
		while p and p.get("class", "") != ["Chapter-Style"]:
			if isinstance(p, Tag) and p.get("class", "") != ["Endnotes"]:
				text_dict[title].append(p.text)
			p = p.next_sibling
			while p and not isinstance(p, Tag):
				p = p.next_sibling

with open("return.csv", 'w') as f:
	writer = csv.writer(f)
	for title in text_dict:
		for i, p in enumerate(text_dict[title]):
			writer.writerow(["{} {}".format(title, i+1), p])