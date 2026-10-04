import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from extraction_core import find_spans


class MatchingV2Tests(unittest.TestCase):
    def test_surrounding_quotes_and_internal_abbreviations(self):
        for quote in ['״', '"', "'", '׳', '“', '”']:
            text = quote + 'גְּדוֹלָה' + quote
            self.assertEqual(find_spans(text, 'גדולה', 'vowel_insensitive'), [(1, len(text)-1)])
        for text in ['רש״י', 'רש"י', 'רש׳י']:
            self.assertEqual(find_spans(text, 'רש', 'exact'), [])
            self.assertEqual(find_spans(text, 'י', 'exact'), [])
            self.assertEqual(find_spans(text, text, 'exact'), [(0,len(text))])

    def test_maqaf_offsets_and_logged_mode(self):
        text = 'א בֶּן־גֶּ֖בֶר סוף'
        form = 'בֶּן גֶּבֶר'
        self.assertEqual(find_spans(text, form, 'cantillation_insensitive'), [])
        spans = find_spans(text, form, 'cantillation_insensitive_maqaf')
        self.assertEqual([text[a:b] for a,b in spans], ['בֶּן־גֶּ֖בֶר'])
        self.assertEqual(find_spans('בן גבר', 'בן־גבר', 'exact_maqaf'), [(0,6)])
        self.assertEqual(find_spans('בןגבר', 'בן גבר', 'exact_maqaf'), [])
