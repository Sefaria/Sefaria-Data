from sources.functions import *
text = {}
links = []
root = SchemaNode()
root.add_primary_titles("Maskil LeDavid", "משכיל לדוד")
root.key = "Maskil LeDavid"
intro = JaggedArrayNode()
intro.add_shared_term("Introduction")
intro.key = "Introduction"
intro.add_structure(["Paragraph"])
root.append(intro)
base_text_titles = []
with open("whole_Torah_linked_-_whole_Torah.csv", 'r') as f:
	for row in csv.reader(f):
		ref, comm, link = row
		perek, pasuk, para = ref.split()[-1].split(":")
		perek = int(perek)
		pasuk = int(pasuk)
		para = int(para)
		book = ref.split()[-2]
		if book not in text:
			base_text_titles.append("Rashi on {}".format(book))
			node = JaggedArrayNode()
			he_book = library.get_index(book).get_title('he')
			node.add_primary_titles(book, he_book)
			node.key = book
			node.add_structure(["Chapter", "Verse", "Paragraph"])
			node.validate()
			root.append(node)
			text[book] = {}
		if perek not in text[book]:
			text[book][perek] = {}
		if pasuk not in text[book][perek]:
			text[book][perek][pasuk] = []
		text[book][perek][pasuk].append(comm)
		links.append({"refs": [ref, link], "generated_by": "maskil_ledavid_linker", "type": "Commentary", "auto": True})
		base_ref = link.replace("Rashi on ", "")
		if base_ref.find(":") != base_ref.rfind(":"):
			base_ref = ":".join(base_ref.split(":")[:-1])
		links.append({"refs": [ref, base_ref], "generated_by": "maskil_ledavid_linker", "type": "Commentary", "auto": True})

root.validate()
indx = {
	'categories': ["Tanakh", "Acharonim on Tanakh"],
	'schema': root.serialize(),
	'title': root.key,
	'dependence': 'Commentary',
	'collective_title': root.key,
	'base_text_titles': base_text_titles
}
#post_index(indx, server="https://germantalmud.cauldron.sefaria.org")
versionTitle = "Venice, 1761"
versionSource = "https://www.nli.org.il/he/books/NNL_ALEPH002043467/NLI"
# t = Term()
# t.name = "Maskil LeDavid"
# t.add_primary_titles("Maskil LeDavid", "משכיל לדוד")
# t.save()
# post_term(t.contents(), server="https://germantalmud.cauldron.sefaria.org")
for book in text:
	for perek in text[book]:
		text[book][perek] = convertDictToArray(text[book][perek])
	text[book] = convertDictToArray(text[book])
	send_text = {
		"language": "he",
		"versionSource": versionSource,
		"versionTitle": versionTitle,
		"text": text[book]
	}
	#post_text("Maskil LeDavid, {}".format(book), send_text, server="https://germantalmud.cauldron.sefaria.org")
post_link_in_steps(links, sleep_amt=30, step=500, server="https://www.sefaria.org")