# encoding=utf-8

from sources.Yerushalmi.text_mapping import DividedSegments


class TestDividedSegments:

    @staticmethod
    def get_divider() -> DividedSegments:
        original_segments = [
            'a b c d e',
            'f g h i j',
            'k l m n o'
        ]
        divider = DividedSegments(3)
        divider.segments = original_segments
        return divider

    def test_divide(self):
        divider = self.get_divider()
        assert divider.segments == (
            'a b c',
            'd e',
            'f g h',
            'i j',
            'k l m',
            'n o'
        )
        assert divider.get_division_indices() == (
            (0, 2), (2, 4), (4, 6)
        )

    def test_map_rebuild(self):
        divider = self.get_divider()
        words = 'a b c d e f g h i j k l m n o'.split()
        divider.words = words
        mapping = [
            (0, 2), (3, 4), (5, 7), (8, 9), (10, 12), (13, 14)
        ]
        fixed_mapping = divider.realign_mapping(mapping)
        assert fixed_mapping['matches'] == [
            (0, 4), (5, 9), (10, 14)
        ]
        foo = [
            ('a b c d e', 'a b c d e'),
            ('f g h i j', 'f g h i j'),
            ('k l m n o', 'k l m n o')
        ]
        assert fixed_mapping['match_text'] == [
            ('a b c d e', 'a b c d e'),
            ('f g h i j', 'f g h i j'),
            ('k l m n o', 'k l m n o')
        ]

    def test_map_with_gap(self):
        divider = self.get_divider()
        words = 'a b c d e f g h i j k l m n o'.split()
        divider.words = words
        mapping = [
            (0, 2), (3, 4), (-1, -1), (8, 9), (10, 12), (13, 14)
        ]
        fixed_mapping = divider.realign_mapping(mapping)
        assert fixed_mapping['matches'] == [
            (0, 4), (5, 9), (10, 14)
        ]
        assert fixed_mapping['match_text'] == [
            ('a b c d e', 'a b c d e'),
            ('f g h i j', 'f g h i j'),
            ('k l m n o', 'k l m n o')
        ]
    
    def test_double_gap(self):
        divider = self.get_divider()
        words = 'a b c d e f g h i j k l m n o'.split()
        divider.words = words
        mapping = [
            (0, 2), (3, 4), (-1, -1), (-1, -1), (10, 12), (13, 14)
        ]
        fixed_mapping = divider.realign_mapping(mapping)
        assert fixed_mapping['matches'] == [
            (0, 4), (5, 9), (10, 14)
        ]
        assert fixed_mapping['match_text'] == [
            ('a b c d e', 'a b c d e'),
            ('f g h i j', 'f g h i j'),
            ('k l m n o', 'k l m n o')
        ]

    def test_early_and_late_gap(self):
        divider = self.get_divider()
        words = 'a b c d e f g h i j k l m n o'.split()
        divider.words = words
        mapping = [
            (-1, -1), (3, 4), (5, 7), (8, 9), (10, 12), (-1, -1)
        ]
        fixed_mapping = divider.realign_mapping(mapping)
        assert fixed_mapping['matches'] == [
            (0, 4), (5, 9), (10, 14)
        ]
        assert fixed_mapping['match_text'] == [
            ('a b c d e', 'a b c d e'),
            ('f g h i j', 'f g h i j'),
            ('k l m n o', 'k l m n o')
        ]

    def test_unfixable_gap(self):
        divider = self.get_divider()
        words = 'a b c d e f g h i j k l m n o'.split()
        divider.words = words
        mapping = [
            (0, 2), (-1, -1), (-1, -1), (8, 9), (10, 12), (13, 14)
        ]
        fixed_mapping = divider.realign_mapping(mapping)
        assert fixed_mapping['matches'] == [
            (0, -1), (-1, 9), (10, 14)
        ]
        assert fixed_mapping['match_text'] == [
            ('a b c d e', ''),
            ('f g h i j', ''),
            ('k l m n o', 'k l m n o')
        ]
