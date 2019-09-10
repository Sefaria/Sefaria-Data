#encoding=utf-8
import django
django.setup()
import re
from sefaria.model import *
from sources.functions import *
from sefaria.system.exceptions import *

base_title = "Shulchan Arukh, Orach Chayim"
links = []
def combine_files(dir):
    with open(dir+"/aleph.txt") as a:
        with open(dir+"/bet.txt") as b:
            with open(dir+"/gimmel.txt") as g:
                lines = list(a) + list(b) + list(g)
                with open("{}.txt".format(dir), 'w') as new_file:
                    new_file.writelines(lines)

def replacements(book, prev_book):
    book = book.replace("""מ"ה""", "Magen Avraham")
    book = book.replace("""מ"ק""", "Magen Avraham")
    book = book.replace("""רמ"א""", base_title)
    book = book.replace("""מ"א""", """מג"א""").replace("מא", """מג"א""").replace("""מ'"א""", """מג"א""")
    book = book.replace("""מחבר""", """ש"ע""")
    book = book.replace("""הג"ה""", """ש"ע""").replace("הגה", """ש"ע""")
    book = book.replace("""שו"ע""", """ש"ע""")
    book = book.replace("""רמ"א""", """ש"ע""")
    book = book.replace("""ט"ז""", "Turei Zahav on Shulchan Arukh, Orach Chayim")
    book = book.replace("""מג"א""", "Magen Avraham")
    book = book.replace("""ש"ע""", base_title)
    book = book.strip()
    match = re.search("[a-zA-Z\s,]+", book)
    return match.group(0) if match else None


def get_book_and_seif(seif_k_link, prev_book, curr_siman_seif):
    def get_seif(str, book):
        seif_marker = 'ס'
        if str.startswith(seif_marker):
            str = str.replace(seif_marker, "")
            # assert book == base_title
        if str == 'שם':
            return curr_siman_seif[book][1]
        else:
            value = getGematria(str)
            return value
    seif_k = None
    seif_k_link = seif_k_link.replace("מגן אברהם", """מג"א""")
    seif_k_link = seif_k_link.replace(" עסעיף", "סעיף")
    seif_k_link = seif_k_link.replace("סס", "ס").replace("רס", "ס").replace('ס"ס', "סעיף")
    seif_k_link = seif_k_link.replace("""סק""",  "סעיף").replace("""ס"ק""", "סעיף")
    seif_k_link = seif_k_link.replace("זיין", "ז").replace("]", "").replace("[", "").replace('\' ', "")
    seif_markers = ["סעיף"]
    for word in seif_markers:
        if word in seif_k_link and not word + " " in seif_k_link:
            seif_k_link = seif_k_link.replace(word, word + " ")
    seif_k_link = seif_k_link.strip()
    if "שם" not in seif_k_link:
        book = seif_k_link.split()[0]
        if seif_k_link.count(" ") == 0: #assume it's just a book
            book = replacements(seif_k_link, prev_book)
            seif_k = curr_siman_seif.get("book", (1, 1))[1]
        else:
            book = replacements(book, prev_book)
            if not book:
                book = base_title
            word_seif = "סעיף"
            if word_seif in seif_k_link.split():
                print seif_k_link
                pos = seif_k_link.split().index(word_seif)
            else:
                pos = len(seif_k_link.split())
                for i, word in enumerate(seif_k_link.split()):
                    if word.startswith('ס'):
                        pos = i-1
                        break
            seif_k = get_seif(seif_k_link.split()[pos+1], book)
    else:
        seif_k_link = seif_k_link.replace(" סעיף ", "")
        if seif_k_link.count(" ") == 1:
            non_sham_word = seif_k_link.replace('שם', "").strip()
            book = replacements(non_sham_word, prev_book)
            if not book:
                seif_k = get_seif(non_sham_word, book)
                return (prev_book, seif_k)
            else:
                return (book, curr_siman_seif[book][1])
        elif seif_k_link.count(" ") == 0:
            book = prev_book
            seif_k = prev_seif_k
        else:
            print seif_k_link
            return (None, 1)
    return (book, seif_k)

