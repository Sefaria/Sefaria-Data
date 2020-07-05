# -*- coding: utf-8 -*-
__author__ = 'stevenkaplan'
import django
django.setup()
from sources.Maharsha.parse import *
import os
from sources.functions import post_text, post_link, post_index, convertDictToArray, post_term
from sefaria.model import *

maharam_line = 0

def Gemara(maharam_line, which_line, daf, results):
    maharam_line += 1
    which_line['gemara'] += 1
    if results['gemara'][which_line['gemara']] == '0':
        missing_ones.append(
            title + " on " + masechet + "." + AddressTalmud.toStr("en", daf) + "." + str(maharam_line))
    else:
        links_to_post.append({
            "refs": [
                results['gemara'][which_line['gemara']],
                title + " on " + masechet + "." + AddressTalmud.toStr("en", daf) + "." + str(
                    maharam_line)
            ],
            "type": "commentary",
            "auto": True,
            "generated_by": title + masechet + " linker",
        })
    return maharam_line, which_line


def getTC(category, daf, masechet):
    if category in ["tosafot", "ran", "rosh"]:
        title = "{} on {}".format(category.title(), masechet)
        return Ref(title + "." + AddressTalmud.toStr("en", daf)).text('he')
    elif category == "gemara":
        return Ref(masechet + " " + AddressTalmud.toStr("en", daf)).text('he')
    elif category == "rashi":
        rashi = Ref("Rashi on " + masechet + "." + AddressTalmud.toStr("en", daf)).text('he')
        if len(rashi.text) == 0:
            print("rashbam by default {} {}".format(masechet, AddressTalmud.toStr("en", daf)))
            return Ref("Rashbam on " + masechet + "." + AddressTalmud.toStr("en", daf)).text('he')
        else:
            return rashi
    elif category == "rashbam":
        print("rashbam {} {}".format(masechet, AddressTalmud.toStr("en", daf)))
        return Ref("Rashbam on " + masechet + "." + AddressTalmud.toStr("en", daf)).text('he')
    
    
    
def parseDH(prev_dh, comment, category, same_dh):
    orig_comment = comment
    if same_dh is None:
        len_chulay = len("כו'")
        chulay = comment.find("כו'") + len_chulay
        if chulay > len_chulay - 1:
            dh, comment = comment[0:chulay], comment[chulay:]
        else:
            dh = comment
            comment = ""

        prev_dh = dh
    addDHComment(prev_dh, comment, category, same_dh)
    return prev_dh


def addDHComment(dh, comment, category, same_dh):
    dh = removeAllTags(dh)
    comment = removeAllTags(comment)
    dh = dh
    comment = comment
    dh1_dict[current_daf].append((category, dh))
    if same_dh:
        post_comment = comment
    else:
        post_comment = dh + comment

    post_comment = post_comment.strip()
    first_word = post_comment.split(" ")[0]
    post_comment = u"<b>{}</b> {}".format(first_word, " ".join(post_comment.split(" ")[1:]))
    comm_dict[current_daf].append(post_comment)
    dh_by_cat[category][current_daf].append(dh)
    if looking_for_perakim:
        dh_by_perek[current_perek].append((category, dh, current_daf))
        comm_by_perek[current_perek].append(post_comment)

def dh_extract_method(str):
    str = str
    str = str.replace('בד"ה', '').replace('וכו', '').replace('שם','')
    for each in [rashi, tosafot, gemara, ran, rashbam, rosh, 'בא"ד']:
        if each in str[0]:
            str = " ".join(str.split(" ")[1:])
            break
    return str

def determineCategory(category, count, comment):
    comment = comment + ':'
    if count == 0 and len(comment) == 0:
        return "", category
    comment = comment.strip()
    word = comment.split(" ")[0]
    if rashi in word:
        category = 'rashi'
    elif tosafot in word:
        category = 'tosafot'
    elif gemara in word or word in mishnah or shom in word:
        category = 'gemara'
    elif ran in word:
        category = 'ran'
    elif rosh in word:
        category = 'rosh'
    elif rashbam in word:
        category = "rashbam"
    elif word in dibbur_hamatchil:
        return "same_dh", category
    return None, category

def convertToOldFormat(arr):
    arr = arr['matches']
    for index, item in enumerate(arr):
        if item is None:
            arr[index] = '0'
        else:
            arr[index] = arr[index].normal()
    return arr

