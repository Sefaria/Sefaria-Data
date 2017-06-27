__author__ = 'stevenkaplan'
import csv
import re
from sources.functions import *
import json
from BeautifulSoup import BeautifulSoup
'''2 CSV versions: ste and prod
go through each segment with all_segment_refs() and for each segment, use re.findall
<sup>1</sup><i class="footnote">See above, Lev. 7:7.</i>
to get all i-tags,
then make sure both versions have the same number
then say segment_text_of_production.replace(my_i_tag[0], ste_i_tag[0])
and so on'''

def replace_i_tags(prod_ch, i_tags_prod, i_tags_ste):
    i_tag_counter = 0
    for pos, prod_text in enumerate(prod_ch):
        while i_tag_counter < len(i_tags_prod) and i_tags_prod[i_tag_counter] in prod_text:
            prod_ch[pos] = prod_ch[pos].replace(i_tags_prod[i_tag_counter], i_tags_ste[i_tag_counter])
            i_tag_counter += 1

    assert i_tag_counter == len(i_tags_prod)

    for pos, prod_text in enumerate(prod_ch):
        prod_ch[pos] = prod_ch[pos].replace("<j>", "<i>").replace("</j>", "</i>")
    return prod_ch

def pre_process(text_arr):
    for count in range(len(text_arr)):
        i_tags = re.findall(u"<i>.*?</i>", text_arr[count])
        for i_tag in i_tags:
            new_i_tag = i_tag.replace("<i>", "<j>").replace("</i>", "</j>")
            text_arr[count] = text_arr[count].replace(i_tag, new_i_tag)
    return text_arr

if __name__ == "__main__":
    prod = {}
    ste = {}
    prod_json = json.load(open("buber_prod.json"))["text"]
    for node, text_arr in prod_json.items():
        for ch_count, chapter in enumerate(text_arr):
            ref = "Midrash Tanchuma Buber, {} {}".format(node, ch_count+1)
            prod[ref] = chapter


    ste_json = json.load(open("buber_ste.json"))["text"]
    for node, text_arr in ste_json.items():
        for ch_count, chapter in enumerate(text_arr):
            ref = "Midrash Tanchuma Buber, {} {}".format(node, ch_count+1)
            ste[ref] = chapter

    prob_refs = []

    for ref, prod_ch in prod.items():
        if ref not in ste:
            continue

        parsha = ref.split(", ")[-1].replace("Appendix to ", "")
        book = Ref(parsha).book
        if book in ["Numbers", "Deuteronomy"]:
            continue

        ste_ch = pre_process(ste[ref])
        prod_ch = pre_process(prod_ch)

        i_tags_prod = []
        i_tags_ste = []
        for ste_text in ste_ch:
            i_tags_ste += re.findall(u'<sup>\d+</sup><i class="footnote">.*?</i>', ste_text)

        for prod_text in prod_ch:
            i_tags_prod += re.findall(u'<sup>\d+</sup><i class="footnote">.*?</i>', prod_text)


        if len(i_tags_prod) == 0 == len(i_tags_ste):
            continue

        if not len(i_tags_ste) == len(i_tags_prod):
            print len(i_tags_ste) - len(i_tags_prod)
            prob_refs.append(ref)
        else:
            text_to_modify = replace_i_tags(prod_ch, i_tags_prod, i_tags_ste)

        send_text = {
            "language": "en",
            "text": text_to_modify,
            "versionTitle": "Midrash Tanhuma, S. Buber Recension; trans. by John T. Townsend, 1989.",
            "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001095601"
        }
        post_text(ref, send_text, server="https://www.sefaria.org")


    print "****"
    print prob_refs