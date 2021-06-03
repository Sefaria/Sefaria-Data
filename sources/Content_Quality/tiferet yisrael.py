from sources.functions import *
version_info = """Index Title,"Tiferet Yisrael on Shulchan Arukh, Yoreh De'ah"
Version Title,"Ashlei Ravrevei: Shulchan Aruch Yoreh Deah, Lemberg, 1888"
Language,he
Version Source,http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002097765
Version Notes,""".splitlines()
root = JaggedArrayNode()
root.add_primary_titles("Tiferet Yisrael on Shulchan Arukh, Yoreh De'ah", "תפארת ישראל על שולחן ערוך יורה דעה")
root.key = "Tiferet Yisrael on Shulchan Arukh, Yoreh De'ah"
root.add_structure(["Siman", "Seif"])
indx = {
	"title": root.key,
	"categories": ["Halakhah", "Shulchan Arukh", "Commentary", "Tiferet Yisrael"],
	"schema": root.serialize(),
	"dependence": "Commentary",
	"base_text_titles": ["Shulchan Arukh, Yoreh De'ah"],
	"collective_title": "Tiferet Yisrael"
}
post_index(indx, server="https://arukhtanakh.cauldron.sefaria.org")
links = []
with open("Tiferet_new.csv", 'w') as new_f:
	writer = csv.writer(new_f)
	for x in version_info:
		writer.writerow(x.split(","))
	with open("Tiferet_Yisrael_-_to_parse.csv", 'r') as f:
		for row in list(csv.reader(f))[1:]:
			ref, comm, link = row
			links.append({"generated_by": "tiferetyisrael", "refs": [ref, link], "type": "Commentary", "auto": True})
			writer.writerow([ref, comm])

post_link(links, server="https://arukhtanakh.cauldron.sefaria.org")
