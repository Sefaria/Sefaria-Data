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
    files = [file for file in os.listdir("./") if not file == "intro.txt" and file.endswith(".txt") and not file == "vayikra.txt"]
    for file in files:
        perek_num = 0
        line_num = 0
        pasuk_num = 0
        text = {}
        DHs = {}
        print "START....{}".format(file)
        for line in open(file):
            orig_line = line
            line = line.replace("\n", "").replace("\r", "").decode('utf-8')
            if len(line) == 0 or line.startswith("$") or "@02" in line or "@01" in line:
                continue

            if line.find("00") >= 0:
                poss_perek_num = getGematria(line)
                poss_perek_num = ChetAndHey(poss_perek_num, perek_num)
                if poss_perek_num <= perek_num:
                    print "PEREK ISSUE: {} {} {}".format(file, poss_perek_num, perek_num)
                    print line
                    print " ".join(prev_line.split(" ")[0:10])
                perek_num = poss_perek_num
                assert perek_num not in text
                text[perek_num] = []
                DHs[perek_num] = []
                line_num = 0
            elif line.find("22") >= 0:
                poss_pasuk_num = getGematria(line)
                poss_pasuk_num = ChetAndHey(poss_pasuk_num, pasuk_num)
                if poss_pasuk_num <= pasuk_num:
                    print "PASUK ISSUE: {}, found {} after {}".format(file, poss_pasuk_num, pasuk_num)
                    pasuk_num += 1
                text[perek_num].append([])
                DHs[perek_num].append([])
            elif line.find("@11") >= 0:# or (line.find(".") > 0 and line.split(".", 1)[0].find(u"כו'") >= 0):
                line = removeAllTags(line)
                DH, comment = get_DH_comment(line)
                line = u"<b>{}></b>{}".format(DH, comment)
                current = len(text[perek_num]) - 1
                text[perek_num][current].append(line)
                DHs[perek_num][current].append(DH)
            else:
                line = removeAllTags(line)
                #DHs[perek_num][current].append("")
                #text[perek_num][current].append(line)

            prev_line = orig_line

        #match(file, DHs, text)

