import django, re, requests, json
from collections import defaultdict

import sefaria.system.exceptions

django.setup()
from collections import namedtuple
import unicodecsv as csv
from sources.functions import *
from sources.Scripts.pesukim_linking import *
import numpy as np
import pymongo
from sefaria.settings import *
import logging
import multiprocessing
# from data_utilities.util import * #get_mapping_after_normalization, convert_normalized_indices_to_unnormalized_indices
from research.link_disambiguator.modify_tanakh_links import get_mapping_after_normalization, convert_normalized_indices_to_unnormalized_indices
import datetime
# logging.basicConfig(filename='wordLevelData.log', encoding='utf-8', level=logging.DEBUG)
path = os.getcwd()
client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)  # (MONGO_ASPAKLARIA_URL)
db_qf = client.quotations
mode ='tanakh'  #'mishna', 'tanakh', 'talmud'
Mish = lambda x: 'משנה ' + x if mode == 'mishna' else x

wl = WeightedLevenshtein()
min_thresh=22
find_url = "https://talmudfinder-1-3.loadbalancer.dicta.org.il/TalmudFinder/api/markpsukim"  # PasukFinder
# parse_url = f"https://talmudfinder-1-1x.loadbalancer.dicta.org.il/PasukFinder/api/parsetogroups?smin={min_thresh}&smax=10000"
SLEEP_TIME = 0
ff_headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:96.0) Gecko/20100101 Firefox/96.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Content-Type': 'text/plain;charset=UTF-8',
    'Origin': 'https://citation.dicta.org.il',
    'Connection': 'keep-alive',
    'Referer': 'https://citation.dicta.org.il/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'DNT': '1',
    'Sec-GPC': '1',
    'TE': 'trailers',
}

run_type = f'date: {datetime.date} type: chasidut night run'

sandbox = SEFARIA_SERVER.split(".")[0] if SEFARIA_SERVER != "http://localhost:8000" else ''
vtitle = 'Miqra according to the Masorah'  # "Tanach with Ta'amei Hamikra"  #

def retreive_bold(st):
    return ' '.join([re.sub('<.*?>', '', w) for w in st.split() if '<b>' in w])


def find_pesukim(base_text, thresh=0): #mode="tanakh",
    """
    Using the dicta citations finder returns results of optional pesukim that correspond to text in the base text and other metadata
    :param base_text: stripped text to look through.
    :param mode: defaults to Tanakh because we are looking to match text to Pesukim can potentially also be 'mishna' and 'talmud'
    :param thresh: from learning the api it seams to always be 0 and not make a difference when changed.
    :return: dictionary: {'downloadId': int,
                             'allText' : st | it is the base_text
                             'results': list of dicts | {
                                                'mode' :0,
                                                'iVerse': int,
                                                'ijWordPairs': list of dicts ot keys: item1, item2 values: int,
                                                'score':int (0-1000),
                                                'debScore':None
                                                }
                                }
    """
    data_text = {
        "data": base_text,
        "mode": mode,
        "thresh": thresh,
        "fdirectonly": False
    }
    response = requests.post(find_url, data=json.dumps(data_text), headers =ff_headers)
    response_json = response.json()
    sleep(SLEEP_TIME)
    #todo: add a timeout
    return response_json


def dicta_parse(response_json, min_thresh=22):
    parse_url = f"https://talmudfinder-1-1x.loadbalancer.dicta.org.il/TalmudFinder/api/parsetogroups?smin={min_thresh}&smax=10000"  # PasukFinder
    result = response_json['results']
    downloadId = response_json["downloadId"]
    allText = response_json["allText"]

    data_parse = {
        "allText": allText,
        "downloadId": downloadId,
        "keepredundant": True,
        "results": result
    }

    response = requests.post(parse_url, data=json.dumps(data_parse), headers=ff_headers)
    parsed_results = response.json()
    keep = {allText: parsed_results}
    with open(f'{path}/api_results/keep_{mode}.json', 'a+') as fp:
        json.dump(keep, fp)
    sleep(SLEEP_TIME)
    return parsed_results


