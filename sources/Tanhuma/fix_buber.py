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


def pre_process(text):
    i_tags = re.findall(u"<i>.*?</i>", text)
    for i_tag in i_tags:
        new_i_tag = i_tag.replace("<i>", "<j>").replace("</i>", "</j>")
        text = text.replace(i_tag, new_i_tag)
    return text

if __name__ == "__main__":
    prod = {}
    ste = {}
    prod_json = json.load(open("buber_prod.json"))["text"]
    for node, text_arr in prod_json.items():
        for ch_count, chapter in enumerate(text_arr):
            for p_count, paragraph in enumerate(chapter):
                ref = "Midrash Tanchuma Buber, {} {}:{}".format(node, ch_count+1, p_count+1)
                prod[ref] = paragraph


    ste_json = json.load(open("buber_ste.json"))["text"]
    for node, text_arr in ste_json.items():
        for ch_count, chapter in enumerate(text_arr):
            for p_count, paragraph in enumerate(chapter):
                ref = "Midrash Tanchuma Buber, {} {}:{}".format(node, ch_count+1, p_count+1)
                ste[ref] = paragraph

    prob_refs = []
    for ref, prod_text in prod.items():
        if ref not in ste:
            prob_refs.append(ref)
            continue

        parsha = ref.split(", ")[-1].replace("Appendix to ", "")
        book = Ref(parsha).book
        if book in ["Numbers", "Deuteronomy"]:
            continue

        ste_text = pre_process(ste[ref])
        prod_text = pre_process(prod_text)

        i_tags_ste = re.findall(u'<sup>{}</sup><i class="footnote">.*?</i>', ste_text)
        i_tags_prod = re.findall(u'<sup>{}</sup><i class="footnote">.*?</i>', prod_text)


        if len(i_tags_prod) == 0 == len(i_tags_ste):
            continue

        if not len(i_tags_ste) == len(i_tags_prod):
            print len(i_tags_ste) - len(i_tags_prod)
            prob_refs.append(ref)
        else:
            text_to_modify = prod_text
            for count in range(len(i_tags_prod)):
                text_to_modify = text_to_modify.replace(i_tags_prod[count], i_tags_ste[count])
            text_to_modify = text_to_modify.replace("<j>", "<i>").replace("</j>", "</i>")

        send_text = {
            "language": "en",
            "text": text_to_modify,
            "versionTitle": "Midrash Tanhuma, S. Buber Recension; trans. by John T. Townsend, 1989.",
            "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001095601"
        }
        print ref
        #post_text(ref, send_text, server="http://ste.sefaria.org")


    print "****"
    print prob_refs

