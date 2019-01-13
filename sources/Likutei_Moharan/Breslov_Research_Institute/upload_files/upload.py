# encoding = utf-8

import re
import unicodecsv
from data_utilities.util import convert_dict_to_array


class ClashError(Exception):
    pass


class Comment(object):
    pass


class Seif(object):
    child = Comment

    def __init__(self, seif_lines):
        self.lines = seif_lines

    @classmethod
    def parse(cls, lines):
        seif_mapping = {}

        for line_num, line in enumerate(lines):
            seif_mark = re.search(u'^<b>(\d+)\.?</b>', line['English'])
            if seif_mark:
                seif_value = int(seif_mark.group(1))
                if seif_value in seif_mapping:
                    raise ClashError

                seif_mapping[seif_value] = line_num
        if 1 not in seif_mapping:
            seif_mapping[1] = 0

        seifim = sorted(seif_mapping.keys())
        list_mapping = {}
        for seif, next_seif in zip(seifim[:-1], seifim[1:]):
            list_mapping[seif] = lines[seif_mapping[seif]:seif_mapping[next_seif]]
        last_seif = seifim[-1]
        list_mapping[last_seif] = lines[seif_mapping[last_seif]:]
        return [cls(l) for l in convert_dict_to_array(list_mapping, list)[1:]]


class Torah(object):
    child = Seif

    def __init__(self, torah_lines):
        self.children = self.child.parse(torah_lines)

    @classmethod
    def parse(cls, lines):
        last_chap = 1
        indices = [0]
        for line_num, line in enumerate(lines):
            cur_chap = int(line['Chapter'])
            if cur_chap > last_chap:
                indices.append(line_num)
                last_chap = cur_chap
        indices.append(len(lines))

        ranges = zip(indices[:-1], indices[1:])
        return [cls(lines[i:j]) for i, j in ranges]


class Likutei(object):
    child_cls = Torah

    def __init__(self, doc_lines):
        self.children = self.child_cls.parse(doc_lines)


with open('Likutei_Moharan_1-50.csv') as fp:
    my_lines = list(unicodecsv.DictReader(fp))

lik = Likutei(my_lines)
print lik.children[-1].children[-1].lines[-1]