def many_pesukim_match(result, base_ref, matched, priority_tanakh_chunk=None):
    many_pesukim_he = [match['verseDispHeb'] for match in result['matches']]
    many_pesukim_refs = [Ref(Mish(he_disp)) for he_disp in many_pesukim_he]
    many_pesukim_score = [match['score'] for match in result['matches']]
    mean = np.mean(many_pesukim_score)
    var = np.var(many_pesukim_score)
    if mean > 20 and var < 5:
        wordLeveldata = [match['verseiWords'] for match in result['matches']]
        suffex = ''.join(
            [f"&p{i + 1}={many_pesukim_refs[i].normal()}&lang2=he" for i in list(range(1, len(many_pesukim_refs)))])
        url = re.sub(" ", "_", f'{sandbox}.cauldron.sefaria.org/{many_pesukim_refs[0].normal()}?lang=he{suffex}\n')
        intra_tanakh_dict = {
            "refs": [r.normal() for r in many_pesukim_refs],
            "wordLevelData": wordLeveldata,
            "mean": mean,
            "var": var,
            "base_ref": base_ref.normal(),
            "url": url,
            "score": many_pesukim_score
        }
        # json.dump(intra_tanakh_dict, f)
        db_qf.intraTanakh.insert_one(intra_tanakh_dict)
        print(url)
        # print(f"more than one pasuk option for {base_ref.normal()}: {many_pesukim_he}")
    if priority_tanakh_chunk:
        best_match_option_ref = list(set(priority_tanakh_chunk.all_segment_refs()) & set(many_pesukim_refs))
        best_match = [match for match in result['matches'] if Ref(Mish(match['verseDispHeb'])) in best_match_option_ref]
        matched = best_match[-1] if best_match else matched
    return matched

def priority_section(parsed_results):
    if not parsed_results:
        return None
    all_results = [sr for seg_results in  parsed_results for sr in seg_results]
    def match_section_ref(match):
        if match['mode'] =='Mishna':
            heb_disp = f" משנה {match['verseDispHeb']}"
        else:
            heb_disp = match['verseDispHeb']
        return Ref(heb_disp).section_ref()
    all_matches = [(match_section_ref(match), match) for result in all_results for match in
                   result['matches']]
    d = dict()
    for k, v in all_matches:
        if d.get(k, []):
            d[k].append(v)
        else:
            d[k] = [v]
    all_matches_dict = d
    d_lengths = [(k,len(v)) for k,v in all_matches_dict.items()]
    d_lengths.sort(key = lambda x: x[1])
    if max(l[1] for l in d_lengths)> np.mean([l[1] for l in d_lengths]):
        return d_lengths[-1][0]
    return None

def link_options_from_text(text):
    pass

