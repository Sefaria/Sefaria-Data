
import csv

# Load map from Noah's names to Sefaria's names

noahs_names = {}
with open('noam_prakim/perek_name_map.csv', 'rb') as csvfile:
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
    fname = "noam_prakim/data/" + f + ".txt"
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

for chapter in chapters:
    print chapter
print len(chapters)


# book; chapter; name; mishna count; description

#
#
#