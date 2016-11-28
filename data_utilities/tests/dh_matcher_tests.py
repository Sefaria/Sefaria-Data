# -*- coding: utf-8 -*-
from data_utilities import dibur_hamatchil_matcher as dhm
import regex as re


def sp(string):
    return re.split(u'\s+', string)

def setup_module(module):
    global daf
    dhm.InitializeHashTables()

    daf_words = sp(u'משעה שהכהנים נכנסים לאכול בתרומתן עד סוף האשמורה הראשונה דברי רבי אליעזר. וחכמים אומרים עד חצות. ר"ג אומר עד שיעלה עמוד השחר. מעשה ובאו בניו מבית המשתה אמרו לו')
    comments = [u'משעה שהכהנים נכנסים לאכול', #exact
                u'עד האשמורה הראשונה דברי רבי אליעזר.', # 1 skip
                u'עד הראשונה דברי רבי אליעזר.', # 2 skip
                u'עד סוף האשמורה הראשונה דברי.', # 2 skip at end of word
                u'רבן גמליאל אומר עד שיעלה', # abbrev in base_text
                u'משעה שהכהנים עלין נכנסים לאכול'] #extra word in Rashi
    daf = dhm.GemaraDaf(daf_words,comments)

class TestDHMatcherFunctions:

    def test_is_abbrev(self):
        iam = dhm.isAbbrevMatch


        assert (True, 1, False) == iam(0,u'אל',sp(u'אמר ליה'),0)
        assert (True, 2, False) == iam(0,u'אעפ',sp(u'אף על פי'),0)
        assert (True, 1, False) == iam(0,u'בביכנ',sp(u'בבית כנסת'),0)
        assert (True, 4, False) == iam(0,u'aabbcde',sp(u'aa123 bb123 c123 d123 e123'),0)
        assert (True, 3, False) == iam(0,u'aaabbcd',sp(u'aaa123 bb123 c123 d123'),0)

    # test full matches and 1 word missing matches at end of daf

    def test_GetAllApproximateMatchesWithWordSkip_one_rashi_skip(self):
        textMatchList = dhm.GetAllApproximateMatchesWithWordSkip(daf,daf.allRashi[5],0,len(daf.allWords) - 1,0,0)
        assert daf.allRashi[5].startingText == textMatchList[0].textToMatch
        assert len(textMatchList) == 1
        assert textMatchList[0].textMatched == u'משעה שהכהנים נכנסים לאכול'
        assert textMatchList[0].startWord == 0
        assert textMatchList[0].endWord == 3

    def test_GetAllApproximateMatchesWithWordSkip_one_skip(self):
        textMatchList = dhm.GetAllApproximateMatchesWithWordSkip(daf,daf.allRashi[1],0,len(daf.allWords) - 1,0,0)
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
        textMatchList = dhm.GetAllApproximateMatchesWithWordSkip(daf,daf.allRashi[2],0,len(daf.allWords) - 1,0,0)
        assert daf.allRashi[2].startingText == textMatchList[0].textToMatch
        assert len(textMatchList) == 2
        assert textMatchList[0].textMatched == u'עד סוף האשמורה הראשונה דברי רבי אליעזר.'
        assert textMatchList[0].startWord == 5
        assert textMatchList[0].endWord == 11
        assert textMatchList[1].textMatched == u'הראשונה דברי רבי אליעזר.'
        assert textMatchList[1].startWord == 8
        assert textMatchList[1].endWord == 11

    def test_GetAllApproximateMatchesWithWordSkip_two_skip_at_end(self):
        textMatchList = dhm.GetAllApproximateMatchesWithWordSkip(daf, daf.allRashi[3], 0, len(daf.allWords) - 1, 0, 0)
        assert len(textMatchList) == 2
        assert textMatchList[0].textMatched == u'עד סוף האשמורה הראשונה דברי'
        assert textMatchList[0].startWord == 5
        assert textMatchList[0].endWord == 9
        assert textMatchList[1].textMatched == u'סוף האשמורה הראשונה דברי'
        assert textMatchList[1].startWord == 6
        assert textMatchList[1].endWord == 9

class Test_MatchMatrix:

    def test_nomismatch(self):
        rashi_hashes = [1,2]
        daf_hashes = [1, 3, 2]

        mm = dhm.MatchMatrix(daf_hashes, rashi_hashes, 0,0,1,1)
        print 'first'
        print mm.matrix
        paths = mm.find_paths()
        for p in paths:
            if p:
                print 'PATH {}'.format(p)
                print mm.print_path(p)


