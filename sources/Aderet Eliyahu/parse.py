#encoding=utf=8
import sys
from sources.local_settings import *

sys.path.insert(0, "/home/steve/Sefaria/Sefaria-Data")
sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from data_utilities.dibur_hamatchil_matcher import match_text
from sources.functions import *
import os
from collections import Counter

os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"

server = "http://draft.sefaria.org"

def get_poss_parsha(line):
    line = line.replace(u"@00", u"")[0:-1]
    while line[-1] == u" ":
        line = line[0:-1]
    return line

def parse_after_chukat(lines, allowed):
    current_parsha = "intro"
    parsha_order = []
    current_ch = 19
    aderet_text["Bamidbar"] = {19: {}}
    aderet_text["Devarim"] = {1: {}}
    current_book = "Bamidbar"
    current_segment = 0
    num = 0

    for line_n, line in enumerate(lines):
        line = line.decode('utf-8')
        if u"@00דברים" in line:
            current_ch = 0
            current_book = "Devarim"
        if line.startswith(u"@22"):
            num = getGematria(line)
            if prev_num >= num:
                if num not in [1, 2, 3, 4, 5]:
                    print "ERROR"
                current_ch += 1
            if current_ch not in aderet_text[current_book]:
                aderet_text[current_book][current_ch] = {}
            aderet_text[current_book][current_ch][num] = []
            current_segment = num
        elif line.startswith(u"@11"):
            for line in divide_lines(line):
                aderet_text[current_book][current_ch][current_segment].append(line)
        prev_num = num

    return aderet_text, parsha_order



def divide_lines(line):
    line = line.replace("@44", "\n").replace("@11", "").replace("@55", "@33").replace(":", ":\n")
    lines = line.splitlines()
    lines = [line for line in lines if line.replace(" ", "") != ""]
    return lines

def dh_extract_method(str):
    end = str.find("@33")
    if end >= 0:
        return str[0:end]
    else:
        str = " ".join(str.split(" ")[0:15])
        end = str.find(".")
        if end >= 0:
            return str[0:end]
        elif end == -1:
            return str

def base_tokenizer(str):
    str = str.replace(u"־", u" ").replace(u"  ", u" ")
    return [word for word in str.split(" ") if word]

def get_pasukim(aderet_text, parsha_order):
    overall = 0.0
    overall_good = 0.0
    found_this_ref = {}
    found_refs = Counter()
    with open("Aderet_Eliyahu.csv", 'w') as f:
        parsha_csv = UnicodeWriter(f)
        parsha_csv.writerow(["Aderet Eliyahu Text", "Aderet Eliyah Ref"])
        parshiot = aderet_text.keys()
        for parsha in parsha_order:
            comments = aderet_text[parsha]
            gaps = Counter()
            total = 0.0
            good = 0.0
            biggest_gap = 0
            prev_good = True # whether or not the previous ref had a match
            curr_gap = 0
            curr_gap_started_ref = None
            if parsha == "intro":
                continue
            print(parsha)
            full_parsha = "Parashat "+parsha
            # refs = Ref(full_parsha).split_spanning_ref()
            # base_text = [TextChunk(ref, vtitle="Tanach with Text Only", lang='he') for ref in refs]
            # for ref, tc in zip(refs, base_text):
            base_text = TextChunk(Ref(full_parsha), vtitle="Tanach with Text Only", lang='he')
            results = match_ref(base_text, comments, base_tokenizer, dh_extract_method=dh_extract_method)
            assert len(comments) == len(results["matches"])
            for i, base_ref in enumerate(results["matches"]):
                if base_ref and base_ref.is_range():
                    base_ref = base_ref.starting_ref()
                comment = comments[i]
                base_ref = "" if base_ref is None else base_ref.normal()
                if base_ref:
                    found_refs[base_ref] += 1
                    this_ref = "Aderet Eliyahu, {}:{}".format(base_ref, found_refs[base_ref])
                    good += 1
                    prev_good = True
                else:
                    if prev_good:
                        curr_gap_started_ref = this_ref
                    gaps[curr_gap_started_ref] += 1
                    prev_good = False
                    this_ref = ""

                parsha_csv.writerow([comment, this_ref])
                #post_line(comment, this_ref)
                total += 1


