# -*- coding: utf-8 -*-
from data_utilities import dibur_hamatchil_matcher as dhm
from sefaria.model import *
from sefaria.utils import hebrew
import regex as re
import pickle


def sp(string):
    return re.split(u'\s+', string)

def setup_module(module):
    global daf

    dhm.InitializeHashTables()

    daf_words = sp(u'משעה שהכהנים נכנסים לאכול בתרומתן עד סוף האשמורה הראשונה דברי רבי אליעזר. וחכמים אומרים עד חצות ר"ג אומר עד שיעלה עמוד השחר. מעשה ובאו בניו מבית המשתה אמרו לו')
    comments = [u'משעה שהכהנים נכנסים לאכול', #exact
                u'עד האשמורה הראשונה דברי רבי אליעזר.', # 1 skip
                u'עד הראשונה דברי רבי אליעזר.', # 2 skip
                u'עד סוף האשמורה הראשונה דברי.', # 2 skip at end of word
                u'רבן גמליאל אומר עד שיעלה', # abbrev in base_text
                u'משעה שהכהנים עלין נכנסים לאכול', #extra word in Rashi
                u'בניו מבית המשתה אמרו לו וולה!', #extra (ridiculous) word in rashi at end of daf
                u'עד סוף האשמורה הראשונה דברי רבי בלהבלה.', #last word is a mismatch
                u'וחכמים אומרים עד חצות', #small rashi
                u'וחכמים אומרים סבבה עד חצות ר"ג שיעלה עמוד השחר.', #too many skips
                u'וחכמים אומרים סבבה עד חצות ר"ג אומר שיעלה עמוד השחר'] #max skips
    daf = dhm.GemaraDaf(daf_words,comments)



def mb_base_tokenizer(str):
    punc_pat = re.compile(ur"(\.|,|:|;)$")

    str = re.sub(ur"\([^\(\)]+\)", u"", str)
    str = re.sub(ur"''", ur'"', str)  # looks like double apostrophe in shulchan arukh is meant to be a quote
    str = re.sub(r"</?[a-z]+>", "", str)  # get rid of html tags
    str = hebrew.strip_cantillation(str, strip_vowels=True)
    word_list = re.split(ur"\s+", str)
    word_list = [re.sub(punc_pat, u"", w).strip() for w in word_list if len(
        re.sub(punc_pat, u"", w).strip()) > 0]  # remove empty strings and punctuation at the end of a word
    return word_list


def mb_dh_extraction_method(str):
    # searches for '(blah) other blah -' or '{blah} other blah -'
    m = re.search(ur"((\([^\(]+\))|(\{[^\{]+\}))([^–]+)–", str)
    if m is None:
        m = re.search(ur"((\([^\(]+\))|(\{[^\{]+\}))([^-]+)-", str)
    if m:
        dh = m.group(4).strip()
        return dh.replace(u"וכו'", u"")
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
            matched['abbrevs'] = [[unicode(am) for am in seg] for seg in matched['abbrevs']]
            all_matched.append(matched)
        #pickle.dump(all_matched, open('mb_matched.pkl','wb'))
        comparison = pickle.load(open('mb_matched.pkl', 'rb'))
        #comparison = [comparison[1]]
        assert comparison == all_matched

    def test_empty_comment(self):
        daftext = u'אע״ג שאמרו ככה בלה בלה בלה'.split()
        rashi = [u'', u'אף על גב שאמרו']
        matched = dhm.match_text(daftext, rashi, verbose=True)



