#encoding=utf-8
import django
django.setup()
from sefaria.model import *
from sources.functions import *
import csv
links = []
with open("links.csv") as f:
    for row in csv.reader(f):
        chelkat, job = row
        links.append({"refs": [chelkat, job], "auto": True, "type": "Commentary", "generated_by": "alshich_to_job"})

post_link(links, server="http://rosh.sandbox.sefaria.org")