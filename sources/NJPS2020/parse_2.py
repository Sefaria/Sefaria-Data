from sources.functions import *
from docx2python import docx2python
from bs4 import BeautifulSoup


def get_body_html(document, ftnotes):
    def add_pasukim(str, pasukim):
        pasukim = re.split("<font size=\"\d+\">[\d ]+</font>", str)
        if re.search("<font size=\"\d+\">[\d ]+</font>", str) is None:
            new_body[book][curr_perek][-1] += " "+pasukim[0].strip()
        else:
            for pasuk in pasukim:
                if len(pasuk.strip()) > 1:
                    new_body[book][curr_perek].append(pasuk.strip())

    def are_ftnotes_in_perek(perek):
        if len(perek) == 0:
            return True
        for comment in perek:
            matches = list(re.finditer("-{1,}footnote\d*-{1,}", comment)) + list(re.finditer("<i>([a-z]{1})-{1,}</i>.+<i>-([a-z]{1})</i>", comment))
            if len(matches) > 0 or "footnote" in comment:
                return True
        return False

    new_body = {}
    book = ""
    curr_perek = 0
    last_perek = []
    total = 0
    body = document.body[0][0][0]
    for c, comment in enumerate(body):
        comment = comment.replace("1 Kings", "I Kings").replace("2 Kings", "II Kings")
        if len(comment) > 0 and is_index(BeautifulSoup(comment).text):
            last_perek = new_body[book].get(curr_perek, []) if len(book) > 0 else []
            book = comment
            new_body[book] = {}
            total += curr_perek
            curr_perek = 0
        elif len(book) > 0 and not comment.startswith("BOOK"):
            full_perek = re.search("<font size=\"\d+\"><b>\d+[ \t]*\d?</b></font>", comment)
            perek = re.search("<b>(\d+)[ \t]*\d?</b>", comment)
            pasukim = re.findall("<font size=\"\d+\">[\d ]+</font>", comment)
            if perek:
                if curr_perek > 0:
                    last_perek = new_body[book].get(curr_perek, [])
                if not comment.startswith(full_perek.group(0)):
                    before, comment = comment.split(perek.group(0))
                    add_pasukim(before, pasukim)
                    comment = perek.group(0) + comment

                if not are_ftnotes_in_perek(last_perek):
                    ftnotes.insert(curr_perek + total - 1, {})
                perek_group_1 = perek.group(1).strip()
                if curr_perek > 0:
                    assert int(perek_group_1) - 1 in new_body[book]
                curr_perek = int(perek_group_1)
                new_body[book][curr_perek] = []
                comment = comment.replace(full_perek.group(0), "")


            add_pasukim(comment, pasukim)
    return new_body, ftnotes
#
# def get_footnotes(document):
#     ftnotes = list(document.footnotes[0][0][0])
#     new_ftnotes = {}
#     last_ftnote = ""
#     curr = 0
#     for i, ftnote in enumerate(ftnotes):
#         if not ftnote or not " " in ftnote:
#             continue
#         ftnote = BeautifulSoup(ftnote).text
#         basic_pattern = re.search("([a-z]{1}) (.+)", ftnote)
#         dash_pattern = re.search("([a-z]{1})-[a-z]{1} (.+)", ftnote)
#         pattern = basic_pattern if basic_pattern else dash_pattern
#         if pattern:
#             ftnote = pattern.group(1)
#             comment = pattern.group(2)
#             last_ftnote = ftnote
#             if last_ftnote == "a":
#                 curr += 1
#                 new_ftnotes[curr] = {}
#         else:
#             comment = ftnote
#             ftnote = chr(ord(last_ftnote)+1)
#             last_ftnote = ftnote
#         new_ftnotes[curr][ftnote] = comment
#     return convertDictToArray(new_ftnotes)



