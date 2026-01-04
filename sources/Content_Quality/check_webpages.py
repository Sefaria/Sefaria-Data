import django
django.setup()
import csv
from sefaria.model import *
from sefaria.helper.schema import *
hs = UserHistorySet({'uid': 1, 'saved': True})
# temp = UserHistory().load(
#     {"uid": attrs["uid"], "ref": attrs["ref"], "versions": attrs["versions"], "secondary": attrs['secondary']})

b = library.get_index("Redeeming Relevance; Exodus")
ft = b.nodes.children[-1]
print(ft)
remove_branch(ft)


from tqdm import tqdm
from sefaria.export import import_versions_from_stream, _import_versions_from_csv
message = ""
count = 0
with open("./Notes by Rabbi Yehoshua Hartman on Gevurot Hashem - he - Gevurot Hashem, with footnotes and annotations by Rabbi Yehoshua D. Hartman, Machon Yerushalyim, 2015-2020 (1) - for upload (1).csv", 'r') as f:
    lines = list(csv.reader(list(f)))
    #import_versions_from_stream(lines, [1], 1)
    for x in tqdm(lines[5:]):
        count += 1
        vtitle = lines[1][1]+" Part II"
        # if 1570 > count > 1567:
        #     continue
        r, text = x
        tc = TextChunk(Ref(r), vtitle=vtitle, lang='he')
        tc.text = text
        try:
            tc.save()
        except Exception as e:
            print(e)
    #_import_versions_from_csv(lines, [1], 1)
    message += "Imported: {}.  ".format(f.name)
print()
raise Exception
from sefaria.model.webpage import *
from sefaria.utils.hebrew import *
import csv
import json

import django
django.setup()
from sefaria.model import *
from sefaria.helper.schema import insert_last_child, reorder_children
from sefaria.helper.schema import remove_branch
from sefaria.tracker import modify_bulk_text
from sefaria.helper.category import create_category
from sefaria.system.database import db

import csv

superuser_id = 171118
# import statistics

import json
from sefaria.model import *



def csv_to_dict(csv_file):
    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        result_dict = {}
        for row in reader:
            result_dict[row[0]] = row[1]
    return result_dict

def insert_links_to_db(list_of_links):
    for l in list_of_links:

        l.save()

def list_of_dict_to_links(dicts):
    list_of_dicts = []
    for d in dicts:
        list_of_dicts.append(Link(d))
    return list_of_dicts

def post_playground_index():
    from sources.functions import post_index, post_text
    index = {"title": "Mishnat Eretz Yisrael on Pirkei Avot"}
    index = post_index(index, method='GET', server="https://images-in-text-v4.cauldron.sefaria.org") #https://piaseczno.cauldron.sefaria.org
    index["title"] = "Mishnat Eretz Yisrael on Pirkei Avot"
    index["schema"]["titles"] = [{'text': 'משנת ארץ ישראל על משנה אבות מגרש משחקים', 'lang': 'he', 'primary': True},
                                 {'text': 'Mishnat Eretz Yisrael on Pirkei Avot', 'lang': 'en', 'primary': True}]

    post_index(index, server="https://images-in-text-v4.cauldron.sefaria.org")



def clean():
    cur_version = VersionSet({'title': 'Mishnat Eretz Yisrael on Pirkei Avot'})
    if cur_version.count() > 0:
        cur_version.delete()
        print("deleted existing version")

def ingest_playground_version(version_map, lang):
    vs = VersionState(index=library.get_index("Mishnat Eretz Yisrael on Pirkei Avot"))
    vs.delete()
    print("deleted version state")

    index = library.get_index("Mishnat Eretz Yisrael on Pirkei Avot")

    chapter = index.nodes.create_skeleton()
    version_obj = Version({"versionTitle": "Mishnat Eretz Yisrael, Seder Nezikin, Jerusalem, 2013-",
                               "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH003570676/NLI",
                               "title": "Mishnat Eretz Yisrael on Pirkei Avot",
                               "chapter": chapter,
                               "language": lang,
                               "digitizedBySefaria": True,
                               "license": "CC-BY-NC",
                               "status": "locked"
                               })

    modify_bulk_text(superuser_id, version_obj, version_map)

    print("finished updating version db")

def insert_links_to_db(list_of_links):
    for l in list_of_links:

        l.save()
def add_links_manually_to_db(list_of_ref_pairs): #first crescas second guide
    links = []
    for pair in list_of_ref_pairs:
        links.append({
            "refs": [
                pair[0],
                pair[1]
            ],
            "generated_by": "imgs_in_txt_playground",
            "auto": True
        })

    links = list_of_dict_to_links(links)
    insert_links_to_db(links)