def Commentary(which_line, maharam_line, daf, category, results):
    maharam_line += 1
    which_line[category] += 1
    title = category.title() + " on " + masechet
    base_ref = results[category][which_line[category]]
    comm_ref = "Chokhmat Shlomo on Shevuot " + "."+AddressTalmud.toStr("en", daf)+"."+str(maharam_line)
    if base_ref == '0':
        missing_ones.append(comm_ref)
    else:
        links_to_post.append({
            "refs": [
                         base_ref,
                        comm_ref
                    ],
            "type": "commentary",
            "auto": True,
            "generated_by": title+masechet+" linker"
        })
        gemara_ref = getGemaraRef(base_ref)
        links_to_post.append({
            "refs": [
                comm_ref,
                gemara_ref
            ],
            "type": "commentary",
            "auto": True,
            "generated_by": title+masechet+" linker"
        })
    return which_line, maharam_line

def getGemaraRef(ref):
    ref = Ref(ref)
    assert len(ref.sections) == 3 ^ (not ref.is_segment_level())
    d = ref._core_dict()
    if len(d['sections']) == 3:
        d['sections'] = d['sections'][0:-1]
        d['toSections'] = d['toSections'][0:-1]
        gemara_ref = Ref(_obj=d)
    return gemara_ref.normal().replace("Tosafot on ", "").replace("Rashi on ", "").replace("Rosh on ", "").replace("Ran on ", "")

def postLinks(masechet):
    def base_tokenizer(str):
        str = re.sub(r"\([^\(\)]+\)", u"", str)
        word_list = re.split(r"\s+", str)
        word_list = [w for w in word_list if w]  # remove empty strings
        return word_list

    rosh_results = []
    perek_key = {}
    for perek in sorted(dh_by_perek.keys()):
        tuples = filter(lambda x: x[0] is 'rosh', dh_by_perek[perek])
        if len(tuples) > 0:
            cats, dhs, dappim = zip(*tuples)
            #for each daf and dh pair, that's the key to get the perek
            for daf, dh in zip(list(dappim), list(dhs)):
                perek_key[(daf, dh)] = perek
            base = Ref("Rosh on {} {}".format(masechet, perek)).text('he')
            assert len(base.text) > 0
            these_results = match_ref(base, list(dhs), base_tokenizer, dh_extract_method=dh_extract_method, verbose=False, with_num_abbrevs=False)['matches']
            assert len(tuples) is len(these_results)
            rosh_results.append(these_results)

    results = {}
    comments = {}

    for daf in sorted(dh1_dict.keys()):
        comments[daf] = {}
        results[daf] = {}
        for each_cat in categories:
            if each_cat == 'rosh':
                continue
            comments[daf][each_cat] = dh_by_cat[each_cat][daf]
        for each_type in comments[daf]:
            if each_type == 'rosh':
                continue
            results[daf][each_type] = []
            if len(comments[daf][each_type]) > 0:
                base = getTC(each_type, daf, masechet)
                if len(base.text) == 0:
                    comm_wout_base.write("{} {}: {}\n".format(masechet, daf, each_type))
                    base = getTC(each_type, daf-1, masechet)
                    combined_comments = comments[daf-1][each_type]+comments[daf][each_type]
                    if len(base.text) == 0:
                        print("Problem in {}".format(AddressTalmud.toStr("en", daf)))
                    else:
                        results[daf-1][each_type] = match_ref(base, combined_comments, base_tokenizer, dh_extract_method=dh_extract_method, verbose=False, with_num_abbrevs=False)
                        results[daf-1][each_type] = convertToOldFormat(results[daf-1][each_type])
                    dh1_dict[daf] = [x for x in dh1_dict[daf] if x[0] != each_type]
                else:
                    results[daf][each_type] = match_ref(base, comments[daf][each_type], base_tokenizer, dh_extract_method=dh_extract_method, verbose=False, with_num_abbrevs=False)
                    results[daf][each_type] = convertToOldFormat(results[daf][each_type])

    prev_perek = 0
    for daf in sorted(dh1_dict.keys()):
        maharam_line = 0
        which_line = {"rashi": -1, "tosafot": -1, "rosh": -1, "ran": -1, "gemara": -1, "rashbam": -1}
        for category, dh in dh1_dict[daf]:
            if category == 'gemara':
                Gemara(maharam_line, which_line, daf, results[daf])
            elif category == 'rosh':
                perek = perek_key[(daf, dh)]
                if perek > prev_perek:
                    rosh_line = -1
                prev_perek = perek
                maharam_line = Rosh(maharam_line, perek, daf, dh, rosh_results)
            else:
                which_line, maharam_line = Commentary(which_line, maharam_line, daf, category, results[daf])

    post_link(links_to_post, server=SEFARIA_SERVER)


