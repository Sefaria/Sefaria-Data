import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from benchmark_core import normalize, map_target, align_token, stanza_lemma, label_key, require_token_budget


class BenchmarkTests(unittest.TestCase):
    def test_marks_preserve_punctuation_and_target_identity(self):
        raw = 'שָׁם־שֵׁם׃'
        start = raw.index('שֵ')
        clean,a,b,_ = map_target(raw,start,len(raw)-1,raw[start:-1])
        self.assertEqual(clean,'שם-שם:')
        self.assertEqual((a,b),(3,5))
        self.assertEqual(clean[a:b],'שם')

    def test_presentation_forms_bidi_and_non_hebrew_accents(self):
        self.assertEqual(normalize('\u200f\ufb2a \ufb4f café')[0],'ש אל café')
        self.assertEqual(normalize('רש״י')[0],'רש"י')
        self.assertEqual(normalize('a\u0301')[0],'a\u0301')

    def test_raw_and_source_validation(self):
        self.assertEqual(normalize('שָׁם','raw-v1'),('שָׁם',[0,1,2,3,4]))
        with self.assertRaises(ValueError):map_target('שלום',0,2,'שלום')

    def test_repeated_spelling_uses_offsets(self):
        tokens=[{'start':0,'end':2,'lemma':'a'},{'start':3,'end':5,'lemma':'b'}]
        self.assertEqual(align_token(tokens,3,5)[0]['lemma'],'b')
        self.assertEqual(align_token(tokens,3,4)[1],'unaligned_target')

    def test_stanza_segmentation_and_abstentions(self):
        self.assertEqual(stanza_lemma([{'lemma':'ב','upos':'ADP'},{'lemma':'ספר','upos':'NOUN'},
            {'lemma':'הוא','upos':'PRON'}]),('ספר','single_lexical_component'))
        self.assertIsNone(stanza_lemma([{'lemma':'א','upos':'NOUN'},{'lemma':'ב','upos':'NOUN'}])[0])
        self.assertIsNone(label_key('[BLANK]'))
        self.assertEqual(label_key('קַבֵּל'),'קבל')

    def test_no_silent_truncation(self):
        tok=lambda text,**kwargs:{'input_ids':list(range(161))}
        with self.assertRaises(ValueError):require_token_budget(tok,'text',160)
        self.assertEqual(require_token_budget(tok,'text',512),161)
