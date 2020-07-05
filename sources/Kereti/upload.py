from sefaria.export import *
with open("Recent.csv") as f:
    stuff = import_versions_from_stream(f, [1], 1)
    print
