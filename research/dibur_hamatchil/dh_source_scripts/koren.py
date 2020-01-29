# -*- coding: utf-8 -*-

import csv
import os
import sys
import re

from data_utilities import dibur_hamatchil_matcher
from sefaria.model import *


# TODO this path is deliberately outside of the repo so that people don't know we have PROJECT K (wink wink)
num_split = 0
num_missed = 0
total_koren = 0
total_sef = 0

mesechtot = ["Berakhot"]

for mes in mesechtot:
    super_base_ref = Ref(mes)
    with open("/Users/nss/Documents/Sefaria-Docs/Project K/{}.csv".format(mes), "r") as f:
        koren_csv = csv.DictReader(f, delimiter="%")
        found_start_row = False
        first_row = None

        for base_ref in super_base_ref.all_subrefs()[27:28]:
            if base_ref.is_empty(): continue

            print("DAF {} -----START-----".format(base_ref))
            base_tc = TextChunk(base_ref, "he")

            # comm_ref = Ref("Rashi on Berakhot 2a")
            # comm_tc = TextChunk(comm_ref,'he')
            comment_list = []

            if first_row:
                comment_list.append(first_row['hebrew'].decode('utf8'))
                first_row = None
            for row in koren_csv:
                if Ref("{} {}".format(mes,row['daf'])) == base_ref:
                    comment_list.append(row['hebrew'].decode('utf8'))
                    found_start_row = True
                elif found_start_row:
                    first_row = row
                    break


            def base_tokenizer(str):
                str = re.sub(r"\([^\(\)]+\)", "", str)
                word_list = re.split(r"\s+", str)
                word_list = [w for w in word_list if w]  # remove empty strings
                return word_list


            def dh_extraction_method(str):
                m = re.match(r"([^\.]+\.\s)?([^–]+)\s–", str)
                if m:
                    return m.group(2)
                else:
                    return ""

            yo = dibur_hamatchil_matcher.match_ref(base_tc, comment_list, base_tokenizer=base_tokenizer)
            for i,yoyo in enumerate(yo):
                if yoyo is None:
                    num_missed += 1

                if i > 0 and not yo[i-1] is None and not yoyo is None:
                    prange = yo[i-1].range_list()
                    nrange = yoyo.range_list()


                    if prange[-1] == nrange[0]:
                        print("{} is split".format(nrange[0]))
                        num_split += 1

                total_sef += len(yoyo.range_list()) if yoyo else 0
                total_koren += 1

            print("MATCHES - {}".format(yo))
            print("DAF {} -----END-----".format(base_ref))
            print("NUM SPLIT ({} / {}) - ({}%)".format(num_split, total_sef, round(100.0 * num_split / total_sef, 3)))
            print("NUM MISSED ({} / {}) - ({}%)".format(num_missed, total_sef, round(100.0 * num_missed / total_sef, 3)))

#print "NUM SPLIT ({} / {}) - ({}%)".format(num_split, total, round(100.0*num_split/total, 3))
#print "NUM MISSED ({} / {}) - ({}%)".format(num_missed, total, round(100.0*num_missed/total, 3))
print("AVG Num Sef segs per Koren seg: {}".format(round(1.0*total_sef/total_koren,3)))