# -*- coding: utf-8 -*-

import unicodecsv as csv
from sefaria.model import *

# Load map from Noah's names to Sefaria's names
# start daf(index), end daf, chapter
def parse_noah():
    """ Returns set of (Book Name, Chapter Number)
    """
    noahs_names = {}
    with open('noah_prakim/perek_name_map.csv', 'rb') as csvfile:
        cread = csv.reader(csvfile)
        for row in cread:
            if row[0]:
                noahs_names[row[0]] = row[1]

    books = {}
    chapters = []

    # Load each file of Noah's
    for f, title in noahs_names.iteritems():
        books[title] = {
            "mishnayot": [],
        }
        fname = "noah_prakim/data/" + f + ".txt"
        with open(fname, 'rb') as csvfile:
            cread = csv.reader(csvfile)
            for row in cread:
                if int(row[0]) <= 0 or int(row[1]) <= 0:
                    continue
                books[title]["mishnayot"].append({
                    "start daf": int(row[0]),
                    "end daf": int(row[1]),
                    "chapter": int(row[2])
                })
                # Create a set of numbers of prakim
                chapters.append((title, int(row[2])))

    chapters = sorted(set(chapters))
    """
    for chapter in chapters:
        print chapter
    print len(chapters)
    """
    return chapters


# from wikipedia, we have:
# book (he title); chapter num; name (hebrew); mishna count; description
def parse_wikipedia():
    """ Returns set of (Book Name, Chapter Number)
    """
    chapters = set()
    with open('wikipedia/prakim.csv', 'rb') as csvfile:
        next(csvfile)
        cread = csv.reader(csvfile, delimiter=";", encoding='utf-8')
        for row in cread:
            #print row[0]
            try:
                index = get_index(row[0])
                if "Bavli" not in index.categories:
                    print u"Skipping {}".format(row[0])
                    continue
                title = index.title
            except Exception as e:
                print u"Failed to load {}".format(row[0])
                continue
            chapters.add((title, int(row[1])))
    chapters = sorted(chapters)
    return chapters

# from Mishnah Map we have:
# book, Mishnah Chapter, Start Mishnah, End Mishnah, Start Daf (2a form), Start Line, End Daf, End Line
def parse_mishnah_map():
    """ Returns set of (Book Name, Chapter Number)
    """
    chapters = set()
    with open('mishnah_mappings.csv', 'rb') as csvfile:
        next(csvfile)
        cread = csv.reader(csvfile, encoding='utf-8')
        for row in cread:
            chapters.add((row[0].replace("_", " "), int(row[1])))
    return sorted(chapters)


n = set(parse_noah())
m = set(parse_mishnah_map())
w = set(parse_wikipedia())

t = n | m | w

print
print "{} ({} to go)".format(len(m), len(w-m))
for x in sorted(w-m):
    print x