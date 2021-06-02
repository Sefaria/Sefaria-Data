import re
import csv

def find_siman(line, part):
    siman = "(?:סימן|סי') (.{,5})"
    before = '@00' if part == 2 else '@22'
    after = '@33' if part == 1 else '$'
    siman = f'{before}{siman}{after}'
    found = re.findall(siman, line)
    if not found:
        return None, None
    if len(found) > 1:
        print('more than one siman', line)
    found = re.search(siman, line)
    return found.group(0), found.group(1)

def find_ref(line):
    line = ' '.join(line.split()[:7])
    if 'ש"ך' in line:
        basis = 'Siftei Kohen'
    elif 'סמ"ע' in line:
        basis = "Me'irat Einayim"
    elif 'ט"ז' in line:
        basis = 'Turei Zahav'
    else:
        basis = 'Shulchan Arukh'
    seif = "(?:סעיף|סעי'|ס\"ק)"
    sak = 'סק(.?".) '
    seifim = re.findall(f'{seif} ([^ ]*)|{sak}', line)
    if seifim:
        if len(seifim) > 1:
            print('more than one seif', line)
        seifim = [s for s in seifim[0] if s]
        if len(seifim) > 1:
            print('more than one seif', line)
        return basis, seifim[0]
    print('no seif', line)
    return basis, None


comments = []
for n in range(1,4):
    with open(f'cs{n}.txt', encoding='utf=8') as fp:
        data = fp.readlines()
    for line in data:
        line = line.strip()
        to_del, siman = find_siman(line, n)
        if not siman:
            siman = old_siman
        old_siman = siman
        if to_del:
            line = line.replace(to_del, '').strip()
        if not line:
            continue
        basis, seif = find_ref(line)
        line = re.sub('@|\d', '', line)
        line = ' '.join(line.split())
        row = {'siman': siman, 'content': line, 'basis': basis, 'seif': seif}
        comments.append(row)

with open('cs.csv', 'w', encoding='utf=8', newline='') as fp:
    writer = csv.DictWriter(fp, fieldnames=['siman', 'content', 'basis', 'seif'])
    writer.writeheader()
    for item in comments:
        writer.writerow(item)