def get_dicta_matches(base_refs, offline=None, mode="tanakh", onlyDH = False, thresh=0, min_thresh=22, priority_tanakh_chunk=None, wrods_to_wipe='', seg_split = None):
    """
    the heart of the quotation finder input Ref and output links
    :param base_refs:
    :param offline: list of 2 files each containing a dictionary, 1: mapping of the text keys:trefs, values: he_text (sent to offline dicta) 2: mapping of results from dicta, keys: trefs values: dicta_results
    :param mode:
    :param onlyDH:
    :param thresh:
    :param min_thresh:
    :param priority_tanakh_chunk: oRef the their is strong reson to look for the best match there first ex: base_text: Ref('ילקוט שמעוני על התורה, חקת') priority_tanakh_chunk: Ref('פרשת חקת')
    :param seg_split: a string that can be used to split a obviously splittable segment (ex: a perek of psalms use seg_split=':')
    :return: list (as long as the list of base_refs - segs) of matches
    """
    Match = namedtuple("Match", ["textMatched", "textToMatch", "score", "startIChar", "endIChar", "pasukStartIWord", "pasukEndIWord", "dh"])
    link_options = []
    dh_link_options = []

    def get_dicta_matches_text(parsed_results):
        dh_res = [res for res in parsed_results if res['startIChar'] <= 10]  # todo: put this in it's own function
        for result in parsed_results:
            # result['matches'] = [m for m in result['matches'] if m['mode'] == 'Tanakh' and m['score']>=min_thresh]  # use the same parameter name "Tanakh"
            result['matches'] = [m for m in result['matches'] if
                                 m['score'] >= min_thresh]  # use the same parameter name "Tanakh"
            if len(result['matches']) == 0:
                continue
            result['matches'].sort(key=lambda x: x['score'])
            priority_section_matches = [match for match in result['matches'] if priority and priority == Ref(match['verseDispHeb']).section_ref()]
            if priority and priority_section_matches:
                    matched = priority_section_matches[-1]
            else:
                matched = result['matches'][-1]
                if len(result['matches']) > 1:
                    matched = many_pesukim_match(result, base_ref, matched, priority_tanakh_chunk=priority_tanakh_chunk)

            pasuk_ref = Ref(Mish(matched['verseDispHeb']))
            if not pasuk_ref.text('he').text:
                if pasuk_ref.normal() == 'Numbers 25:19':
                    pasuk_ref = Ref('Numbers 26:1')
                else:
                    print(f'{pasuk_ref} has no text in it')
                    continue
            if mode == 'tanakh':
                matched_pasuk_start, matched_pasuk_end = wordLevel2charLevel(matched['verseiWords'], pasuk_ref,
                                                                             matched['matchedText'])
                matched_wds_base = retreive_bold(result['text'])
                matched_wds_pasuk = retreive_bold(matched['matchedText'])
                score = matched['score']
                dh_match = result in dh_res
                if priority_tanakh_chunk:
                    dh_match = dh_match and pasuk_ref in priority_tanakh_chunk.all_segment_refs()
                m = Match(matched_wds_base, matched_wds_pasuk, score, result["startIChar"], result["endIChar"],
                          matched_pasuk_start, matched_pasuk_end, dh_match)
            link_option = [pasuk_ref, base_ref, m.textMatched, m]
            if mode == 'tanakh':
                # if dh_match:
                #     trivial_ref = pasuk_ref.normal()
                #     link_option.append("dh")
                #     dh_link_options.append(link_option)
                link_option.append(trivial_ref)
                tc = link_option[1].text('he')
                html_regex = re.compile("<[^>]*?>")
                find_text_to_remove = lambda x: [(m, '') for m in re.finditer(html_regex, x)]
                normalization_mapping = get_mapping_after_normalization(tc.text, find_text_to_remove=find_text_to_remove)
                lv_score = validate_wordLevel2charLevel(tc, [m[3], m[4]], m[0], pasuk=False, wl_min_score=200)
                if lv_score < 200:
                    normolized = convert_normalized_indices_to_unnormalized_indices([(m[3], m[4])], normalization_mapping)[
                        0]
                    lv_score = validate_wordLevel2charLevel(tc, normolized, m[0], pasuk=False, wl_min_score=200,
                                                            html_regex=html_regex)
                    try:
                        assert lv_score == 200
                        link_option[3] = Match(matched_wds_base, matched_wds_pasuk, score, normolized[0], normolized[1],
                                               matched_pasuk_start, matched_pasuk_end, dh_match)
                    except AssertionError:
                        # log.write(f'{tc._oref} take_2 lv score is: {lv_score}\n')
                        pass
            link_options.append(link_option)
            # if onlyDH:
            #     return dh_link_options
            # return link_options

    for base_ref in base_refs:
        trivial_ref = None
        if offline:
            base_text = offline[0][base_ref.normal()]
            parsed_results = [offline[1].get(base_ref.normal(), [])]
        else:
            if seg_split:
                texts = base_ref.text('he').text.split(seg_split)
            else:
                texts = [base_ref.text('he').text]

            # base_text = strip_cantillation(bleach.clean(base_text, tags=[], strip=True), strip_vowels=True)
            # base_text = re.sub(f"{wrods_to_wipe}", "", base_text)
            response_jsons = [find_pesukim(base_text, thresh=thresh) for base_text in texts if base_text]
            # response_json["results"][0]["ijWordPairs"]
            parsed_results = [dicta_parse(response_json, min_thresh=min_thresh) for response_json in response_jsons]
        parsed_results = [p for p in parsed_results if p]
        priority = priority_section(parsed_results)
        for i, response in enumerate(parsed_results):
            get_dicta_matches_text(response)
    return link_options


def data_to_link(link_option, type="quotation_auto", generated_by="", auto=True):
    match = link_option[3]
    pasuk_ref = link_option[0]
    book_match = link_option[1]
    link_json = {"type": type,
     "refs": [pasuk_ref.normal(), book_match.normal()],
     "auto": auto,
     "charLevelData": [],
    "score": match.score,
     "inline_citation": True,
     "qf_run_type": run_type
     }
    if generated_by:
        link_json.update({"generated_by": generated_by})
    link_json["charLevelData"] = [
        {
            "startWord": match.pasukStartIWord,
            "endWord": match.pasukEndIWord,
            "versionTitle": link_option[0].text('he').version().versionTitle,
            "language": "he"},
        {
            "startChar": match.startIChar,
             "endChar": match.endIChar,
             "versionTitle": link_option[1].text('he').version().versionTitle,
             "language": "he"
        }
        ]
    link_json["dh"] = match.dh
    if match.dh:
        link_json["type"] = "dibur_hamatchil"
    if link_option[-1]:
        link_json["trivial_ref"] = link_option[-1]
    return link_json, match

