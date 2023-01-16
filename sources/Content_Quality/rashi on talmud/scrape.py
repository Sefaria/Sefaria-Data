from sources.functions import *
from linking_utilities.weighted_levenshtein import WeightedLevenshtein
from linking_utilities.dibur_hamatchil_matcher import *
# 1. scrape
# 2. check that number of rashi comments is same as wiki source rashi comments
# 3. use WeightedLevenshtein
def rashis_by_daf(urls, title):
	rashis_by_daf = {}
	for daf, url in urls.items():
		print(daf)
		pageSource = selenium_get_url("/Users/stevenkaplan/Downloads/chromedriver", "https://he.wikisource.org"+url)
		try:
			curr = [h2 for h2 in BeautifulSoup(pageSource).find_all("h2") if 'רש"י' in h2.text][0].next_sibling
			rashis = []
			while curr.next_sibling:
				if isinstance(curr, Tag) and curr.name == "p":
					rashis.append(curr.text)
				curr = curr.next_sibling
			rashis_by_daf[int(daf)] = rashis
		except:
			print("Not finding anything in {} {}".format(title, daf))


	with open('rashis_by_daf_{}.json'.format(title), 'w') as f:
		json.dump(rashis_by_daf, f)

def matcher(title):
	wiki_rashis = json.load(open('rashis_by_daf_{}.json'.format(title), 'r'))
	our_rashis = {}

	i = library.get_index("Rashi on {}".format(title))


	for ref in i.all_top_section_refs():
		our_rashis[ref] = [r.text('he').text for r in ref.all_segment_refs()]

	with open("results_{}.csv".format(title), 'w') as f:
		writer = csv.writer(f)
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
							writer.writerow(["Bad Order", actual_ref, our])
						else:
							writer.writerow(["Can't Find", actual_ref, our])
				else:
					prev = their


json_files = {f: json.load(open(f, 'r')) for f in os.listdir(".") if f.startswith("daf_mapping")}
count = 0
titles = []
for f, data in json_files.items():
	count += 1
	if count < 12:
		continue
	f = f.replace("daf_mapping_", "").replace(".json", "").replace("בבלי מסכת ", "")
	f = library.get_index(f).title
	#rashis_by_daf(data, f)

for f in os.listdir("."):
	if f.startswith("rashis_by_daf"):
		title = f.replace(".json", "").replace("rashis_by_daf_", "")
		print(title)
		matcher(title)