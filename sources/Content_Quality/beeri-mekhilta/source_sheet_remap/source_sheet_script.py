import django

django.setup()

from sefaria.model import *

import json
from source_sheet_map_utilities import get_sheets_quoting_mekhilta, retrieve_sheets_collection

# Specify the file path from which you want to read the JSON data
file_path = "sheets_data.json"

# Open the file in read mode and use json.load() to load the JSON data into a Python dictionary
with open(file_path, 'r') as json_file:
    data_dict = json.load(json_file)

collection = retrieve_sheets_collection(cauldron=True)


for sheet in data_dict:
    collection.update_one(
        {"id": sheet["sheet_id"]},
        {"$set": {"includedRefs": sheet["newIncludedRefs"],
                  "expandedRefs": sheet["newExpandedRefs"],
                  "sources": sheet["newSources"]}}
    )

print("Source sheet remap is complete.")