def chars_per_wrod_tuples(text_words_list):
    word_char_tuples = []
    end = None
    for w in text_words_list:
        start = end+1 if end else 0
        end = start + len(w)
        if w == '׀' or re.match('[({]', w):  #
            continue
        w_chars = (start, end)
        word_char_tuples.append(w_chars[:])
    return word_char_tuples

def wordLevel2charLevel(wordLevel, pasuk_ref, matched_text):
    """

    :param wordLevelData: [startWord, endWord]
    :param pasuk_ref:
    :return:
    """
    wordLevel.sort()
    wordLevelData = [wordLevel[0], wordLevel[-1]]
    tc = TextChunk(pasuk_ref, lang='he', vtitle=vtitle)
    html_regex = re.compile("(<[^>]*?>|\(.*?\)|\[|\])")
    pasuk_text = re.sub(html_regex, "", tc.text)
    find_text_to_remove = lambda x: [(m, '') for m in re.finditer(html_regex, x)]
    normalization_mapping = get_mapping_after_normalization(tc.text, find_text_to_remove=find_text_to_remove)#re.findall(html_regex, tc.text))
    pasuk_words = re.split('\s+|־', pasuk_text.strip())  # re.sub('<.*?>', '', tc.text))
    word_char_tuples = chars_per_wrod_tuples(pasuk_words)
    startChar = word_char_tuples[wordLevelData[0]][0]
    try:
        endChar = word_char_tuples[wordLevelData[1]][1]
        chars = convert_normalized_indices_to_unnormalized_indices([(startChar, endChar)], normalization_mapping)[0]
        validate_wordLevel2charLevel(tc, chars, matched_text, html_regex)
    except IndexError:
        endChar = word_char_tuples[-1][1]
        # logging.debug(f"IndexError, pasuk: {pasuk_ref.normal()}")
        return [0,0]
    return chars #[0], chars[0][1]
    # return startChar, endChar


def validate_wordLevel2charLevel(tc, charData, dictas_text, html_regex='', pasuk=True, wl_min_score=160):
    """

    :param tc:
    :param charData: tuple of first and last char positions
    :param dictas_text:
    :param html_regex: the regex used to normolize the text before prossessed (according to which the char level data was determined)
    :param wl_min_score: Weighted Levenshtein minimum score for granting the 2 string close enough
    :return: this function writes not accurate char level data to a log file wordLevelData.log
    """
    ours = tc.text[charData[0]:charData[1]]
    theirs = ' '.join(re.findall('<.*?>(.*?)<.*?>', dictas_text)) if pasuk else dictas_text.translate(str.maketrans('', '', string.punctuation))
    ours_words = re.split('\s+|־', strip_cantillation(re.sub(html_regex, '', ours), strip_vowels=True).translate(str.maketrans('', '', string.punctuation)))
    ours_words = [w for w in ours_words if w]
    theirs_words = re.split('\s+|־', strip_cantillation(theirs, strip_vowels=True))
    if not ours_words or not theirs_words:
        return 0
    wl_score = wl.calculate(ours_words[0], theirs_words[0], normalize=True) + wl.calculate(ours_words[-1], theirs_words[-1], normalize=True)
    if wl_score<wl_min_score and pasuk:
        pass
        # logging.debug(f'charLevelData is not returning the same words as dicta. ours: {ours}, dicta: {theirs}')
        # log.write(f'{tc._oref} charLevelData is not returning the same words as dicta. ours: {ours}, dicta: {theirs} : wl={wl_score}\n')
        # print(f'www.sefaria.org/{tc._oref}: {[ours_words[0], ours_words[-1],theirs_words[0], theirs_words[-1]]}')
    return wl_score

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

    with open(f'{path}/csvs/{filename}.csv', 'a') as csv_file:
        writer = csv.DictWriter(csv_file, ['url', 'pasuk', base_text_name, 'words pasuk', 'words base', 'score', "dh"])  # fieldnames = obj_list[0].keys())
        writer.writeheader()
        writer.writerows(list_dict)


