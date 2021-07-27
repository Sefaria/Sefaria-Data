from sources.functions import *
from sources.Kereti.i_tags_tiferet import *
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
	mb_url = siman_url.replace(".html", "")+"_mishna.html"
	beur_url = siman_url.replace(".html", "")+"_beur.html"
	mb_soup = BeautifulSoup(selenium_get_url(driver, mb_url))
	beur_soup = BeautifulSoup(selenium_get_url(driver, beur_url))

	mb_text = {}
	beur_text = {}
	siman = ""
	seif = 0
	for title, soup, text in [("mb", mb_soup.find_all("p"), mb_text), ("beur", beur_soup.find_all("p"), beur_text)]:
		for p in soup:
			if p.text.strip() != "":
				if isinstance(p.previousSibling, NavigableString) and p.previousSibling != "" and p.previousSibling.strip().count(" ") == 3 and "סימן" in p.previousSibling:
					siman = getGematria(p.previousSibling.replace("ביאור הלכה סימן ", "").replace("משנה ברורה סימן ", "").strip())
					seif = 0
					text[siman] = {}
				elif (isinstance(p, Tag) and p.text.strip().count(" ") == 3 and "סימן" in p.text):
					siman = getGematria(p.text.replace("ביאור הלכה סימן ", "").replace("משנה ברורה סימן ", "").strip())
					seif = 0
					text[siman] = {}
				elif re.search("^\(.{,2}\)", p.text):
					seif_text = re.search("^(\(.{,2}\))", p.text).group(0)
					seif = getGematria(seif_text)
					text[siman][seif] = str(p).replace(seif_text, "").strip().replace("<p>", "").replace("</p>", "").strip()
				elif isinstance(p, NavigableString) or p.text.replace("=", "").strip() != "":
					seif += 1
					text[siman][seif] = str(p).replace("<p>", "").replace("</p>", "").strip()
		with open("Mishnah Berurah/"+siman_url.split("/")[-1].replace(".html", "")+"_{}".format(title)+".json", 'w') as open_f:
			json.dump(text, open_f)

	txt = {}
	siman = ""
	seif = ""
	# for x in sa_soup.find_all("div", {"style": "text-align: right;"})[0].contents:
	# 	x_text = x.text if isinstance(x, Tag) else x
	# 	x_text = x_text.replace("\xa0", "").strip()
	# 	if len(x_text.strip()) > 0:
	# 		if re.search("^סימן .{1,5} -", x_text):
	# 			siman = getGematria(x_text.split(" - ")[0].replace("סימן ", "").strip())
	# 			txt[siman] = {}
	# 			seif = ""
	# 		elif x.name == "b" and re.search("^.{1,4}\.$", x.text.strip()):
	# 			seif = getGematria(x.text.strip())
	# 			txt[siman][seif] = []
	# 		elif seif != "":
	# 			if isinstance(x, Tag):
	# 				assert x.name == "a"
	# 				if "mishna" in x.attrs["href"]:
	# 					mb_text[siman][seif]
	# 				elif "beur" in x.attrs["href"]:
	# 					pass
	# 				else:
	# 					raise Exception
	# 				txt[siman][seif].append(x)
	# 			elif isinstance(x, NavigableString):
	# 				txt[siman][seif].append(x)
	# pass


for siman in get_simanim():
	get_seifim(siman)
