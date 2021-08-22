from sources.functions import *
driver = "/Users/stevenkaplan/Downloads/chromedriver"
# pageSource = selenium_get_url("/Users/stevenkaplan/Downloads/chromedriver", "https://he.wikisource.org/wiki/%D7%AA%D7%9C%D7%9E%D7%95%D7%93_%D7%91%D7%91%D7%9C%D7%99")
# mapping = {y.find("a")["title"]: y.find("a")["href"] for x in BeautifulSoup(pageSource).find_all("tr")[2:-1] for y in x.contents if y != '\n' and y.find("a") and not y.find("a")["title"].startswith("ירושלמי")}
# with open("masechet_mapping.json", 'w') as f:
# 	json.dump(mapping, f)
# with open("masechet_mapping.json", 'r') as f:
# 	mapping = json.load(f)
# mapping_by_title = {}
# for title, url in mapping.items():
# 	mapping_by_title[title] = {}
# 	pageSource = selenium_get_url(driver, "https://he.wikisource.org"+url)
# 	a_tags = BeautifulSoup(pageSource).find("div", {"class": "mw-parser-output"}).find_all("a")
# 	prev_ref = 2
# 	for i, a_tag in enumerate(a_tags):
# 		try:
# 			ref = Ref(a_tag["title"]).sections[0]
# 			if (ref - prev_ref) not in [0, 1]:
# 				print("Warning: Issue at {}, {} after {}".format(title, ref, prev_ref))
# 			mapping_by_title[title][ref] = a_tag["href"]
# 			prev_ref = ref
# 		except Exception as e:
# 			pass
#
# for title in mapping_by_title:
# 	with open("daf_mapping_{}.json".format(title), 'w') as f:
# 		json.dump(mapping_by_title[title], f)