def get_links_ys(pear=None, post=False):
    """
    :param post: boolean to post to SEFARIA_SERVER
    :param pear: tuple (oRef Tanakh, oRef base book)
    :return: list of links (to be posted)
    """
    if not pear:
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
    thresh = ''
    # for thresh in [10, 22, 50]:
    base_refs = pear[1].all_segment_refs()
    link_options = get_dicta_matches(base_refs, onlyDH=False, priority_tanakh_chunk=pear[0], min_thresh=0)
    links, linkMatchs = zip(*[data_to_link(link_option, generated_by="Yalkut_shimoni_quotations") for link_option in link_options])
    # links, link_data = link_options_to_links(link_options, min_score=thresh)
    write_to_csv(links, linkMatchs, filename=f"dicta_{thresh}")
    print(len(links))

    write_links_to_json("ys_links", links)

    if post:
        post_link(links)
    return links

    # # dh code
    # matches = get_matches(pear)
    # links, link_data = link_options_to_links(matches, link_type="Midrash")
    # write_to_csv(links, link_data, filename="dh")


def write_links_to_json(filename, links):
    with open(f'{filename}.json', "w+") as fl:
        json.dump(links, fl)


def get_from_file(file_name):
    with open(file_name, "r") as link_file:
        links = json.load(link_file)
    return links


def post_links_from_file(file_name, score=22, server=SEFARIA_SERVER):
    links_to_post = []
    links = get_from_file(file_name)
    for l in links:
        if l["score"] > score:
            links_to_post.append(l)
    post_link(links_to_post, server=server)



def bunch_refs_to_ranged_refs(links):
    # assuming all of one side is the same segment looking here at the other side
    ref_groups = []
    Rl = lambda l: Ref(l['refs'][0])
    links = list(links)
    links.sort(key=lambda l: int(re.search(':(.*$)', l['refs'][0]).group(1)))
    to_side_orefs = [Rl(l) for l in links]
    for l in links:
        found_group = []
        prev_r = Rl(l).prev_segment_ref()
        next_r = Rl(l).next_segment_ref()
        if prev_r in to_side_orefs or next_r in to_side_orefs:
            for group_i, group in enumerate(ref_groups):
                Rlgroup = [Rl(l) for l in group]
                if prev_r in Rlgroup or next_r in Rlgroup:
                    # if found_group:
                    #     ref_groups[group_i].extend(found_group)
                    group.append(l)
                    ref_groups[group_i] = group
                    found_group = True
                    break
        if not found_group:
            ref_groups.append([l])

    # print([Rl(l) for group in ref_groups for l in group])
    output_links = []
    for group in ref_groups:
        if len(group) > 1:
            ranged_ref_json = group[0].copy()
            try:
                ranged_ref_json['refs'][0] = Ref(f'{Rl(group[0]).he_normal()} - {Rl(group[-1]).he_normal()}').normal()
                output_links.append(ranged_ref_json)
            except sefaria.system.exceptions.InputError as e:
                output_links.extend(group)
                print("fyi caught this in bunch_refs_to_ranged_refs", e)
        else:
            output_links.append(group[0])
    # print([Rl(l) for l in output_links])
    return output_links

def dicta_links_from_ref(tref, post=False, onlyDH=False, min_thresh=22, priority_tanakh_chunk=None, offline=None, mongopost=True, seg_split= None):
    oref = Ref(tref)
    base_refs = oref.all_segment_refs()
    # if mode == 'mishna':
    #     get_dicta_matches_mishna(seg.normal(), onlyDH=False, min_thresh=25, priority_tanakh_chunk=Ref('psalms'),
    #                              offline=None,
    #                              seg_split=':')
    link_options = get_dicta_matches(base_refs, onlyDH=onlyDH, min_thresh=min_thresh, priority_tanakh_chunk=priority_tanakh_chunk, offline=offline, seg_split=seg_split)
    if not link_options:
        # print("no links found")
        return
    links, linkMatchs = zip(*[data_to_link(link_option, generated_by='quotation_finder_ranged', type='quotation_auto') for link_option in link_options])
    links = bunch_refs_to_ranged_refs(links)
    write_to_csv(links, linkMatchs, filename=f"dicta_{oref.book}")
    # print(links)
    # write_links_to_json(f'{tref}', links)
    if post:
        post_link(links)
    if mongopost:
       mongo_post([l.copy() for l in links])  # todo: post wordLevelData to local as well. (since it is not perfect Data anyway :) )
#, server="http://localhost:8000")
    return links


