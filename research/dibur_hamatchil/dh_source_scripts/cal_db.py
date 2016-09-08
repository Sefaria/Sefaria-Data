# -*- coding: utf-8 -*-

import codecs
import json
import re
import sys,os

sys.path.insert(0,'../../../')

from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"

from sefaria.model import *

from data_utilities import dibur_hamatchil_matcher
from research.talmud_pos_research.language_classifier import cal_tools


cal_db_location = "../../talmud_pos_research/language_classifier/caldb_"

def make_cal_segments(mesechta):

    def get_daf_str(daf_num,daf_side_num):
        return '{}{}'.format(daf_num,'a' if daf_side_num == 1 else 'b')

    cal_gem_lines = []
    with open("{}{}.txt".format(cal_db_location,mesechta),"rb") as f:
        temp_gem_line = []
        curr_gem_line_num = -1
        curr_daf = ''
        for line in f:
            line_obj = cal_tools.parseCalLine(line,True,False)
            line_obj["daf"] = get_daf_str(line_obj['pg_num'],line_obj['side']) #add a daf str prop
            line_obj["word"] = line_obj["word"].replace("'",'"')
            if len(line_obj["word"]) > 1 and line_obj["word"][-1] == '"':
                line_obj["word"] = line_obj["word"][0:-1] #remove abbreviations

            if line_obj["line_num"] != curr_gem_line_num:
                if len(temp_gem_line) > 0:
                    small_gem_lines = [temp_gem_line]
                    has_big_lines = True

                    #recursively split up big lines until they're not big
                    while has_big_lines:
                        has_big_lines = False
                        new_small_gem_lines = []
                        for gem_line in small_gem_lines:
                            if len(gem_line) > 5:
                                has_big_lines = True
                                cut_index = len(gem_line)/2
                                new_small_gem_lines.append(gem_line[:cut_index])
                                new_small_gem_lines.append(gem_line[cut_index:])
                            else:
                                new_small_gem_lines.append(gem_line)
                        small_gem_lines = new_small_gem_lines
                    for gem_line in small_gem_lines:
                        cal_gem_lines.append(gem_line)
                temp_gem_line = [line_obj]
                curr_gem_line_num = line_obj["line_num"]
            else:
                temp_gem_line.append(line_obj)

    '''
    #clean up lines with only 1 or 2 words
    new_cal_gem_lines = []
    new_cal_gem_dafs = []

    for i,clt in enumerate(zip(cal_gem_lines,cal_gem_line_nums,cal_gem_dafs)):
        cal_line = clt[0], line_num = clt[1], daf = clt[2]
        if i > 0 and cal_gem_dafs[i-1] == daf and line_num-cal_gem_line_nums[i-1] <= 1:
            p_cal_line = cal_gem_lines[i-1]
        else:
            p_cal_line = None

        if i < len(cal_gem_lines)-1 and cal_gem_dafs[i+1] == daf and cal_gem_line_nums[i+1]-line_num <= 1:
            n_cal_line = cal_gem_lines[i+1]
        else:
            n_cal_line = None

        if len(cal_line) <= 2
    '''

    #break up by daf, concat lines to strs
    all_daf_lines = []
    all_dafs = []
    curr_daf = ''
    curr_daf_lines = []
    for line in cal_gem_lines:
        if line[0]["daf"] != curr_daf:
            if len(curr_daf_lines) > 0:
                all_daf_lines.append(curr_daf_lines)
                all_dafs.append(curr_daf)
            curr_daf = line[0]["daf"]
            curr_daf_lines = [line]
        else:
            curr_daf_lines.append(line)

    cal_tools.saveUTFStr({"lines":all_daf_lines,"dafs":all_dafs},"cal_lines_{}.json".format(mesechta))



