import django, re, requests, json
from collections import defaultdict
django.setup()
from sefaria.model import *
from sefaria.system.exceptions import InputError
from tqdm import tqdm
from time import sleep
import random
from collections import namedtuple
import unicodecsv as csv

min_thresh=22
find_url = "https://talmudfinder-1-1x.loadbalancer.dicta.org.il/PasukFinder/api/markpsukim"
parse_url = f"https://talmudfinder-1-1x.loadbalancer.dicta.org.il/PasukFinder/api/parsetogroups?smin={min_thresh}&smax=10000"
SLEEP_TIME = 1


def retreive_bold(st):
    return ' '.join([re.sub('<.*?>', '', w) for w in st.split() if '<b>' in w])


def find_pesukim(base_text, mode="tanakh", thresh=0):
    data_text = {
        "data": base_text,
        "mode": mode,
        "thresh": thresh,
        "fdirectonly": False
    }
    response = requests.post(find_url, data=json.dumps(data_text))
    response_json = response.json()
    sleep(SLEEP_TIME)
    return response_json


def dicta_parse(response_json, min_thresh=22):
    parse_url = f"https://talmudfinder-1-1x.loadbalancer.dicta.org.il/PasukFinder/api/parsetogroups?smin={min_thresh}&smax=10000"
    result = response_json['results']
    downloadId = response_json["downloadId"]
    allText = response_json["allText"]

    data_parse = {
        "allText": allText,
        "downloadId": downloadId,
        "keepredundant": True,
        "results": result
    }

    response = requests.post(parse_url, data=json.dumps(data_parse))
    parsed_results = response.json()
    sleep(SLEEP_TIME)
    return parsed_results


def get_dicta_matches(base_refs, mode="tanakh", onlyDH = False, thresh=0, min_thresh=22):
    """

    :param base_refs:
    :param mode:
    :param onlyDH:
    :param thresh:
    :param min_thresh:
    :return: list (as long as the list of base_refs - segs) of matches
    """
    Match = namedtuple("Match", ["textMatched", "textToMatch", "score", "startIChar", "endIChar", "pasukStartIChar", "pasukEndIChar", "dh"])
    link_options = []
    dh_link_options = []
    for base_ref in base_refs:
        base_text = base_ref.text('he').text
        response_json = find_pesukim(base_text, mode, thresh=thresh)
        # response_json["results"][0]["ijWordPairs"]
        parsed_results = dicta_parse(response_json, min_thresh=min_thresh)
        dh_res = [res for res in parsed_results if res['startIChar'] == 0]
        for result in parsed_results:
            matched = result['matches'][0]
            # matched_pasuks = [match['verseDispHeb'] for match in result['matches']]
            # matched_pasuk = matched_pasuks[0]
            if len(result['matches']) > 1:
                print(f"more than one pasuk option: {[match['verseDispHeb'] for match in result['matches']]}")
            pasuk_ref = Ref(matched['verseDispHeb'])
            matched_pasuk_start = matched['verseiWords'][0]
            matched_pasuk_end = matched['verseiWords'][-1]
            # print(re.sub(" ", "_", f'www.sefaria.org/{base_ref.normal()}?lang=he&p2={pasuk_ref.normal()}'))
            matched_wds_base = retreive_bold(result['text'])
            matched_wds_pasuk = retreive_bold(matched['matchedText'])
            # print(f"{matched_wds_base} | {matched_wds_pasuk}")
            score = matched['score']
            m = Match(matched_wds_base, matched_wds_pasuk, score, result["startIChar"], result["endIChar"], matched_pasuk_start, matched_pasuk_end, result in dh_res)
            link_option = [pasuk_ref, base_ref, m.textMatched, m]
            if result in dh_res:
                link_option.append("dh")
                dh_link_options.append(link_option)
            link_options.append(link_option)
    if onlyDH:
        return dh_link_options
    return link_options


def data_to_link(link_option, generated_by="", auto=True):
    match = link_option[3]
    pasuk_ref = link_option[0]
    book_match = link_option[1]
    link_json = {"type": "qutation",
     "refs": [pasuk_ref.normal(), book_match.normal()],
     "auto": auto,
     "charLevelData": {},
    "score": match.score
     }
    if generated_by:
        link_json.update({"generated_by": generated_by})
    link_json["charLevelData"] = {
        "charLevelDataBook": {
            "startChar": match.startIChar,
             "endChar": match.endIChar,
             "versionTitle": link_option[1].text('he').version().versionTitle,
             "language": "he"
        },
     "charLevelDataPasuk": {
         "startWord": match.pasukStartIChar,
         "endWord": match.pasukEndIChar,
         "versionTitle": link_option[0].text('he').version().versionTitle,
         "language": "he"}
        }
    return link_json, match


def write_to_csv(links, linkMatchs,  filename='quotation_links'):
    list_dict = []
    base_text_name = Ref(links[0]["refs"][1]).book
    for link, linkMatch in zip(links, linkMatchs):
        row = {"url": link2url(link),
               "pasuk": link["refs"][0],
               base_text_name: link["refs"][1],
               "words pasuk": linkMatch.textToMatch,
               "words base": linkMatch.textMatched,
               "score": linkMatch.score,
                "dh": linkMatch.dh}
        list_dict.append(row)

    with open(u'{}.csv'.format(filename), 'w') as csv_file:
        writer = csv.DictWriter(csv_file, ['url', 'pasuk', base_text_name, 'words pasuk', 'words base', 'score', "dh"])  # fieldnames = obj_list[0].keys())
        writer.writeheader()
        writer.writerows(list_dict)


if __name__ == '__main__':
    from sources.Scripts.pesukim_linking import *
    peared = get_zip_ys()  # ys, perek (Torah)
    books = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy']
    book = random.sample(range(5), 1)[0]
    pear = peared[book][random.sample(range(len(peared[book])), 1)[0]]
    print(pear)
    # from pathlib import Path
    # Path(f"{os.getcwd()}/{pear[0]}").mkdir(parents=True, exist_ok=True)
    os.makedirs(pear[0].normal(), exist_ok=True)   # os.mkdir(f"{os.getcwd()}/{pear[1].normal()}")
    os.chdir(pear[0].normal())
    # dicta code
    for thresh in [10, 22, 50]:
        base_refs = pear[1].all_segment_refs()
        link_options = get_dicta_matches(base_refs, onlyDH=False)
        links, linkMatchs = zip(*[data_to_link(link_option, generated_by="Yalkut_shimoni_quotations") for link_option in link_options])
        # links, link_data = link_options_to_links(link_options, min_score=thresh)
        write_to_csv(links, linkMatchs, filename=f"dicta_{thresh}")
        print(len(links))
        post_link(links)

    # # dh code
    # matches = get_matches(pear)
    # links, link_data = link_options_to_links(matches, link_type="Midrash")
    # write_to_csv(links, link_data, filename="dh")