def Rosh(maharam_line, perek, daf, dh, results):
    maharam_line += 1
    rosh_line += 1
    if results[perek - 1][rosh_line]:
        links_to_post.append({
            "refs": [
                results[perek - 1][rosh_line].normal(),
                title + " on " + masechet + "." + AddressTalmud.toStr("en", daf) + "." + str(
                    maharam_line)
            ],
            "type": "commentary",
            "auto": True,
            "generated_by": title + masechet + " linker",
        })
    return maharam_line

def create_index(tractate, title, heTitle):
    categories = library.get_index(tractate).categories
    root=JaggedArrayNode()
    heb_masechet = library.get_index(tractate).get_title('he')
    root.add_title(title+" on "+tractate.replace("_"," "), "en", primary=True)
    root.add_title(heTitle+u" על "+heb_masechet, "he", primary=True)
    root.key = title+tractate
    root.sectionNames = ["Daf", "Comment"]
    root.depth = 2
    root.addressTypes = ["Talmud", "Integer"]

    root.validate()

    index = {
        "title": title+" on "+tractate.replace("_"," "),
        "categories": ["Talmud", "Bavli", "Commentary", title, categories[-1]],
        "schema": root.serialize(),
        "base_text_titles": [tractate],
        "collective_title": title,
        "dependence": "Commentary",

    }
    post_index(index, server=SEFARIA_SERVER)
    return tractate

heb_numbers = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "ששי", "שביעי", "שמיני", "תשיעי", "עשירי", "אחד עשר", "שנים עשר", "שלשה עשר", "ארבעה עשר", "חמשה", "ששה"]
comm_dict = {}
dh1_dict = {}
rashi ='רש"י'
rashbam = 'פרשב"ם'
ran = 'ר"ן'
rosh = 'רא"ש'
tosafot = "תוס"
dibbur_hamatchil = ['בד"ה', 'ד"ה', 'בא"ד', """ד'"ה"""]
gemara = "גמ"
shom = "שם"
amud_bet = 'ע"ב'
mishnah = ['במשנה', 'מתני']
current_daf = 2
current_perek = 0
categories = ['rashi', 'tosafot', 'gemara', 'ran', 'rosh', 'rashbam']
dh_by_cat = {cat: {} for cat in categories}
links_to_post = []
category = "gemara"
prev_dh = ""
comm_by_perek = {}
dh_by_perek = {}
rosh_line = 0
looking_for_perakim = False
missing_ones = []
which_line = {}
comm_wout_base = open("comm_wout_base.txt", 'w')


if __name__ == "__main__":
    masechet = "Shevuot"
    title = "Chokhmat Shlomo"
    heTitle = "חכמת שלמה"
    file = "shevuot.tsv"
    create_index(masechet, title, heTitle)
    prev_dh = ""
    with open(file) as f:
        prev_daf = 1
        for n, line in enumerate(f):
            poss_daf, comment = line.split("\t")
            if poss_daf == "":
                current_daf = prev_daf
            else:
                curr_amud = int(poss_daf.find(".") == -1) - 1   # result is -1 for . and 0 for :
                current_daf = 2*getGematria(poss_daf) + curr_amud
                assert current_daf > prev_daf, line
                prev_daf = current_daf
                prev_dh = ""

            if not current_daf in dh1_dict:
                dh1_dict[current_daf] = []
                comm_dict[current_daf] = []
                for each_cat in categories:
                    dh_by_cat[each_cat][current_daf] = []

            comments = comment.strip().split(":")
            for count, comment in enumerate(comments):
                if len(comment.replace(" ", "")) < 3:
                    continue
                if comment[0] == ' ':
                    comment = comment[1:]
                comment += ':'
                same_dh, new_category = determineCategory(category, count, comment)
                if category != new_category:
                    category = new_category
                prev_dh = parseDH(prev_dh, comment, category, same_dh)
    text_to_post = convertDictToArray(comm_dict)
    send_text = {
        "versionTitle": "Vilna Edition",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957",
        "language": "he",
        "text": text_to_post,
    }
    post_text("{} on {}".format(title, masechet), send_text, "on", server=SEFARIA_SERVER)
    postLinks(masechet)




