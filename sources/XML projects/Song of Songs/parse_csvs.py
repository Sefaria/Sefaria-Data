import csv
rows = list(csv.reader(open("Commentary_on_Song_of_Songs2 (1).csv", 'r')))
start = False
text = []
for r, row in enumerate(rows):
    if row[0] == 'Commentary on Song of Songs 1:1':
        start = True
    if start:
        ref = row[0]
        comments = row[1].split("\n")
        filtered_comments = []
        for c in comments:
            if not c.strip().endswith("</b>"):
                filtered_comments.append((ref, c))
            else:
                assert c.strip().startswith("<b>")
        for i, comm_tuple in enumerate(filtered_comments):
            ref, c = comm_tuple
            text.append([f"{ref}:{i+1}", c])
with open("new song of songs.csv", 'w') as f:
    writer = csv.writer(f)
    for row in text:
        writer.writerow(row)