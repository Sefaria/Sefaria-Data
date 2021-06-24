import csv
new = []
with open('cs-final.csv', encoding='utf-8', newline='') as fp:
    data = csv.DictReader(fp)
    for row in data:
        new.append(row)
        if row['content'].count(':') > 1:
            segs = [s.strip() for s in row['content'].split(':') if s.strip()]
            row['content'] = segs[0]+':'
            for seg in segs[1:]:
                new.append({'content': seg+':'})
with open('cs.csv', 'w', encoding='utf-8', newline='') as fp:
    writer = csv.DictWriter(fp, fieldnames=['siman', 'content', 'basis', 'seif'])
    writer.writeheader()
    for item in new:
        writer.writerow(item)
