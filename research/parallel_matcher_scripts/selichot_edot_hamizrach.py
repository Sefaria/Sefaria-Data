import django, re, csv, json
django.setup()
from sefaria.model import *
from sefaria.utils.hebrew import strip_cantillation
from data_utilities.parallel_matcher import ParallelMatcher

stop_words = set(["ר'", 'רב', 'רבי', 'בן', 'בר', 'בריה', 'אמר', 'כאמר', 'וכאמר', 'דאמר', 'ודאמר', 'כדאמר',
                'וכדאמר', 'ואמר', 'כרב',
                'ורב', 'כדרב', 'דרב', 'ודרב', 'וכדרב', 'כרבי', 'ורבי', 'כדרבי', 'דרבי', 'ודרבי', 'וכדרבי',
                "כר'", "ור'", "כדר'",
                "דר'", "ודר'", "וכדר'", 'א״ר', 'וא״ר', 'כא״ר', 'דא״ר', 'דאמרי', 'משמיה', 'קאמר', 'קאמרי',
                'לרב', 'לרבי',
                "לר'", 'ברב', 'ברבי', "בר'", 'הא', 'בהא', 'הך', 'בהך', 'ליה', 'צריכי', 'צריכא', 'וצריכי',
                'וצריכא', 'הלל', 'שמאי', "וגו'", 'וגו׳', 'וגו', 'כל', 'לכם', 'לכן', 'לו', 'לה', 'כאשר', 'דבר', 'וידבר', 'אל', 'לא', 'אשר', 'כי', 'אין', 'את', 'הוא'])
def tokenize_words(base_str):
    base_str = base_str.strip()
    base_str = strip_cantillation(base_str, strip_vowels=True)
    base_str = re.sub(r"<[^>]+>", "", base_str)
    for match in re.finditer(r'\(.*?\)', base_str):
        if len(match.group().split()) <= 5:
            base_str = base_str.replace(match.group(), "")
            # base_str = re.sub(ur"(?:\(.*?\)|<.*?>)", u"", base_str)
    base_str = re.sub(r'־', ' ', base_str)
    base_str = re.sub(r'\[[^\[\]]{1,7}\]', '', base_str)  # remove kri but dont remove too much to avoid messing with brackets in talmud
    base_str = re.sub(r'[A-Za-z.,"?!״:׃]', '', base_str)
    # replace common hashem replacements with the tetragrammaton
    base_str = re.sub(r"(^|\s)([\u05de\u05e9\u05d5\u05db\u05dc\u05d1]?)(?:\u05d4['\u05f3]|\u05d9\u05d9)($|\s)",
                "\1\2\u05d9\u05d4\u05d5\u05d4\3", base_str)
    # replace common elokim replacement with elokim
    base_str = re.sub(r"(^|\s)([\u05de\u05e9\u05d5\u05db\u05dc\u05d1]?)(?:\u05d0\u05dc\u05e7\u05d9\u05dd)($|\s)",
                "\1\2\u05d0\u05dc\u05d4\u05d9\u05dd\3", base_str)

    word_list = re.split(r"\s+", base_str)
    word_list = [w for w in word_list if len(w.strip()) > 0 and w not in stop_words]
    return word_list

def get_snippet_from_mesorah_item(mesorah_item, pm):
    words = pm.word_list_map[mesorah_item.mesechta]
    return " ".join(words[mesorah_item.location[0]:mesorah_item.location[1]+1])

if __name__ == "__main__":
    selichot = "Selichot Edot HaMizrach"
    tanakh_refs = library.get_indexes_in_category("Tanakh")
    pm = ParallelMatcher(
        tokenize_words, min_words_in_match=5, min_distance_between_matches=0, all_to_all=False, verbose=True,
        only_match_first=True, ngram_size=4, max_words_between=0)
    results = pm.match([selichot] + tanakh_refs, return_obj=True)
    results.sort(key=lambda x: x.score)
    rows = []
    for r in results:
        if r.score < -10:
            continue
        rows += [{
            "Ref 1": r.a.ref,
            "Ref 2": r.b.ref,
            "Text 1": get_snippet_from_mesorah_item(r.a, pm),
            "Text 2": get_snippet_from_mesorah_item(r.b, pm),
            "Location Start": r.b.location[0],
            "Location End": r.b.location[1],
            "Score": r.score
        }]
    with open("Selichot Edot HaMizrach Parallel Matcher Results Small.csv", "w") as fout:
       c = csv.DictWriter(fout, ["Ref 1", "Ref 2", "Text 1", "Text 2", "Score", "Location Start", "Location End"])
       c.writeheader()
       c.writerows(rows) 