from collections import defaultdict


class LevenshteinError(Exception):
    pass


class WeightedLevenshtein:
    """
    Use this class to calculate the Weighted Levenshtein between strings. The default letter frequencies defined here
    are based off of the Talmud. The default min_cost value is recommended, and should only be changed by engineers with
    a proficient understanding of the weighted Levenshtein algorithm.
    """

    def __init__(self, letter_freqs=None, min_cost=None, swap_costs=None):
        """
        :param swap_costs: dict of form `{(c1, c2): cost}` where `c1` and `c2` are two characters and `cost` is the cost for swapping them. overides costs listed in `letter_freqs`
        """
        if letter_freqs is None:
            self.letter_freqs = {
                'י': 0.0,
                'ו': 0.2145,
                'א': 0.2176,
                'מ': 0.3555,
                'ה': 0.4586,
                'ל': 0.4704,
                'ר': 0.4930,
                'נ': 0.5592,
                'ב': 0.5678,
                'ש': 0.7007,
                'ת': 0.7013,
                'ד': 0.7690,
                'כ': 0.8038,
                'ע': 0.8362,
                'ח': 0.8779,
                'ק': 0.9124,
                'פ': 0.9322,
                'ס': 0.9805,
                'ט': 0.9924,
                'ז': 0.9948,
                'ג': 0.9988,
                'צ': 1.0
            }
        else:
            self.letter_freqs = letter_freqs

        self.sofit_map = {
            'ך': 'כ',
            'ם': 'מ',
            'ן': 'נ',
            'ף': 'פ',
            'ץ': 'צ',
        }

        if min_cost is None:
            self.min_cost = 1.0
        else:
            self.min_cost = min_cost

        #self._cost is a dictionary with keys either single letters, or tuples of two letters.
        # note that for calculate, we remove the sofit letters.  We could probably remove them from here as well, save for cost_str().
        all_letters = list(self.letter_freqs.keys()) + list(self.sofit_map.keys())
        self._cost = defaultdict(lambda: self.min_cost)
        self._cost.update({c: self._build_cost(c) for c in all_letters})  # single letters
        self._cost.update({(c1, c2): self._build_cost(c1, c2) for c1 in all_letters for c2 in all_letters}) # tuples
        if swap_costs is not None:
            self._cost.update(swap_costs)

        self._most_expensive = max(self.letter_freqs.values())

        # dict((ord(char), sofit_map[char]) for char in self.sofit_map.keys())
        self._sofit_transx_table = {
            1498: '\u05db',
            1501: '\u05de',
            1503: '\u05e0',
            1507: '\u05e4',
            1509: '\u05e6'
        }
    #Cost of calling this isn't worth the syntax benefit
    """
    def sofit_swap(self, c):
        return self.sofit_map.get(c, c)
    """


    #This is a pure function with limited inputs.  Building as a lookup saves lots of time.
    def _build_cost(self, c1, c2=None):
        c1 = self.sofit_map.get(c1, c1)
        c2 = self.sofit_map.get(c2, c2)
        w1 = self.letter_freqs[c1] if c1 in self.letter_freqs else 0.0
        if c2:
            w2 = self.letter_freqs[c2] if c2 in self.letter_freqs else 0.0
            return w1 + self.min_cost if w1 > w2 else w2 + self.min_cost
        else:
            return w1 + self.min_cost

    # used?
    def cost_str(self, string):
        cost = 0
        for c in string:
            cost += self._cost[c]
        return cost

    _calculate_cache = {}
    def calculate(self, s1, s2, normalize=True):
        """
        This method calculates the Weighted Levenshtein between two strings. It should be noted however that the
        Levenshtein score between two strings is dependant on the lengths of the two strings. Therefore, it is possible
        that two short strings with a low Levenshtein score may score more poorly than two long strings with a higher
        Levenshtien score.

        The code for this method is redacted from https://en.wikipedia.org/wiki/Levenshtein_distance. As we are only
        calculating the distance, without building an alignment, we only save two rows of the Levenshtein matrix at
        any given time.
        :param s1: First string. Determines the number of rows in the Levenshtein matrix.
        :param s2: Second string. Determines the number of columns in the Levenshtein matrix.
        :param normalize: True to get a score between 0-100, False to get the weighted Levenshtein score.
        :return: If normalize is True, will return an integer between 0-100, with 100 being a perfect match and 0 being
        two ompletely different strings with the most expensive swap at every location. Otherwise, the exact weighted
        Levenshtein score will be returned.
        """
        original_s1, original_s2 = s1, s2
        if not self._calculate_cache.get((original_s1, original_s2, normalize), None):
            s1_len = len(s1)
            s2_len = len(s2)


            if s1_len == 0 and s2_len == 0 and normalize:
                raise LevenshteinError("both strings can't be empty with normalize=True. leads to divide by zero")

            if s1 == s2:
                score = 0

            else:
                """
                v0 corresponds to row i-1 in the Levenshtein matrix, where i is the index of the current letter in s1.
                It is initialized to the cost of deleting every letter in s2 up to letter j for each letter j in s2
                v1 corresponds to row i of the Levenshtein matrix.
                """
                s1 = s1.translate(self._sofit_transx_table)
                s2 = s2.translate(self._sofit_transx_table)
                s1_cost = [self._cost[c] for c in s1]
                s2_cost = [self._cost[c] for c in s2]
                total_delete_cost = 0
                v0 = [0]
                for j in range(s2_len):
                    v0 += [s2_cost[j] + v0[j]]
                v1 = [0] * (s2_len + 1)

                for i in range(s1_len):
                    cost_del = s1_cost[i]
                    v1[0] = total_delete_cost = cost_del + total_delete_cost  # Set to cost of deleting char from s1
                    for j in range(s2_len):
                        cost_ins = s2_cost[j]
                        cost_sub = 0.0 if s1[i] == s2[j] else self._cost.get(
                            (s1[i], s2[j]), cost_ins if cost_ins > cost_del else cost_del)
                        v1[j + 1] = min(v1[j] + cost_ins, v0[j + 1] + cost_del, v0[j] + cost_sub)

                    v0, v1 = v1, v0
                score = v0[-1]

            if normalize:
                length = max(s1_len, s2_len)
                max_score = length * (self._most_expensive + self.min_cost)
                self._calculate_cache[(original_s1, original_s2, normalize)] = int(100.0 * (1 - (score / max_score)))

            else:
                self._calculate_cache[(original_s1, original_s2, normalize)] = score

        return self._calculate_cache[(original_s1, original_s2, normalize)]

    def calculate_best(self, s, words, normalize=True):
        """
        :param s: str
        :param words: list of str
        :return: the lowest distance for s in words and return the index and distance
        """
        best_dist = 0 if normalize else 10000 # large number
        best_ind = -1
        for i, w in enumerate(words):
            dist = self.calculate(s, w, normalize)
            if (dist < best_dist and not normalize) or (dist > best_dist and normalize):
                best_dist = dist
                best_ind = i
        return best_ind, best_dist
