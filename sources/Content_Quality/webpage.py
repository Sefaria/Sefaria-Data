
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

if __name__ == "__main__":
	import tracemalloc



	# starting the monitoring
	tracemalloc.start()

	# function call
	app()

	# displaying the memory
	print(tracemalloc.get_traced_memory())

	# stopping the library
	tracemalloc.stop()
