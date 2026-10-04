import json
from pathlib import Path
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from finalize_review import finalize
from prepare_review import cited_refs
from sample_entries import rank


class ReviewTests(unittest.TestCase):
    def test_seed_and_citation_extraction(self):
        self.assertEqual(rank(7,'a'),rank(7,'a'))
        self.assertNotEqual(rank(7,'a'),rank(8,'a'))
        self.assertEqual(cited_refs({'senses':[{'definition':'<a data-ref="Genesis 1:1">Gen</a>'}]}), {'Genesis 1:1'})

    def fixture(self,path,invalid=False):
        cases=[]; annotations=[]; features=[]
        for i,label in enumerate(['correct','uncertain','not_assessable']):
            cid=f'c{i}';rid=f'R{i}'
            f={'has_proposed_span':i<2,'matches_in_source_ref':1 if i<2 else 0,
               'same_dictionary_entry_candidates':1,'match_method':'exact' if i<2 else 'none'}
            cases.append({'case_id':cid,'review_id':rid,'entry_id':'e'+str(i//2),
                'word_form_id':'w'+str(i),'passages':[{'passage_id':'p'+str(i//2)}],
                'occurrence':{'surface':'x'} if i<2 else None,'features':f,
                'dictionary':'D','headword':'h','source_ref':'Ref'})
            annotations.append({'case_id':cid,'review_id':rid,'alignment_label':'correct' if i<2 else 'not_proposed',
                'association_label':'incorrect' if invalid and i==2 else label,'reason':'Contextual evidence.'})
            features.append({'case_id':cid,'review_id':rid,**f})
        for name,rows in [('cases',cases),('annotations',annotations),('features',features)]:
            (path/(name+'.jsonl')).write_text(''.join(json.dumps(r)+'\n' for r in rows))
        (path/'manifest.json').write_text('{}')

    def test_no_label_leakage_or_absent_negatives(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);self.fixture(p)
            with redirect_stdout(StringIO()):finalize(p)
            examples=[json.loads(l) for l in (p/'model_examples.jsonl').read_text().splitlines()]
            self.assertEqual(len(examples),1)
            self.assertNotIn('reason',examples[0]['features'])
            self.assertEqual(examples[0]['association_target'],1)
            ledger=[json.loads(l) for l in (p/'review_ledger.jsonl').read_text().splitlines()]
            self.assertEqual(ledger[0]['overlap_group'],ledger[1]['overlap_group'])
            self.assertNotEqual(ledger[0]['overlap_group'],ledger[2]['overlap_group'])

    def test_absent_proposal_cannot_be_negative(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);self.fixture(p,invalid=True)
            with self.assertRaises(ValueError):finalize(p)


if __name__=='__main__':unittest.main()
