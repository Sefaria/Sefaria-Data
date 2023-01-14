import django, json, srsly, csv
import Levenshtein
django.setup()
import re
from sefaria.model import *

csv.field_size_limit(1000000)


french_bible_books = {'Genèse','Exod.','Exode', 'Lévit.', 'Nombres', 'Nomb.', 'Deutéron.', 'Deutér.', 'Josué', 'Juges', 'I Sam.', 'II Sam.', 'I Rois', 'II Rois',
    'Isaïe', 'Jésaïe', 'Jérémie', 'Ézéch.', 'Osée', 'Joël', 'Amos', 'Abdias', 'Jonas', 'Micha', 'Nahum', 'Habacuc', 'Sophonie', 'Aggée', 'Zacharie', 'Malach.',
    'Ps.', 'Prov.', 'Job', 'Cantique des cant.', 'Ruth', 'Lament.', 'Esther', 'Daniel', 'Esdras', 'Néhémie', 'I Chron.', 'II Chron.', 'Ecclésiaste', 'Ibid.'}

def is_roman(s):
    chars = ["c", "x", "v", "i", "."]
    return all([x in chars for x in s.lower()])

def latin_to_num(s):
    numerals = {'I':1, 'V':5, 'X':10, 'L':50, 'C':100, 'D':500, 'M':1000}
    result = 0
    for i in range(len(s)):
        if i > 0 and numerals[s[i]] > numerals[s[i - 1]]:
            result += numerals[s[i]] - 2 * numerals[s[i - 1]]
        else:
            result += numerals[s[i]]
    return result



def fix_part_1():
    with open('MorehNevukhim_French_1.xml', 'r') as f:
        xml_data = f.read()


if __name__ == "__main__":
    print("hello world")
    margin = 30

    with open('moreh_fixed_all_parts_with_imgs.csv', 'r') as file_r:
        with open('moreh_fixed_all_parts_with_imgs_arabic_numerals.csv', 'w', newline='') as file_w:
            # Create a CSV writer object
            writer = csv.writer(file_w)
            reader = csv.reader(file_r)
            i = 1
            for row in reader:
                if "Je ne pense pas que tu aies un doute" in row[2]:
                    a = 9
                for book in french_bible_books:
                    index = row[2].find(book)
                    while index != -1:
                        sub = row[2][index: index+margin]
                        pattern = r'[MDCLXVI]+(,| )'
                        sub_without_book = row[2][index + len(book) : index+margin]
                        print("sub without book: " + sub_without_book)
                        match = re.search(pattern, sub_without_book)
                        if match:
                            print(row[2])
                            arabic_numeral = latin_to_num(sub_without_book[match.start() : match.end()-1])
                            print(arabic_numeral)
                            row[2] = row[2][ 0 : index + len(book) + match.start()] + str(arabic_numeral) + row[2][index + len(book) + match.end()-1 : ]
                            print(row[2])

                        else:
                            print("not numeral")

                        index = row[2].find(book, index + len(book))

                writer.writerow(row)



# Print the list of sup tags with ref tags

