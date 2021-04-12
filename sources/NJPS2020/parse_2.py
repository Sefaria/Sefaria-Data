from sources.functions import *
from docx2python import docx2python
import difflib
from bs4 import BeautifulSoup
import time


def get_body_html(document, ftnotes):
    def add_pasukim(str):
        str = str.replace("<b></b>", "").replace("<i></i>", "")
        pasukim = re.split("<font size=\"\d+\">[\d\t ]+</font>", str)
        if re.search("<font size=\"\d+\">[\d\t ]+</font>", str) is None:
            pasukim[0] = re.sub("<font size=\"\d+\">", "", pasukim[0])
            pasukim[0] = re.sub("</font>", "", pasukim[0])
            pasukim[0] = pasukim[0].replace("LORD", "L<small>ORD</small>")
            new_body[book][curr_perek][-1] += "<br/>" +pasukim[0].strip()
        else:
            pasukim[0] = re.sub("<font size=\"\d+\">", "", pasukim[0])
            pasukim[0] = re.sub("</font>", "", pasukim[0])
            pasukim[0] = pasukim[0].replace("LORD", "L<small>ORD</small>")
            if len(pasukim[0].strip()) > 2:
                if len(new_body[book][curr_perek]) == 0:
                    new_body[book][curr_perek] = [pasukim[0].strip()]
                else:
                    new_body[book][curr_perek][-1] += "<br/>" + pasukim[0].strip()
            for p, pasuk in enumerate(pasukim):
                if p == 0:
                    continue
                if len(pasuk.strip()) > 1:
                    pasuk = pasuk.strip()
                    pasuk = re.sub("<font size=\"\d+\">", "", pasuk)
                    pasuk = re.sub("</font>", "", pasuk)
                    pasuk = pasuk.replace("LORD", "L<small>ORD</small>")
                    if pasuk.endswith("(") and ")" in pasukim[p+1]:
                        pasuk = pasuk[:-1]
                        pasukim[p+1] = "("+pasukim[p+1]
                    new_body[book][curr_perek].append(pasuk)

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
        comment = comment.replace(chr(8195), " ")
        comment = re.sub("[\u05d0-\u05ea]{1,}", "", comment)
        if len(comment) > 0 and is_index(BeautifulSoup(comment).text):
            last_perek = new_body[book].get(curr_perek, []) if len(book) > 0 else []
            book = comment
            new_body[book] = {}
            total += curr_perek
            curr_perek = 0
        elif comment.isupper() == False and len(book) > 0 and not comment.startswith("BOOK"):
            full_perek = re.search("<font size=\"\d+\"><b>\d+[ \t]*\d?</b></font>", comment)
            perek = re.search("<b>(\d+)[ \t]*\d?</b>", comment)
            if perek:
                if curr_perek > 0:
                    last_perek = new_body[book].get(curr_perek, [])
                if not comment.startswith(full_perek.group(0)):
                    before, comment = comment.split(perek.group(0))
                    add_pasukim(before)

                if not are_ftnotes_in_perek(last_perek):
                    ftnotes.insert(curr_perek + total - 1, {})
                perek_group_1 = perek.group(1).strip()
                if curr_perek > 0:
                    assert int(perek_group_1) - 1 in new_body[book]
                curr_perek = int(perek_group_1)
                new_body[book][curr_perek] = []
                comment = comment.replace(full_perek.group(0), "")


            add_pasukim(comment)
    return new_body, ftnotes

