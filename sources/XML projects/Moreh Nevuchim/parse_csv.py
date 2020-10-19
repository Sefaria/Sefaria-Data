import django
django.setup()
from sefaria.model import *
from data_utilities.XML_to_JaggedArray import *
fr_books = """Genèse
Exode
Lévitique
Nombres
Deutéronome
Josué
Juges
1 Samuel
2 Samuel
1 Rois
2 Rois
Ésaïe
Jérémie
Ézéchiel
Osée
Joël
Amos
Abdias
Jonas
Michée
Nahum
Habacuc
Zéphanie
Aggée
Zacharie
Malachie
Psaumes
Proverbes
Job
Cantique des Cantiques
Ruth
Lamentations
Ecclésiaste
Esther
Daniel
Esdras
Néhémie
1 Chroniques
2 Chroniques""".splitlines()
en_tanakh = library.get_indexes_in_category("Tanakh")
books = "|".join(fr_books)
from sources.functions import *
with open("new_full_text.csv", 'w') as new_f:
    writer = csv.writer(new_f)
    with open("full_text.csv", 'r') as f:
        for row in csv.reader(f):
            finds = re.findall("("+books+"), ([ILVXC]+), (\d+)", row[1])
            if finds:
                for find in finds:
                    find = list(find)
                    old_citation = "{}, {}, {}".format(*find)
                    if len(find) != 3:
                        print("ERROR")
                    else:
                        find[1] = roman_to_int(find[1])
                        print(find)
                        loc = fr_books.index(find[0])
                        actual_book = en_tanakh[loc]
                        find[0] = actual_book
                        new_citation = "{}, {}:{}".format(*find)
                        row[1] = row[1].replace(old_citation, new_citation)

            writer.writerow(row)