class TestDHMatcherFunctions:

    def test_is_abbrev(self):
        iam = dhm.isAbbrevMatch

        #abbreviations
        assert (True, 1, False) == iam(0,u'אל',sp(u'אמר ליה'),0)
        assert (True, 2, False) == iam(0,u'אעפ',sp(u'אף על פי'),0)
        assert (True, 1, False) == iam(0,u'בביכנ',sp(u'בבית כנסת'),0)
        assert (True, 4, False) == iam(0,u'aabbcde',sp(u'aa123 bb123 c123 d123 e123'),0)
        assert (True, 3, False) == iam(0,u'aaabbcd',sp(u'aaa123 bb123 c123 d123'),0)

        #numbers
        assert (True, 2, True) == iam(0, u'רלט',sp(u'מאתיים שלשים ותשע'),0)
        assert (True, 2, True) == iam(0, u'ברלט',sp(u'במאתיים שלשים ותשע'),0) #with prefix
        assert (False, 0, False) == iam(0, u'רלט',sp(u'מה שלשים תא'),0.1)

    def test_is_string_match(self):
        ism = dhm.IsStringMatch

        score,ismatch = ism(u'אבגדהוז',u'אבגדהוז',0) # exact
        assert ismatch == True
        score, ismatch = ism(u'אבגדהז',u'אבגדהוז',0.2) #small change
        print score
        assert ismatch == True
        score, ismatch = ism(u'אבגדהז',u'אבגדהוז',0) # exact wrong
        assert ismatch == False


    def test_GetAllMatches_nonempty(self):
        daftext = sp(u'אע״ג שאמרו ככה בלה בלה בלה')
        rashi = [u'אף על גב שאמרו']
        daf = dhm.GemaraDaf(daftext,rashi)
        textMatchList = dhm.GetAllMatches(daf,daf.allRashi[0],0,len(daf.allWords)-1,0.27,0.2)
        for tm in textMatchList:
            print u'{}'.format(tm)

    def test_GetAllMatches_empty(self):
        print 'yo'
        daftext = u'אע״ג שאמרו ככה בלה בלה בלה'.split()
        rashi = [u'', u'אף על גב שאמרו']
        daf = dhm.GemaraDaf(daftext,rashi)
        textMatchList = dhm.GetAllMatches(daf,daf.allRashi[0],0,len(daf.allWords)-1,0.27,0.2)
        for tm in textMatchList:
            print u'{}'.format(tm)

    def test_GetAllApproximateMatchesWithAbbrev(self):
        daftext = sp(u'מימיך רב נחמן בר יצחק אמר עשה כדברי בית שמאי חייב מיתה דתנן אמר ר"ט אני הייתי בא בדרך והטתי לקרות כדברי ב"ש וסכנתי בעצמי מפני הלסטים אמרו לו כדאי היית לחוב בעצמך שעברת על דברי ב"ה: מתני׳')
        rashi = [u'רב נחמן בר יצחק אמר עשה כדברי בית שמאי חייב מיתה דתנן אמר רבי טרפון אני הייתי בא בדרך והטתי לקרות כדברי בית שמאי וסכנתי בעצמי מפני הלסטים אמרו לו כדאי היית לחוב בעצמך שעברת על דברי בית הלל']
        daf = dhm.GemaraDaf(daftext,rashi)
        textMatchList = dhm.GetAllMatches(daf,daf.allRashi[0],0,len(daf.allWords)-1,0.27,0.2)
        for tm in textMatchList:
            print u'{}'.format(tm)
    # test full matches and 1 word missing matches at end of daf

    def test_GetAllApproximateMatchesWithWordSkip_one_rashi_skip(self):
        textMatchList = dhm.GetAllMatches(daf,daf.allRashi[5],0,len(daf.allWords) - 1,0,0)
        assert daf.allRashi[5].startingText == textMatchList[0].textToMatch
        assert len(textMatchList) == 1
        assert textMatchList[0].textMatched == u'משעה שהכהנים נכנסים לאכול'
        assert textMatchList[0].startWord == 0
        assert textMatchList[0].endWord == 3

    def test_GetAllApproximateMatchesWithWordSkip_one_skip(self):
        textMatchList = dhm.GetAllMatches(daf,daf.allRashi[1],0,len(daf.allWords) - 1,0,0)
        assert daf.allRashi[1].startingText == textMatchList[0].textToMatch
        assert len(textMatchList) == 2
        assert textMatchList[0].textMatched == u'עד סוף האשמורה הראשונה דברי רבי אליעזר.'
        assert textMatchList[0].startWord == 5
        assert textMatchList[0].endWord == 11
        assert textMatchList[1].textMatched == u'האשמורה הראשונה דברי רבי אליעזר.'
        assert textMatchList[1].startWord == 7
        assert textMatchList[1].endWord == 11

    def test_GetAllApproximateMatchesWithWordSkip_two_skip(self):
        #skip 2 word
        textMatchList = dhm.GetAllMatches(daf,daf.allRashi[2],0,len(daf.allWords) - 1,0,0)
        assert daf.allRashi[2].startingText == textMatchList[0].textToMatch
        assert len(textMatchList) == 2
        assert textMatchList[0].textMatched == u'עד סוף האשמורה הראשונה דברי רבי אליעזר.'
        assert textMatchList[0].startWord == 5
        assert textMatchList[0].endWord == 11
        assert textMatchList[1].textMatched == u'הראשונה דברי רבי אליעזר.'
        assert textMatchList[1].startWord == 8
        assert textMatchList[1].endWord == 11

    def test_GetAllApproximateMatchesWithWordSkip_two_skip_at_end(self):
        textMatchList = dhm.GetAllMatches(daf, daf.allRashi[3], 0, len(daf.allWords) - 1, 0, 0)
        assert len(textMatchList) == 2
        assert textMatchList[0].textMatched == u'עד סוף האשמורה הראשונה דברי'
        assert textMatchList[0].startWord == 5
        assert textMatchList[0].endWord == 9
        assert textMatchList[1].textMatched == u'סוף האשמורה הראשונה דברי'
        assert textMatchList[1].startWord == 6
        assert textMatchList[1].endWord == 9


    def test_GetAllApproximateMatchesWithWordSkip_rashi_skip_end_of_daf(self):
        textMatchList = dhm.GetAllMatches(daf, daf.allRashi[6], 0, len(daf.allWords) - 1, 0, 0)
        assert len(textMatchList) == 1
        assert textMatchList[0].textMatched == u'בניו מבית המשתה אמרו לו'
        assert textMatchList[0].startWord == 24
        assert textMatchList[0].endWord == 28

    def test_GetAllApproximateMatchesWithWordSkip_mismatch_on_last_word_of_daf(self):
        textMatchList = dhm.GetAllMatches(daf, daf.allRashi[7], 0, len(daf.allWords) - 1, 0, 0)
        assert len(textMatchList) == 1
        assert textMatchList[0].textMatched == u'עד סוף האשמורה הראשונה דברי רבי'
        assert textMatchList[0].startWord == 5
        assert textMatchList[0].endWord == 10

    def test_GetAllApproximateMatchesWithWordSkip_small_rashi(self):
        textMatchList = dhm.GetAllMatches(daf, daf.allRashi[8], 0, len(daf.allWords) - 1, 0, 0)
        assert len(textMatchList) == 2
        assert textMatchList[0].textMatched == u'וחכמים אומרים עד חצות'
        assert textMatchList[0].startWord == 12
        assert textMatchList[0].endWord == 15
        assert textMatchList[1].textMatched == u'אומרים עד חצות'
        assert textMatchList[1].startWord == 13
        assert textMatchList[1].endWord == 15

    def test_GetAllApproximateMatchesWithWordSkip_too_skips(self):
        textMatchList = dhm.GetAllMatches(daf, daf.allRashi[9], 0, len(daf.allWords) - 1, 0, 0)
        assert len(textMatchList) == 0

    def test_GetAllApproximateMatchesWithWordSkip_max_skips(self):
        textMatchList = dhm.GetAllMatches(daf, daf.allRashi[10], 0, len(daf.allWords) - 1, 0, 0)
        assert len(textMatchList) == 1
        assert textMatchList[0].textMatched == u'וחכמים אומרים עד חצות ר"ג אומר עד שיעלה עמוד השחר.'
        assert textMatchList[0].startWord == 12
        assert textMatchList[0].endWord == 21

class Test_MatchMatrix:

    def test_skip_one_base_word(self):
        rashi_hashes = [1,2,7,5]
        daf_hashes =   [1,3,2,7,5]
        jump_coords =  [((0,0),(0,2))]

        mm = dhm.MatchMatrix(daf_hashes, rashi_hashes, jump_coords, 0, 1, 0, 1)
        print "First"
        print mm.matrix
        paths = mm.find_paths()
        #assert len(paths) == 1
        #assert paths[0]["daf_indexes_skipped"] == [1]
        #assert paths[0]["daf_start_index"] == 0
        #assert paths[0]["comment_indexes_skipped"] == []
        for p in paths:
            if p:
                print 'PATH {}'.format(p)
                print mm.print_path(p)

