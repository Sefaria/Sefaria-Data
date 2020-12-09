# -*- coding: utf-8 -*-
import django
django.setup()
from data_utilities import dibur_hamatchil_matcher as dhm
from sefaria.model import *
from sefaria.utils import hebrew
import regex as re
import json
import codecs


def sp(string):
    return re.split('\s+', string)

def setup_module(module):
    global daf

    dhm.InitializeHashTables()

    daf_words = sp('משעה שהכהנים נכנסים לאכול בתרומתן עד סוף האשמורה הראשונה דברי רבי אליעזר. וחכמים אומרים עד חצות ר"ג אומר עד שיעלה עמוד השחר. מעשה ובאו בניו מבית המשתה אמרו לו')
    comments = ['משעה שהכהנים נכנסים לאכול', #exact
                'עד האשמורה הראשונה דברי רבי אליעזר.', # 1 skip
                'עד הראשונה דברי רבי אליעזר.', # 2 skip
                'עד סוף האשמורה הראשונה דברי.', # 2 skip at end of word
                'רבן גמליאל אומר עד שיעלה', # abbrev in base_text
                'משעה שהכהנים עלין נכנסים לאכול', #extra word in Rashi
                'בניו מבית המשתה אמרו לו וולה!', #extra (ridiculous) word in rashi at end of daf
                'עד סוף האשמורה הראשונה דברי רבי בלהבלה.', #last word is a mismatch
                'וחכמים אומרים עד חצות', #small rashi
                'וחכמים אומרים סבבה עד חצות ר"ג שיעלה עמוד השחר.', #too many skips
                'וחכמים אומרים סבבה עד חצות ר"ג אומר שיעלה עמוד השחר'] #max skips
    daf = dhm.GemaraDaf(daf_words,comments)



def mb_base_tokenizer(str):
    punc_pat = re.compile(r"(\.|,|:|;)$")

    str = re.sub(r"\([^\(\)]+\)", "", str)
    str = re.sub(r"''", r'"', str)  # looks like double apostrophe in shulchan arukh is meant to be a quote
    str = re.sub(r"</?[a-z]+>", "", str)  # get rid of html tags
    str = hebrew.strip_cantillation(str, strip_vowels=True)
    word_list = re.split(r"\s+", str)
    word_list = [re.sub(punc_pat, "", w).strip() for w in word_list if len(
        re.sub(punc_pat, "", w).strip()) > 0]  # remove empty strings and punctuation at the end of a word
    return word_list


def mb_dh_extraction_method(str):
    # searches for '(blah) other blah -' or '{blah} other blah -'
    m = re.search(r"((\([^\(]+\))|(\{[^\{]+\}))([^–]+)–", str)
    if m is None:
        m = re.search(r"((\([^\(]+\))|(\{[^\{]+\}))([^-]+)-", str)
    if m:
        dh = m.group(4).strip()
        return dh.replace("וכו'", "")
    else:
        return ""

class TestDHMatcher:

    def test_mb(self):
        simanim = [1, 51, 202]
        all_matched = []
        for sim in simanim:
            ocRef = Ref('Shulchan Arukh, Orach Chayim {}'.format(sim))
            mbRef = Ref('Mishnah Berurah {}'.format(sim))
            octc = TextChunk(ocRef,"he")
            mbtc = TextChunk(mbRef,"he")
            matched = dhm.match_ref(octc, mbtc, base_tokenizer=mb_base_tokenizer, dh_extract_method=mb_dh_extraction_method, with_abbrev_matches=True)
            # store dict in json serializable format
            matched['abbrevs'] = [[str(am) for am in seg] for seg in matched['abbrevs']]
            matched['comment_refs'] = [str(r.normal()) if r is not None else r for r in matched['comment_refs']]
            matched['matches'] = [r.normal() if r is not None else r for r in matched['matches']]
            matched['match_word_indices'] = [list(tup) for tup in matched['match_word_indices']]
            matched['match_text'] = [list(tup) for tup in matched['match_text']]
            all_matched.append(matched)
        #json.dump(all_matched, codecs.open('mb_matched.json', 'wb', encoding='utf8'))
        comparison = json.load(codecs.open('mb_matched.json', 'rb', encoding='utf8'))
        for a_siman, b_siman in zip(all_matched, comparison):
            for k, v in list(a_siman.items()):
                assert v == b_siman[k]
                # DEBUG
                # print u""
                # if v != b_siman[k]:
                #     for i, (v1, b1) in enumerate(zip(v, b_siman[k])):
                #         if v1 != b1:
                #             print u"Me:  {}".format(v1)
                #             print u"You: {}".format(b1)
                #             print a_siman[u'comment_refs'][i]



    def test_empty_comment(self):
        daftext = 'אע״ג שאמרו ככה בלה בלה בלה'.split()
        rashi = ['', 'אף על גב שאמרו']
        matched = dhm.match_text(daftext, rashi, verbose=True)

    def test_duplicate_comment(self):
        daftext = 'אע״ג שאמרו ככה בלה בלה בלה'.split()
        rashi = ['בלה', 'בלה']
        matched = dhm.match_text(daftext, rashi, verbose=True)


