import random
from functools import partial
from Levenshtein import distance
import re
import diff_match_patch as dmp


class LevenshteinCalc(object):

    def __init__(self):
        # self.wl = WeightedLevenshtein()
        self._cache = {}

    def __call__(self, word_list, segments, indices):
        scores = []
        for start, end, segment in zip([0] + indices, indices + [len(word_list)], segments):
            new_seg = ' '.join(word_list[start:end])

            # scores.append(self.wl.calculate(segment, new_seg, normalize=False))
            cur_score = self._cache.get((segment, new_seg), None)
            if cur_score is None:
                cur_score = distance(segment, new_seg)
                self._cache[(segment, new_seg)] = cur_score
            scores.append(cur_score)
        return sum(scores)

calculate_error_levenshtein = LevenshteinCalc()


def find_best_indices(word_list, segments, indices=None, num_iterations=1000, verbose=False):
    if indices is None:
        indices = sorted(random.sample(range(1, len(word_list)), len(segments) - 1))
    assert len(segments) - len(indices) == 1
    score_method = partial(calculate_error_levenshtein, word_list, segments)

    cur_score = score_method(indices)
    old_score = cur_score
    cur_iteration = 0
    last_index_ceiling = len(word_list) - 1
    learning_rate = int(cur_score / 10000 + 1)

    while cur_iteration < num_iterations:
        if cur_iteration % 5 == 0 and verbose:
            print("Epoch {}: score = {}".format(cur_iteration, cur_score))
        for i in range(len(indices)):
            new_learning_rate = int(cur_score / 5000 + 1)
            if new_learning_rate < learning_rate:
                learning_rate = new_learning_rate
            add, subtract = indices[:], indices[:]
            add[i] = indices[i] + learning_rate
            subtract[i] = indices[i] - learning_rate

            if i == 0:
                if subtract[i] <= 0:
                    subtract[i] = 1
            else:
                if subtract[i] <= subtract[i-1]:
                    subtract[i] = indices[i]

            if i == len(indices) - 1:
                if add[i] >= last_index_ceiling:
                    add[i] = last_index_ceiling - 1
            else:
                if add[i] >= add[i+1]:
                    add[i] = indices[i]

            indices = min([subtract, indices, add], key=score_method)

        new_score = score_method(indices)

        if new_score == cur_score:
            if learning_rate == 1:
                break
            else:
                learning_rate -= 1
        elif new_score > cur_score and verbose:
            print("Got worse at iteration {}".format(cur_iteration))
        old_score = cur_score
        cur_score = new_score

        cur_iteration += 1
    else:
        print("Did not converge. Old Score: {}; New Score: {}".format(old_score, cur_score))
    return indices, cur_score


def initialize_indices(word_list, segments):
    offset = 0
    max_index = len(word_list)

    while True:
        indices = []
        retry = False
        for i, segment in enumerate(segments[:-1]):
            if i == 0:
                cur_index = len(segment.split()) + offset
            else:
                cur_index = indices[-1] + len(segment.split()) + offset

            if cur_index >= max_index:
                retry = True
                offset -= 1
                break
            indices.append(cur_index)

        if not retry:
            break
    return indices


class CompareBreaks(object):

    def __init__(self, a, b, markers=['α', 'β']):
        # a, b: lists of strings (sections
        # markers: pair of chars that aren't contained in the strings
        assert all(x not in y for x in markers for y in a+b), 'markers should not be in text'
        assert len(markers) == 2 and markers[0] != markers[1], 'markers should be two different charts'
        self.a = a
        self.b = b
        self._marker_a = markers[0]
        self._marker_b = markers[1]

    def insert_break_marks(self):
        # returns the a list with markers of b division.
        # e.g. for a = ['foo bar', 'foo bar', 'foo bar'], b = ['foo bar foo', 'bar foo bar']
        # returns ['β1βfoo bar', 'foo β2βbar', 'foo bar']
        a_text = self._marker_a.join(self.a)
        b_text = self._marker_b.join(self.b)
        compared = dmp.diff_match_patch().diff_main(a_text, b_text)
        a = []
        for status, word in compared:
            if status < 1:
                a.append(word)
            for _ in range(word.count(self._marker_b)):
                a.append(self._marker_b)
        a = ''.join(a)
        a = re.sub(f'{self._marker_b} *{self._marker_a}', f'{self._marker_a}{self._marker_b}', a)
        z = zip([f'{self._marker_b}{i + 1}{self._marker_b}' for i in range(len(a.split(self._marker_b)))], a.split(self._marker_b))
        a = ''.join([x for y in z for x in y])
        a = a.split(self._marker_a)
        return a

    def create_mapping(self):
        # returns dict with a indexes (starting by 1) as keys and set of indexes in b as values
        # e.g. for a = ['foo bar', 'foo bar', 'foo bar'], b = ['foo bar foo', 'bar foo bar']
        # returns {1: {1}, 2: {1, 2}, 3:{2}}
        map = {}
        b = 1
        for i, section in enumerate(self.insert_break_marks(), 1):
            map[i] = set()
            for b in re.findall(f'{self._marker_b}(\d+){self._marker_b}', section):
                map[i].add(int(b))
            map[i].add(int(b))
        return map
