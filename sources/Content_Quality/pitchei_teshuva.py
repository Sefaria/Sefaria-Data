from sources.functions import *
from sefaria.model.webpage import *
from sefaria.helper.link import *
rebuild_links_from_text("Shabbat", 1)
server = "https://germantalmud.cauldron.sefaria.org"
for i in range(5):
	root = JaggedArrayNode()
	root.key = "asdf"+str(i)
	he_title = u"שד"
	he_title += numToHeb(i+1)
	root.add_primary_titles(root.key, he_title)
	root.add_structure(["Chapter", "Paragraph"])
	root.validate()
	indx = {
		"title": root.key,
		"categories": ["Jewish Thought", "Rishonim"],
		"schema": root.serialize()
	}
	post_index(indx, server=server)
	send_text = {
		"language": 'en',
		"text": [['hi'], ['bye', 'f']],
		"versionTitle": "asdf",
		"versionSource": "https://www.sefaria.org"
	}
	post_text(root.key, send_text, server=server)
# print(Ref("Zohar").as_ranged_segment_ref())
# print(Ref("Berakhot").as_ranged_segment_ref())
# print(Ref("Genesis 1").as_ranged_segment_ref())
# print(Ref("Genesis").as_ranged_segment_ref())
# print(Ref("Berakhot 4a").as_ranged_segment_ref())
# print(Ref("Zohar 2").as_ranged_segment_ref())
# titles = ["Choshen Mishpat", "Even HaEzer", "Yoreh De'ah"]
# for t in titles:
# 	indx = get_index_api("Pitchei Teshuva on Shulchan Arukh, {}".format(t))
# 	newStruct = []
# 	for node in indx["alt_structs"]["Topic"]["nodes"]:
# 		node["wholeRef"] = node["wholeRef"].replace("Pithei Teshuva", "Pitchei Teshuva")
# 		newStruct.append(node)
# 	indx["alt_structs"]["Topic"]["nodes"] = newStruct
# 	post_index(indx, server="https://www.sefaria.org")