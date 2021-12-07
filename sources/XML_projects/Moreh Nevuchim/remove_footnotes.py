from sources.functions import *
from bs4 import BeautifulSoup
ftnotes = []
curr = 1
with open("Moreh Wout Footnotes.csv", 'w') as new_f:
    writer = csv.writer(new_f)
    with open("Moreh Nevukhim.csv", 'r') as f:
        rows = list(csv.reader(f))
        for row in rows:
            ref, comm = row
            soup = BeautifulSoup(comm)
            sups = soup.find_all("sup")
            for sup in sups:
                i_tag = sup.next_sibling
                if i_tag.name == "i":
                    ftnote = str(sup) + str(i_tag)
                    for word in ftnote.split():
                        assert word in comm
                    comm = comm.replace(ftnote, "fn{}".format(curr))
                    curr += 1
                    ftnotes.append(ftnote)
            writer.writerow([ref, comm])

with open("ftnotes.json", 'w') as f:
    json.dump(ftnotes, f)

