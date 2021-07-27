from sources.functions import *
from data_utilities.util import WeightedLevenshtein
from data_utilities.dibur_hamatchil_matcher import *
# 1. scrape
# 2. check that number of rashi comments is same as wiki source rashi comments
# 3. use WeightedLevenshtein
def rashis_by_daf():
	urls = {'דף ב ע"א': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%91_%D7%90', 'דף ב ע"ב': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%91_%D7%91', 'דף ג ע"א': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%92_%D7%90', 'דף ג ע"ב': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%92_%D7%91', 'דף ד ע"א': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%93_%D7%90', 'דף ד ע"ב': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%93_%D7%91', 'דף ה ע"א': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%94_%D7%90', 'דף ה ע"ב': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%94_%D7%91', 'דף ו ע"א': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%95_%D7%90', 'דף ו ע"ב': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%95_%D7%91', 'דף ז ע"א': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%96_%D7%90', 'דף ז ע"ב': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%96_%D7%91', 'דף ח ע"א': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%97_%D7%90', 'דף ח ע"ב': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%97_%D7%91', 'דף ט ע"א': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%98_%D7%90', 'דף ט ע"ב': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%98_%D7%91', 'דף י ע"א': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%99_%D7%90', 'דף י ע"ב': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%99_%D7%91', 'דף יא ע"א': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%99%D7%90_%D7%90', 'דף יא ע"ב': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%99%D7%90_%D7%91', 'דף יב ע"א': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%99%D7%91_%D7%90', 'דף יב ע"ב': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%99%D7%91_%D7%91', 'דף יג ע"א': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%99%D7%92_%D7%90', 'דף יג ע"ב': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%99%D7%92_%D7%91', 'דף יד ע"א': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%99%D7%93_%D7%90', 'דף יד ע"ב': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%99%D7%93_%D7%91', 'דף טו ע"א': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%98%D7%95_%D7%90', 'דף טו ע"ב': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%98%D7%95_%D7%91', 'דף טז ע"א': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%98%D7%96_%D7%90', 'דף טז ע"ב': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%98%D7%96_%D7%91', 'דף יז ע"א': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%99%D7%96_%D7%90', 'דף יז ע"ב': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%99%D7%96_%D7%91', 'דף יח ע"א': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%99%D7%97_%D7%90', 'דף יח ע"ב': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%99%D7%97_%D7%91', 'דף יט ע"א': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%99%D7%98_%D7%90', 'דף יט ע"ב': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%99%D7%98_%D7%91', 'דף כ ע"א': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%9B_%D7%90', 'דף כ ע"ב': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%9B_%D7%91', 'דף כא ע"א': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%9B%D7%90_%D7%90', 'דף כא ע"ב': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%9B%D7%90_%D7%91', 'דף כב ע"א': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%9B%D7%91_%D7%90', 'דף כב ע"ב': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%9B%D7%91_%D7%91', 'דף כג ע"א': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%9B%D7%92_%D7%90', 'דף כג ע"ב': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%9B%D7%92_%D7%91', 'דף כד ע"א': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%9B%D7%93_%D7%90', 'דף כד ע"ב': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%9B%D7%93_%D7%91', 'דף כה ע"א': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%9B%D7%94_%D7%90', 'דף כה ע"ב': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%9B%D7%94_%D7%91', 'דף כו ע"א': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%9B%D7%95_%D7%90', 'דף כו ע"ב': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%9B%D7%95_%D7%91', 'דף כז ע"א': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%9B%D7%96_%D7%90', 'דף כז ע"ב': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%9B%D7%96_%D7%91', 'דף כח ע"א': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%9B%D7%97_%D7%90', 'דף כח ע"ב': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%9B%D7%97_%D7%91', 'דף כט ע"א': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%9B%D7%98_%D7%90', 'דף כט ע"ב': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%9B%D7%98_%D7%91', 'דף ל ע"א': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%9C_%D7%90', 'דף ל ע"ב': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%9C_%D7%91', 'דף לא ע"א': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%9C%D7%90_%D7%90', 'דף לא ע"ב': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%9C%D7%90_%D7%91', 'דף לב ע"א': 'https://he.wikisource.org/wiki/%D7%9E%D7%92%D7%99%D7%9C%D7%94_%D7%9C%D7%91_%D7%90', 'דף תוכן': 'https://he.wikisource.org/wiki/%D7%91%D7%91%D7%9C%D7%99_%D7%9E%D7%92%D7%99%D7%9C%D7%94', 'דף אקראי': 'https://he.wikisource.org/wiki/%D7%9E%D7%99%D7%95%D7%97%D7%93:%D7%90%D7%A7%D7%A8%D7%90%D7%99'}
	rashis_by_daf = {}
	for daf, url in urls.items():
		pageSource = selenium_get_url("/Users/stevenkaplan/Downloads/chromedriver", url)
		try:
			curr = [h2 for h2 in BeautifulSoup(pageSource).find_all("h2") if 'רש"י' in h2.text][0].next_sibling
		except:
			continue
		rashis = []
		while curr.next_sibling:
			if isinstance(curr, Tag) and curr.name == "p":
				rashis.append(curr.text)
			curr = curr.next_sibling
		rashis_by_daf[AddressTalmud(0).toNumber('he', " ".join(daf.split()[1:]))] = rashis

	with open('rashis_by_daf.json', 'w') as f:
		json.dump(rashis_by_daf, f)

wiki_rashis = json.load(open('rashis_by_daf.json', 'r'))
our_rashis = {}
our_rashis_by_ref = {}

i = library.get_index("Rashi on Megillah")


for ref in i.all_top_section_refs():
	our_rashis[ref] = [r.text('he').text for r in ref.all_segment_refs()]

for ref in our_rashis:
	ours = our_rashis[ref]
	prev = ""
	theirs = wiki_rashis[str(ref.sections[0])]
	theirs = " ".join(theirs).replace("\n", " ").split()
	results = match_text(theirs, ours, strict_boundaries="True", dh_extract_method=lambda x: " ".join(x.split()[:7]))
	for i, m in enumerate(results["match_text"]):
		their, our = m
		if their == "":
			orig_theirs = " ".join(theirs)
			prev_i = orig_theirs.find(prev)
			j = i
			while j < len(results["match_text"]) - 1 and results["match_text"][j][0] == "":
				j += 1
			next_i = orig_theirs.find(results["match_text"][j][0])
			if our not in orig_theirs[prev_i:next_i]: #actually not there
				actual_ref = ref.all_segment_refs()[i]
				if our in orig_theirs:
					print("{},{},Bad Order".format(actual_ref, our))
				else:
					print("{},{},Can't Find".format(actual_ref, our))
		else:
			prev = their

