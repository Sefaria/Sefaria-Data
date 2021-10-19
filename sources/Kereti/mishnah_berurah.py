from sources.functions import *
from sources.Kereti.i_tags import *
import json
def i_tags():
	tiferet = get_kereti_dhs_in_mechaber(["Tiferet Yisrael/Base Text.txt"])

	all_dhs = get_kereti_tags(title, tiferet)
	# create_new_tags("", default, all_dhs, change_nothing=True)
	create_new_tags("CHIDDUSHEI", default, all_dhs, change_nothing=False)

driver = "/Users/stevenkaplan/Downloads/chromedriver"
def get_simanim():
	soup = BeautifulSoup(selenium_get_url("/Users/stevenkaplan/Downloads/chromedriver", "http://mishnaberura.eu5.org/menu.html"))
	a_tags = soup.find_all("a")
	return ["http://mishnaberura.eu5.org/"+a.attrs["href"] for a in a_tags]

def get_seifim(siman_url):
	sa_soup = BeautifulSoup(selenium_get_url(driver, siman_url))
	# mb_url = siman_url.replace(".html", "")+"_mishna.html"
	# beur_url = siman_url.replace(".html", "")+"_beur.html"
	# mb_soup = BeautifulSoup(selenium_get_url(driver, mb_url))
	# beur_soup = BeautifulSoup(selenium_get_url(driver, beur_url))
	#
	# mb_text = {}
	# beur_text = {}
	# siman = ""
	# seif = 0
	# for title, soup, text in [("mb", mb_soup.find_all("p"), mb_text), ("beur", beur_soup.find_all("p"), beur_text)]:
	# 	for p in soup:
	# 		if p.text.strip() != "":
	# 			if isinstance(p.previousSibling, NavigableString) and p.previousSibling != "" and p.previousSibling.strip().count(" ") == 3 and "סימן" in p.previousSibling:
	# 				siman = getGematria(p.previousSibling.replace("ביאור הלכה סימן ", "").replace("משנה ברורה סימן ", "").strip())
	# 				seif = 0
	# 				text[siman] = {}
	# 			elif (isinstance(p, Tag) and p.text.strip().count(" ") == 3 and "סימן" in p.text):
	# 				siman = getGematria(p.text.replace("ביאור הלכה סימן ", "").replace("משנה ברורה סימן ", "").strip())
	# 				seif = 0
	# 				text[siman] = {}
	# 			elif re.search("^\(.{,2}\)", p.text):
	# 				seif_text = re.search("^(\(.{,2}\))", p.text).group(0)
	# 				seif = getGematria(seif_text)
	# 				text[siman][seif] = str(p).replace(seif_text, "").strip().replace("<p>", "").replace("</p>", "").strip()
	# 			elif isinstance(p, NavigableString) or p.text.replace("=", "").strip() != "":
	# 				seif += 1
	# 				text[siman][seif] = str(p).replace("<p>", "").replace("</p>", "").strip()
	# 	with open("Mishnah Berurah/"+siman_url.split("/")[-1].replace(".html", "")+"_{}".format(title)+".json", 'w') as open_f:
	# 		json.dump(text, open_f)

	txt = {}
	siman = ""
	seif = ""
	for x in sa_soup.find_all("div", {"style": "text-align: right;"})[0].contents:
		x_text = x.text if isinstance(x, Tag) else x
		x_text = x_text.replace("\xa0", "").strip()
		if len(x_text.strip()) > 0:
			if re.search("^סימן .{1,5} -", x_text):
				siman = getGematria(x_text.split(" - ")[0].replace("סימן ", "").strip())
				txt[siman] = {}
				seif = ""
			elif x.name == "b" and re.search("^.{1,4}\.$", x.text.strip()):
				seif = getGematria(x.text.strip())
				txt[siman][seif] = ""
			elif seif != "":
				if isinstance(x, Tag):
					if x.name == "a":
						if "mishna" in x.attrs["href"]:
							txt[siman][seif] += "{}{}{}".format("MB", x.text.strip(), "MB") + " "
						elif "beur" in x.attrs["href"]:
							txt[siman][seif] += "{}{}{}".format("BH", x.text.strip(), "BH") + " "
						else:
							raise Exception
					else:
						txt[siman][seif] += str(x) + " "
				elif isinstance(x, NavigableString):
					txt[siman][seif] += x.strip() + " "

	with open("Mishnah Berurah/"+siman_url.split("/")[-1].replace(".html", "")+"_base.json", 'w') as open_f:
		json.dump(txt, open_f)


