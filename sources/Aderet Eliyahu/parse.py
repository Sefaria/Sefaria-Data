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

SERVER = "http://draft.sefaria.org"

def get_poss_parsha(line):
    line = line.replace(u"@00", u"")[0:-1]
    while line[-1] == u" ":
        line = line[0:-1]
    return line

def parse_after_chukat(lines, allowed):
    current_parsha = "intro"
    parsha_order = []
    aderet_text = {}
    prev_22 = False

    for line_n, line in enumerate(lines):
        line = line.decode('utf-8')
        if line.startswith("@00"):
            current_parsha = removeAllTags(line).replace("\n", "").strip()
            parsha_order.append(current_parsha)
            aderet_text[current_parsha] = []
        elif line.startswith("@11") or aderet_text[current_parsha] == []:
            if prev_22:
                aderet_text[current_parsha][0] += "<br>"+line
            line = line.replace("@44", "@11").replace("@55", "@33")
            aderet_text[current_parsha].append(line)
        elif line.startswith("@22"):
            if aderet_text[current_parsha] == []:
                aderet_text[current_parsha].append(line[3:])
            else:
                aderet_text[current_parsha][0] += "<br>"+line[3:]
        else:
            if "@44" not in line:
                line = removeAllTags(line)
            aderet_text[current_parsha].append(line)

        prev_22 = line.startswith("@22")


    return aderet_text, parsha_order



def divide_lines(line):
    line = line.replace("@44", "\n").replace("@11", "").replace("@55", "@33").replace(":", ":\n")
    lines = line.splitlines()
    lines = [line for line in lines if line.replace(" ", "") != ""]
    return lines

def dh_extract_method(line):
    if "@11" in line and "@44" not in line:
        start = line.find("@11")
        end = line.find("@33")
        return line[start + 3:end]
    else:
        return ""

def base_tokenizer(str):
    str = str.replace(u"־", u" ").replace(u"  ", u" ")
    return [word for word in str.split(" ") if word]

def get_pasukim(aderet_text, parsha_order):
    overall = 0.0
    overall_good = 0.0
    found_this_ref = {}
    he_books = [library.get_index(book).get_title('he') for book in library.get_indexes_in_category("Torah")]
    found_refs = Counter()
    actual_parshiot = [term.get_titles('he')[-1] for term in TermSet({'scheme': 'Parasha'})]
    print actual_parshiot
    with open("Tzror HaMor.csv", 'w') as f:
        parsha_csv = UnicodeWriter(f)
        parsha_csv.writerow(["Tzror HaMor Text", "Tzror HaMor Ref", "Torah Ref"])
        parshiot = aderet_text.keys()
        rows = []
        for parsha in parsha_order:
            print parsha
            comments = aderet_text[parsha]
            gaps = Counter()
            prev_base_ref = ""
            total = 0.0
            good = 0.0
            biggest_gap = 0
            prev_good = True # whether or not the previous ref had a match
            curr_gap = 0
            this_ref = ""
            curr_gap_started_ref = None
            if parsha == "intro":
                continue

            # check if parsha is also name of a book
            if parsha in he_books:
                book = library.get_indexes_in_category("Torah")[he_books.index(parsha)]
                full_parsha = "Parashat "+book
            else:
                term = Term().load({"titles.text": parsha})
                if not term or "ref" not in term.contents():
                    print parsha
                    corrected_parsha = find_almost_identical(parsha, actual_parshiot, 0.8)
                    continue
                full_parsha = parsha

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
                    this_ref = "Tzror HaMor, {}:{}".format(base_ref, found_refs[base_ref])
                    good += 1
                    prev_good = True
                    rows.append([comment, this_ref, base_ref])
                    prev_base_ref = base_ref
                else:
                    if comment.startswith("@44") and prev_base_ref != "":
                        found_refs[prev_base_ref] += 1
                        this_ref = "Tzror HaMor, {}:{}".format(prev_base_ref, found_refs[prev_base_ref])
                        rows.append([comment, this_ref, prev_base_ref])
                    else:
                        rows.append([comment, "", ""])
                        prev_base_ref = ""

                    if prev_good:
                        curr_gap_started_ref = this_ref
                    gaps[curr_gap_started_ref] += 1
                    prev_good = False

                #post_line(comment, this_ref)
                total += 1

        parsha_csv.writerows(rows)