def match_cal_segments(mesechta):
    def tokenize_words(str):
        str = str.replace(u"־", " ")
        str = re.sub(r"</?[a-z]+>", "", str)  # get rid of html tags
        str = re.sub(r"\([^\(\)]+\)", "", str)  # get rid of refs
        str = str.replace("'", '"')
        word_list = filter(bool, re.split(r"[\s\:\-\,\.\;\(\)\[\]\{\}]", str))
        return word_list

    def merge_cal_word_objs(s,e,word_obj_list):
        obj_list = word_obj_list[s:e]
        m_word = u" ".join([o["word"] for o in obj_list])
        m_head_word = u" ".join([o["head_word"] for o in obj_list])
        m_pos_list = [o["POS"] for o in obj_list]
        m_pos = max(set(m_pos_list), key=m_pos_list.count)

        new_obj = obj_list[0].copy()
        new_obj["word"] = m_word
        new_obj["head_word"] = m_head_word
        new_obj["POS"] = m_pos
        return [new_obj] #returns a single element array which will replace a range s:e in the original array

    cal_lines = json.load(open("cal_lines_{}.json".format(mesechta), "r"), encoding="utf8")
    dafs = cal_lines["dafs"][12:13]
    lines_by_daf = cal_lines["lines"][12:13]

    super_base_ref = Ref(mesechta)
    subrefs = super_base_ref.all_subrefs()
    ical = 0

    for curr_sef_ref in subrefs:
        if curr_sef_ref.is_empty(): continue
        if ical >= len(dafs): break


        daf = dafs[ical]
        print "----- DAF {}  ({}/{})-----".format(daf,ical,len(dafs))


        base_tc = TextChunk(curr_sef_ref, "he")
        bas_word_list = []  # re.split(r"\s+"," ".join(base_text.text))
        for segment in base_tc.text:
            bas_word_list += tokenize_words(segment)

        temp_out = [{"word": w, "class": "unknown"} for w in bas_word_list]



        lines = [[word_obj["word"] for word_obj in temp_line] for temp_line in lines_by_daf[ical]]
        word_obj_list = [word_obj for temp_line in lines_by_daf[ical] for word_obj in temp_line]
        lines_by_str = [u' '.join(line_array) for line_array in lines]

        curr_cal_ref = Ref("{} {}".format(mesechta, daf))

        out = []
        word_for_word_se = []
        cal_words = []
        missed_words = []

        global_offset = 0
        if curr_sef_ref == curr_cal_ref:
            start_end_map,abbrev_matches = dibur_hamatchil_matcher.match_text(bas_word_list, lines_by_str, verbose=False, word_threshold=0.5, with_abbrev_matches=True)
            abbrev_ranges = [[am.rashiRange for am in am_list] for am_list in abbrev_matches ]
            for iline,se in enumerate(start_end_map):

                curr_cal_line = lines[iline]

                # if there is an expanded abbrev, concat those words into one element
                if len(abbrev_ranges[iline]) > 0:
                    offset = 0 # account for the fact that you're losing elements in the array as you merge them
                    for ar in abbrev_ranges[iline]:
                        if ar[1] - ar[0] <= 0: continue #TODO there's an issue with the abbrev func, but i'm too lazy to fix now. sometimes they're zero length
                        curr_cal_line[ar[0]-offset:ar[1]+1-offset] = [u' '.join(curr_cal_line[ar[0]-offset:ar[1]+1-offset])]
                        word_obj_list[ar[0]-offset+len(cal_words):ar[1]+1-offset+len(cal_words)] = merge_cal_word_objs(ar[0]-offset+len(cal_words),ar[1]+1-offset+len(cal_words),word_obj_list)
                        offset += ar[1]-ar[0]
                        global_offset += offset
                        print offset

                cal_words += curr_cal_line
                if se[0] == -1:
                    word_for_word_se += [(-1,-1) for i in range(len(curr_cal_line))]
                    continue
                # matched_cal_objs_indexes = language_tools.match_segments_without_order(lines[iline],bas_word_list[se[0]:se[1]+1],2.0)
                curr_bas_line = bas_word_list[se[0]:se[1]+1]

                matched_words_base = dibur_hamatchil_matcher.match_text(curr_bas_line, curr_cal_line, char_threshold=0.4)
                word_for_word_se += [(tse[0]+se[0],tse[1]+se[0]) if tse[0] != -1 else tse for tse in matched_words_base]

            matched_word_for_word = dibur_hamatchil_matcher.match_text(bas_word_list, cal_words, char_threshold=0.4, prev_matched_results=word_for_word_se)

            bad_word_offset = 0
            for ical_word,temp_se in enumerate(matched_word_for_word):
                if temp_se[0] == -1:
                    missed_words.append({"word":word_obj_list[ical_word]["word"],"index":ical_word})
                    continue

                #dictionary juggling...
                for i in xrange(temp_se[0],temp_se[1]+1):
                    #in case a cal_words and word_obj_list aren't the same length bc a word got split up
                    if cal_words[ical_word] != word_obj_list[ical_word-bad_word_offset]["word"]:
                        if ical_word+1 < len(cal_words) and cal_words[ical_word+1] != word_obj_list[ical_word-bad_word_offset+1]["word"]:
                            bad_word_offset += 1
                        continue
                    cal_word_obj = word_obj_list[ical_word].copy()
                    cal_word_obj["cal_word"] = cal_word_obj["word"]
                    temp_sef_word = temp_out[i]["word"]
                    temp_out[i] = cal_word_obj
                    temp_out[i]["class"] = "talmud"
                    temp_out[i]["word"] = temp_sef_word

            cal_len = len(matched_word_for_word)
            print u"\n-----\nFOUND {}/{} ({}%)".format(cal_len - len(missed_words), cal_len, (1 - round(1.0 * len(missed_words) / cal_len, 4)) * 100)
            #print u"MISSED: {}".format(u" ,".join([u"{}:{}".format(wo["word"], wo["index"]) for wo in missed_words]))
            ical += 1
        out += temp_out

        sef_daf = curr_sef_ref.__str__().replace("{} ".format(mesechta),"").encode('utf8')
        doc = {"words": out,"missed_words":missed_words}
        fp = codecs.open("cal_matcher_output/{}/lang_naive_talmud/lang_naive_talmud_{}.json".format(mesechta,sef_daf), "w", encoding='utf-8')
        json.dump(doc, fp, indent=4, encoding='utf-8', ensure_ascii=False)
        fp.close()





def make_cal_lines_text(mesechta):
    cal_lines = json.load(open("cal_lines_{}.json".format(mesechta), "r"), encoding="utf8")
    dafs = cal_lines["dafs"]
    lines_by_daf = cal_lines["lines"]

    out = u""
    for ical in xrange(len(dafs)):
        out += u"----- DAF {} -----\n".format(dafs[ical])
        lines = [[word_obj["word"] for word_obj in temp_line] for temp_line in lines_by_daf[ical]]
        for i,l in enumerate(lines):
            out += u"({}a) - {}\n".format(i+1,u" ,".join(l))
    fp = codecs.open("cal_lines_text_{}.txt".format(mesechta),"w",encoding='utf-8')
    fp.write(out)
    fp.close()

mesechta = "Pesachim"
make_cal_segments(mesechta)
match_cal_segments(mesechta)
#make_cal_lines_text(mesechta)