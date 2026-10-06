import sys
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from search_lemma_core import token_spans,chunks
from offline_search import query_body,check_destination,request
from score_search_runs import score_hits

class OfflineSearchTests(unittest.TestCase):
    def test_connection_failure_has_recovery_command(self):
        with patch('offline_search.urlopen',side_effect=URLError(ConnectionRefusedError(61,'Connection refused'))):
            with self.assertRaisesRegex(ConnectionError,'docker compose.*up -d'):
                request('http://127.0.0.1:19200')

    def test_http_not_found_preserved_for_index_creation(self):
        error=HTTPError('http://127.0.0.1:19200/lemma-poc-test',404,'Not Found',{},None)
        with patch('offline_search.urlopen',side_effect=error):
            with self.assertRaises(HTTPError) as caught:
                request(error.url)
        self.assertEqual(caught.exception.code,404)

    def test_contexts_preserve_all_tokens_and_repetitions(self):
        text='אמר אמר רמב"ם בבית-ספר'
        tokens=token_spans(text)
        self.assertEqual([t['form'] for t in tokens],['אמר','אמר','רמב"ם','בבית','ספר'])
        windows=list(chunks(text,tokens,lambda s:len(s)<=10))
        covered=[]
        for lo,hi,w in windows:
            covered.extend(range(lo,hi));a,b=w
            self.assertLessEqual(b-a,10)
            for t in tokens[lo:hi]:self.assertEqual(text[a:b][t['start']-a:t['end']-a],t['form'])
        self.assertEqual(covered,list(range(len(tokens))))

    def test_oversized_token_not_truncated(self):
        tokens=token_spans('abcdefghijkl אב')
        self.assertEqual(list(chunks('abcdefghijkl אב',tokens,lambda s:len(s)<5))[0],(0,1,None))

    def test_enhanced_keeps_baseline_phrase_and_ranking(self):
        base=query_body('בני ישראל')
        enhanced=query_body('בני ישראל','בן ישראל',.5)
        a=base['query']['function_score'];b=enhanced['query']['function_score']
        self.assertEqual(a['query'],b['query']['bool']['should'][0])
        self.assertEqual(a['field_value_factor'],b['field_value_factor'])
        self.assertEqual(b['query']['bool']['minimum_should_match'],1)

    def test_shared_slop_and_zero_weight(self):
        for slop in [0, 2, 10]:
            body=query_body('בני ישראל','בן ישראל',slop=slop)
            clauses=body['query']['function_score']['query']['bool']['should']
            self.assertEqual([next(iter(c['match_phrase'].values()))['slop'] for c in clauses],[slop,slop])
        self.assertEqual(query_body('בני ישראל','בן ישראל',weight=0),query_body('בני ישראל'))
        self.assertEqual(query_body('x')['query']['function_score']['query']['match_phrase']['naive_lemmatizer']['slop'],10)
        for value in [-1, 51, 1.5, True]:
            with self.assertRaises(ValueError): query_body('x',slop=value)

    def test_destination_guard(self):
        check_destination('http://127.0.0.1:19200','lemma-poc-test')
        for url,index in [('https://prod.example:19200','lemma-poc-test'),('http://localhost:19200','text'),('http://localhost:9200','lemma-poc-test')]:
            with self.assertRaises(ValueError):check_destination(url,index)

    def test_missing_judgment_is_not_irrelevant(self):
        hits=[{'doc_id':'a'},{'doc_id':'b'}]
        score=score_hits(hits,{'a':3},2)
        self.assertIsNone(score['ndcg_at_k']);self.assertIsNone(score['precision_at_k'])
        score=score_hits(hits,{'a':3,'b':0,'c':2},2)
        self.assertEqual(score['precision_at_k'],.5)
        self.assertEqual(score['recall_of_judged_positives'],.5)
        self.assertGreater(score['ndcg_at_k'],.5)

    def test_empty_results_with_known_relevance_score_zero(self):
        score=score_hits([],{'a':3},10)
        self.assertEqual(score['ndcg_at_k'],0)
        self.assertEqual(score['precision_at_k'],0)

    def test_no_judgments_means_no_quality_scores(self):
        self.assertIsNone(score_hits([],{},10)['precision_at_k'])