def get_body_insert_ftnotes(body, ftnotes):
    def ftnote_range(match, pasuk, book, found_ftnotes):
        char = match.group(1)
        double_ftnote_exist = False
        if char == match.group(2):
            double_ftnote_exist = True
            relevant_ftnote = ftnotes_perek[char]
            found_ftnotes.writerow([book, relevant_ftnote])
            i_tag = '<sup>{}</sup><i class="footnote">{}</i>'.format(char, relevant_ftnote)
            first_regexes = ["<i>([a-z]{1})</i>", "<i>([a-z]{1})-{1,}</i>", "<i>([a-z]{1})-{1,}footnote\d*-{1,}</i>",
                             "<i>-{1,}footnote\d*-{1,}([a-z]{1}</i>)"]
            ending_regexes = ["<i>-?([a-z]{1})[\s-]?</i>"]
            #first replace beginning parts with actual i_tag
            #then replace ending parts with <sup>char</sup>
            if re.search("<i>.*?(-{1,}footnote\d*-{1,}).*?</i>", pasuk):
                pasuk = pasuk.replace(re.search("<i>.*?(-{1,}footnote\d*-{1,}).*?</i>", pasuk).group(1), "", 1)
            for regex in first_regexes:
                if re.search(regex, pasuk) and re.search(regex, pasuk).group(1) == char:
                    pasuk = re.sub(regex, i_tag, pasuk, 1)
            for regex in ending_regexes:
                for poss_char in re.findall(regex, pasuk):
                    if poss_char == char:
                        pasuk = re.sub("<i>-?"+char+"\s?</i>", "<sup>-{}</sup>".format(char), pasuk, 1)
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
                    pasuk = pasuk.replace("\t", "")
                    double_ftnotes = list(re.finditer("<i>([a-z]{1})</i>.*?footnote\d*.*?<i>-?([a-z]{1})</i>", pasuk)) + list(
                        re.finditer("<i>([a-z]{1})-{1,}</i>.*?<i>-?([a-z]{1})</i>", pasuk)) + list(
                        re.finditer("<i>([a-z]{1})-{1,}footnote\d*-{1,}</i>.*?<i>-?([a-z]{1})</i>", pasuk)) + list(
                        re.finditer("<i>-{1,}footnote\d*-{1,}([a-z]{1})</i>.*?<i>-?([a-z]{1})</i>", pasuk))

                    double_ftnote_exist = False
                    for match in double_ftnotes:
                        pasuk, poss_double_ftnote_exist = ftnote_range(match, pasuk, book, found_ftnotes)
                        double_ftnote_exist = double_ftnote_exist or poss_double_ftnote_exist


                    one_tag_re = "<[\"a-zA-Z\d ]+>"
                    one_tag_closer_re = "</[\"a-zA-Z\d ]+>"
                    cases = [one_tag_re+"-{1,}footnote\d*-{1,}([a-z]{1})"+one_tag_closer_re,
                             one_tag_re+"([a-z]{1})-{1,}footnote\d*-{1,}"+one_tag_closer_re,
                            "<i>([a-z]{1})</i>",
                             "^-{1,}footnote\d*-{1,}([a-z]{1})",
                             "-{1,}footnote\d*-{1,}([a-z]{1})$"]
                    for case in cases:
                        for match in re.finditer(case, pasuk):
                            char = match.group(1)
                            relevant_ftnote = ftnotes_perek[char]
                            found_ftnotes.writerow([book, relevant_ftnote])
                            relevant_ftnote = '<sup>{}</sup><i class="footnote">{}</i>'.format(char, relevant_ftnote)
                            pasuk = pasuk.replace(match.group(0),
                                                  relevant_ftnote, 1)

                    for c, case in enumerate(["-{1,}footnote\d*-{1,}([a-z]{1})[ <—.;,A-Z]{1}"]):
                        for match in re.finditer(case, pasuk):
                            char = match.group(1)
                            relevant_ftnote = ftnotes_perek[char]
                            found_ftnotes.writerow([book, relevant_ftnote])
                            relevant_ftnote = '<sup>{}</sup><i class="footnote">{}</i>'.format(char, relevant_ftnote)
                            pasuk = re.sub("-{1,}footnote\d*-{1,}" + char, relevant_ftnote, pasuk, 1)


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
                                relevant_ftnote = '<sup>{}</sup><i class="footnote">{}</i>'.format(char,
                                                                                                   relevant_ftnote)
                                pasuk = pasuk.replace(m.group(0), relevant_ftnote)

                    for regex in ["<i>-?([a-z]{1})[\s-]?</i>"]:
                        for poss_char in re.findall(regex, pasuk):
                            pasuk = re.sub("<i>-?([a-z]{1})[\s-]?</i>", "<sup>-{}</sup>".format(poss_char), pasuk)
                    pasuk = re.sub("-{1,}footnote\d*-{1,}", "", pasuk)
                    new_body[book][perek].append(pasuk)

    return new_body


