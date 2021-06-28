from sources.functions import *
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
from bs4 import BeautifulSoup, Tag
import os
import time

def rambam_pages(driver):
	stopped_at_book = "Mishneh Torah, The Sanhedrin and the Penalties within their Jurisdiction"
	stopped_at_perek = 24
	stopped_at_pasuk = 2
	start = False
	cats = ["Sefer Madda", "Sefer Ahavah", "Sefer Zemanim", "Sefer Nashim", "Sefer Kedushah", "Sefer Haflaah", "Sefer Zeraim", "Sefer Avodah", "Sefer Korbanot", "Sefer Taharah", "Sefer Nezikim", "Sefer Kinyan", "Sefer Mishpatim", "Sefer Shoftim"]
	total_books = -1
	for c, cat in enumerate(cats):
		for b, book in enumerate(library.get_indexes_in_category(cat)):
			if c > 6 and library.get_index(book) in books:
				perek_pasuk = []
				for seg in library.get_index(book).all_segment_refs():
					perek_pasuk.append(seg.sections)
				for perek, pasuk in perek_pasuk:
					url = "https://www.hebrewbooks.org/rambam.aspx?sefer={}&hilchos={}&perek={}&halocha={}".format(c+1, total_books+1, perek, pasuk)
					if stopped_at_book == book and stopped_at_pasuk == pasuk and stopped_at_perek == perek:
						start = True
						print("STARTING...")
					if start:
						driver.get(url)
						pageSource = driver.page_source
						fileToWrite = open("hebrew books/{} {},{}.html".format(book, perek, pasuk), "w")
						fileToWrite.write(pageSource)
						fileToWrite.close()
			total_books += 1
	driver.quit()

def lechem_pages(driver):
	deleted = 0
	lechem_pages_dict = {}
	for f in os.listdir("hebrew books/"):
		if f.endswith("html"):
			book = " ".join(f.split()[:-1])
			perek_pasuk = f.split()[-1].replace(".html", "")
			perek_pasuk = perek_pasuk.replace(',', ":")
			perek, pasuk = perek_pasuk.split(":")
			perek = int(perek)
			pasuk = int(pasuk)
			if book not in lechem_pages_dict:
				lechem_pages_dict[book] = {}
			if perek not in lechem_pages_dict[book]:
				lechem_pages_dict[book][perek] = {}
			if f.endswith("html"):
				delete = True
				soup = BeautifulSoup(open("hebrew books/"+f))
				a_tags = soup.find_all("a")
				for a_tag in a_tags:
					if a_tag.text == "לחם משנה":
						delete = False
						lechem_pages_dict[book][perek][pasuk] = "http://hebrewbooks.org/"+a_tag["href"]
				if delete:
					os.remove("hebrew books/"+f)
					deleted += 1
	print(deleted)
	return lechem_pages_dict


books = [Index().load({'title': 'Mishneh Torah, Sacrificial Procedure'}),
 Index().load({'title': 'Mishneh Torah, Sacrifices Rendered Unfit'}),
 Index().load({'title': 'Mishneh Torah, Paschal Offering'}),
 Index().load({'title': 'Mishneh Torah, Festival Offering'}),
 Index().load({'title': 'Mishneh Torah, Offerings for Unintentional Transgressions'}),
 Index().load({'title': 'Mishneh Torah, Offerings for Those with Incomplete Atonement'}),
 Index().load({'title': 'Mishneh Torah, Substitution'}),
 Index().load({'title': 'Mishneh Torah, Damages to Property'}),
 Index().load({'title': 'Mishneh Torah, Theft'}),
 Index().load({'title': 'Mishneh Torah, One Who Injures a Person or Property'}),
 Index().load({'title': 'Mishneh Torah, Sales'}),
 Index().load({'title': 'Mishneh Torah, Neighbors'}),
 Index().load({'title': 'Mishneh Torah, Agents and Partners'}),
 Index().load({'title': 'Mishneh Torah, Slaves'}),
 Index().load({'title': 'Mishneh Torah, Hiring'}),
 Index().load({'title': 'Mishneh Torah, Plaintiff and Defendant'}),
 Index().load({'title': 'Mishneh Torah, Inheritances'}),
 Index().load({'title': 'Mishneh Torah, The Sanhedrin and the Penalties within their Jurisdiction'}),
 Index().load({'title': 'Mishneh Torah, Testimony'}),
 Index().load({'title': 'Mishneh Torah, Rebels'}),
 Index().load({'title': 'Mishneh Torah, Mourning'}),
 Index().load({'title': 'Mishneh Torah, Kings and Wars'})]


chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome("/Users/stevenkaplan/Downloads/chromedriver", chrome_options=chrome_options)

# rambam_pages(driver)

#lechem_URL_dict = lechem_pages(driver)
#json.dump(lechem_URL_dict, open("lechem_pages_sanhedrin_onward.json", 'w'))
# before_sanhedrin = json.load(open("lechem mishneh/lechem_pages_up_to_sanhedrin.json", 'r'))
# after_sanhedrin = json.load(open("lechem mishneh/lechem_pages_sanhedrin_onward.json", 'r'))
# before_sanhedrin.update(after_sanhedrin)
# for book in before_sanhedrin:
# 	for perek in before_sanhedrin[book]:
# 		for pasuk in before_sanhedrin[book][perek]:
# 			print(pasuk)
# 			url = before_sanhedrin[book][perek][pasuk]
# 			source = selenium_get_url(driver, url)
# 			with open("lechem mishneh html/{} {} {}.html".format(book, perek, pasuk), 'w') as f:
# 				f.write(source)
text_dict = {}
for f in os.listdir("lechem mishneh html"):
	perek = int(f.split()[-2])
	pasuk = int(f.split()[-1].replace('.html', ''))
	book = " ".join(f.split()[:-2])
	if book not in text_dict:
		text_dict[book] = {}
	if perek not in text_dict[book]:
		text_dict[book][perek] = {}
	text_dict[book][perek][pasuk] = []
	orig = f
	with open("lechem mishneh html/"+f, 'r') as f:
		soup = BeautifulSoup(f)
		el = soup.find(class_="peirush")
		for i, line in enumerate(el.contents):
			line_text = line.text if isinstance(line, Tag) else str(line)
			if isinstance(line, Tag) and line.get('class', None) in [["five"], ["four"]]:
				text_dict[book][perek][pasuk].append("<b>{}</b>".format(line_text))
				continue
			elif isinstance(line, Tag) and line.get('class', False) != False:
					text_dict[book][perek][pasuk].append(line_text)
			elif line_text.strip() != "":
				if len(text_dict[book][perek][pasuk]) == 0:
					print(orig)
					text_dict[book][perek][pasuk].append(line_text)
				else:
					text_dict[book][perek][pasuk][-1] += line_text

for book in text_dict:
	root = JaggedArrayNode()
	index = library.get_index(book)
	subcat = index.categories[-1]
	book_he = index.get_title('he')
	root.add_primary_titles("Lechem Mishneh on {}".format(book), "לחם משנה על {}".format(book_he))
	root.key = "Lechem Mishneh on {}".format(book)
	root.add_structure(["Chapter", "Halakhah", "Paragraph"])
	root.validate()
	indx = {
		"schema": root.serialize(),
		"dependence": "Commentary",
		"base_text_titles": [book],
		"base_text_mapping": "many_to_one",
		"title": "Lechem Mishneh on {}".format(book),
		"categories": ["Halakhah", "Mishneh Torah", "Commentary", "Lechem Mishneh", subcat],
		"collective_title": "Lechem Mishneh"
	}
	add_category(subcat, indx["categories"], server="https://resetwebsites.cauldron.sefaria.org")
	post_index(indx, server="https://resetwebsites.cauldron.sefaria.org")
	for perek in text_dict[book]:
		text_dict[book][perek] = convertDictToArray(text_dict[book][perek])
	text_dict[book] = convertDictToArray(text_dict[book])
	send_text = {
		"text": text_dict[book],
		"language": "he",
		"versionTitle": "Friedberg Edition",
		"versionSource": "https://fjms.genizah.org/"
	}
	post_text("Lechem Mishneh on {}".format(book), send_text, server="https://resetwebsites.cauldron.sefaria.org")
	time.sleep(5)