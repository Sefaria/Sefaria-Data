from sources.functions import *

for v in VersionSet({"versionTitle": 'Steinsaltz Mishneh Torah'}):
    v.versionTitle = "Mishneh Torah with Commentary by Rabbi Adin Even-Israel Steinsaltz, Koren Publishers"
    v.purchaseInformationImage = "https://korenpub.com/cdn/shop/products/mishneh_torah_hc_set_web_1_600x.jpg?v=1574183896"
    v.purchaseInformationURL = "https://korenpub.com/products/rambam-mishneh-torah-sethardcover"
    v.license = "CC-BY-NC"
    v.status = "locked"
    print(v)
    #v.save()
    """ "purchaseInformationImage",
"purchaseInformationURL",
"license",
"status","""

with open('steinsaltz_rambam - section.csv') as f:
    section = list(csv.DictReader(f))

text_dict = {}
for sec in section:
    title = sec['name_eng']
    text = sec['intro']
    if text != "NULL":
        text_dict[(title, sec['name'])] = text
root = SchemaNode()
root.add_primary_titles("Steinsaltz Introduction to Mishneh Torah", "")
for node, he_node in text_dict:
    n = JaggedArrayNode()
    n.add_primary_titles(node, he_node)
    n.key = node
    n.validate()