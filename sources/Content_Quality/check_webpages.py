import django
django.setup()
from sefaria.model.webpage import *
import csv
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

def app():
	lists = ["Linker uninstalled", "Site uses linker but is not whitelisted"]

	idList_mapping = {}
	url = f'https://api.trello.com/1/boards/{BOARD_ID}/lists?key={TRELLO_KEY}&token={TRELLO_TOKEN}'
	response = requests.request(
		"GET",
		url,
		headers={"Accept": "application/json"}
	)

	for list_on_board in json.loads(response.content):
		if list_on_board["name"] in lists:
			idList_mapping[list_on_board["name"]] = list_on_board["id"]

	run_job(test=False, board_id=BOARD_ID, idList_mapping=idList_mapping)


if __name__ == "__main__":
	#dedupe_webpages(False)
	# importing the module
	import tracemalloc


	# code or function for which memory
	# has to be monitored


	# starting the monitoring
	tracemalloc.start()

	sites_that_may_have_removed_linker_days = 20  # num of days we care about in find_sites_that_may_have_removed_linker and find_webpages_without_websites
	webpages_without_websites_days = sites_that_may_have_removed_linker_days  # same timeline is relevant

	test = True
	sites = {}
	print("Original webpage stats...")
	orig_count = WebPageSet().count()
	orig_count = int(WebPageSet().count()/30)
	print(orig_count)
	skip = 0
	limit = 500
	print("Cleaning webpages...")
	clean_webpages(test=test)

	while (skip + limit) < orig_count:
		webpages = WebPageSet(limit=limit, skip=skip)
		print("Deduping...")
		dedupe_webpages(webpages, test=test)
		print("Find sites that no longer have linker...")
		sites["Linker uninstalled"] = find_sites_that_may_have_removed_linker(
			last_linker_activity_day=sites_that_may_have_removed_linker_days)
		print(
			"Looking for webpages that have no corresponding website.  If WebPages have been accessed in last 20 days, create a new WebSite for them.  Otherwise, delete them.")
		sites["Site uses linker but is not whitelisted"] = find_webpages_without_websites(webpages, test=test,
																						  hit_threshold=50,
																						  last_linker_activity_day=webpages_without_websites_days)
		sites["Websites that may need exclusions set"] = find_sites_to_be_excluded_relative(webpages,
																							relative_percent=3)
		skip += limit
	sites["Webpages removed"] = orig_count - WebPageSet().count()
	# displaying the memory
	print(sites)
	print(tracemalloc.get_traced_memory())

	# stopping the library
	tracemalloc.stop()
