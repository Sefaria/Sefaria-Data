#encoding=utf-8
import django
django.setup()
import re
from sefaria.model import *
from sources.functions import *
import timeit
import time
from sefaria.system.exceptions import *
from collections import Counter
from numpy import *
base_title = "Shulchan Arukh, Orach Chayim"
links = []
root = JaggedArrayNode()
root.add_primary_titles("Levushei Serad on Shulchan Arukh, Orach Chayim", u"לבושי שרד על שלחן ערוך אורח חיים")
root.key = "Levushei Serad on Shulchan Arukh, Orach Chayim"
root.add_structure(["Siman", "Paragraph"])
root.validate()
indx = {
    "title": root.key,
    "schema": root.serialize(),
    "categories": ["Halakhah", "Shulchan Arukh", "Commentary", "Levushei Serad"]
}
post_index(indx)

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
    seif_k_link = seif_k_link.replace("""ס"ק""", """סק""")
    seif_k_link = seif_k_link.replace("זיין", "ז").replace("]", "").replace("[", "").replace('\' ', "")
    seif_markers = ["סעיף", """סק"""]
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
                book = prev_book
            pos = None
            for word_seif in seif_markers:
                if word_seif in seif_k_link.split():
                    pos = seif_k_link.split().index(word_seif)
                    seif_k = get_seif(seif_k_link.split()[pos+1], book)
            if not seif_k:
                seif_k = get_seif(seif_k_link.split()[-1], book)
    else:
        seif_k_link = seif_k_link.replace(" סעיף ", "")
        if seif_k_link.count(" ") == 1:
            non_sham_word = seif_k_link.replace('שם', "").strip()
            book = replacements(non_sham_word, prev_book)
            if not book:
                seif_k = get_seif(non_sham_word, book)
                book = prev_book
            else:
                seif_k = curr_siman_seif[book][1]
        elif seif_k_link.count(" ") == 0:
            book = prev_book
            seif_k = curr_siman_seif[found_book][1]
        else:
            book = None
            seif_k = -1
    return (book, seif_k)

def create_SA_link(book, base_ref, curr_pos_in_levushei):
    # base_ref = Ref("{} {}:{}".format(book, siman, seif_k)).normal()
    # links.append((base_ref, levushei_ref))
    siman = base_ref.split()[-1].rsplit(":", 1)[0]
    levushei_ref = "Levushei Serad on {} {}:{}".format(base_title, siman, curr_pos_in_levushei)
    links.append({"refs": [levushei_ref, base_ref], "auto": "True", "type": "Commentary", "generated_by": "levushei_serad"})
    if book != base_title:
        link = Link().load({"$and": [{"refs": {"$regex": base_ref}},
                              {"refs": {"$regex": "^Shulchan Arukh, Orach"}}]})
        if link:
            shulchan_ref = link.refs[0] if link.refs[0].startswith("Shulchan") else link.refs[1]
            links.append({"refs": [levushei_ref, shulchan_ref], "auto": "True", "type": "Commentary", "generated_by": "levushei_serad"})
            #links.append((shulchan_ref, levushei_ref))
        else:
            print "NO LINK! Didn't find link between Shulchan Aruch and {}".format(base_ref)

prev_row = 0

def write_row(row, n, prev_row):
    if n - prev_row != 0:
        prev_row = n
        print n
    #writer.writerow(row)
    prev_row += 1
    return prev_row

if __name__ == "__main__":
    file = "CSV Levushei Serad/Levushei Serad 9_23_19.csv"
    new_file = file[0:-4] + "_NEW.csv"
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
    with open("extra_books.txt", 'w') as extra_books, \
    open("simanim_in_our_text_but_not_list.txt", 'w') as simanim_in_our_text, \
    open("errors.csv", 'w') as errors, open(new_file, 'w') as new_csv, open(file) as f:
        reader = csv.reader(f)
        writer = csv.writer(new_csv)
        rows = list(reader)
        errors_csv = csv.writer(errors)
        prev_row = 0
        time_to_run = {}
        before = None
        for n, row in enumerate(rows):
            if not before:
                before = time.time()
            else:
                time_to_run[n-1] = time.time() - before
                before = time.time()
            if n % 100 == 0:
                print(n)
            siman = row[0]
            line = row[4]
            link = row[5]
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
                prev_row = write_row(row, n, prev_row)
                continue



            seif_k_re = re.search("@11(.*?)@33", line)
            if not seif_k_re:
                prev_row = write_row(row, n, prev_row)
                #errors_csv.writerow([n+1, "No clear @11...@33 format", line])
            else:
                seif_k_link = seif_k_re.group(1)
            seif_k_link = re.sub("[\(#\)\.\:]{1,3}", "", seif_k_link).strip()
            assert '@11' in line and '@33' in line
            line = line.replace("@11", "<small>").replace("@33", "</small>")
            text[found_siman].append(line)
            if seif_k_link:
                try:
                    found_book, found_seif_k = get_book_and_seif(seif_k_link, prev_book, curr_siman_seif)
                except IndexError as e:
                    #prev_row = write_row(row, n, prev_row)
                    print e.message
                    continue
                if not found_book:
                    found_book = base_title
                curr_siman, curr_seif = curr_siman_seif[found_book]
                try:
                    siman_greater = found_siman - curr_siman >= 0
                    seif_greater = found_seif_k - curr_seif >= 0
                    assert seif_greater or siman_greater
                    assert found_seif_k >= 1
                except AssertionError as e:
                    #prev_row = write_row(row, n, prev_row)
                    #errors_csv.writerow([n+1, "Problem with siman/seif katan number", line])
                    continue
                try:
                    for poss_book in [found_book]+known_books:
                        found_text = Ref("{} {}:{}".format(poss_book, found_siman, found_seif_k)).text('he').text
                        if found_text:
                            found_book = poss_book
                            break
                    assert found_text
                except AssertionError:
                    prev_row = write_row(row, n, prev_row)
                    #errors_csv.writerow([n+1, "Invalid Ref: {}".format(Ref("{} {}:{}".format(found_book, found_siman, found_seif_k)).normal()), line])
                    continue

                if found_book != base_title:
                    prev_book = found_book
                curr_siman_seif[found_book] = (found_siman, found_seif_k)
                curr_pos_in_levushei_siman = len(text[found_siman])
                create_SA_link(found_book, link, curr_pos_in_levushei_siman)
                prev_row = write_row(row+[link], n, prev_row)
            else:
                prev_row = write_row(row, n, prev_row)
                pass



    print("check links")
    text = convertDictToArray(text)
    send_text = {
        "text": text,
        "versionTitle": "Maginei Eretz: Shulchan Aruch Orach Chaim, Lemberg, 1893",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002084080",
        "language": 'he'
    }
    #post_text("Levushei Serad on Shulchan Arukh, Orach Chayim", send_text)
    post_link(links)
    print std(time_to_run.values())
    print mean(time_to_run.values())
    print max(time_to_run.values())
    print min(time_to_run.values())