def link_a_parashah_node_struct_index(index_name, onlyDH=False, post=False):
    """
    input index with an assumed Parashah structure
    :param index_name: index name
    :param onlyDH: choses to look only at quotations in the beginning of the segment for the commentary type of linking
    :param post: option to post atomatically to SEFARIA-SERVER
    :return: list(:Link): list of all the links
    """
    peared = get_zip_parashot_refs(index_name)
    all_links = []
    for pear in peared:
        base_refs = pear[1].all_segment_refs()
        w2w = '''(ב?מדרש|ב?פסוק|והנה|כתיב|פ?רש"?י|ו?כו'?)''' if not post and onlyDH else None
        link_options = get_dicta_matches(base_refs, onlyDH=onlyDH, min_thresh=22, priority_tanakh_chunk=pear[0], wrods_to_wipe=w2w)
        if not link_options:
            continue
        links, linkMatchs = zip(*[data_to_link(link_option, generated_by='quotation_linker_dh', type='quotation_auto') for link_option in link_options])
        write_to_csv(links, linkMatchs, filename=f"dicta_{base_refs[0].index.title}")
        print(links)
        all_links.extend(links)
        write_links_to_json(f'{index_name}', links)
        if post:
            post_link(links)
            print(f"posted Parashah {pear[1]}")
            # f.write(f"posted Parashah {pear[1]}\n")
    return all_links


def create_file_for_offline_run(version: Version, filename: str):
    vm = get_version_mapping(version)
    write_links_to_json(filename, vm)
    return vm


def get_version_mapping(version: Version) -> dict:
    """
    version: version object of text being modified
    """
    def populate_change_map(old_text, en_tref, he_tref, _):
        nonlocal mapping
        mapping[en_tref] = old_text

    mapping = {}
    version.walk_thru_contents(populate_change_map)
    return mapping


def mongo_post(links):
    db_qf.quotations.insert_many(links)


def run_offline(title, cat, min_thresh=22, post=False, mongopost=True, priority_tanakh_chunk_type=None, priority_fallback=None, max_word_number=30, offline=True, seg_split=None):
    """

    :param title:
    :param cat:
    :param min_thresh:
    :param post:
    :param mongopost:
    :param priority_tanakh_chunk:
    :param seg_split:
    :return:
    """
    text_mapping = get_from_file(f"offline/text_mappings/{cat}/{title}.json")
    dicta_results_mapping = get_from_file(f"dicta_answers/{cat}/{title}.json")
    priority = trivial_priority(title, text_mapping, priority_tanakh_chunk_type)
    all_links = []
    for r in text_mapping.keys():
        if offline: # or dicta_results_mapping.get(r, None):
            offline1 = [text_mapping, dicta_results_mapping]
        else:
            print(f'API call, ref {r}')
            offline1 = None
        if max_word_number and Ref(r).word_count() > max_word_number:
            continue
        links = dicta_links_from_ref(f'{r}', post=post, min_thresh=min_thresh, offline=offline1, mongopost=mongopost, priority_tanakh_chunk=priority.get(r,  priority_fallback), seg_split=seg_split)
        if links:
            all_links.extend(links)
    if post:
        post_link(all_links)



def trivial_priority(title, text_mapping, priority_type="perek"):
    """
    This function returns a dictionary that maps tref in base text to a matching oref in Tanakh that suppsedaly has priority over other pesukim results for this base ref.
    :param title: book title
    :param text_mapping: Dictionary keys are refs of the book and values are the text
    :param priority_type: 'perek': gets the trivial structure based on perek pasuk (often tanakh commentaries)
                'parasha': gets the trivial structure if there is a parasha structure (often Midrash and Chasidut books)
                str: if this string can be read as a Ref like 'psalms' then the priority will be that book (a good idea for Liturgy books)
    :return: Dictionary. keys: trefs in the base book. values: oref from Tanakh
    """
    if isinstance(priority_type, dict):
        assert set(priority_type.keys()).intersection(set(text_mapping.keys()))
        return priority_type
    priority = dict()
    if priority_type == 'perek':
        for k in text_mapping.keys():
            #todo: look at the depth of the parshan to know if it is a perek level structur dictionary or a pasuk level
            orefs_list = library.get_refs_in_string(re.sub(f'{title}', '', k))
            if orefs_list:
                priority[k] = orefs_list[0]
    elif priority_type == 'parasha':
        peared = get_zip_parashot_refs(title)
        priority = dict([(r.normal(), item[1]) for item in peared if item[0] for r in item[0].all_segment_refs()])
    else:
        try:
            r = Ref(priority_type)
            priority = dict((k, r) for k in text_mapping.keys())
        except AttributeError:
            return {}
    return priority


