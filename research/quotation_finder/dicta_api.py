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


def retreive_bold(st):
    return ' '.join([re.sub('<.*?>', '', w) for w in st.split() if '<b>' in w])


def get_dicta_matches(base_refs):
    Match = namedtuple("Match", ["textMatched", "textToMatch", "score"])
    link_options = []
    for base_ref in base_refs:
        base_text = base_ref.text('he').text
        mode = "tanakh"
        data_text = {
            "data": base_text,
            "mode": mode,
            "thresh": 0,
            "fdirectonly": False
        }

        response = requests.post(find_url, data=json.dumps(data_text))
        response_json = response.json()
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
        response_json = response.json()
        for result in response_json:
            matched_pasuk = [match['verseDispHeb'] for match in result['matches']][0]
            pasuk_ref = Ref(matched_pasuk)
            # print(re.sub(" ", "_", f'www.sefaria.org/{base_ref.normal()}?lang=he&p2={pasuk_ref.normal()}'))
            matched_wds_base = retreive_bold(result['text'])
            matched_wds_pasuk = retreive_bold(result['matches'][0]['matchedText'])
            # print(f"{matched_wds_base} | {matched_wds_pasuk}")
            score = result['matches'][0]['score']
            match = Match(matched_wds_base, matched_wds_pasuk, score)
            link_option = [base_ref, pasuk_ref, match.textMatched, match]
            link_options.append(link_option)
    return link_options


def write_to_csv(links, link_datas, filename='quotation_links'):
    list_dict = []
    base_text_name = Ref(links[0].refs[0]).index.title
    for link, link_data in zip(links, link_datas):
        row = {"url": link2url(link),
               "pasuk": link.refs[0],
               base_text_name: link.refs[1],
               "words (in text)":link_data[2],
               "score": link_data[3].score}
        list_dict.append(row)

    with open(u'{}.csv'.format(filename), 'w') as csv_file:
        writer = csv.DictWriter(csv_file, ['url', 'pasuk', base_text_name, 'words (in text)', 'score'])  # fieldnames = obj_list[0].keys())
        writer.writeheader()
        writer.writerows(list_dict)


if __name__ == '__main__':
    from sources.Scripts.pesukim_linking import *
    peared = get_zip_ys()
    books = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy']
    book = random.sample(range(5), 1)[0]
    pear = peared[book][random.sample(range(len(peared[book])), 1)[0]]

    # dicta code
    base_refs = pear[1].all_segment_refs()
    link_options = get_dicta_matches(base_refs)
    links, link_data = link_options_to_links(link_options)
    os.mkdir(pear[1].normal())  # os.mkdir(f"{os.getcwd()}/{pear[1].normal()}")
    os.chdir(pear[1].normal())
    write_to_csv(links, link_data, filename="dicta")

    # dh code
    matches = get_matches(pear)
    links, link_data = link_options_to_links(matches, link_type="Midrash")
    write_to_csv(links, link_data, filename="dh")
