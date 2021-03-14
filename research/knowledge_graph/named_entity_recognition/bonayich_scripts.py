import django, re, csv, json
django.setup()
from sefaria.model import *

DATASET_LOC = "/home/nss/sefaria/datasets/ner/sefaria"

def strip_prefixes(rabbi, slugs):
    prefixes = [
            "ובכ",
            "וכב",
            "וככ",
            "וכל",
            "וכמ",
            "וכש",
            "ולכ",
            "ומה",
            "ומכ",
            "ומש",
            "ומד",
            "ודב",
            "ושב",
            "ודה",
            "ושה",
            "ודכ",
            "ושכ",
            "ודל",
            "ושל",
            "ודמ",
            "ושמ",
            "כמה",
            "כשב",
            "כשה",
            "כשכ",
            "כשל",
            "כשמ",
            "לכש",
            "משב",
            "משה",
            "משכ",
            "משל",
            "משמ",
            "שבכ",
            "שכב",
            "שככ",
            "שכל",
            "דכל",
            "שכמ",
            "דכמ",
            "שכש",
            "שלכ",
            "דלכ",
            "שמה",
            "דמה",
            "שמכ",
            "שמש",
            "אד",
            "ואד",
            "וא",
            "בכ",
            "וב",
            "וה",
            "וכ",
            "ול",
            "ומ",
            "וד",
            "וש",
            "כב",
            "ככ",
            "כל",
            "כמ",
            "כש",
            "כד",
            "לכ",
            "מב",
            "מה",
            "מכ",
            "מל",
            "מש",
            "מד",
            "דב",
            "שב",
            "דה",
            "שה",
            "דכ",
            "שכ",
            "דל",
            "של",
            "דמ",
            "שמ",
            "ב",
            "ה",
            "ו",
            "כ",
            "ל",
            "מ",
            "ש",
            "א",
            "ד"
    ]
    prefixes.sort(key=lambda x: len(x), reverse=True)
    t = Topic.init(slugs[0])
    he_titles = t.get_titles('he', with_disambiguation=False) if t is not None else ['רב', 'רבי']
    prefixed_rabbi = rabbi
    for prefix in prefixes:
        found = False
        for he_name in he_titles:
            if rabbi.startswith(f"{prefix}{he_name}"):
                prefixed_rabbi = rabbi[len(prefix):]
                found = True
                break
        if found:
            break
    return prefixed_rabbi
def get_rabbis_in_book(book):
    index = library.get_index(book)
    mentions = []
    for iperek, perek in enumerate(index.alt_structs['Chapters']['nodes']):
        prev_rabbi_count = 0 if len(mentions) == 0 else mentions[-1]['rabbi_count']+1
        perek_tref = perek['wholeRef']
        temp_mentions = get_rabbis_in_perek(perek_tref)
        for i, m in enumerate(temp_mentions):
            m['perek_num'] = iperek
            m['he_book'] = index.get_title('he')
            m['rabbi_count'] = prev_rabbi_count + i
        mentions += temp_mentions
    return mentions

def get_rabbis_in_perek(perek_tref):
    oref = Ref(perek_tref)
    segment_set = {r.normal() for r in oref.all_segment_refs()}
    with open(f'{DATASET_LOC}/ner_output_talmud.json', 'r') as fin:
        j = json.load(fin)
    
    temp_mentions = []
    for m in j:
        if m['ref'] in segment_set and m['versionTitle'] == 'William Davidson Edition - Aramaic':
            m['cleaned_mention'] = strip_prefixes(m['mention'], m['id_matches'])
            temp_mentions += [m]
    temp_mentions.sort(key=lambda x: (Ref(x['ref']).order_id(), x['start']))
    return temp_mentions

def make_rabbi_csv(book_list):
    for book in book_list:
        mentions = get_rabbis_in_book(book)
        rows = []
        for m in mentions:
            rows += [{
                "מסכת": m['he_book'],
                "מספר במסכת": m['rabbi_count']+1,
                "פרק": m['perek_num']+1,
                "השם בסוגיה": m['cleaned_mention'],
                "השם המקורי בסוגיה": m['cleaned_mention']
            }]
        with open(f'{DATASET_LOC}/bonayich_{book}.csv', 'w') as fout:
            c = csv.DictWriter(fout, ['מסכת', 'מספר במסכת', 'פרק', 'השם בסוגיה', 'השם המקורי בסוגיה'])
            c.writeheader()
            c.writerows(rows)
    
    
if __name__ == "__main__":
    make_rabbi_csv(['Bava Metzia'])