def post(body):
    def remove_ftnotes(pasuk):
        pasuk = re.sub("<sup>.{1,2}</sup><i class=\"footnote\">.*?</i>", "", pasuk)
        pasuk = re.sub("<sup>-?[a-z]{1}</sup>", "", pasuk)
        return pasuk
    probs = []
    wout_ftnotes = {}
    for book in body:
        try:
            library.get_index(book)
            title = book
        except:
            title = BeautifulSoup(book).text
        wout_ftnotes[book] = {}
        for perek in body[book]:
            wout_ftnotes[book][perek] = []
            for p, pasuk in enumerate(body[book][perek]):
                if "<font" in pasuk:
                    probs.add(book)
                wout_ftnotes[book][perek].append(remove_ftnotes(pasuk))
                our_text = TextChunk(Ref("{} {}:{}".format(title, perek, p+1)), lang='en', vtitle='Tanakh: The Holy Scriptures, published by JPS').text
                our_text = BeautifulSoup(our_text).text.lower().replace("  ", " ")
                new_text = wout_ftnotes[book][perek][-1].lower()
                our_text = BeautifulSoup("<body>{}</body>".format(our_text)).text
                new_text = BeautifulSoup("<body>{}</body>".format(new_text)).text
                results = [y for x, y in (enumerate(difflib.ndiff(our_text, new_text))) if y.startswith("+") or y.startswith("-")]
                if len(results) > 0:
                    extra = ""
                    for x, y in enumerate(difflib.ndiff(our_text, new_text)):
                        if not y[0].startswith(" "):
                            extra += y[-1]
                        elif len(extra) > 0 and extra[-1] != "\n":
                            extra += "\n"
                    for char in ['’', '.', '’', '-', '\n', '—', ':', ',', ';', '(', ')', '?']:
                        extra = extra.replace(char, "")
                    extra = extra.strip()
                    if len(extra) > 0:
                        # if "footnote" in extra or (len(extra) == 1 and "<" in pasuk):
                        #     print(pasuk)
                        #     print("{} {}:{}".format(title, perek, p + 1))
                        #     print()
                        # print(extra)
                        prev = probs[-1] if len(probs) > 0 else ""
                        curr = Ref("{} {}:{}".format(title, perek, p + 1))
                        if len(prev) > 0:
                            prev = Ref(prev)
                            if curr.section_ref() == prev.section_ref():
                                probs[-1] = prev.to(curr).normal()
                            else:
                                probs.append(curr.normal())
                        else:
                            probs.append(curr.normal())

                    # if re.search("\d+", new_text) and len(extra) > 2:
                    #     print(pasuk)
                    #     prev_prev_prob_ref = prev_prob_ref
                    #     prev_prob_ref = curr_prob_ref
                    #     curr_prob_ref = "{} {}:{}".format(title, perek, p + 1)
                    #     perek_probs.add("{} {}".format(title, perek))
                        # if prev_prob_ref and prev_prev_prob_ref and Ref(curr_prob_ref).prev_segment_ref() == Ref(prev_prob_ref) and Ref(prev_prob_ref).prev_segment_ref() == Ref(prev_prev_prob_ref):
                        #     print(Ref(prev_prev_prob_ref).to(Ref(curr_prob_ref)))

        body[book] = convertDictToArray(body[book])
        wout_ftnotes[book] = convertDictToArray(wout_ftnotes[book])
        send_text = {
            "versionTitle": "NJPS footnotes",
            "language": "en",
            "versionSource": "https://jps.org/books/tanakh-the-holy-scriptures-blue/",
            "text": body[book]
        }
        post_text(title, send_text)
        send_text = {
            "versionTitle": "NJPS no footnotes",
            "language": "en",
            "versionSource": "https://jps.org/books/tanakh-the-holy-scriptures-blue/",
            "text": wout_ftnotes[book]
        }
        post_text(title, send_text)
        time.sleep(5)
    print(probs)


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
                        print(row[1:])
                        pass
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
post(body)