#
# for siman in get_simanim()[:-1]:
# 	get_seifim(siman)
# #
base = {}
MB_comm = {}
BH_comm = {}
for f in os.listdir("Mishnah Berurah"):
	if f.endswith("json") and "_mb" in f:
		with open("Mishnah Berurah/"+f) as open_f:
			MB_comm.update(json.load(open_f))
	if f.endswith("json") and "_beur" in f:
		with open("Mishnah Berurah/"+f) as open_f:
			BH_comm.update(json.load(open_f))
	if f.endswith("json") and "base" in f:
		with open("Mishnah Berurah/"+f, 'r') as open_f:
			base.update(json.load(open_f))

with open("MB.csv", 'w') as f:
	writer = csv.writer(f)
	for ch in sorted([int(x) for x in MB_comm.keys()]):
		for pasuk in MB_comm[str(ch)]:
			writer.writerow(["Mishnah Berurah {}:{}".format(ch, pasuk), MB_comm[str(ch)][pasuk]])

with open("SA.csv", 'w') as f:
	writer = csv.writer(f)
	for ch in sorted([int(x) for x in base.keys()]):
		for pasuk in base[str(ch)]:
			writer.writerow(["Shulchan Arukh, Orach Chayim {}:{}".format(ch, pasuk), base[str(ch)][pasuk]])


MB = {}
BH = {}
new_base = {}
for sec in base:
	new_base[int(sec)] = {}
	for seg in base[sec]:
		new_base[int(sec)][int(seg)] = base[sec][seg]

base = new_base
for sec in sorted(base.keys()):
	base_sec_ref = Ref("Shulchan Arukh, Orach Chayim {}".format(sec))
	assert base_sec_ref.text('he').text != []
	if len(base_sec_ref.all_segment_refs()) != len(base[sec]):
		print("Siman {}".format(sec))
		print("Our Shulchan Arukh has {} comments but http://mishnaberura.eu5.org/ has {} comments\n".format(len(base_sec_ref.all_segment_refs()), len(base[sec])))
	our_BH = Ref("Biur Halacha {}".format(sec))
	our_MB = Ref("Mishnah Berurah {}".format(sec))
	if sec in MB_comm:
		if len(our_MB.all_segment_refs()) != len(MB_comm[sec]):
			print("Siman {}".format(sec))
			print("MB comm: {} vs {}".format(len(our_MB.all_segment_refs()), len(MB_comm[sec])))
	if sec in BH_comm:
		if len(our_BH.all_segment_refs()) != len(BH_comm[sec]):
			print("Siman {}".format(sec))
			print("BH comm: {} vs {}".format(len(our_BH.all_segment_refs()), len(BH_comm[sec])))

	MB[int(sec)] = {}
	BH[int(sec)] = {}
	our_BH = Ref("Biur Halacha {}".format(sec))
	our_MB = Ref("Mishnah Berurah {}".format(sec))
	MB_tags = 0
	BH_tags = 0
	for seg in base[sec]:
		MB_base_text = re.sub("BH.*?BH", "", base[sec][seg]).replace("  ", " ")
		BH_base_text = re.sub("MB.*?MB", "", base[sec][seg]).replace("  ", " ")
		chars = ["$", "!", ".", ":", ",", ")", "("]
		for char in chars:
			MB_base_text = MB_base_text.replace(char, "")
			BH_base_text = BH_base_text.replace(char, "")
		MB_tags += len(re.split("MB.*?MB", MB_base_text.strip())) - 1
		BH_tags += len(re.split("BH.*?BH", BH_base_text.strip())) - 1
		curr_MB = [" ".join(dh.split()[:6]) for dh in re.split("MB.*?MB", MB_base_text.strip())][1:]
		curr_BH = [" ".join(dh.split()[:6]) for dh in re.split("BH.*?BH", BH_base_text.strip())][1:]
		for i, item in enumerate(curr_MB):
			if item == "":
				curr_MB[i] = curr_MB[i+1]
		for i, item in enumerate(curr_BH):
			if item == "":
				curr_BH[i] = curr_BH[i+1]
		MB[sec][seg] = curr_MB
		BH[sec][seg] = curr_BH
	if MB_tags != len(our_MB.all_segment_refs()):
		print("Siman {}".format(sec))
		print("Mishnah Berurah: EU5 has {} tags, but our text has {} comments\n".format(MB_tags, len(our_MB.all_segment_refs())))
	if BH_tags != len(our_BH.all_segment_refs()):
		print("Siman {}".format(sec))
		print("Beur Halacha: EU5 has {} tags, but our text has {} comments\n".format(BH_tags, len(our_BH.all_segment_refs())))

#MB_dhs = get_kereti_tags("Mishnah Berurah", MB)
# BH_dhs = get_kereti_tags("Be'ur Halakhah", BH)
#create_new_tags("whatever", "Maginei Eretz: Shulchan Aruch Orach Chaim, Lemberg, 1893", MB_dhs, change_nothing=False)