def derive_tzror_from_base(tzror, base, prev_row):
    if not tzror: #nothing here so derive it solely from base
        prev_tzror = ""
        if len(prev_row) > 0:
            prev_tzror = prev_row[1]

        if base in prev_tzror:
            # derive it from prev_tzror so that if prev_tzror was
            # Tzror HaMor, Genesis 1:2:3 the new one should be Tzror HaMor, Genesis 1:2:4
            segment = int(prev_tzror.split(":")[-1]) + 1
            assert segment >= 1
            tzror = ":".join(prev_tzror.split(":")[0:-1]) + ":" + str(segment)
        else:
            #if base not in prev_tzror then this is the first one
            tzror = "Tzror HaMor on Torah, {}:1".format(base)

    if base not in tzror: #if base doesn't fit inside tzror, they are not connected properly
        print base
    return tzror


def interpret_csv():
    def add_prev_text_and_ref(range_starts_at_row, how_many_in_current_range, running_comment, text_and_ref):
        assert range_starts_at_row != "" and how_many_in_current_range > 0
        prev_base_ref = range_starts_at_row[2]
        prev_tzror_start_ref = range_starts_at_row[1]
        prev_tzror_section_ref = ":".join(prev_tzror_start_ref.split(":")[:-1])
        start_sec = int(prev_tzror_start_ref.split(":")[-1])
        end_sec = start_sec + how_many_in_current_range
        for i in range(start_sec, end_sec+1):
            curr_ref = prev_tzror_section_ref + ":" + str(i)
            curr_comment = running_comment[i - start_sec]
            curr_comment = curr_comment.replace("@11", "<b>").replace("@33", "</b>")
            curr_comment = curr_comment.replace("@44", "<b>").replace("@55", "</b>")
            assert len(curr_comment.split("<b>")) == len(curr_comment.split("</b>"))
            text_and_ref.append((curr_comment, curr_ref))
        prev_tzror_ref = prev_tzror_start_ref + "-" + str(end_sec)
        return prev_tzror_ref, prev_base_ref


    #Everytime there's an 11, add it to comment with current ref
    #but when there's a first 44, remove previous one and make that beginning   of running_comment
    text_and_ref = [] #tuples
    with open("Tzror HaMor.csv") as f:
        parsha_csv = UnicodeReader(f)
        prev_row = []
        links = []
        range_starts_at_row = ""
        how_many_in_current_range = 0
        running_comment = []
        for row_n, row in enumerate(parsha_csv):
            if row_n == 0:
                continue
            comment, tzror_ref, base_ref, other = row
            if tzror_ref == "" and base_ref:
                row[1] = tzror_ref = derive_tzror_from_base(tzror_ref, base_ref, prev_row)
            if "@44" in comment and "@11" not in comment:
                if "@11" in prev_row[0] and "@44" not in prev_row[0]:
                    del links[-1]
                    running_comment.append(text_and_ref.pop()[0])
                    range_starts_at_row = prev_row
                running_comment.append(comment)
                how_many_in_current_range += 1
            elif "@44" not in comment and "@11" in comment:
                if prev_row and "@44" in prev_row[0] and "@11" not in prev_row[0]:
                    #before creating link for this row, create a link for previous rows that are a range
                    #link creation is fine, but need to add individual text and ref
                    prev_tzror_ref, prev_base_ref = add_prev_text_and_ref(range_starts_at_row, how_many_in_current_range, running_comment, text_and_ref)
                    how_many_in_current_range = 0
                    range_starts_at_row = ""
                    running_comment = []
                    assert prev_base_ref in prev_tzror_ref
                    links.append({'refs': [prev_tzror_ref, prev_base_ref], 'type': 'commentary', 'auto': 'True',
                                  'generated_by': "tzrorhamor"})
                comment = comment.replace("@11", "<b>").replace("@33", "</b>")
                assert len(comment.split("<b>")) == len(comment.split("</b>"))
                text_and_ref.append((comment, tzror_ref))
                links.append({'refs': [tzror_ref, base_ref], 'type': 'commentary', 'auto': 'True',
                              'generated_by': "tzrorhamor"})
            else:
                print row[1]
                print row[0]

            prev_row = row

    post_text_and_ref(text_and_ref, "Tzror HaMor on Torah", SERVER, 'he')
    post_link(links, server=SERVER)



