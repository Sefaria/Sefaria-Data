import pytest
from linking_utilities.weighted_levenshtein import WeightedLevenshtein, LevenshteinError


class TestWeightedLevenshtein:

    @classmethod
    def setup_class(cls):
        cls.instance = WeightedLevenshtein()

    def test_exact_match(self):
        assert self.instance.calculate('שלום עולם', 'שלום עולם') == 100

    def test_biggest_difference(self):
        assert self.instance.calculate('שלום', 'צצצצצ') == 0

    def test_sofit(self):
        assert self.instance.calculate('שלומ', 'שלום') == 100

    def test_nothing(self):
        with pytest.raises(LevenshteinError):
            self.instance.calculate('', '')