def create_link(book, siman, seif_k, curr_pos_in_levushei):
    levushei_ref = "Levushei Serad on {} {}:{}".format(base_title, siman, curr_pos_in_levushei)
    base_ref = Ref("{} {}:{}".format(book, siman, seif_k)).normal()
    links.append((base_ref, levushei_ref))
    if book != base_title:
        link = Link().load({"$and": [{"refs": {"$regex": base_ref}},
                              {"refs": {"$regex": "^Shulchan Arukh, Orach"}}]})
        if link:
            shulchan_ref = link.refs[0] if link.refs[0].startswith("Shulchan") else link.refs[1]
            links.append((shulchan_ref, levushei_ref))
        else:
            print "NO LINK! Didn't find link between Shulchan Aruch and {}".format(base_ref)



if __name__ == "__main__":
    file = "CSV Levushei Serad/Levushei Serad on Shulchan Arukh, Orach Chaim.csv"
    simanim_f = open("{}_simanim.csv".format(file.split()[0]), 'w')
    with open("Levushei Serad/list of simanim.csv") as f:
        actual_simanim = [el.replace("\r\n", "") for el in list(f)]
        actual_simanim_gematrias = [getGematria(el) for el in actual_simanim]
    simanim = csv.writer(simanim_f)
    found = set()
    book_set = set()
    known_books = ["Turei Zahav on " + base_title, base_title, "Magen Avraham"]
    prev_book = base_title
    prev_siman = 1
    prev_seif_k = 1
    curr_siman_seif = {book: (1, 1) for book in known_books}
    prev_line = ""
    text = {}
    base_text = file.split(" on ")[-1][0:-4]
    with open("extra_books.txt", 'w') as extra_books, open("simanim_in_our_text_but_not_list.txt", 'w') as simanim_in_our_text, open("errors.csv", 'w') as errors, open(file) as f:
        reader = csv.reader(f)
        rows = list(reader)
        errors_csv = csv.writer(errors)
        for n, row in enumerate(rows):
            print n
            siman = row[0]
            line = row[4]
            words = line.split()
            if siman:
                #assert siman > prev or not siman < prev - 5
                siman = siman.replace('סימן', '').replace("@22", "").strip()
                if siman.count(" ") == 1:
                    siman = siman.split()[-1]
                found_siman = getGematria(siman)
                text[found_siman] = []
                if siman not in actual_simanim_gematrias:
                    simanim_in_our_text.write(line)
                #simanim.writerow([siman, line, third])
                prev_line = n

            if line == "":
                continue

            text[found_siman].append(line)

            seif_k_re = re.search("@11(.*?)@33", line)
            if not seif_k_re:
                errors_csv.writerow([n+1, "No clear @11...@33 format", line])
            else:
                seif_k_link = seif_k_re.group(1)
            seif_k_link = re.sub("[\(#\)\.\:]{1,3}", "", seif_k_link).strip()
            line = re.sub("@11\((.*?)\)@33", "", line).strip()
            if seif_k_link:
                try:
                    found_book, found_seif_k = get_book_and_seif(seif_k_link, prev_book, curr_siman_seif)
                except IndexError as e:
                    print e.message
                    continue
                if not found_book:
                    found_book = base_title
                curr_siman, curr_seif = curr_siman_seif[found_book]
                try:
                    siman_greater = found_siman - curr_siman >= 0
                    seif_greater = found_seif_k - curr_seif >= 0
                    assert seif_greater or siman_greater
                except AssertionError as e:
                    errors_csv.writerow([n+1, "Problem with siman/seif katan number", line])
                    continue
                try:
                    for poss_book in [found_book]+known_books:
                        found_text = Ref("{} {}:{}".format(poss_book, found_siman, found_seif_k)).text('he').text
                        if found_text:
                            found_book = poss_book
                            break
                    assert found_text
                except AssertionError:
                    errors_csv.writerow([n+1, "Invalid Ref: {}".format(Ref("{} {}:{}".format(found_book, found_siman, found_seif_k)).normal()), line])
                    continue

                curr_siman_seif[found_book] = (found_siman, found_seif_k)
                curr_pos_in_levushei_siman = len(text[found_siman])
                create_link(found_book, found_siman, found_seif_k, curr_pos_in_levushei_siman)
        prev_book = found_book

        with open("simanim_in_list_but_in_our_text.txt", 'w') as simanim_in_list:
            for siman, siman_gematria in zip(actual_simanim, actual_simanim_gematrias):
                if siman_gematria not in found:
                    simanim_in_list.write(siman+"\n")

    print("check links")

