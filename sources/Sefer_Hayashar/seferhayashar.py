# -*- coding: utf-8 -*-
__author__ = 'stevenkaplan'
import sys
import re
from sources.functions import *
from sefaria.model import *
from data_utilities.XML_to_JaggedArray import XML_to_JaggedArray
from data_utilities.dibur_hamatchil_matcher import *


class Sefer:
    def __init__(self):
        self.not_found = []
        self.footnote_map = {}
        self.he_chapters = [u"הקדמה",
                            u"השער הראשון - סוד בריאת העולם.",
                            u"השער השני - מפורש בו עמודי העבודה וסיבותיה.",
                            u"השער השלישי - באמונה ובענינים בסודות הבורא יתברך.",
                            u"השער הרביעי - העבודה על דרך קצרה.",
                            u"השער החמישי - בעמודי העבודה. והם חמישה, ואלו הם, השכל, והאהבה, והיראה,   והחכמה, והאמונה.",
                            u"השער השישי - בפירוש הדברים המסייעים על עבודת האל, יתעלה, והמעכבים אותה.",
                            u"השער השביעי - בעניני התשובה וכל הדברים התלויים בה והנלוים אליה מסדר התפילה   ועניני הפרישות.",
                            u"השער השמיני - מעניני דעת הבורא יתברך.",
                            u"השער התשיעי - בסימני רצון הבורא ובאשר יוכל אדם להכיר אם מצא חן בעיני אלהיו   ואם קבל מעשיו.",
                            u"השער העשירי - בעניני התשובה.",
                            u"השער האחד עשר - במעלות הצדיקים.",
                            u"השער השנים עשר - בסודות העולם הבא.",
                            u"השער השלושה עשר - בכל עניני העבודה.",
                            u"השער הארבעה עשר - בחשבון האדם עם נפשו.",
                            u"השער החמישה עשר - בפירוש העת הראויה לעבודת האל יתברך.",
                            u"השער השישה עשר - אזכור בו קצת חמודות העולם הבא, וכנגדם אזכיר פגעי העולם   הזה ומכשלותיו ורעותיו.",
                            u"השער השבעה עשר - בזכרון האדם יום המות.",
                            u"השער השמונה עשר - בהפרש אשר בין צדיק ורשע.",
                            u"הקדמת המתרגם",
                            u"נספח א",
                            u"נספח ב"]

        self.en_chapters = ["INTRODUCTION",
                "CHAPTER I The Mystery of the Creation of the World",

                "CHAPTER II The Pillars Of The Service Of God And Its Motivation",

                "CHAPTER III Concerning Faith and Matters Involved In The Mysteries Of The Creator Blessed Be He",

                "CHAPTER IV Service Briefly Discussed",

                "CHAPTER V Concerning The Pillars Of Worship",

                "CHAPTER VI An Explanation Of The Things Which Help In The Worship Of God May He Be Extolled And The Things Which Hinder",

                "CHAPTER VII Concerning Repentance And All Matters Pertaining To It From The Order Of Prayer And The Matters Of Self Restraint",

                "CHAPTER VIII Matters Concerning The Knowledge Of The Creator Blessed Be He",

                "CHAPTER IX Concerning The Signs Of The Will Of The Creator And How A Man Can Know He Has Found Favor In The Eyes Of His God And If God Has Accepted His Deeds",

                "CHAPTER X Concerning Repentance",

                "CHAPTER XI Concerning The Virtues Of The Righteous",

                "CHAPTER XII Concerning The Mysteries Of The World To Come",

                "CHAPTER XIII Concerning Service to God",

                "CHAPTER XIV Concerning The Reckoning A Man Must Make With Himself",

                "CHAPTER XV Explaining The Time Which Is Most Proper For The Service Of God Blessed Be He",

                "CHAPTER XVI I shall note in this chapter some of the delights of the world to come and as opposed to them I will note the plagues the stumbling blocks and the evil of this world",

                "CHAPTER XVII When A Man Remembers The Day Of Death",

                "CHAPTER XVIII Concerning The Difference Between The Righteous Man And The Wicked One",

                "TRANSLATORS FOREWORD",

                "Addendum I THE ETHICAL WORK SEFER HAYASHAR AND THE PHILOSOPHICAL VIEWS CONTAINED THEREIN",

                "Addendum II THE LOVE AND THE FEAR OF GOD IN THE SEFER HAYASHAR"]


    def matchFootnotes(self):
        def base_tokenizer(str):
            str = re.sub(ur"\([^\(\)]+\)", u"", str)
            word_list = re.split(ur"\s+", str)
            word_list = [w for w in word_list if w]  # remove empty strings
            return word_list

        results = match_ref(yashar_text, dhs_arr, base_tokenizer, verbose=True)['matches']


    def getDHs(self):
        tc = TextChunk(Ref("Sefer HaYashar, Footnotes, Main Content"), vtitle="Sefer Hayashar, trans. Seymour J. Cohen. 1973.")
        dhs = []
        self.full_dhs = []
        for count, line in enumerate(tc.text):
            start_pos = line.find(u'\n\u201c')
            if start_pos is not -1:
                end_pos = line.find(u'\u201d')
                dhs.append(line[start_pos+2:end_pos-1])
                self.full_dhs.append(line)
            else:
                self.not_found.append(line)
        return dhs


    def getBaseText(self):
        base_text = []
        base_text_as_str = ""
        self.footnote_map = {}
        prev_count = 0
        for ch_count, ch_title in enumerate(self.en_chapters):
            if ch_count not in [0, 19, 20, 21]:
                ref = "Sefer HaYashar, {}".format(ch_title)
                tc = TextChunk(Ref(ref), vtitle="Sefer Hayashar, trans. Seymour J. Cohen. 1973.")
                for count, line in enumerate(tc.text):
                    base_text.append(line)
                    self.footnote_map[count + prev_count] = "Sefer HaYashar, {} {}".format(ch_title, count+1)
                    base_text_as_str += line
                prev_count += len(tc.text)
        return base_text, base_text_as_str


    def getTuples(self, dhs, base_text, base_text_as_str):
        prev_line_num = 0
        how_many = 0
        how_outer = 0
        ftnotes_tuples = {}
        for dh_index, dh in enumerate(dhs):
            found = False
            if base_text_as_str.lower().find(dh.lower()) >= 0:
                how_outer += 1
                for count, line in enumerate(base_text):
                    if count < prev_line_num:
                        continue
                    start_pos = self.getStartPos(line, dh)
                    if start_pos >= 0:
                        if count not in ftnotes_tuples:
                            ftnotes_tuples[count] = []
                        ftnotes_tuples[count].append((dh, u"<i class='footnote' data-order='{}'></i>".format(dh_index+1)))
                        prev_line_num = count
                        how_many += 1
                        found = True
                        break
                if found == False:
                    self.not_found.append(self.full_dhs[dh_index])
            else:
                self.not_found.append(self.full_dhs[dh_index])

        return ftnotes_tuples

    def match_quotes_and_post(self):
        dhs = self.getDHs()
        base_text, base_text_as_str = self.getBaseText()
        ftnotes_tuples = self.getTuples(dhs, base_text, base_text_as_str)
        for line_n in ftnotes_tuples:
            for ftnote_tuple in ftnotes_tuples[line_n]:
                dh = ftnote_tuple[0]
                i_tag = ftnote_tuple[1]
                start_pos = self.getStartPos(base_text[line_n], dh)
                if start_pos == -1:
                    self.not_found.append(dh)
                else:
                    base_text[line_n] = u"{}{}{}".format(base_text[line_n][:start_pos], i_tag, base_text[line_n][start_pos:])

        for line_n in self.footnote_map:
            ref = self.footnote_map[line_n]
            send_text = {
                "language": "en",
                "text": base_text[line_n],
                "versionTitle": "Sefer Hayashar, trans. Seymour J. Cohen. 1973.",
                "versionSource":"http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002199310"
                }
            post_text(ref, send_text)
        for count, not_found in enumerate(self.not_found):
            print "FOOTNOTE NOT FOUND:".format(count+1)
            print not_found
            print "\n"
        '''
        for line_n in self.footnote_map:
            ref = self.footnote_map[line_n]
            tc = TextChunk(Ref(ref), vtitle="Sefer Hayashar, trans. Seymour J. Cohen. 1973.")
            tc.text = base_text[line_n]
            tc.save()
        '''


    def getStartPos(self, line, dh):
        start_pos = line.find(dh)
        if start_pos == -1:
            start_pos = line.find(dh)
        if start_pos == -1:
            start_pos = line.find(dh.lower())
        return start_pos

