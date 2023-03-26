import django

django.setup()

django.setup()
superuser_id = 171118
import csv
from sefaria.model import *
from sefaria.system.database import db
import json
import re

links = []

def list_of_dict_to_links(dicts):
    list_of_dicts = []
    for d in dicts:
        list_of_dicts.append(Link(d))
    return list_of_dicts

def insert_links_to_db(list_of_links):
    for l in list_of_links:

        l.save()


def f(colA, colC):
    # Do something with colA and colC
    print(colA, colC)
    links.append({
        "refs": [
            colA,
            colC
        ],
        "generated_by": None,
        "type": "Commentary",
        "auto": False
    })

def read_links(csv_filename):
    with open(csv_filename, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)

        # Skip first 6 lines
        for i in range(5):
            next(csv_reader)

        # Iterate over remaining lines and extract columns A and C
        for row in csv_reader:
            colA = row[0]
            colC = row[2]
            f(colA, colC)


def clean():
    query = {"generated_by": {"$regex": "Guide for the Perplexed_to"}}
    list_of_links = LinkSet(query).array()
    for l in list_of_links:
        l.delete()

if __name__ == '__main__':
    print("hello world")
    clean()
    read_links('abarbanel_manual_links.csv')
    read_links('crescas_manual_links.csv')
    read_links('efodi_manual_links.csv')
    read_links('shem_tov_manual_links.csv')
    links = list_of_dict_to_links(links)
    insert_links_to_db(links)
    print("hi")


    # post_link(links)







