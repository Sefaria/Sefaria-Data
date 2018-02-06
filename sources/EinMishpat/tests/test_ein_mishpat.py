# encoding=utf-8

import pytest
from sources.EinMishpat import ein_parser
import pickle
import codecs
import unicodecsv as csv

def test_dict_dict():
    new_file = "avodah_zarah_little_letters.csv"
    ein_parser.run2("az_collapsed", "avodah_zarah")
    comp_file = "avodah_zarah_done_jan18.csv"
    new = []
    comp = []
    new_has_segments = False
    comp_has_segments = False
    with open(new_file, 'r') as csvfile:
        file_reader = csv.DictReader(csvfile)
        if "Line" in file_reader.fieldnames:
            new_has_segments = True
        for i, row in enumerate(file_reader):
            if not row:
                continue
            else:
                new_dict = {"EM": row["original"], "Rambam": row["Rambam"], "Semag":row["Semag"],"TurShA":row["Tur Shulchan Arukh"]}
                if new_has_segments:
                    new_dict['segment'] = '{}.{}'.format(row['Daf'], row['Line'])
                new.append(new_dict)
    with open(comp_file, 'r') as csvfile:
        file_reader = csv.DictReader(csvfile)
        if "Line" in file_reader.fieldnames:
            comp_has_segments = True
        for i, row in enumerate(file_reader):
            if not row:
                continue
            else:
                new_dict = {"EM": row["original"],"Rambam": row["Rambam"],
                            "Semag": row["Semag"], "TurShA": row["Tur Shulchan Arukh"]}
                if comp_has_segments:
                    new_dict['segment'] = '{}.{}'.format(row['Daf'], row['Line'])
                comp.append(new_dict)
    missmatch_cnt = 0
    with open(u'az_test_diff.csv', 'w') as csv_file:
        writer = csv.DictWriter(csv_file, [u'line', u'old', u'new', u'EM'])
        writer.writeheader()
        if new_has_segments:
            lineseg = "a['segment']"
        elif comp_has_segments:
            lineseg = "b['segment']"
        else:
            lineseg = "i"
        for i, (a,b) in enumerate(zip(new, comp)):
            # assert a == b
            for k in a.keys():
                if a[k] != b[k]:
                    writer.writerow({u'line': eval(lineseg), u'new':a[k], u'old': b[k], u'EM': a['EM']})
                    missmatch_cnt += 1
    assert missmatch_cnt == 6