def offline_text_mapping_cat(cat):
    os.chdir(f'offline/text_mappings/{re.sub(" ", "_",cat)}')
    for ind_name in library.get_indexes_in_category(cat):
        ind = library.get_index(ind_name)
        # vs = [v for v in ind.all_segment_refs()[1].versionset('he')]
        vset = VersionSet({'title': ind.title, 'language': 'he', "priority" : { '$exists' : 'true' }})
        vs = vset.records
        if vs:
            try:
                create_file_for_offline_run(vs[0], ind_name)
            except KeyError:
                print(ind_name)
                pass
def read_keep(key):
    with open(f'{path}/api_results/keep_{mode}.json', 'r') as fp:
        keep = json.load(fp)
        if keep.get(key, None):
            print(keep.get(key, None))

run_all_night_list = library.get_index('Siddur Sefard').all_segment_refs()[3760: 4200]

def run_all_night(seg):

    dicta_links_from_ref(seg.normal(), post=False, onlyDH=False, min_thresh=25, offline=None,
                         mongopost=True, seg_split='.')


if __name__ == '__main__':

    # # range_ref = 'ילקוט שמעוני על התורה, חקת' #'Tzror_HaMor_on_Torah, Numbers.15-17.'# "Noam_Elimelech"
    # range_ref = 'Tzror HaMor on Torah, Deuteronomy'#'Yalkut Shimoni on Torah' #'Chatam Sofer on Torah, Pinchas'
    # range_name = range_ref
    # f = open(f"intraTanakhLinks_{range_name}.txt", "a+")  # not the right place to open this for the other functions. read doc.
    # # f.write(range_name)
    # # links = link_a_parashah_node_struct_index(range_name, onlyDH=False, post=True)
    # # pear = (Ref('פרשת שלח'), Ref("ילקוט שמעוני על התורה, שלח לך")) #(Ref('Numbers 13:1-15:41'), Ref('Yalkut Shimoni on Torah 742'))  # :7-750:13 ( Ref('פרשת שלח'), Ref("ילקוט שמעוני על התורה, שלח לך"))
    #
    # # ys = get_zip_ys()
    # # ys_pairs = [(item[1], item[0]) for b in ys for item in b]
    # # ys_pairs_dict = dict([(r.normal(), item[1]) for item in ys_pairs if item[0] for r in item[0].all_segment_refs()])
    # # mapping = get_version_mapping(Version().load({'title': 'Yalkut Shimoni on Torah', 'versionTitle': 'Yalkut Shimoni on Torah'}))
    # # for seg in list(mapping.keys())[4286:4287]:  # [895:1925]:
    # #     links = dicta_links_from_ref(seg, post=True, min_thresh=22, priority_tanakh_chunk=ys_pairs_dict.get(seg, None))
    # #
    # # pear = (Ref('פרשת חקת'), Ref('ילקוט שמעוני על התורה, חקת'))
    # # links = get_links_ys(pear, post=True)
    # text_mappings = get_links_from_file("Tzror_HaMor_on_Torah.json")
    # dicta_results_mapping = get_links_from_file("dicta_answers/Tzror_HaMor_on_Torah.json")
    # links = dicta_links_from_ref(f'{range_ref}', post=False, min_thresh=22, priority_tanakh_chunk=Ref('Deuteronomy'), offline=[text_mappings, dicta_results_mapping])
    # # f.close()
    # log.close()
    # # post_links_from_file("Numbers 13:1-15:41/ys_links.txt", score=10)
    # liturgy_list = [f.split(".json")[0] for f in os.listdir(f'{os.getcwd()}/dicta_answers/Liturgy')][1::]
    # liturgy_ls = os.listdir("offline/text_mappings/Liturgy")
    # liturgy_ls = ['Hallel.json',
    # 'Shir HaKavod.json',
    # 'Yizkor.json',
    # 'Selichot Nusach Lita Linear.json',
    # 'Azharot of Solomon ibn Gabirol.json',
    # 'Selichot Nusach Polin.json',
    # "Seder Tisha B'Av (Edot HaMizrach).json",
    # 'Shabbat Siddur Sefard Linear.json',
    # 'Selichot Edot HaMizrach.json',
    # 'Yedid Nefesh.json',
    # 'Siddur Sefard.json',
    # 'Machzor Yom Kippur Sefard.json',
    # 'Pesach Haggadah Edot Hamizrah.json',
    # 'Siddur Edot HaMizrach.json',
    # "Seder Ma'amadot.json",
    # 'Keter Malkhut.json',
    # 'Lekha Dodi.json',
    # 'current_ref_stats.csv',
    # 'Weekday Siddur Sefard Linear.json',
    # "Kinnot for Tisha B'Av (Ashkenaz).json"]
    # # for title in liturgy_ls:
    # #     try:
    # #         if title in ['Selichot Nusach Ashkenaz Lita', 'Selichot Nusach Lita Linear', 'Selichot Nusach Polin', 'Selichot Edot HaMizrach']:
    # #             continue
    # #     except FileNotFoundError:
    # #         continue
    # #     n_title = re.split("\.", title)[0]
    # #     run_offline(n_title, 'Liturgy', min_thresh=25, post=False, mongopost=True, priority_tanakh_chunk_type='psalms', max_word_number=50) #Machzor Rosh Hashanah Sefard', 'Siddur Ashkenaz' #{'status': 'ok. Link: Selichot Nusach Ashkenaz Lita, Yom Kippur Eve 3:15 | Psalms 86:5 Saved'}
    # # for title in ['Enei Moshe on Ruth']:#['Devarim Tovim on Ecclesiastes', 'Massat Moshe on Esther', 'Shoshanat HaAmakim on Song of Songs', 'Rav Peninim on Proverbs']:
    # #     run_offline(title, 'tanakh_comm', min_thresh=25, post=False, mongopost=True, priority_tanakh_chunk_type='perek', max_word_number=None)
    # # log.close()
    # ls_chasidut = [re.split("\.", t)[0] for t in os.listdir('dicta_answers/Chasidut')]
    # for title in ls_chasidut:#['Devarim Tovim on Ecclesiastes', 'Massat Moshe on Esther', 'Shoshanat HaAmakim on Song of Songs', 'Rav Peninim on Proverbs']:
    #     print(f'in book: {title}')
    #     try:
    #         if title in ['Shivchei HaBesht', 'Arvei Nachal', 'Beit Yaakov on Torah', 'Chiddushei HaRim on Torah', 'Ohr Zarua LaTzadik', "Me'or Einayim", 'Toldot Yaakov Yosef', 'Divrei Chalomot']:
    #             continue
    #         run_offline(title, 'Chasidut', min_thresh=25, post=False, mongopost=True, priority_tanakh_chunk_type='perek', max_word_number=None)
    #     except:
    #         print(f"book {title} failed!")
    # log.close()
    # offline_text_mapping_cat("Liturgy")
    # run_offline("Siddur Sefard", 'Liturgy', min_thresh=25, post=False, mongopost=True, priority_tanakh_chunk_type='psalms', max_word_number=100)
    # offline_text_mapping_cat("Liturgy")
    # run_offline("Siddur Sefard", 'Liturgy', min_thresh=22, post=True, mongopost=True, priority_tanakh_chunk_type='psalms', max_word_number=500, offline=False, seg_split=":")
    # seg = Ref('Siddur Ashkenaz, Festivals, Rosh Chodesh, Hallel, Berakhah before the Hallel 1')
    # seg = Ref('Siddur Sefard, Weekday Maariv, The_Shema 1')
    # seg = Ref('Siddur Sefard, Upon_Arising, Modeh Ani 1')
    # while seg:
    #     dicta_links_from_ref(seg.normal(), post=True, onlyDH=False, min_thresh=25, priority_tanakh_chunk=Ref('psalms'), offline=None,
    #                      mongopost=True, seg_split=':')
    #     seg = seg.next_segment_ref()
    # dicta_links_from_ref('Siddur Ashkenaz, Festivals, Rosh Chodesh, Hallel, Psalm 115:1', post=False, onlyDH=False, min_thresh=25, priority_tanakh_chunk=Ref('psalms'), offline=None,
    #                      mongopost=True, seg_split=':')

    # pool = multiprocessing.Pool(5)
    # pool.map(run_all_night, run_all_night_list)

    # dicta_links_from_ref('Siddur Ashkenaz, Festivals, Rosh Chodesh, Hallel, Psalm 115:1', post=False, onlyDH=False, min_thresh=25, priority_tanakh_chunk=Ref('psalms'), offline=None,
    #                      mongopost=True, seg_split=':')

    dicta_links_from_ref("Siddur Sefard, Upon Arising, Upon Entering Synagogue 4", post=True, onlyDH=False, min_thresh=25, priority_tanakh_chunk=Ref('psalms'), offline=None,
                         mongopost=True, seg_split=':')