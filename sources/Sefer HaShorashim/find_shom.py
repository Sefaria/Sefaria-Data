from sources.functions import *
with open("new_sefer.csv", 'w') as new_f:
    writer = csv.writer(new_f)
    with open("sefer.csv", 'r') as f:
        prev = None
        text = {}
        for row in csv.reader(f):
            if row[0].startswith("Sefer Ha"):
                ref, comm = row
                finds = re.findall("\(.*?\)", comm)
                for i, find in enumerate(finds):
                    new_ref = ""
                    if "שם" in find and "," in find and len(find.split()) in [3, 4]:
                        perek, pasuk = find.split()[1], find.split()[2]
                        prev_title = prev.replace(" ".join(prev.split()[-2:]), "").strip()
                        new_ref = "{} {} {}".format(prev_title, perek, pasuk)
                    elif "שם" in find and "," in find and len(find.split()) == 2:
                        print("Found 2")
                    else:
                        prev = find
                    if new_ref:
                        comm = comm.replace(find, new_ref, 1)
                writer.writerow([ref, comm])
            else:
                writer.writerow(row)
