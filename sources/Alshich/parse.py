# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
from sources.functions import *
from data_utilities.dibur_hamatchil_matcher import *


def match(file, DHs, text):
    def base_tokenizer(str):
        str = re.sub(ur"\([^\(\)]+\)", u"", str)
        word_list = re.split(ur"\s+", str)
        word_list = [strip_nekud(w) for w in word_list]
        new_list = []
        for w in word_list:
            if len(w) > 0:
                new_list.append(w)

        return new_list

    title = file.replace(".txt", "").title()
    for perek_num in DHs:
        print "!!!!!!!!!!!!!!!!"
        print perek_num

        for pasuk_num in range(len(DHs[perek_num])):
            base = TextChunk(Ref("{} {}:{}".format(title, perek_num, pasuk_num+1)), lang="he")
            results = match_ref(base, DHs[perek_num][pasuk_num], base_tokenizer=base_tokenizer)
            print results['matches']
    pass


def get_DH_comment(line):
    ten_word_pos = line.find(" ".join(line.split(" ")[10:11]))

    if 0 < line.find(".") < ten_word_pos:
        DH, comment = line.split(".", 1)
    elif 0 < line.find(u"וכו'") < ten_word_pos:
        DH, comment = line.split(u"וכו'", 1)
    else:
        DH, comment = line[0:ten_word_pos], line[ten_word_pos:]

    return DH, comment



if __name__ == "__main__":
    files = [file for file in os.listdir("./") if not file == "intro.txt" and file.endswith(".txt")]
    for file in files:
        perek_num = 0
        line_num = 0
        last_tag = ""
        last_perek_tag = ""
        pasuk_num = 0
        text = {}
        pasuk_list = []
        DHs = {}
        print
        print "In file {}:".format(file)
        for line in open(file):
            orig_line = line
            line = line.replace("\n", "").replace("\r", "").decode('utf-8')
            if len(line) == 0 or line.startswith("$") or "@02" in line or "@01" in line:
                continue

            if len(line.split(" ")) > 3:
                continue
            elif line.find("00") >= 0:
                poss_perek_num = getGematria(line)
                poss_perek_num = ChetAndHey(poss_perek_num, perek_num)
                if poss_perek_num <= perek_num:
                    print u"PEREK ISSUE: found {} after {}".format(line, last_perek_tag)
                    print poss_perek_num
                    print " ".join(prev_line.split(" ")[0:10])
                    perek_num += 1
                else:
                    perek_num = poss_perek_num
                    last_perek_tag = line
                pasuk_num = 0
                #assert perek_num not in text
                #text[perek_num] = []
                #DHs[perek_num] = []
                line_num = 0
            elif line.find("22") >= 0:
                pasuk_list.append(line)
                poss_pasuk_num = getGematria(line)
                poss_pasuk_num = ChetAndHey(poss_pasuk_num, pasuk_num)
                if poss_pasuk_num <= pasuk_num:
                    print u"In Perek {}: found {} after {}".format(last_perek_tag, line, last_tag)
                    print
                    pasuk_num += 1
                else:
                    pasuk_num = poss_pasuk_num
                    last_tag = line
                #text[perek_num].append([])
                #DHs[perek_num].append([])
            prev_line = orig_line

        #match(file, DHs, text)

