#encoding=utf=8
from sefaria.model import *
from data_utilities.dibur_hamatchil_matcher import match_text
from sources.functions import *

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
    if end == -1:
        end = str.find(".")
        if end == -1:
            end = str.find(" ".join(str.split()[0:5]))
        else:
            if abs(end - len(str)) <= 5:
                return ""
    return str[0:end]

def get_pasukim(aderet_text):
    overall = 0.0
    overall_good = 0.0
    for parsha, comments in aderet_text.iteritems():
        total = 0.0
        good = 0.0
        if parsha == "intro":
            continue
        print parsha
        parsha = "Parashat "+parsha
        text_ja = TextChunk(Ref(parsha), vtitle="Tanach with Text Only", lang='he').text
        how_many = 0
        for i in range(len(text_ja)):
            how_many += len(text_ja[i])
            text_ja[i] = " ".join(text_ja[i])
        base_text = " ".join(text_ja).split()
        results = match_text(base_text, comments, dh_extract_method)["matches"]
        total = len(results)
        for tuple in results:
            if tuple != (-1, -1):
                good += 1
        percent = good*100.0/total
        print "{0:.2f}%\n".format(percent)
        overall += total
        overall_good += good
    overall_percent = overall_good*100.0/overall
    print "{0:.2f}%\n".format(overall_percent)


def create_index(text):
    root = SchemaNode()
    root.add_primary_titles("Eliyahu Aderet", u"אליהו אדרת")
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
        "title": "Eliyahu Aderet",
        "categories": ["Other"]
    }
    post_index(index, server="http://ste.sefaria.org")

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
            "versionSource": "http://ste.sefaria.org"
        }
        post_text("Eliyahu Aderet, {}".format(parsha), new_comments, server="http://ste.sefaria.org")


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
    with open("eliyahu_aderet.txt") as f:
        lines = list(f)
        lines = [line for line in lines if line]
        aderet_text = parse_until_chukat(lines, allowed)
    create_index(aderet_text)
    #post_fake_text(aderet_text)
    get_pasukim(aderet_text)




