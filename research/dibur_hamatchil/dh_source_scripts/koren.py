# -*- coding: utf-8 -*-

from research.dibur_hamatchil import sefaria_program
import re
from sefaria.model import *
import csv

super_base_ref = Ref("Berakhot")
# TODO this path is deliberately outside of the repo so that people don't know we have PROJECT K (wink wink)
with open("/Users/nss/Documents/Sefaria-Docs/Parsed_Brachot.csv", "r") as f:
    koren_csv = csv.DictReader(f, delimiter="%")
    first_row = None
    for base_ref in super_base_ref.all_subrefs():
        if base_ref.is_empty(): continue

        print "DAF {} -----START-----".format(base_ref)
        base_tc = TextChunk(base_ref, "he")

        # comm_ref = Ref("Rashi on Berakhot 2a")
        # comm_tc = TextChunk(comm_ref,'he')
        comment_list = []

        if first_row:
            comment_list.append(first_row['hebrew text'].decode('utf8'))
            first_row = None
        for row in koren_csv:
            if Ref("Berakhot {}".format(row['daf'])) == base_ref:
                comment_list.append(row['hebrew text'].decode('utf8'))
            else:
                first_row = row
                break


        def base_tokenizer(str):
            str = re.sub(ur"\([^\(\)]+\)", u"", str)
            word_list = re.split(ur"\s+", str)
            word_list = [w for w in word_list if w]  # remove empty strings
            return word_list


        def dh_extraction_method(str):
            m = re.match(ur"([^\.]+\.\s)?([^–]+)\s–", str)
            if m:
                return m.group(2)
            else:
                return ""

        yo = sefaria_program.match_ref(base_tc, comment_list, base_tokenizer=base_tokenizer)
        print "MATCHES - {}".format(yo)
        print "DAF {} -----END-----".format(base_ref)