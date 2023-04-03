import re
import os

path = 'commentary/mikdash_melekh/'
for file in os.listdir(path):
    print(file)
    with open(f'{path}/{file}') as fp:
        data = fp.readlines()
    if 'בראשית' in file:
        vol = 1
    elif 'שמות' in file:
        vol = 2
    else:
        vol = 3

    for line in data:
        line = line.replace('\ufeff', '')
        line = ' '.join(line.split())
        if not line:
            continue
        if line.startswith('@00'):
            if re.search('פרש[הת]', line):
                print(0, line)
            elif re.search('מדרש הנעלם', line):
                print(1, line)
            elif re.search('תוספתא', line):
                print(2, line)
            elif re.search('סתרי תורה|ס"ת', line):
                print(3, line)
            elif re.search('ע"כ', line):
                print(3, line)
            else:
                print(4, line)
        # elif line.startswith('@22'):
        #     pass
        # elif line.startswith('@11'):
        #     pass
        # else:
        #     print(2, line)