if __name__ == '__main__':
    from tqdm import tqdm

    from sefaria.helper.link import rebuild_links_from_text, add_links_from_text
    book = library.get_index("Mishnat Eretz Yisrael on Pirkei Avot")
    for oref in tqdm(library.get_index("Mishnat Eretz Yisrael on Pirkei Avot").all_segment_refs()):
        tc = TextChunk(oref, lang='he')

    assert 5 == 6
    # post_playground_index()
    # img_title_html_str = '<p class="mishna_project_image_title">Lorem ipsum dolor sit amet</p>'
    img_title_html_str_en = "this is a marvelous image"
    img_title_html_str_he = "זו תמונה מופלאה"
    img_title_html_str_long_en = "this is a marvelous image this is a marvelous image this is a marvelous image this is a marvelous image this is a marvelous image"
    img_title_html_str_long_he = "זו תמונה מופלאה זו תמונה מופלאה זו תמונה מופלאה זו תמונה מופלאה זו תמונה מופלאה זו תמונה מופלאה זו תמונה מופלאה זו תמונה מופלאה"

    # img1_html_str = '<div class="mishna_project_image"><img src = "/static/imgs_playground/img1.jpg"   alt = "My Image" >' + img_title_html_str + "</div>"
    # img2_html_str = '<div class="mishna_project_image"><img src = "/static/imgs_playground/img2.jpg"  alt = "My Image" >'+ img_title_html_str + "</div>"
    # img3_html_str = '<div class="mishna_project_image"><img src = "/static/imgs_playground/img3.jpg"  alt = "My Image" >'+ img_title_html_str + "</div>"
    # img4_html_str = '<div class="mishna_project_image"><img src = "/static/imgs_playground/img4.jpg"  alt = "My Image" >'+ img_title_html_str + "</div>"
    # lorem_str = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
    # duis_str = "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."

    lorem_he_str = "לורם איפסום לורם איפסום לורם איפסום לורם איפסום לורם איפסום לורם איפסום לורם איפסום לורם איפסום לורם איפסום לורם איפסום לורם איפסום לורם איפסום לורם איפסום לורם איפסום לורם איפסום לורם איפסום לורם איפסום לורם איפסום לורם איפסום לורם איפסום"
    duis_he_str = "דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה דואיס אוטה"

    img1_html_str_en = f'<img src = "https://cdn.pixabay.com/photo/2016/04/30/13/12/sutterlin-1362879_960_720.jpg">'
    img2_html_str_en = f'<img src = "https://cdn.pixabay.com/photo/2016/03/26/22/21/books-1281581_960_720.jpg"   alt ="{img_title_html_str_en}">'
    img3_html_str_en = f'<img src = "https://cdn.pixabay.com/photo/2016/11/29/02/26/library-1866844_960_720.jpg"   alt ="{img_title_html_str_long_en}">'
    img4_html_str_en = f'<img src = "https://cdn.pixabay.com/photo/2016/11/29/07/21/book-1868068_960_720.jpg"   alt ="{img_title_html_str_long_en}">'

    img1_html_str_he = f'<img src = "https://cdn.pixabay.com/photo/2016/04/30/13/12/sutterlin-1362879_960_720.jpg"   alt ="{img_title_html_str_he}">'
    img2_html_str_he = f'<img src = "https://cdn.pixabay.com/photo/2016/03/26/22/21/books-1281581_960_720.jpg"   alt ="{img_title_html_str_he}">'
    img3_html_str_he = f'<img src = "https://cdn.pixabay.com/photo/2016/11/29/02/26/library-1866844_960_720.jpg"   alt ="{img_title_html_str_long_he}">'
    img4_html_str_he = f'<img src = "https://cdn.pixabay.com/photo/2016/11/29/07/21/book-1868068_960_720.jpg"   alt ="{img_title_html_str_long_he}">'

    lorem_str = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
    duis_str = "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
    version_map_en ={
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 1": lorem_str,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 2": img1_html_str_en,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 3": duis_str,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 4": lorem_str,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 5": img2_html_str_en,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 6": duis_str,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 7": lorem_str,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 8": img3_html_str_en,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 9": duis_str,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 10": lorem_str,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 11": img4_html_str_en,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 12": duis_str,
    }

    version_map_he = {
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 1": lorem_he_str,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 2": img1_html_str_he,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 3": duis_he_str,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 4": lorem_he_str,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 5": img2_html_str_he,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 6": duis_he_str,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 7": lorem_he_str,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 8": img3_html_str_he,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 9": duis_he_str,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 10": lorem_he_str,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 11": img4_html_str_he,
        "Mishnat Eretz Yisrael on Pirkei Avot, Introduction 12": duis_he_str,
    }
    # links_refs = [("Mishnat Eretz Yisrael on Pirkei Avot, Introduction, 8", "Genesis 1 1")]
    # add_links_manually_to_db(links_refs)

    # post_playground_index()
    clean()
    ingest_playground_version(version_map_he, "he")
    ingest_playground_version(version_map_en, "en")
    #
    #
    #
    # encode_hebrew_numeral(2000)
    # with open("./Downloads/rambam.json", 'r') as rambam:
    # 	r = json.load(rambam)
    # x = encode_hebrew_numeral(1304)
    # y = decode_hebrew_numeral(x)
    # pass


