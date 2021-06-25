# encoding=utf-8

import yutil
output_file = 'code_output/compare_counts.csv'

mesechtot = yutil.get_machon_mamre_data()
# get shape
for m, paras in mesechtot.items():
    highest_perek = 0
    for p in paras:
        if p["perek_num"] > highest_perek:
            highest_perek = p["perek_num"]

    shape = [0] * highest_perek
    for p in paras:
        if p["halacha_num"] > shape[p["perek_num"] - 1]:
            shape[p["perek_num"] - 1] = p["halacha_num"]

    print("{}:{},".format(m, shape))