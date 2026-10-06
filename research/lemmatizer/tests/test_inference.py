import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from inference_adapters import common_window, dicta_tokens, exact_target, AlignmentError


class InferenceTests(unittest.TestCase):
    def test_window_preserves_repeated_target_and_attached_punctuation(self):
        text = 'a b word c word! d e'
        start = text.rindex('word')
        a, b = common_window(text, start, start + 4, lambda s: len(s.split()) <= 3)
        self.assertEqual(text[a:b], 'c word! d')
        self.assertEqual(text[a:b][start-a:start-a+4], 'word')

    def test_short_context_is_unchanged(self):
        self.assertEqual(common_window(' a b ', 3, 4, lambda s: True), (0, 5))

    def test_no_partial_word_to_satisfy_budget(self):
        with self.assertRaisesRegex(AlignmentError, 'target_exceeds_context_budget'):
            common_window('ablongword cd', 2, 6, lambda s: len(s) <= 4)

    def test_wordpieces_and_repeated_words_align_by_position(self):
        class Tokenizer:
            all_special_tokens = ['[CLS]', '[SEP]', '[UNK]', '[MASK]']
            unk_token, mask_token = '[UNK]', '[MASK]'
            def convert_ids_to_tokens(self, ids):
                return ['[CLS]', 'abc', '##d', 'abcd', '[SEP]']
        encoded = {'input_ids': list(range(5)), 'offset_mapping': [(0,0),(0,3),(3,4),(5,9),(0,0)]}
        result = dicta_tokens(encoded, Tokenizer(), [('abcd','one'),('abcd','two')])
        self.assertEqual(exact_target(result, 5, 9)['lemma'], 'two')
        with self.assertRaises(AlignmentError):
            exact_target(result, 5, 8)
        with self.assertRaisesRegex(AlignmentError, 'sequence_mismatch'):
            dicta_tokens(encoded, Tokenizer(), [('wrong','one'),('abcd','two')])


if __name__ == '__main__':
    unittest.main()