def get_body_insert_ftnotes(body, ftnotes):
    def ftnote_range(match, pasuk, book, found_ftnotes):
        char = match.group(1)
        double_ftnote_exist = False
        if char == match.group(2):
            double_ftnote_exist = True
            relevant_ftnote = ftnotes_perek[char]
            found_ftnotes.writerow([book, relevant_ftnote])
            i_tag = '<sup>{}</sup><i class="footnotes">{}</i>'.format(char, relevant_ftnote)
            first_regexes = ["<i>([a-z]{1})</i>", "<i>([a-z]{1})-{1,}</i>", "<i>([a-z]{1})-{1,}footnote\d*-{1,}</i>",
                             "<i>-{1,}footnote\d*-{1,}([a-z]{1}</i>)"]
            ending_regexes = ["<i>-?([a-z]{1})</i>"]
            #first replace beginning parts with actual i_tag
            #then replace ending parts with <sup>char</sup>
            for regex in first_regexes:
                if re.search(regex, pasuk) and re.search(regex, pasuk).group(1) == char:
                    pasuk = re.sub(regex, i_tag, pasuk)
            for regex in ending_regexes:
                if re.search(regex, pasuk) and re.search(regex, pasuk).group(1) == char:
                    pasuk = re.sub(regex, "<sup>-{}</sup>".format(char), pasuk)
        return pasuk, double_ftnote_exist

    new_body = {}
    curr = 0
    with open("found_ftnotes.csv", 'w') as found_ftnote_f:
        found_ftnotes = csv.writer(found_ftnote_f)
        for book in body:
            new_body[book] = {}
            for perek in body[book]:
                new_body[book][perek] = []
                ftnotes_perek = ftnotes[curr]
                curr += 1
                last_char_double_ftnotes_spread_across_pasukim = ""

                for p, pasuk in enumerate(body[book][perek]):
                    double_ftnotes = list(re.finditer("<i>([a-z]{1})</i>.*?footnote\d*.*?<i>-?([a-z]{1})</i>", pasuk)) + list(
                        re.finditer("<i>([a-z]{1})-{1,}</i>.*?<i>-?([a-z]{1})</i>", pasuk)) + list(
                        re.finditer("<i>([a-z]{1})-{1,}footnote\d*-{1,}</i>.*?<i>-?([a-z]{1})</i>", pasuk)) + list(
                        re.finditer("<i>-{1,}footnote\d*-{1,}([a-z]{1})</i>.*?<i>-?([a-z]{1})</i>", pasuk))

                    double_ftnote_exist = False
                    for match in double_ftnotes:
                        pasuk, double_ftnote_exist = ftnote_range(match, pasuk, book, found_ftnotes)


                    for match in re.finditer("<.*?>-{1,}footnote\d*-{1,}([a-z]{1})</.*?>", pasuk):
                        char = match.group(1)
                        relevant_ftnote = ftnotes_perek[char]
                        found_ftnotes.writerow([book, relevant_ftnote])
                        relevant_ftnote = '<sup>{}</sup><i class="footnotes">{}</i>'.format(char, relevant_ftnote)
                        pasuk = pasuk.replace(match.group(0),
                                              relevant_ftnote)
                    for match in re.finditer("<.*?>([a-z]{1})-{1,}footnote\d*-{1,}</.*?>", pasuk):
                        char = match.group(1)
                        relevant_ftnote = ftnotes_perek[char]
                        found_ftnotes.writerow([book, relevant_ftnote])
                        relevant_ftnote = '<sup>{}</sup><i class="footnotes">{}</i>'.format(char, relevant_ftnote)
                        pasuk = pasuk.replace(match.group(0),
                                              relevant_ftnote)

                    if double_ftnote_exist == False and len(last_char_double_ftnotes_spread_across_pasukim) > 0:
                        if re.search("<i>-[a-z]{1}</i>", pasuk):
                            pasuk = pasuk.replace(re.search("<i>-[a-z]{1}</i>", pasuk).group(0), "<sup>{}</sup>".format(last_char_double_ftnotes_spread_across_pasukim))
                            last_char_double_ftnotes_spread_across_pasukim = ""
                    if double_ftnote_exist == False:
                        for only_first_match in ["<i>([a-z]{1})</i>", "<i>([a-z]{1})-{1,}</i>",
                                                 "<i>([a-z]{1})-{1,}footnote\d*-{1,}</i>"]:
                            if re.search(only_first_match, pasuk):
                                m = re.search(only_first_match, pasuk)
                                char = m.group(1)
                                last_char_double_ftnotes_spread_across_pasukim = char
                                relevant_ftnote = ftnotes_perek[last_char_double_ftnotes_spread_across_pasukim]
                                found_ftnotes.writerow([book, relevant_ftnote])
                                pasuk = pasuk.replace(match.group(0), relevant_ftnote)

                    pasuk = re.sub("-{1,}footnote\d*-{1,}", "", pasuk)





                    new_body[book][perek].append(pasuk)

    return new_body


def check_for_ftnotes(body):
    found = []
    with open("found_ftnotes.csv", 'r') as f:
        for row in csv.reader(f):
            ftnote_found = row[1]
            found.append(ftnote_found)
    with open("ftnotes.csv", 'r') as orig_f:
        for row in csv.reader(orig_f):
            if len(row) > 1:
                perek, orig_ftnote_marker, orig_ftnote = row
                if orig_ftnote not in found:
                    if len(orig_ftnote) > 2:
                        print(row)
                    else:
                        print("Strange case")


bible_sections = [ref.normal() for el in library.get_indexes_in_category("Tanakh") for ref in library.get_index(el).all_section_refs()]
start_at = 0
document = docx2python("JPS.docx", html=True)
ftnotes = {}
increment_perek = 0
heb_uncertain = 0
with open("ftnotes.csv", 'r') as f:
    for row in csv.reader(f):
        heb_uncertain = 0
        if row[0] == "increment":
            increment_perek += 1
        elif row[0] == "decrement":
            increment_perek -= 1
        else:
            perek, ftnote, comm = row
            perek = int(perek) + increment_perek
            if perek not in ftnotes:
                ftnotes[perek] = {}
            ftnotes[perek][ftnote] = comm
ftnotes = convertDictToArray(ftnotes)
body, ftnotes = get_body_html(document, ftnotes)
body = get_body_insert_ftnotes(body, ftnotes)
check_for_ftnotes(body)
