#encoding=utf-8
import django
django.setup()
import re
from sefaria.model import *
from sources.functions import *
def combine_files(dir):
    with open(dir+"/aleph.txt") as a:
        with open(dir+"/bet.txt") as b:
            with open(dir+"/gimmel.txt") as g:
                lines = list(a) + list(b) + list(g)
                with open("{}.txt".format(dir), 'w') as new_file:
                    new_file.writelines(lines)

def replacements(book, prev_book):
    book = book.replace("""מ"א""", """מג"א""").replace("מא", """מג"א""").replace("""מ'"א""", """מג"א""")
    book = book.replace("""מחבר""", """ש"ע""")
    book = book.replace("""הג"ה""", """ש"ע""").replace("הגה", """ש"ע""")
    book = book.strip()
    return book

if __name__ == "__main__":
    file = "Levushei Serad.txt"
    simanim_f = open("{}_simanim.csv".format(file.split()[0]), 'w')
    with open("Levushei Serad/list of simanim.csv") as f:
        actual_simanim = [el.replace("\r\n", "") for el in list(f)]
        actual_simanim_gematrias = [getGematria(el) for el in actual_simanim]
    simanim = csv.writer(simanim_f)
    found = set()
    book_set = set()
    known_books = ["""ט"ז""", """ש"ע""",  """מג"א"""]
    prev_book = ""
    prev = 1
    prev_line = ""
    with open("extra_books.txt", 'w') as extra_books, open("simanim_in_our_text_but_not_list.txt", 'w') as simanim_in_our_text, open(file) as f:
        lines = list(f)
        for n, line in enumerate(lines):
            if line == "\r\n":
                continue
            seif_k_link = re.search("@11(.*?)@33", line)
            words = line.split()
            siman = None
            he_simans = ["", "", "1סי'", "1סימן", "סי'", "סימן"]
            has_siman = -1
            intro = " ".join(words[0:2])
            if ("סי'" in intro or "סימן" in intro) and (not "בסי" in intro and not "הסי" in intro):
                for i, word in enumerate(words[0:2]):
                    if "סי" in word:
                        has_siman = i
                        break

            # if len(words) <= 2 and not seif_k:
            #     siman = getGematria(words[-1])
            # elif (line.startswith("@") or line[0].isdigit()) and has_siman > -1:
            #     siman = getGematria(words[has_siman+1])
            if "@22" in line and len(words) <= 2 and not seif_k_link:
                siman = words[-1]
            elif "@22" in line and has_siman > -1:
                siman = words[has_siman+1]
            if not siman and getGematria(words[0]) == prev + 1:
                pass
            if siman:
                #assert siman > prev or not siman < prev - 5
                third = ""
                if siman <= prev:
                    third = "X"
                siman = getGematria(siman)
                found.add(siman)
                if siman not in actual_simanim_gematrias:
                    simanim_in_our_text.write(line)
                simanim.writerow([siman, line, third])
                prev = siman
                prev_line = n

            if seif_k_link:
                seif_k_link = seif_k_link.group(1)
                seif_k_link = seif_k_link.replace("(#)", "").strip()
                seif_k_link = seif_k_link.replace("מגן אברהם", """מג"א""")
                seif_k_link = seif_k_link.replace("""סק""", """ס"ק """)
                seif_k_link = seif_k_link.replace("שם", prev_book)
                if len(seif_k_link.split()) == 3:
                    book = seif_k_link.split()[0]
                    seif_k = seif_k_link.split()[-1]
                    if book in ["""ס"ק""", "סעיף"]:
                        seif_k = seif_k_link.split()[1]
                        book = seif_k_link.split()[2]

                    book = replacements(book, prev_book)
                    for known_book in known_books:
                        if known_book in book:
                            book = known_book
                            break
                    if book not in known_books:
                         extra_books.write(re.search("@11(.*?)@33", line).group(1)+"\n")
                    prev_book = book
                elif len(seif_k_link.split()) == 2:
                    book = prev_book
                    seif_k = seif_k_link.split()[-1]
                else:
                    pass


        with open("simanim_in_list_but_in_our_text.txt", 'w') as simanim_in_list:
            for siman, siman_gematria in zip(actual_simanim, actual_simanim_gematrias):
                if siman_gematria not in found:
                    simanim_in_list.write(siman+"\n")



    # with open("yoreh deah helek bet.txt") as f:
    #     for line in f:
    #         line = line.decode('utf-8')
    #         if line.startswith("@22"):
    #             siman = re.search(u"סימן (.*?)[\s|^]", line)
    #             seif = re.search(u"סעיף (.*?)[\s|^]", line)
    #             if siman:
    #                 siman = getGematria(siman.group(1))
    #                 assert siman not in text.keys()
    #                 current_siman = siman
    #                 text[current_siman] = {}
    #                 current_seif = 1
    #                 text[current_siman][current_seif] = []
    #             if seif:
    #                 seif = getGematria(seif.group(1))
    #                 current_seif = seif
    #                 if current_seif not in text[current_siman].keys():
    #                     text[current_siman][current_seif] = []
    #         elif line.startswith("@11"):
    #             text[current_siman][current_seif].append(removeAllTags(line))
    # pass