class TestDHMatcherFunctions:

    def test_is_abbrev(self):
        iam = dhm.isAbbrevMatch

        #abbreviations
        assert (True, 1, False) == iam(0,'אל',sp('אמר ליה'),0)
        assert (True, 2, False) == iam(0,'אעפ',sp('אף על פי'),0)
        assert (True, 1, False) == iam(0,'בביכנ',sp('בבית כנסת'),0)
        assert (True, 4, False) == iam(0,'aabbcde',sp('aa123 bb123 c123 d123 e123'),0)
        assert (True, 3, False) == iam(0,'aaabbcd',sp('aaa123 bb123 c123 d123'),0)

        #prefixes
        assert (True, 0, False) == iam(0, 'ר', sp('רבי'), 0, word_prefix=True)
        assert (True, 0, False) == iam(0, 'ור', sp('ורבי'), 0, word_prefix=True)
        assert (True, 0, False) == iam(0, 'ולר', sp('ולרבי'), 0, word_prefix=True)

        #numbers
        assert (True, 2, True) == iam(0, 'רלט',sp('מאתיים שלשים ותשע'),0)
        assert (True, 2, True) == iam(0, 'ברלט',sp('במאתיים שלשים ותשע'),0) #with prefix
        assert (False, 0, False) == iam(0, 'רלט',sp('מה שלשים תא'),0.1)

    def test_is_string_match(self):
        ism = dhm.IsStringMatch

        score,ismatch = ism('אבגדהוז','אבגדהוז',0) # exact
        assert ismatch == True
        score, ismatch = ism('אבגדהז','אבגדהוז',0.2) #small change
        print(score)
        assert ismatch == True
        score, ismatch = ism('אבגדהז','אבגדהוז',0) # exact wrong
        assert ismatch == False


    def test_GetAllMatches_nonempty(self):
        daftext = sp('אע״ג שאמרו ככה בלה בלה בלה')
        rashi = ['אף על גב שאמרו']
        daf = dhm.GemaraDaf(daftext,rashi)
        textMatchList = dhm.GetAllMatches(daf,daf.allRashi[0],0,len(daf.allWords)-1,0.27,0.2)
        for tm in textMatchList:
            print('{}'.format(tm))

    def test_GetAllMatches_empty(self):
        print('yo')
        daftext = 'אע״ג שאמרו ככה בלה בלה בלה'.split()
        rashi = ['', 'אף על גב שאמרו']
        daf = dhm.GemaraDaf(daftext,rashi)
        textMatchList = dhm.GetAllMatches(daf,daf.allRashi[0],0,len(daf.allWords)-1,0.27,0.2)
        for tm in textMatchList:
            print('{}'.format(tm))

    def test_GetAllApproximateMatchesWithAbbrev(self):
        daftext = sp('מימיך רב נחמן בר יצחק אמר עשה כדברי בית שמאי חייב מיתה דתנן אמר ר"ט אני הייתי בא בדרך והטתי לקרות כדברי ב"ש וסכנתי בעצמי מפני הלסטים אמרו לו כדאי היית לחוב בעצמך שעברת על דברי ב"ה: מתני׳')
        rashi = ['רב נחמן בר יצחק אמר עשה כדברי בית שמאי חייב מיתה דתנן אמר רבי טרפון אני הייתי בא בדרך והטתי לקרות כדברי בית שמאי וסכנתי בעצמי מפני הלסטים אמרו לו כדאי היית לחוב בעצמך שעברת על דברי בית הלל']
        daf = dhm.GemaraDaf(daftext,rashi)
        textMatchList = dhm.GetAllMatches(daf,daf.allRashi[0],0,len(daf.allWords)-1,0.27,0.2)
        for tm in textMatchList:
            print('{}'.format(tm))
    # test full matches and 1 word missing matches at end of daf

    def test_GetAllApproximateMatchesWithWordSkip_one_rashi_skip(self):
        textMatchList = dhm.GetAllMatches(daf,daf.allRashi[5],0,len(daf.allWords) - 1,0,0)
        assert daf.allRashi[5].startingText == textMatchList[0].textToMatch
        assert len(textMatchList) == 1
        assert textMatchList[0].textMatched == 'משעה שהכהנים נכנסים לאכול'
        assert textMatchList[0].startWord == 0
        assert textMatchList[0].endWord == 3

    def test_GetAllApproximateMatchesWithWordSkip_one_skip(self):
        textMatchList = dhm.GetAllMatches(daf,daf.allRashi[1],0,len(daf.allWords) - 1,0,0)
        assert daf.allRashi[1].startingText == textMatchList[0].textToMatch
        assert len(textMatchList) == 2
        assert textMatchList[0].textMatched == 'עד סוף האשמורה הראשונה דברי רבי אליעזר.'
        assert textMatchList[0].startWord == 5
        assert textMatchList[0].endWord == 11
        assert textMatchList[1].textMatched == 'האשמורה הראשונה דברי רבי אליעזר.'
        assert textMatchList[1].startWord == 7
        assert textMatchList[1].endWord == 11

    def test_GetAllApproximateMatchesWithWordSkip_two_skip(self):
        #skip 2 word
        textMatchList = dhm.GetAllMatches(daf,daf.allRashi[2],0,len(daf.allWords) - 1,0,0)
        assert daf.allRashi[2].startingText == textMatchList[0].textToMatch
        assert len(textMatchList) == 2
        assert textMatchList[0].textMatched == 'עד סוף האשמורה הראשונה דברי רבי אליעזר.'
        assert textMatchList[0].startWord == 5
        assert textMatchList[0].endWord == 11
        assert textMatchList[1].textMatched == 'הראשונה דברי רבי אליעזר.'
        assert textMatchList[1].startWord == 8
        assert textMatchList[1].endWord == 11

    def test_GetAllApproximateMatchesWithWordSkip_two_skip_at_end(self):
        textMatchList = dhm.GetAllMatches(daf, daf.allRashi[3], 0, len(daf.allWords) - 1, 0, 0)
        assert len(textMatchList) == 2
        assert textMatchList[0].textMatched == 'עד סוף האשמורה הראשונה דברי'
        assert textMatchList[0].startWord == 5
        assert textMatchList[0].endWord == 9
        assert textMatchList[1].textMatched == 'סוף האשמורה הראשונה דברי'
        assert textMatchList[1].startWord == 6
        assert textMatchList[1].endWord == 9


    def test_GetAllApproximateMatchesWithWordSkip_rashi_skip_end_of_daf(self):
        textMatchList = dhm.GetAllMatches(daf, daf.allRashi[6], 0, len(daf.allWords) - 1, 0, 0)
        assert len(textMatchList) == 1
        assert textMatchList[0].textMatched == 'בניו מבית המשתה אמרו לו'
        assert textMatchList[0].startWord == 24
        assert textMatchList[0].endWord == 28

    def test_GetAllApproximateMatchesWithWordSkip_mismatch_on_last_word_of_daf(self):
        textMatchList = dhm.GetAllMatches(daf, daf.allRashi[7], 0, len(daf.allWords) - 1, 0, 0)
        assert len(textMatchList) == 1
        assert textMatchList[0].textMatched == 'עד סוף האשמורה הראשונה דברי רבי'
        assert textMatchList[0].startWord == 5
        assert textMatchList[0].endWord == 10

    def test_GetAllApproximateMatchesWithWordSkip_small_rashi(self):
        textMatchList = dhm.GetAllMatches(daf, daf.allRashi[8], 0, len(daf.allWords) - 1, 0, 0)
        assert len(textMatchList) == 2
        assert textMatchList[0].textMatched == 'וחכמים אומרים עד חצות'
        assert textMatchList[0].startWord == 12
        assert textMatchList[0].endWord == 15
        assert textMatchList[1].textMatched == 'אומרים עד חצות'
        assert textMatchList[1].startWord == 13
        assert textMatchList[1].endWord == 15

    def test_GetAllApproximateMatchesWithWordSkip_too_skips(self):
        textMatchList = dhm.GetAllMatches(daf, daf.allRashi[9], 0, len(daf.allWords) - 1, 0, 0)
        assert len(textMatchList) == 0

    def test_GetAllApproximateMatchesWithWordSkip_max_skips(self):
        textMatchList = dhm.GetAllMatches(daf, daf.allRashi[10], 0, len(daf.allWords) - 1, 0, 0)
        assert len(textMatchList) == 1
        assert textMatchList[0].textMatched == 'וחכמים אומרים עד חצות ר"ג אומר עד שיעלה עמוד השחר.'
        assert textMatchList[0].startWord == 12
        assert textMatchList[0].endWord == 21

class Test_MatchMatrix:

    def test_skip_one_base_word(self):
        rashi_hashes = [1,2,7,5]
        daf_hashes =   [1,3,2,7,5]
        jump_coords =  [((0,0),(0,2))]

        mm = dhm.MatchMatrix(daf_hashes, rashi_hashes, jump_coords, 0, 1, 0, 1)
        print("First")
        print(mm.matrix)
        paths = mm.find_paths()
        #assert len(paths) == 1
        #assert paths[0]["daf_indexes_skipped"] == [1]
        #assert paths[0]["daf_start_index"] == 0
        #assert paths[0]["comment_indexes_skipped"] == []
        for p in paths:
            if p:
                print('PATH {}'.format(p))
                print(mm.print_path(p))

