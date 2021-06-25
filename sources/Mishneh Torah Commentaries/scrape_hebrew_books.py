from sources.functions import *
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
from bs4 import BeautifulSoup
import os
def rambam_pages():
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
					if start:
						driver.maximize_window()
						driver.get(url)
						pageSource = driver.page_source
						fileToWrite = open("hebrew books/{} {}/{}.html".format(book, perek, pasuk), "w")
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
			perek, pasuk = f.split()[-1].replace(".html", "").split(":")
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


def load_and_store_lechem_comments(lechem_dict):
	start = True
	for book in lechem_dict:
		for perek in lechem_dict[book]:
			for pasuk in lechem_dict[book][perek]:
				if start:
					driver.maximize_window()
					driver.get(lechem_dict[book][perek][pasuk])
					pageSource = driver.page_source
					fileToWrite = open("lechem mishneh/{} {},{}.html".format(book, perek, pasuk), "w")
					fileToWrite.write(pageSource)
					fileToWrite.close()

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

#rambam_pages(driver)

lechem_URL_dict = lechem_pages(driver)
json.dump(lechem_URL_dict, open("lechem_pages_up_to_sanhedrin.json", 'w'))
load_and_store_lechem_comments(lechem_URL_dict)
