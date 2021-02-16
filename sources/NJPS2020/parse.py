from sources.functions import *
from docx2python import docx2python
from bs4 import BeautifulSoup


def get_body_html(document, ftnotes):
    def add_pasukim(str, pasukim):
        pasukim = re.split("<font size=\"\d+\">[\d ]+</font>", comment)
        if re.search("<font size=\"\d+\">[\d ]+</font>", comment) is None:
            new_body[book][curr_perek][-1] += " "+pasukim[0].strip()
        else:
            for pasuk in pasukim:
                if len(pasuk.strip()) > 1:
                    new_body[book][curr_perek].append(pasuk.strip())

    new_body = {}
    book = ""
    curr_perek = 0
    footnotes_in_perek = False
    total = 0
    body = document.body[0][0][0]
    for c, comment in enumerate(body):
        comment = comment.replace("1 Kings", "I Kings").replace("2 Kings", "II Kings")
        if len(comment) > 0 and is_index(BeautifulSoup(comment).text):
            book = comment
            new_body[book] = {}
            total += curr_perek
            curr_perek = 0
            footnotes_in_perek = False
        elif len(book) > 0 and not comment.startswith("BOOK"):
            full_perek = re.search("<font size=\"\d+\"><b>\d+[ \t]*\d?</b></font>", comment)
            perek = re.search("<b>(\d+)[ \t]*\d?</b>", comment)
            pasukim = re.findall("<font size=\"\d+\">[\d ]+</font>", comment)
            if perek:
                if not comment.startswith(full_perek.group(0)):
                    before, comment = comment.split(perek.group(0))
                    add_pasukim(before, pasukim)
                    comment = perek.group(0) + comment
                if curr_perek > 0 and not footnotes_in_perek:
                    ftnotes.insert(curr_perek + total - 1, {})
                perek_group_1 = perek.group(1).strip()
                if curr_perek > 0:
                    assert int(perek_group_1) - 1 in new_body[book]
                curr_perek = int(perek_group_1)
                new_body[book][curr_perek] = []
                comment = comment.replace(full_perek.group(0), "")
                footnotes_in_perek = False
            for match in re.finditer("-{1,}footnote(\d+)-{1,}", comment):
                comment = comment.replace(match.group(0), "--footnote--")
                footnotes_in_perek = True
            for match in re.finditer("<i>([a-z]{1})-{1,}</i>.+<i>-([a-z]{1})</i>", comment):
                footnotes_in_perek = True

            add_pasukim(comment, pasukim)
    return new_body, ftnotes

def get_footnotes(document):
    ftnotes = list(document.footnotes[0][0][0])
    new_ftnotes = {}
    last_ftnote = ""
    curr = 0
    for i, ftnote in enumerate(ftnotes):
        if not ftnote or not " " in ftnote:
            continue
        ftnote = BeautifulSoup(ftnote).text
        basic_pattern = re.search("([a-z]{1}) (.+)", ftnote)
        dash_pattern = re.search("([a-z]{1})-[a-z]{1} (.+)", ftnote)
        pattern = basic_pattern if basic_pattern else dash_pattern
        if pattern:
            ftnote = pattern.group(1)
            comment = pattern.group(2)
            last_ftnote = ftnote
            if last_ftnote == "a":
                curr += 1
                new_ftnotes[curr] = {}
        else:
            comment = ftnote
            ftnote = chr(ord(last_ftnote)+1)
            last_ftnote = ftnote
        new_ftnotes[curr][ftnote] = comment
    return convertDictToArray(new_ftnotes)



def insert_ftnotes_html(body, ftnotes):
    pass

def get_body_insert_ftnotes(body, ftnotes):
    def ftnote_range(match, pasuk):
        char = match.group(1)
        if char == match.group(2):
            relevant_ftnote = ftnotes_perek[char]
            relevant_ftnote = '<sup>{}</sup><i class="footnotes">{}</i>'.format(char, relevant_ftnote)
            pasuk = pasuk.replace(match.group(0),
                                  '<sup>{}</sup><i class="footnotes">{}</i>'.format(char, relevant_ftnote))
        return pasuk
    new_body = {}
    curr = 0
    #ftnotes = re.findall("<i>-{1,}footnote\d+-{1,}[a-z]{1}</i>", comment)
    for book in body:
        new_body[book] = {}
        for perek in body[book]:
            new_body[book][perek] = []
            ftnotes_perek = ftnotes[curr]
            curr += 1

            for p, pasuk in enumerate(body[book][perek]):
                double_ftnotes = list(re.finditer("<i>([a-z]{1})</i>.+footnote.+<i>-([a-z]{1})</i>", pasuk)) + list(
                    re.finditer("<i>([a-z]{1})-{1,}</i>.+<i>-([a-z]{1})</i>", pasuk)) + list(
                    re.finditer("<i>([a-z]{1})-{1,}footnote-{1,}.+<i>-([a-z]{1})</i>", pasuk))

                for match in double_ftnotes:
                    pasuk = ftnote_range(match, pasuk)

                for match in re.finditer("<i>--footnote--([a-z]{1})</i>", pasuk):
                    char = match.group(1)
                    relevant_ftnote = ftnotes_perek[char]
                    relevant_ftnote = '<sup>{}</sup><i class="footnotes">{}</i>'.format(char, relevant_ftnote)
                    pasuk = pasuk.replace(match.group(0),
                                          '<sup>{}</sup><i class="footnotes">{}</i>'.format(char, relevant_ftnote))


                new_body[book][perek].append(pasuk)

    return new_body


def check_for_ftnotes(body):
    for book in body:
        for perek in body[book]:
            for pasuk in body[book][perek]:
                if "footnote" in pasuk:
                    print("{} {}:{}".format(book, perek, pasuk))

bible_sections = [ref.normal() for el in library.get_indexes_in_category("Tanakh") for ref in library.get_index(el).all_section_refs()]
start_at = 0
document = docx2python("JPS.docx", html=True)
ftnotes = get_footnotes(document)
body, ftnotes = get_body_html(document, ftnotes)
body = get_body_insert_ftnotes(body, ftnotes)
check_for_ftnotes(body)
