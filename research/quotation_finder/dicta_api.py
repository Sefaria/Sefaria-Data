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


find_url = "https://talmudfinder-1-1x.loadbalancer.dicta.org.il/PasukFinder/api/markpsukim"
parse_url = "https://talmudfinder-1-1x.loadbalancer.dicta.org.il/PasukFinder/api/parsetogroups?smin=22&smax=10000"
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


def dicta_parse(response_json):
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


def get_dicta_matches(base_refs, mode="tanakh", onlyDH = False):
    Match = namedtuple("Match", ["textMatched", "textToMatch", "score"])
    link_options = []
    dh_link_options = []
    for base_ref in base_refs:
        base_text = base_ref.text('he').text
        response_json = find_pesukim(base_text, mode)
        response_json["results"][0]["ijWordPairs"]
        parsed_results = dicta_parse(response_json)
        dh_res = [res for res in parsed_results if res['startIChar'] == 0]
        for result in parsed_results:
            matched_pasuk = [match['verseDispHeb'] for match in result['matches']][0]
            pasuk_ref = Ref(matched_pasuk)
            # print(re.sub(" ", "_", f'www.sefaria.org/{base_ref.normal()}?lang=he&p2={pasuk_ref.normal()}'))
            matched_wds_base = retreive_bold(result['text'])
            matched_wds_pasuk = retreive_bold(result['matches'][0]['matchedText'])
            # print(f"{matched_wds_base} | {matched_wds_pasuk}")
            score = result['matches'][0]['score']
            match = Match(matched_wds_base, matched_wds_pasuk, score)
            link_option = [pasuk_ref, base_ref, match.textMatched, match]
            if result in dh_res:
                link_option.append("dh")
                dh_link_options.append(link_option)
            link_options.append(link_option)
    if onlyDH:
        return dh_link_options
    return link_options


def write_to_csv(links, link_datas, filename='quotation_links'):
    list_dict = []
    base_text_name = Ref(links[0].refs[0]).book
    for link, link_data in zip(links, link_datas):
        row = {"url": link2url(link),
               "pasuk": link.refs[0],
               base_text_name: link.refs[1],
               "words 1": link_data[2],
               "words 2": link_data[3].textToMatch,
               "score": link_data[3].score,
                "dh": True if len(link_data)>4 and link_data[4]=="dh" else None}
        list_dict.append(row)

    with open(u'{}.csv'.format(filename), 'w') as csv_file:
        writer = csv.DictWriter(csv_file, ['url', 'pasuk', base_text_name, 'words 1', 'words 2', 'score', "dh"])  # fieldnames = obj_list[0].keys())
        writer.writeheader()
        writer.writerows(list_dict)


if __name__ == '__main__':
    from sources.Scripts.pesukim_linking import *
    peared = get_zip_ys() # ys, perek (Torah)
    books = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy']
    book = random.sample(range(5), 1)[0]
    pear = peared[book][random.sample(range(len(peared[book])), 1)[0]]

    # dicta code
    base_refs = pear[1].all_segment_refs()
    link_options = get_dicta_matches(base_refs, onlyDH=False)
    links, link_data = link_options_to_links(link_options)
    os.mkdir(pear[1].normal())  # os.mkdir(f"{os.getcwd()}/{pear[1].normal()}")
    os.chdir(pear[1].normal())
    write_to_csv(links, link_data, filename="dicta")

    # dh code
    matches = get_matches(pear)
    links, link_data = link_options_to_links(matches, link_type="Midrash")
    write_to_csv(links, link_data, filename="dh")
