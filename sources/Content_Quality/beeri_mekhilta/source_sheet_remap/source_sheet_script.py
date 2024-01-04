import django

django.setup()

from sefaria.model import *
import time
import json
from source_sheet_map_utilities import get_sheets_quoting_mekhilta, retrieve_sheets_collection
from pymongo import UpdateOne, ASCENDING
from sefaria.system.database import db


# TODO - run on cauldron

# Specify the file path from which you want to read the JSON data
file_path = "sheets_data2.json"

# Open the file in read mode and use json.load() to load the JSON data into a Python dictionary
with open(file_path, 'r') as json_file:
    data_dict = json.load(json_file)

# collection = retrieve_sheets_collection()
collection = db.sheets

total = len(data_dict)
count = 1


# Ensure an index on the 'id' field for faster lookup
# start = time.time()
# index_name = "id_index"
# collection.create_index([("id", ASCENDING)], name=index_name)
# end = time.time()
# print(f"Index creation took {end-start} seconds || {(end-start)//60} min")

total = len(data_dict)
count = 1

# Create a list of UpdateOne operations
update_operations = [
    UpdateOne({'id': sheet["sheet_id"]}, {"$set": {"includedRefs": sheet["newIncludedRefs"],
                                                   "expandedRefs": sheet["newExpandedRefs"],
                                                   "sources": sheet["newSources"]}})
    for sheet in data_dict
]

chunks = [update_operations[x:x+100] for x in range(0, len(data_dict), 100)]

count = 1
for chunk in chunks:
    print(f"Matching chunk #{count}")

    # Record the start time
    start_time = time.time()

    result = collection.bulk_write(chunk)

    # Record the end time
    end_time = time.time()

    # Print the result and elapsed time in minutes
    print(f"Matched: {result.matched_count}, Modified: {result.modified_count}")
    elapsed_time = end_time - start_time
    elapsed_minutes = elapsed_time / 60  # Convert seconds to minutes
    print(f"Elapsed Time: {elapsed_minutes:.2f} minutes")

    count += 1

# Drop the index after all bulk writes are complete
# collection.drop_index(index_name)
# print(f"Index '{index_name}' dropped.")

print("Source sheet remap is complete.")