def post_line(comment, this_ref):
    if this_ref:
        send_text = {
            "text": comment,
            "versionTitle": "Aderet Eliyahu",
            "versionSource": server,
            "language": "he"
        }
        post_text(this_ref, send_text, server=server)


def create_index(text):
    root = SchemaNode()
    root.add_primary_titles("Aderet Eliyahu", u"אדרת אליהו")
    for book in library.get_indexes_in_category("Torah"):
        node = JaggedArrayNode()
        node.add_primary_titles(book, library.get_index(book).get_title('he'))
        node.add_structure(["Perek", "Pasuk", "Paragraph"])
        root.append(node)
    root.validate()
    index = {
        "schema": root.serialize(),
        "title": "Aderet Eliyahu",
        "categories": ["Tanakh", "Commentary", "Aderet Eliyahu"]
    }
    post_index(index, server=server)

def restruct_text(text, parsha_order):
    for parsha in parsha_order:
        book = Ref(parsha).index.title
        comments = text[parsha]
        new_comments = []
        for comment in comments:
            dh = dh_extract_method(comment)
            comment = comment.replace(dh, "", 1).replace("@33", "")
            comment = u"<b>{}</b>{}".format(dh, comment)
            assert type(comment) is str or type(comment) is unicode
            new_comments.append(comment)
        text[parsha] = new_comments
    return text


def post_line(comment, this_ref):
    if this_ref:
        send_text = {
            "text": comment,
            "versionTitle": "Aderet Eliyahu",
            "versionSource": server,
            "language": "he"
        }
        post_text(this_ref, send_text, server=server)


if __name__ == "__main__":
    others = set()
    parshiot = []
    parshiot_poss = [term.get_primary_title('he') for term in TermSet({"scheme": "Parasha"})]
    aderet_text = {}
    current_parsha = ""
    allowed = [u"""הקדמת בני הגר"א לספר אדרת אליהו""",
               u"""פי' שירת הבאר כא"""]
    allowed.append(u"""מהדורא קמא""")
    allowed.append(u"""מהדורא תניינא""")
    allowed.append(u"""מהדורא תליתאה.""")
    allowed.append(u"""מהדורא רביעאה""")
    allowed.append(u"""מהדורא חמישאה""")
    allowed.append(u"""מהדורא שתיתאה""")
    allowed.append(u"""אופן שני""")
    with open("aderet_eliyahu.txt") as f:
        lines = list(f)
        lines = [line for line in lines if line]
        aderet_text, parsha_order = parse_after_chukat(lines, allowed)

    for book, book_dict in aderet_text.items():
        for perek, perek_dict in book_dict.items():
            perek_dict = convertDictToArray(perek_dict)
            aderet_text[book][perek] = perek_dict
        aderet_text[book] = convertDictToArray(aderet_text[book])

    send_text = {
        "text": aderet_text["Bamidbar"],
        "language": "he",
        "versionTitle": "Aderet Eliyahu",
        "versionSource": "http://draft.sefaria.org"
    }

    post_text("Aderet Eliyahu, Numbers", send_text, server="http://draft.sefaria.org")

    send_text = {
        "text": aderet_text["Devarim"],
        "language": "he",
        "versionTitle": "Aderet Eliyahu",
        "versionSource": "http://draft.sefaria.org"
    }
    post_text("Aderet Eliyahu, Deuteronomy", send_text, server="http://draft.sefaria.org")

    #create_index(aderet_text)
    # aderet_text = restruct_text(aderet_text, parsha_order)
    # get_pasukim(aderet_text, parsha_order)
