import django

django.setup()

from sefaria.model import *
import json
from pymongo import MongoClient

def retrieve_sheets_collection(cauldron=False):

    # local_uri
    local_uri = "mongodb://localhost:27017"

    # cauldron uri - 'mongodb://user:pass@ip:port/'
    cauldron_uri = "mongodb://mongo:27017/"

    # Connect to MongoDB
    if cauldron:
        client = MongoClient(cauldron_uri)
    else:
        client = MongoClient(local_uri)

    db = client['sefaria']
    collection = db['sheets']
    client.close()
    return collection


def get_sheets_quoting_mekhilta(collection, search_term='Mekhilta DeRabbi Yishmael Old'):

    # Query the collection
    query = {"includedRefs": {"$regex": search_term}}
    result = collection.find(query)
    return result


def write_to_json(mapper_dictionary):
    with open("sheets_data2.json", 'w') as json_file:
        json.dump(mapper_dictionary, json_file, indent=4)