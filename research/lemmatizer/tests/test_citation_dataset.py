import copy
from pathlib import Path
import sys, unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from build_citation_dataset import extract
from extraction_core import sha


def case(text='נִשְׁמְתָךְ'):
    return {'audit_id':'test','dictionary':'BDB Aramaic Dictionary','dictionary_ref':'BDB Aramaic, נשמה 1',
        'target_ref':'Daniel 5:23','link':{'_id':'l','refs':['BDB Aramaic, נשמה 1','Daniel 5:23']},
        'entry':{'headword':'נשמה','content':{'senses':[{'definition':'breath; sf. <span dir="rtl">נִשְׁמְתָךְ</span> <a data-ref="Daniel 5:23">Dn 5:23</a>'}]}},
        'passages':[{'passage_id':'p','ref':'Daniel 5:23','text':text,'text_sha256':sha(text),'version_id':'v','version_title':'Primary Hebrew','is_fallback':False}]}


class CitationTests(unittest.TestCase):
    def test_conjunction_preserves_pointing_and_host_span(self):
        c=case('וְנִשְׁמְתָךְ');e,_=extract(c)
        self.assertEqual(e['surface'],'וְנִשְׁמְתָךְ')
        self.assertEqual(e['match_method'],'conjunction_waw_pointing_preserved')
        self.assertIsNone(extract(case('וְנָשְׁמְתָךְ'))[0])
        self.assertIsNone(extract(case('בְּנִשְׁמְתָךְ'))[0])

    def test_additional_explicit_grammar(self):
        c=case();c['entry']['content']['senses'][0]['definition']=c['entry']['content']['senses'][0]['definition'].replace('sf.','Pf. 3 mpl.')
        self.assertIsNotNone(extract(c)[0])
        c['entry']['content']['senses'][0]['definition']+=' (but v. infr.)'
        self.assertIsNone(extract(c)[0])

    def test_quoted_target_not_other_words(self):
        c=case('עד דְּמָשֵׁיךְ');c['dictionary']='Jastrow Dictionary'
        c['entry']['content']={'definition':'<a data-ref="Daniel 5:23">ref</a> <span dir="rtl">עד דמָשֵׁיךְ</span> until he takes possession'}
        e,_=extract(c)
        self.assertEqual(e['surface'],'דְּמָשֵׁיךְ')
        c['passages'][0]['text']='עד דְּמָשַׁיךְ'
        self.assertIsNone(extract(c)[0])
        c['entry']['content']['definition']=c['entry']['content']['definition'].replace('עד דמָשֵׁיךְ','עַד דמָשֵׁיךְ')
        self.assertEqual(extract(c)[1],'no_supported_evidence_rule')

    def test_explicit_form_original_offsets(self):
        c=case('א נִשְׁמְתָ֥ךְ ב');ex,reason=extract(c)
        self.assertIsNone(reason)
        self.assertEqual(ex['text'][ex['start_char']:ex['end_char']],'נִשְׁמְתָ֥ךְ')
        self.assertEqual(ex['evidence']['rule'],'explicit_inflection_before_citation')

    def test_repeated_positions_are_skipped(self):
        self.assertEqual(extract(case('נִשְׁמְתָךְ נִשְׁמְתָךְ'))[1],'multiple_candidate_positions')

    def test_no_vowel_stripping_fallback(self):
        self.assertEqual(extract(case('נשמתך'))[1],'no_pointing_preserving_match')

    def test_wrong_citation_and_intervening_prose(self):
        for replacement in ['Daniel 5:24','Daniel 5:230']:
            c=case();c['target_ref']=replacement
            self.assertEqual(extract(c)[1],'no_supported_evidence_rule')
        c=case();c['entry']['content']['senses'][0]['definition']=c['entry']['content']['senses'][0]['definition'].replace('</span>','</span> compare another word')
        self.assertEqual(extract(c)[1],'no_supported_evidence_rule')

    def test_wordforms_cannot_authorize(self):
        c=case();c['entry']['content']={};c['candidates']=[{'form':'נִשְׁמְתָךְ'}]
        self.assertEqual(extract(c)[1],'no_supported_evidence_rule')

    def test_missing_text_and_error(self):
        c=case();c['passages']=[]
        self.assertEqual(extract(c)[1],'missing_primary_hebrew_text')
        c=case();c['error']='partial retrieval'
        self.assertEqual(extract(c)[1],'source_retrieval_error')

    def test_klein_requires_noun_and_attestation(self):
        c=case('קֶצַח');c['dictionary']='Klein Dictionary';c['entry']={'headword':'קֶצַח','content':{'morphology':'m.n.','senses':[{'definition':'black cumin (occurring <a data-ref="Daniel 5:23">ref</a>).'}]}}
        self.assertIsNotNone(extract(c)[0])
        c['entry']['content']['morphology']='v.'
        self.assertEqual(extract(c)[1],'no_supported_evidence_rule')
