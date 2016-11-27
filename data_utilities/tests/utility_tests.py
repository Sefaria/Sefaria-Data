# encoding=utf-8

import pytest
from data_utilities import util


class Test_WeightedLevenshtein:

    @classmethod
    def setup_class(cls):
        cls.instance = util.WeightedLevenshtein()

    def test_exact_match(self):
        assert self.instance.calculate(u'שלום עולם', u'שלום עולם') == 100

    def test_biggest_difference(self):
        assert self.instance.calculate(u'שלום', u'צצצצצ') == 0

    def test_sofit(self):
        assert self.instance.calculate(u'שלומ', u'שלום') == 100

    def test_nothing(self):
        with pytest.raises(util.LevenshteinError):
            self.instance.calculate(u'', u'')