def post_text_and_ref(text_and_ref, vtitle, SERVER, lang):
    def post_line(comment, this_ref):
        if this_ref:
            comment = comment
            send_text = {
                "text": comment,
                "versionTitle": vtitle,
                "versionSource": SERVER,
                "language": lang
            }
            post_text(this_ref, send_text, server=SERVER)

    for text, ref in text_and_ref:
        post_line(text, ref)



def create_index(text):
    root = SchemaNode()
    root.add_primary_titles("Tzror HaMor on Torah", u"צרור המור על תורה")
    for book in library.get_indexes_in_category("Torah"):
        node = JaggedArrayNode()
        node.add_primary_titles(book, library.get_index(book).get_title('he'))
        node.add_structure(["Chapter", "Verse", "Paragraph"])
        node.toc_zoom = 2
        root.append(node)
    root.validate()
    index = {
        "dependence": "Commentary",
        "collective_title": "Tzror HaMor",
        "base_text_titles": ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"],
        "schema": root.serialize(),
        "title": "Tzror HaMor on Torah",
        "categories": ["Tanakh", "Commentary"]
    }
    post_index(index, server="http://draft.sefaria.org")

def restruct_text(text, parsha_order):
    for parsha in parsha_order:
        comments = text[parsha]
        new_comments = []
        for comment in comments:
            dh = dh_extract_method(comment)
            comment = comment.replace(dh, "", 1)
            comment = removeAllTags(comment)
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
    with open("tzror hamor.txt") as f:
        lines = list(f)
        lines = [line for line in lines if line]
        aderet_text, parsha_order = parse_after_chukat(lines, allowed)

    # for book, book_dict in aderet_text.items():
    #     for perek, perek_dict in book_dict.items():
    #         perek_dict = convertDictToArray(perek_dict)
    #         aderet_text[book][perek] = perek_dict
    #     aderet_text[book] = convertDictToArray(aderet_text[book])

    #add_term("Aderet Eliyahu", u"אדרת אליהו", server="https://www.sefaria.org")
    #add_category("Aderet Eliyahu", ["Tanakh", "Commentary", "Aderet Eliyahu"], "https://www.sefaria.org")
    create_index(aderet_text)
    #aderet_text = restruct_text(aderet_text, parsha_order)
    #get_pasukim(aderet_text, parsha_order)
    interpret_csv()


    # send_text = {
    #     "text": aderet_text["Bamidbar"],
    #     "language": "he",
    #     "versionTitle": "Aderet Eliyahu",
    #     "versionSource": "http://draft.sefaria.org"
    # }
    #
    # post_text("Aderet Eliyahu, Numbers", send_text, server="http://draft.sefaria.org")
    #
    # send_text = {
    #     "text": aderet_text["Devarim"],
    #     "language": "he",
    #     "versionTitle": "Aderet Eliyahu",
    #     "versionSource": "http://draft.sefaria.org"
    # }
    # post_text("Aderet Eliyahu, Deuteronomy", send_text, server="http://draft.sefaria.org")