if __name__ == "__main__":
    def parse(text_arr):
        assert type(text_arr) is list
        for index, text in enumerate(text_arr):
            text_arr[index] = text_arr[index].replace("<bold>", "<b>").replace("<italic>", "<i>").replace("</bold>", "</b>").replace("</italic>", "</i>")
            text_arr[index] = text_arr[index].replace("<li>", "<br>").replace("</li>", "")
            span_start = re.findall("<span.*?>", text_arr[index])
            span_end = re.findall("</span.*?>", text_arr[index])
            xref_start = re.findall("<xref.*?>", text_arr[index])
            xref_end = re.findall("</xref.*?>", text_arr[index])
            xrefs = xref_start + xref_end
            for xref in xrefs:
                text_arr[index] = text_arr[index].replace(xref, "")
            for tag in span_start:
                text_arr[index] = text_arr[index].replace(tag, "")
            for tag in span_end:
                text_arr[index] = text_arr[index].replace(tag, "")

        return text_arr

    post_info = {}
    post_info["language"] = "en"
    post_info["server"] = sys.argv[1]
    allowed_tags = ["book", "intro", "part", "chapter", "p", "ftnote", "title", "ol", "footnotes", "appendix"]
    allowed_attributes = ["id"]
    grab_title_lambda = lambda x: x[0].tag == "title"
    p = re.compile("\d+a?\.")
    reorder_test_lambda = lambda x: x.tag == "title" and p.match(x.text) is not None
    def reorder_modify(text):
        text = text.split(" ")[0]
        if text.split(".")[-1] == "":
            return text.split(".")[0]
        else:
            return text.split(".")[-1]


    post_info["versionTitle"] = "Sefer Hayashar, trans. Seymour J. Cohen. 1973."
    post_info["versionSource"] = "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002199310"
    file_name = "seferhayashar.xml"
    title = "Sefer HaYashar"

    sefer = Sefer()


    footnote_map = {}
    footnote_map[0] = "Introduction"
    for i in range(18):
        footnote_map[i+1] = "Main Content"
    footnote_map[19] = "Footnotes"
    footnote_map[20] = "Translators Foreword"
    footnote_map[21] = "Addendum I"
    footnote_map[22] = "Addendum II"

    x = 1
    if x == 0:
        parser = XML_to_JaggedArray(title, file_name, allowed_tags, allowed_attributes, post_info, footnote_map=footnote_map, deleteTitles=False)
        parser.set_funcs(parse, grab_title_lambda, reorder_test_lambda, reorder_modify)
        parser.run()
    else:
        sefer.match_quotes_and_post()
    '''sefer hayashar

1. parse everything normal way with XML parser locally
2. then using object model to access local data in main footnotes section, parse them such that every one with a quotation is matched, then we record where each one is matched to a file and the ones with nothing are put where they belong with a note about not being matched.
also is there is a quotation, it must match.  test for that

compile list of quotations, pass into DH matcher
check that they all matched to something
then find the exact place in textchunk where each one actually matches and put an i-tag there, and post that paragraph


    '''