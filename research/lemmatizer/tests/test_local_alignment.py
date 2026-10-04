import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from pilot_local_alignment import parse_dicta_response, dicta_prompt


class DictaOutputTests(unittest.TestCase):
    def test_ignores_intermediate_reasoning_json(self):
        self.assertEqual(parse_dicta_response('{"wrong":1}</think>{"final":2}'), {'final': 2})

    def test_rejects_unfinished_reasoning(self):
        with self.assertRaises(ValueError):
            parse_dicta_response('considering {"token_ids":[]}')

    def test_fenced_final_json(self):
        self.assertEqual(parse_dicta_response('done</think>```json\n{"x":1}\n```'), {'x': 1})

    def test_prompt_ends_at_official_thinking_prefix(self):
        self.assertTrue(dicta_prompt({'headword': 'אב'}).endswith('<|im_start|>assistant\n<think>'))


if __name__ == '__main__':
    unittest.main()
