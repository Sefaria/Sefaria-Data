import re
from sources.functions import *
books = []
with open("Ramban Sponsorships - FOR STEVE_Engineering.csv", 'r') as f:
    parshiot = []
    starting = False
    for row in csv.reader(f):
        if row[0] == "Subheader":
            if len(parshiot) > 0:
                books.append(parshiot)
            parshiot = []
        if row[0] == "Parshiot":
            starting = True
        if starting:
            nothing, parasha, names, message = row
            if len(parasha) > 0:
                if not parasha.isupper():
                    parshiot.append([parasha, names, message])


books.append(parshiot)
for book in books:
    print(book)

# with open("ramban_landing", 'r') as f:
#     parshiyot = {}
#     curr_parsha = ""
#     for line in f:
#         if line.startswith("/*"):
#             parsha = re.search("/\* (Parashat .*?) \*/", line)
#             if parsha:
#                 curr_parsha = parsha.group(1)
#                 assert curr_parsha not in parshiyot
#                 parshiyot[curr_parsha] = ""
#             elif line.startswith("/*") and re.search("/\* (.*?) \*/", line).group(1).split()[0].istitle():
#                 line = re.search("/\* (.*?) \*/", line).group(1)
#                 assert parshiyot[curr_parsha] == ""
#                 if line == "Available for Sponsorship":
#                     parshiyot[curr_parsha] = "<b>{}</b>".format(line)
#                 else:
#                     if "In memory" in line or "In honor" in line:
#                         italics = re.search("In (memory|honor) of .*", line).group(0)
#                         line = line.replace(" "+italics, "")
#                         parshiyot[curr_parsha] = line+"<br/><i>{}</i>".format(italics)
#                     else:
#                         parshiyot[curr_parsha] = line
#
# pass