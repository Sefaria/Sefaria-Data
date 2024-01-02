import django

django.setup()

from sefaria.model import *

import json
from source_sheet_map_utilities import get_sheets_quoting_mekhilta, retrieve_sheets_collection
from pymongo import UpdateOne

# Specify the file path from which you want to read the JSON data
file_path = "sheets_data.json"

# Open the file in read mode and use json.load() to load the JSON data into a Python dictionary
with open(file_path, 'r') as json_file:
    data_dict = json.load(json_file)

collection = retrieve_sheets_collection()

total = len(data_dict)
count = 1
# for sheet in data_dict:
#     print(f"Updating sheet {sheet['sheet_id']}. Update {count}/{total}")
#     collection.update_one(
#         {"id": sheet["sheet_id"]},
#         {"$set": {"includedRefs": sheet["newIncludedRefs"],
#                   "expandedRefs": sheet["newExpandedRefs"],
#                   "sources": sheet["newSources"]}}
#     )
#
#     if int(count/total) in [25, 50, 75, 100]:
#         print(f"SHEET UPDATE IS {int(count/total)}% COMPLETE.")
#     count += 1

# Create a list of UpdateOne operations
update_operations = [
    UpdateOne({'id': sheet["sheet_id"]}, {"$set": {"includedRefs": sheet["newIncludedRefs"],
                                                   "expandedRefs": sheet["newExpandedRefs"],
                                                   "sources": sheet["newSources"]}})
    for sheet in data_dict
]

chunks = [update_operations[x:x+500] for x in range(0, len(data_dict), 500)]

count = 1
for chunk in chunks:
    print(f"Matching chunk #{count}")
    result = collection.bulk_write(chunk)

    # Print the result
    print(f"Matched: {result.matched_count}, Modified: {result.modified_count}")
    count += 1

print("Source sheet remap is complete.")