# with open("http versiontitles.csv", 'r') as f:
# 	reader = csv.reader(f)
# 	rows = list(reader)
# print(rows)
# for row in rows:
# 	v = Version().load({"title": row[0], "versionTitle": row[1]+" temp"})
# 	if v:
# 		print("Found")
# 		print(row)
# 		v.versionTitle = row[0] + " temp"
# 		v.save(override_dependencies=True)
# 	else:
# 		print("Not found")
# 		print(row)

base = Ref("Pirkei Avot 4:2")

ls = LinkSet({"refs": base.normal()})
ls.count()
refs = []
phrases = ["Be quick in performing a minor commandment", "the reward for performing a commandment is another commandment"]
for l in ls:
        l = l.contents()
        if l['refs'][0] == base.normal():
            refs.append(l['refs'][1])
        else:
            refs.append(l['refs'][0])

en = {}
for r in refs:
    tc = TextChunk(Ref(r), lang='en')
    if tc.text != [] and tc.text != "":
        en[r] = tc.text

def app():
    lists = ["Linker uninstalled", "Site uses linker but is not whitelisted"]

    idList_mapping = {}
    url = f'https://api.trello.com/1/boards/{BOARD_ID}/lists?key={TRELLO_KEY}&token={TRELLO_TOKEN}'
    response = requests.anonymous_request(
        "GET",
        url,
        headers={"Accept": "application/json"}
    )

    for list_on_board in json.loads(response.content):
        if list_on_board["name"] in lists:
            idList_mapping[list_on_board["name"]] = list_on_board["id"]

    run_job(test=False, board_id=BOARD_ID, idList_mapping=idList_mapping)

#
# if __name__ == "__main__":
# 	#dedupe_webpages(False)
# 	# importing the module
# 	import tracemalloc
#
#
# 	# code or function for which memory
# 	# has to be monitored
#
#
# 	# starting the monitoring
# 	tracemalloc.start()
#
# 	sites_that_may_have_removed_linker_days = 20  # num of days we care about in find_sites_that_may_have_removed_linker and find_webpages_without_websites
# 	webpages_without_websites_days = sites_that_may_have_removed_linker_days  # same timeline is relevant
#
# 	test = True
# 	sites = defaultdict(list)
# 	print("Original webpage stats...")
# 	orig_count = 2000 #WebPageSet().count()
# 	print(orig_count)
# 	skip = 0
# 	limit = 1999
# 	print("Cleaning webpages...")
# 	#clean_webpages(test=test)
# 	print("Find sites that no longer have linker...")
# 	#sites["Linker uninstalled"] += find_sites_that_may_have_removed_linker(last_linker_activity_day=sites_that_may_have_removed_linker_days)
#
# 	while (skip + limit) < orig_count:
# 		webpages = WebPageSet(limit=limit, skip=skip)
# 		# print("Deduping...")
# 		# dedupe_webpages(webpages, test=test)
# 		# print("Looking for webpages that have no corresponding website.  If WebPages have been accessed in last 20 days, create a new WebSite for them.  Otherwise, delete them.")
# 		# sites["Site uses linker but is not whitelisted"] += find_webpages_without_websites(webpages, test=test, hit_threshold=50, last_linker_activity_day=webpages_without_websites_days)
# 		sites["Websites that may need exclusions set"] += find_sites_to_be_excluded_relative(webpages, relative_percent=5)
# 		skip += limit
# 	sites["Webpages removed"] = orig_count - WebPageSet().count()
# 	# displaying the memory
# 	print(sites)
# 	print(tracemalloc.get_traced_memory())
#
# 	# stopping the library
# 	tracemalloc.stop()
