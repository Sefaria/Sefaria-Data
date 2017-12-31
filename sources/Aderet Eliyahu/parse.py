#encoding=utf=8
from sefaria.model import *
from data_utilities.dibur_hamatchil_matcher import match_text
from sources.functions import *
import os
from collections import Counter
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"

server = "http://ste.sefaria.org"

def get_poss_parsha(line):
    line = line.replace(u"@00", u"")[0:-1]
    while line[-1] == u" ":
        line = line[0:-1]
    return line

def parse_until_chukat(lines, allowed):
    current_parsha = "intro"
    aderet_text["intro"] = []

    for line_n, line in enumerate(lines):
        line = line.decode('utf-8')
        if current_parsha == u"חקת":
            break
        if line.startswith(u"@11"):
            for line in divide_lines(line):
                line = line.replace("@33", "")
                aderet_text[current_parsha].append(line)
        elif line.startswith(u"@00"):
            this_parsha = None
            line = get_poss_parsha(line)
            if line in allowed:
                aderet_text[current_parsha].append(line)
            else:
                term = Term().load({"titles.text": line})
                if not term:
                    this_parsha_he = find_almost_identical(line, parshiot_poss, ratio=0.6)
                    term = Term().load({"titles.text": this_parsha_he})
                this_parsha = term.get_primary_title('en')
            if this_parsha:
                aderet_text[this_parsha] = []
                current_parsha = this_parsha
            #else:
            #    aderet_text[current_parsha].append(line)
    return aderet_text

def divide_lines(line):
    line = line.replace("@44", "\n").replace("@11", "").replace("@55", "@33").replace(":", ":\n")
    lines = line.splitlines()
    lines = [line for line in lines if line.replace(" ", "") != ""]
    return lines

def dh_extract_method(str):
    end = str.find("@33")
    if end >= 0:
        return str[0:end]
    elif end == -1:
        str = " ".join(str.split()[0:15])
        end = str.find(".")
        if end:
            return str[0:end]
        elif end == -1:
            return str

def base_tokenizer(str):
    str = str.replace(u"־", u" ").replace(u"  ", u" ")
    return [word for word in str.split(" ") if word]

def get_pasukim(aderet_text):
    overall = 0.0
    overall_good = 0.0
    found_this_ref = {}
    for parsha, comments in aderet_text.iteritems():
        #with open("{}.csv".format(parsha), 'w') as f:
        #parsha_csv = UnicodeWriter(f)
        #parsha_csv.writerow(["Aderet Eliyahu Ref", "Aderet Eliyah Text", "Torah Ref"])
        gaps = Counter()
        total = 0.0
        good = 0.0
        biggest_gap = 0
        prev_good = True # whether or not the previous ref had a match
        curr_gap = 0
        curr_gap_started_ref = None
        if parsha == "intro":
            continue
        print "\n"
        print(parsha)
        full_parsha = "Parashat "+parsha
        # refs = Ref(full_parsha).split_spanning_ref()
        # base_text = [TextChunk(ref, vtitle="Tanach with Text Only", lang='he') for ref in refs]
        # for ref, tc in zip(refs, base_text):
        base_text = TextChunk(Ref(full_parsha), vtitle="Tanach with Text Only", lang='he')
        results = match_ref(base_text, comments, base_tokenizer, dh_extract_method=dh_extract_method)
        for this_ref, base_ref in enumerate(results["matches"]):
            this_ref = "Aderet Eliyahu, {} {}".format(parsha, this_ref + 1)
            if base_ref:
                good += 1
                prev_good = True
            else:
                if prev_good:
                    curr_gap_started_ref = this_ref
                gaps[curr_gap_started_ref] += 1
                prev_good = False
            total += 1
            base_ref = "" if base_ref is None else base_ref.normal()
            #comment = comments[this_ref]
            #parsha_csv.writerow([this_ref, dh_extract_method(comment), base_ref])

        print "{0:.2f}%".format(good*100.0/total)
        if good*100/total < 100:
            most_common_ref, num = gaps.most_common()[0]
            print "Biggest gap: {} starting at {}".format(num, most_common_ref)
        #except ValueError as e:
        #    print "PROBLEM WITH THIS PARSHA"

    #     results = match_text(base_text, comments, dh_extract_method)["matches"]
    #     total = len(results)
    #     for tuple in results:
    #         if tuple != (-1, -1):
    #             good += 1
    #     percent = good*100.0/total
    #     print "{0:.2f}%\n".format(percent)
    #     overall += total
    #     overall_good += good
    # overall_percent = overall_good*100.0/overall
    # print "{0:.2f}%\n".format(overall_percent)


def create_index(text):
    root = SchemaNode()
    root.add_primary_titles("Aderet Eliyahu", u"אדרת אליהו")
    for parsha in text.keys():
        if parsha == "intro":
            continue
        term = Term().load({"name": parsha})
        node = JaggedArrayNode()
        node.add_primary_titles(parsha, term.get_primary_title("he"))
        node.add_structure(["Paragraph"])
        root.append(node)
    root.validate()
    index = {
        "schema": root.serialize(),
        "title": "Aderet Eliyahu",
        "categories": ["Other"]
    }
    post_index(index, server=server)

def post_fake_text(text):
    for parsha, comments in text.iteritems():
        new_comments = []
        for comment in comments:
            dh = dh_extract_method(comment)
            comment = comment.replace(dh, "")
            comment = u"<b>{}</b>{}".format(dh, comment)
            assert type(comment) is str or type(comment) is unicode
            new_comments.append(comment)
        new_comments = {
            "text": new_comments,
            "language": "he",
            "versionTitle": "s",
            "versionSource": server
        }
        post_text("Aderet Eliyahu, {}".format(parsha), new_comments, server=server)


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
        aderet_text = parse_until_chukat(lines, allowed)
    #create_index(aderet_text)
    #post_fake_text(aderet_text)
    get_pasukim(aderet_text)




