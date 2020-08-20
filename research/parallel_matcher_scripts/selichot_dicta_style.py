import django, re, csv, requests
django.setup()
from sefaria.model import *

"""
find_url = "https://talmudfinder-1-1.loadbalancer.dicta.org.il/TalmudFinder/api/markpsukim"
parse_url = "https://talmudfinder-1-1.loadbalancer.dicta.org.il/TalmudFinder/api/parsetogroups?smin=22&smax=10000"

yo = ""
find_params = {
    "data": yo,
    "mode": "tanakh",  # or "mishna" or "talmud"
    "thresh": 0,
    "fdirectonly": False
}

find_response = {
    "downloadId",
    "allText",
    "results"
}


parse_params = {
    "allText": "str",
    "downloadId": "id",
    "keepredundant": True,
    "results": "results"
}

parse_response = [{
    "startIChar", "endIChar", "text", "matches": [
        {
            "matchedText",
            "mode",
            "score",
            "verseId"
        }
    ]
}]
"""
