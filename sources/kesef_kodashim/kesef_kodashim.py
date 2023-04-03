import csv

import django
django.setup()

from parsing_utilities.util import getGematria as gematria

book = "Kesef Kodashim on Shulchan Arukh, Choshen Mishpat"
colluma = ['Version Title', "Language", "Version Source", "Version Notes"]
collumb = ["Apei Ravrevei: Shulchan Aruch Even HaEzer, Lemberg, 1886", "he",
           "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002097680", ""]
dictout=[]
for n in range(0, 4):
    dictout.append({"Index Title": colluma[n], book: collumb[n]})

data=[]
with open('kesefkod.txt', encoding='utf-8') as file:
    data = file.readlines()

siman = 0
par = 0
link = ''
seif = False

for line in data:
    line = line.replace('\n', '')

    if '@22' in line:
        siman = gematria(line.split()[-1])
        par = 1
        link = ''
        continue

    elif '@11' in line:
        dh = line[3:].split('@33')[0]

        if any(word in dh for word in ['סעיף', "סעי'"]) and "@11בסעי' " not in line:
            start = dh.index('סעי') + 5
            end = dh.index(' ', start)
            link = "Shulchan Arukh, Choshen Mishpat " + str(siman) + ':' + str(gematria(dh[start:end]))
            seif = True
        elif any(word in dh for word in ['בהגה', 'בהג"ה']):
            if link[:2] != 'Sh':
                #ad hoc
                link = "Shulchan Arukh, Choshen Mishpat " + str(siman) + ':1'
                seif = True
        elif any(word in dh for word in ['עש"כ', 'עש"ך']):
            link = 'Siftei Kohen on Shulchan Arukh, Choshen Mishpat ' + str(siman) + ':'
            seif = False
        elif 'עסמ"ע' in dh:
            link = "Me'irat Einayim on Shulchan Arukh, Choshen Mishpat " + str(siman) + ':'
            seif = False
        elif 'עקצוה"ח' in dh:
            link = 'Ketzot HaChoshen on Shulchan Arukh, Choshen Mishpat ' + str(siman) + ':'
            seif = False
        elif 'עבט"ז' in dh:
            #ad hoc
            link = 'Turei Zahav on Shulchan Arukh, Choshen Mishpat 75:9'
            seif = True
        elif any(word in dh for word in ['שם', '(שם)', '(שם']):
            pass
        elif dh == 'ס"ב ':
            #ad hoc
            link = "Shulchan Arukh, Choshen Mishpat " + str(siman) + ':2'
            seif = True
        elif link == '':
            #ad hoc
            link = "Shulchan Arukh, Choshen Mishpat " + str(siman) + ':1'
            seif = True
        else:
            #link remains
            seif = True

        if not seif:
            if 'ס"ק' in dh:
                start = dh.index('ס"ק') + 4
                end = dh.index(' ', start)
                link += str(gematria(dh[start:end]))
            elif any(word[:2] == 'סק' and '"' in word for word in dh.split()):
                for word in dh.split():
                    if word[:2] == 'סק' and '"' in word:
                        link += str(gematria(word) - 160)
            else:
                #ad hoc
                link += '26'

    if 'סליק' in line:
        link = ''

    dictout.append({"Index Title": book + ' ' + str(siman) + ':' + str(par),
                    book: line.replace('@11', '<b>').replace(' @33', '</b> ').replace('@33', '</b>'),
                    'link': link})
    par += 1

with open('kesef kodashim.csv', 'w', newline='', encoding='utf-8') as file:
    awriter = csv.DictWriter(file, fieldnames=["Index Title", book, 'link'])
    awriter.writeheader()
    for item in dictout:
        awriter.writerow(item)
