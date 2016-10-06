# -*- coding: utf-8 -*-
import re
import math as mathy
import bisect
import csv
import codecs
from sefaria.model import *
from research.talmud_pos_research.language_classifier import language_tools

fdebug = False
# constants for generating distance score. a 0 means a perfect match, although it will never be 0, due to the smoothing.
normalizingFactor = 100
smoothingFactor = 1
fullWordValue = 3
abbreviationPenalty = 1
ImaginaryContenderPerWord = 22

fSerializeData = False

ourmod = 134217728
pregeneratedKWordValues = []
pregeneratedKMultiwordValues = []
NumPregeneratedValues = 20
kForWordHash = 41
kForMultiWordHash = 39
lettersInOrderOfFrequency = [ u'ו', u'י', u'א', u'מ', u'ה', u'ל', u'ר', u'נ', u'ב', u'ש', u'ת', u'ד', u'כ', u'ע', u'ח', u'ק', u'פ', u'ס', u'ז', u'ט', u'ג', u'צ' ]

sofit_map = {
    u'ך': u'כ',
    u'ם': u'מ',
    u'ן': u'נ',
    u'ף': u'פ',
    u'ץ': u'צ',
}

class TextMatch:
    def __init__(self):
        self.textToMatch = ""
        self.textMatched = ""
        self.startWord = 0
        self.endWord = 0
        self.score = 0
        self.skippedWords = []
        self.abbrev_matches = [] #list of tuples of range of abbreviation found, if any

class AbbrevMatch:
    def __init__(self,abbrev,expanded,rashiRange,gemaraRange,contextBefore,contextAfter):
        self.abbrev = abbrev
        self.expanded = expanded
        self.rashiRange = rashiRange
        self.gemaraRange = gemaraRange
        self.contextBefore = contextBefore
        self.contextAfter = contextAfter
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            #TODO i feel like gemaraRange should be compared here also, but apparently that wasn't right
            return self.abbrev == other.abbrev and self.expanded == other.expanded and self.rashiRange == other.rashiRange
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

# should be private?
class GemaraDaf:
    def __init__(self,word_list,comments,dh_extraction_method=lambda x: x,prev_matched_results=None):
        self.allWords = word_list
        self.gemaraText = " ".join(self.allWords)
        self.wordhashes = CalculateHashes(self.allWords)
        self.allRashi = []
        count = 0
        for i,comm in enumerate(comments):
            prev_result = prev_matched_results[i] if prev_matched_results else (-1,-1)
            self.allRashi.append(RashiUnit(dh_extraction_method(comm),comm,count,prev_result))
            count+=1


class RashiUnit:
    def __init__(self,startingText,fullText,place,prev_result=(-1,-1)):
        self.place = place
        self.disambiguationScore = 0
        self.rashimatches = []  # list of TextMatch
        self.skippedWords = []
        self.abbrev_matches = []
        self.startingText = startingText

        normalizedCV = re.sub(ur" ו" + u"?" + u"כו" + u"'?" + u"$", u"", self.startingText).strip()
        normalizedCV = re.sub(ur"^(גמ|גמרא|מתני|מתניתין|משנה)'? ", u"", normalizedCV)

        # if it starts with הג, then take just 3 words afterwords
        if self.startingText.startswith(u"ה\"ג"):
            normalizedCV = re.search(ur"[^ ]+ ([^ ]+( [^ ]+)?( [^ ]+)?)", normalizedCV).group(1)

        # // now remove all non-letters, allowing just quotes
        normalizedCV = re.sub(ur"[^א-ת \"]", u"", normalizedCV).strip()

        self.startingTextNormalized = normalizedCV
        self.fullText = fullText
        self.startWord = prev_result[0]
        self.endWord = prev_result[1]
        self.cvWordcount = len(re.split(r"\s+",normalizedCV))
        self.matchedGemaraText = ""


def match_ref(base_text, comments, base_tokenizer,dh_extract_method=lambda x: x,verbose=False, word_threshold=0.27,char_threshold=0.2,with_abbrev_matches=False,boundaryFlexibility=0):
    """
    base_text: TextChunk
    comments: TextChunk or list of comment strings
    base_tokenizer: f(string)->list(string)
    dh_extract_method: f(string)->string
    boundaryFlexibility: int which indicates how much leeway there is in the order of rashis
    :returns: [(Ref, Ref)] - base text, commentary
         or
         [Ref] - base text refs - if comments is a list
    """
    bas_word_list = [] #re.split(r"\s+"," ".join(base_text.text))
    base_depth = base_text.ja().depth()
    bas_ind_list,bas_ref_list = base_text.text_index_map(base_tokenizer)

    if base_depth == 1:
        for segment in base_text.text:
            bas_word_list += base_tokenizer(segment)
    elif base_depth == 2:
        for section in base_text.text:
            for segment in section:
                bas_word_list += base_tokenizer(segment)

    #get all non-empty segment refs for 'comments'
    if type(comments) == TextChunk:
        comm_ref = comments._oref
        if comm_ref.get_state_ja("he").depth() == 2:
            comment_ref_list = [comm_ref.subref(i + 1) for k in sub_ja.non_empty_sections() for i in k]
            comment_list = [temp_comm for temp_sec in comments.text]
        elif comm_ref.get_state_ja("he").depth() == 3:
            comment_ind_list, comment_ref_list = base_text.text_index_map(base_tokenizer)
            comment_list = [temp_comm for temp_sec in comments.text for temp_comm in temp_sec]
    elif type(comments) == list:
        comment_list = comments
        comment_ref_list = None
    else:
        raise TypeError("'comments' needs to be either a TextChunk or a list of comment strings")

    if with_abbrev_matches:
        start_end_map,abbrev_matches = match_text(bas_word_list,comment_list,dh_extract_method,verbose,word_threshold,char_threshold,with_abbrev_matches=with_abbrev_matches,boundaryFlexibility=boundaryFlexibility)
    else:
        start_end_map = match_text(bas_word_list,comment_list,dh_extract_method,verbose,word_threshold,char_threshold,boundaryFlexibility=boundaryFlexibility)

    ref_matches = []
    prev_ref = None
    for i,x in enumerate(start_end_map):
        start = x[0]
        end = x[1]
        if start == -1: #meaning, not found
            matched_ref = None
        else:
            start_ref = bas_ref_list[bisect.bisect_right(bas_ind_list,start)-1]
            end_ref = bas_ref_list[bisect.bisect_right(bas_ind_list,end)-1]
            if start_ref == end_ref:
                matched_ref = start_ref
            else:
                matched_ref = start_ref.to(end_ref)

            #if verbose and prev_ref and prev_ref.overlaps(matched_ref):
            #    print u"\t{} overlaps {}. \n\t\tPREV\n\t\t\tSEFARIA:({})\n\t\t\tKOREN({})\n\t\tNEXT\n\t\t\tSEFARIA:({})\n\t\t\tKOREN({})".format(prev_ref,matched_ref,TextChunk(prev_ref,"he").as_string(),comment_list[i-1],TextChunk(matched_ref,"he").as_string(),comment_list[i])

        ref_matches.append(matched_ref)
        prev_ref = matched_ref
    if with_abbrev_matches:
        return zip(ref_matches, comment_ref_list,abbrev_matches) if comment_ref_list else zip(ref_matches,abbrev_matches)
    else:
        return zip(ref_matches,comment_ref_list) if comment_ref_list else ref_matches

def match_text(base_text, comments, dh_extract_method=lambda x: x,verbose=False,word_threshold=0.27,char_threshold=0.2,prev_matched_results=None,with_abbrev_matches=False,boundaryFlexibility=0):
    """
    base_text: list - list of words
    comments: list - list of comment strings
    dh_extract_method: f(string)->string
    prev_matched_results: [(start,end)] list of start/end indexes found in a previous iteration of match_text
    with_abbrev_matches: True if you want a second return value which is a list AbbrevMatch objects (see class definition above)
    returns: [(start,end)] - start and end index of each comment. optionally also returns abbrev_ranges (see with_abbrev_ranges parameter)
    """

    InitializeHashTables()

    curDaf = GemaraDaf(base_text,comments,dh_extract_method,prev_matched_results)

    #now we go through each rashi, and find all potential matches for each, with a rating
    for irashi,ru in enumerate(curDaf.allRashi):
        if ru.startWord != -1:
            #this rashi was initialized with the `prev_matched_results` list and should be ignored with regards to matching
            continue

        startword,endword = (0,len(curDaf.allWords)) if prev_matched_results == None else GetRashiBoundaries(curDaf.allRashi,ru.place,len(curDaf.allWords),boundaryFlexibility)[0:2]
        approxMatches = GetAllApproximateMatches(curDaf,ru,startword,endword,word_threshold,char_threshold)
        approxAbbrevMatches = GetAllApproximateMatchesWithAbbrev(curDaf, ru, startword, endword,char_threshold)
        approxSkipWordMatches = GetAllApproximateMatchesWithWordSkip(curDaf, ru, startword, endword,char_threshold)

        ru.rashimatches += approxMatches + approxAbbrevMatches

        #only add skip-matches that don't overlap with existing matching
        foundpoints = []
        for tm in ru.rashimatches:
            foundpoints.append(tm.startWord)
        # for the skip words, of course, it may find items that are one-off or two-off from the actual match. Filter these out
        for tm in approxSkipWordMatches:
            startword = tm.startWord
            #TODO maybe consider changing the range
            if any([x in foundpoints for x in xrange(startword - 1, startword + 2)]):
                continue
            ru.rashimatches.append(tm)

        #sort the rashis by score
        ru.rashimatches.sort(key=lambda x: x.score) #note: check this works

        #now figure out disambiguation score
        CalculateAndFillInDisambiguity(ru)

    #let's make a list of our rashis in disambiguity order
    rashisByDisambiguity = curDaf.allRashi[:] # note: check if this is what he wanted. List<RashiUnit> rashisByDisambiguity = new List<RashiUnit>(curDaf.allRashi);
    rashisByDisambiguity.sort(key=lambda x: -x.disambiguationScore ) #note: check that this is sorting in the right order. rashisByDisambiguity.Sort((x, y) => y.disambiguationScore.CompareTo(x.disambiguationScore));
    #remove any rashis that have no matches at all
    for temp_rashi in reversed(rashisByDisambiguity):
        if len(temp_rashi.rashimatches) == 0:
            rashisByDisambiguity.remove(temp_rashi)

    while len(rashisByDisambiguity) > 0:

        #take top disambiguous rashi
        topru = rashisByDisambiguity[0]

        #get its boundaries
        startBound,endBound,prevMatchedRashi,nextMatchedRashi = GetRashiBoundaries(curDaf.allRashi,topru.place,len(curDaf.allWords),boundaryFlexibility)

        #take the first bunch in order of disambiguity and put them in
        highestrating = topru.disambiguationScore
        #if we're up to 0 disambiguity, rate them in terms of their plac in the amud
        if highestrating == 0:
            for curru in rashisByDisambiguity:
                #figure out how many are tied, or at least within 5 of each other
                topscore = curru.rashimatches[0].score
                tobesorted = []
                for temp_rashimatchi in curru.rashimatches:
                    if temp_rashimatchi.score == topscore:
                        #this is one of the top matches, and should be sorted
                        tobesorted.append(temp_rashimatchi)

                #sort those top rashis by place
                tobesorted.sort(key=lambda x: x.startWord)
                #now add the rest
                for temp_rashimatchi in curru.rashimatches[len(tobesorted):]:
                    tobesorted.append(temp_rashimatchi)

                #put them all in
                curru.rashimatches = tobesorted
        lowestrating = -1
        rashiUnitsCandidates = []
        for ru in rashisByDisambiguity:
            #if this is outside the region, chuck it
            #the rashis are coming in a completely diff order, hence we need to check each one
            if ru.place <= prevMatchedRashi or ru.place >= nextMatchedRashi:
                continue
            rashiUnitsCandidates.append(ru)

        # now we figure out how many of these we want to process
        # we want to take the top three at the least, seven at most, and anything that fits into the current threshold.
        ruToProcess = []
        threshold = max(rashiUnitsCandidates[0].disambiguationScore -5, rashiUnitsCandidates[0].disambiguationScore/2)
        thresholdBediavad = rashiUnitsCandidates[0].disambiguationScore /2
        for ru in rashiUnitsCandidates:
            curScore = ru.disambiguationScore
            if curScore >= threshold or (len(ruToProcess) < 3 and curScore >= thresholdBediavad):
                ruToProcess.append(ru)
                if highestrating == -1 or ru.disambiguationScore > highestrating:
                    highestrating = ru.disambiguationScore
                if lowestrating == -1 or ru.disambiguationScore < lowestrating:
                    lowestrating = ru.disambiguationScore
            else:
                break

            if len(ruToProcess) == 7:
                break
        # are these in order?
        #.. order them by place in the rashi order
        ruToProcess.sort(key=lambda x: x.place)

        #see if they are in order
        fAllInOrder = True
        fFirstTime = True
        while not fAllInOrder or fFirstTime:
            #if there are ties, allow for those
            fFirstTime = False
            fAllInOrder = True
            prevstartpos = -1
            prevendpos = -1
            for ru in ruToProcess:

                best_rashi = ru.rashimatches[0]
                #if this one is prior to the current position, break
                if best_rashi.startWord < prevstartpos:
                    fAllInOrder = False
                    break
                #if this one is the same as curpos, only ok it it is shorter
                if best_rashi.startWord == prevstartpos:
                    if best_rashi.endWord >= prevendpos:
                        fAllInOrder = False
                        break

                prevstartpos = best_rashi.startWord
                prevendpos = best_rashi.endWord

            # if they are not in order, then we need to figure out which ones are causing trouble and throw them out
            if not fAllInOrder:
                if len(ruToProcess) == 2:
                    #there are only 2 (duh)
                    #if the top one is much higher in its disambig score than the next one, then don't try to reverse; just take the top score
                    if abs(ruToProcess[0].disambiguationScore - ruToProcess[1].disambiguationScore) > 10:
                        ruToProcess.sort(key=lambda x: -x.disambiguationScore)
                        del ruToProcess[1]
                    else:
                        # if there are only 2, see if we can reverse them by going to the secondary matches
                        # try the first
                        ffixed = False
                        if len(ruToProcess[0].rashimatches) > 1:
                            if ruToProcess[0].rashimatches[1].startWord < ruToProcess[1].rashimatches[0].startWord:
                                #make sure they are reasonably close
                                if ruToProcess[0].disambiguationScore < 10:
                                    del ruToProcess[0].rashimatches[0]
                                    ffixed = True
                        if not ffixed:
                            #.. try the second
                            ffixed = False
                            if len(ruToProcess[1].rashimatches) > 1:
                                if ruToProcess[1].rashimatches[1].startWord > ruToProcess[0].rashimatches[0].startWord:
                                    if ruToProcess[1].disambiguationScore < 10:
                                        del ruToProcess[1].rashimatches[0]
                                        ffixed = True
                        if not ffixed:
                            #try the second of both
                            ffixed = False
                            if len(ruToProcess[0].rashimatches) > 1 and len(ruToProcess[1].rashimatches) > 1:
                                if ruToProcess[1].rashimatches[1].startWord > ruToProcess[0].rashimatches[1].startWord:
                                    if ruToProcess[1].disambiguationScore < 10 and ruToProcess[0].disambiguationScore < 10:
                                        del ruToProcess[0].rashimatches[0]
                                        del ruToProcess[1].rashimatches[0]
                                        ffixed = True
                        #if not, take the one with the highest score
                        if not ffixed:
                            ruToProcess.sort( key = lambda x: -x.disambiguationScore)
                            del ruToProcess[1]
                else:
                    outoforder = [0 for i in xrange(len(ruToProcess))]
                    highestDeviation = 0
                    for irashi,temp_irashi in enumerate(ruToProcess):
                        #how many are out of order vis-a-vis this one?
                        for jrashi,temp_jrashi in enumerate(ruToProcess):
                            if jrashi == irashi:
                                continue
                            if irashi < jrashi:
                                #easy case: they start at diff places
                                if temp_irashi.rashimatches[0].startWord > temp_jrashi.rashimatches[0].startWord:
                                    outoforder[irashi] += 1
                                    #deal with case of same starting word. only ok if irashi is of greater length
                                elif temp_irashi.rashimatches[0].startWord == temp_jrashi.rashimatches[0].startWord:
                                    if temp_irashi.rashimatches[0].endWord <= temp_jrashi.rashimatches[0].endWord:
                                        outoforder[irashi] += 1
                            else:
                                #in this case, irashi is after jrashi
                                if temp_irashi.rashimatches[0].startWord < temp_jrashi.rashimatches[0].startWord:
                                    outoforder[irashi] += 1
                                # deal with case of same starting word. only ok if jrashi is of greater length
                                elif temp_irashi.rashimatches[0].startWord == temp_jrashi.rashimatches[0].startWord:
                                    if temp_irashi.rashimatches[0].endWord >= temp_jrashi.rashimatches[0].endWord:
                                        outoforder[irashi] += 1
                        if outoforder[irashi] > highestDeviation:
                            highestDeviation = outoforder[irashi]

                    #now throw out all those that have the highest out-of-order ranking
                    for irashi in reversed(xrange(len(ruToProcess))):
                        if outoforder[irashi] == highestDeviation and len(ruToProcess) > 1:
                            del ruToProcess[irashi]
        #TODO: deal with the case of only 2 in ruToProcess in a smarter way


        #by this point they are all in order, so we can put them all in
        for curru in ruToProcess:
            # put it in
            #TODO: if disambiguity is low, apply other criteria
            if len(curru.rashimatches) == 0: continue
            match = curru.rashimatches[0]
            curru.startWord = match.startWord
            curru.endWord = match.endWord
            curru.matchedGemaraText = match.textMatched
            curru.skippedWords = match.skippedWords
            curru.abbrev_matches = match.abbrev_matches

            # remove this guy from the disambiguities, now that it is matched up
            rashisByDisambiguity.remove(curru) #check remove
            #recalculate the disambiguities for all those who were potentially relevant, based on this one's place
            RecalculateDisambiguities(curDaf.allRashi, rashisByDisambiguity, prevMatchedRashi, nextMatchedRashi, startBound, endBound, curru)

        #resort the disambiguity array
        rashisByDisambiguity.sort(key = lambda x: -x.disambiguationScore)

    unmatched = CountUnmatchedUpRashi(curDaf)
    #now we check for dapim that have a lot of unmatched items, and then we take items out one at a time to see if we can
    #minimize it because usually this results from one misplaced item.

    if verbose: sbreport = u""
    start_end_map = []
    abbrev_matches = []
    #now do a full report
    for ru in curDaf.allRashi:
        if ru.startWord == -1:
            if verbose: sbreport += u"\nUNMATCHED: {}".format(ru.startingText)
            #if not verbose: print u"\tUNMATCHED: {}".format(ru.startingText)
            start_end_map.append((ru.startWord,ru.startWord))
            abbrev_matches.append(ru.abbrev_matches)
        else:
            if verbose:
                if len(ru.skippedWords) > 0:
                    sbreport += u"\n[{}-{} not {},{} ] {} // {} ".format(ru.startWord,ru.endWord,ru.skippedWords[0],ru.skippedWords[1],ru.startingText,ru.matchedGemaraText)
                else:
                    sbreport += u"\n{} //{}[{}-{}]".format(ru.startingText,ru.matchedGemaraText,ru.startWord,ru.endWord)
            start_end_map.append((ru.startWord,ru.endWord))
            abbrev_matches.append(ru.abbrev_matches)

    if verbose: print sbreport
    if with_abbrev_matches:
        return start_end_map,abbrev_matches
    else:
        return start_end_map


def RecalculateDisambiguities(allRashis, rashisByDisambiguity, prevMatchedRashi, nextMatchedRashi, startbound, endbound,
                              newlyMatchedRashiUnit):  # List<RashiUnit>,List<RashiUnit>,int,int,int,int,RashiUnit
    for irashi in xrange(len(rashisByDisambiguity) - 1, -1, -1):
        ru = rashisByDisambiguity[irashi]
        if ru.place <= prevMatchedRashi or ru.place >= nextMatchedRashi or ru.place == newlyMatchedRashiUnit.place:
            continue
        # this rashi falls out somewhere inside the current window, either before the newest match or after the newest match
        localstartbound = startbound if (ru.place < newlyMatchedRashiUnit.place) else newlyMatchedRashiUnit.startWord
        localendbound = endbound if (ru.place > newlyMatchedRashiUnit.place) else newlyMatchedRashiUnit.startWord

        # now remove any potential matches that are blocked by the newly matched rashi
        for imatch in xrange(len(ru.rashimatches) - 1, -1, -1):
            tm = ru.rashimatches[imatch]
            if tm.startWord < localstartbound or tm.startWord > localendbound:
                del ru.rashimatches[imatch]

        # special shift: if there are two close items, and one is an overlap with a current anchor and one is not, switch (them?) and their scores
        endOfPrevRashi = -1 if prevMatchedRashi == -1 else allRashis[prevMatchedRashi].endWord
        startOfNextRashi = 9999 if nextMatchedRashi == len(allRashis) else allRashis[nextMatchedRashi].startWord

        if len(ru.rashimatches) >= 2:
            # if the top one overlaps
            if ru.rashimatches[0].startWord <= endOfPrevRashi or ru.rashimatches[0].endWord >= startOfNextRashi:
                # and if the next one does not overlap
                if ru.rashimatches[1].startWord > endOfPrevRashi and ru.rashimatches[1].endWord < startOfNextRashi:
                    if ru.rashimatches[1].score - ru.rashimatches[0].score < 20:
                        # let's switch them

                        temp = ru.rashimatches[1]
                        ru.rashimatches[1] = ru.rashimatches[0]
                        ru.rashimatches[0] = temp

                        tempscore = ru.rashimatches[1].score
                        ru.rashimatches[0].score = ru.rashimatches[1].score
                        ru.rashimatches[1].score = tempscore
        # if there are none left, remove it altogether
        if len(ru.rashimatches) == 0:
            del rashisByDisambiguity[irashi]
        else:
            # now recalculate the disambiguity
            CalculateAndFillInDisambiguity(ru)


def CalculateAndFillInDisambiguity(ru):  # RashiUnit
    # if just one, it is close to perfect. Although could be that there is no match...
    if len(ru.rashimatches) == 1:
        # ca;culate it vis-a-vis blank
        ru.disambiguationScore = (ImaginaryContenderPerWord * ru.cvWordcount) - ru.rashimatches[0].score

        if ru.disambiguationScore < 0:
            ru.disambiguationScore = 0
    elif len(ru.rashimatches) == 0:
        ru.disambiguationScore = 0xFFFF
    else:
        ru.disambiguationScore = ru.rashimatches[1].score - ru.rashimatches[0].score


def CountUnmatchedUpRashi(curDaf):  # GemaraDar
    # This function counts all the Rashi's in a given daf and
    # returns the amount of rashi's that still don't have a location within the gemara text.
    toRet = 0
    for rashi in curDaf.allRashi:
        if rashi.startWord == -1:
            toRet += 1
    return toRet


def GetAllApproximateMatches(curDaf, curRashi, startBound, endBound,
                             word_threshold,char_threshold):  # inputs (GemaraDaf, RashiUnit, int, int, double)
    global normalizingFactor
    allMatches = []
    startText = curRashi.startingTextNormalized
    wordCount = curRashi.cvWordcount
    if wordCount == 0:
        return allMatches
    # Okay, start going through all the permutations..
    distance = 0

    iWord = startBound
    while iWord <= len(curDaf.allWords) - wordCount and iWord + wordCount - 1 <= endBound:
        fIsMatch = False
        # if phrase is 4 or more words, use the 2-letter hashes
        if wordCount >= 4:
            # get the hashes for the starting text
            cvhashes = CalculateHashes(re.split(ur"\s+", startText.strip()))
            initialhash = cvhashes[0]

            if curDaf.wordhashes[iWord] == initialhash:
                # see if the rest match up
                mismatches = 0

                for icvword in xrange(1, wordCount):
                    if curDaf.wordhashes[iWord + icvword] != cvhashes[icvword]:
                        mismatches += 1

                # now we need to decide if we can let it go
                allowedMismatches = mathy.ceil(wordCount * word_threshold)
                if mismatches <= allowedMismatches:
                    distance = mismatches
                    fIsMatch = True

        else:
            # build the phrase
            targetPhrase = BuildPhraseFromArray(curDaf.allWords, iWord, wordCount)

            # now check if it is a match
            distance, fIsMatch = IsStringMatch(startText, targetPhrase, char_threshold)

        # if it is, add it in
        if fIsMatch:
            curMatch = TextMatch()
            curMatch.textToMatch = curRashi.startingText
            curMatch.textMatched = BuildPhraseFromArray(curDaf.allWords, iWord, wordCount)
            curMatch.startWord = iWord
            curMatch.endWord = iWord + wordCount - 1

            # calculate the score - how distant is it
            dist = ComputeLevenshteinDistanceByWord(startText, curMatch.textMatched)
            normalizedDistance = 1.0*(dist + smoothingFactor) / (len(startText) + smoothingFactor) * normalizingFactor
            curMatch.score = normalizedDistance

            allMatches.append(curMatch)
        iWord += 1

    return allMatches


def GetAllApproximateMatchesWithAbbrev(curDaf, curRashi, startBound, endBound,
                                       char_threshold):  # inputs (GemaraDaf, RashiUnit, int, int, double)
    global normalizingFactor

    allMatches = []
    abbrev_matches = []
    startText = curRashi.startingTextNormalized

    wordCountRashi = curRashi.cvWordcount
    wordCountGemara = len(curDaf.allWords)
    if wordCountRashi == 0:
        return allMatches

    # convert string into an array of words
    startTextWords = re.split(ur"\s+", startText)

    # go through all possible starting words in the gemara text

    iStartingWordInGemara = startBound
    while iStartingWordInGemara < wordCountGemara: #and iStartingWordInGemara + wordCountRashi - 1 <= endBound:
        fIsMatch = False
        offsetWithinGemara = 0
        offsetWithinRashiCV = 0
        distance = 0
        totaldistance = 0

        # now we loop according to the number of words in the cv
        # .. keep track of how the gemara text differs from rashi length
        gemaraDifferential = 0

        iWordWithinPhrase = 0
        while iWordWithinPhrase + offsetWithinRashiCV < wordCountRashi  and iStartingWordInGemara + offsetWithinGemara + iWordWithinPhrase < wordCountGemara:
            # first check if the cv word has a quotemark

            #try:
            if u"\"" in startTextWords[iWordWithinPhrase + offsetWithinRashiCV]:
                # get our ראשי תיבות word without the quote mark
                cleanRT = cleanAbbrev(startTextWords[iWordWithinPhrase + offsetWithinRashiCV])
                maxlen = len(cleanRT)

                # let's see if this matches the start of the next few words
                curpos = iStartingWordInGemara + iWordWithinPhrase + offsetWithinGemara
                fIsMatch,newOffsetWithinGemara = isAbbrevMatch(curpos,cleanRT,curDaf.allWords)


                iStartContext = 3 if curpos >= 3 else curpos

                if fIsMatch:
                    abbrevMatch = AbbrevMatch(cleanRT,curDaf.allWords[curpos:curpos+newOffsetWithinGemara+1],(
                        iWordWithinPhrase+offsetWithinRashiCV,iWordWithinPhrase+offsetWithinRashiCV),
                                                   (curpos,curpos+newOffsetWithinGemara),
                                                   curDaf.allWords[curpos-iStartContext:curpos],
                                                   curDaf.allWords[curpos+newOffsetWithinGemara+1:curpos+4])
                    if not abbrevMatch in abbrev_matches:
                        abbrev_matches.append(abbrevMatch)
                offsetWithinGemara += newOffsetWithinGemara

                if not fIsMatch:
                    break

            # now increment the offset to correspond, so that we'll know we're skipping over x number of words
            elif u"\"" in curDaf.allWords[iStartingWordInGemara + offsetWithinGemara + iWordWithinPhrase]:
                # get our ראשי תיבות word without the quote mark
                cleanRT = cleanAbbrev(curDaf.allWords[iStartingWordInGemara + offsetWithinGemara + iWordWithinPhrase])
                maxlen = len(cleanRT)

                # let's see if this matches the start of the next few words
                curpos = iWordWithinPhrase + offsetWithinRashiCV
                fIsMatch,newOffsetWithinRashiCV = isAbbrevMatch(curpos,cleanRT,startTextWords)

                curposGemara = iStartingWordInGemara + offsetWithinGemara + iWordWithinPhrase
                iStartContext = 3 if curposGemara >= 3 else curposGemara
                if fIsMatch:
                    abbrevMatch = AbbrevMatch(cleanRT, startTextWords[curpos:curpos + newOffsetWithinRashiCV + 1],
                                                   (curpos, curpos + newOffsetWithinRashiCV),
                                                   (curposGemara,curposGemara),
                                                   curDaf.allWords[curposGemara - iStartContext:curposGemara],
                                                   curDaf.allWords[curposGemara + 1:curposGemara + 4])
                    if not abbrevMatch in abbrev_matches:
                        abbrev_matches.append(abbrevMatch)
                offsetWithinRashiCV += newOffsetWithinRashiCV

                if not fIsMatch:
                    break
            else:
                # great, this is a basic compare.
                distance, fMatch = IsStringMatch(startTextWords[iWordWithinPhrase + offsetWithinRashiCV],
                                                 curDaf.allWords[
                                                       iStartingWordInGemara + offsetWithinGemara + iWordWithinPhrase],
                                                 char_threshold)
                totaldistance += distance
                # if these words don't match, break and this isn't a match.
                if not fMatch:
                    fIsMatch = False
                    break
            #except IndexError:
            #    continue
            iWordWithinPhrase += 1
        gemaraDifferential = offsetWithinRashiCV
        gemaraDifferential -= offsetWithinGemara

        # if it is, add it in!
        # else you didn't match the whole rashi b/c you got to the end of the daf too quickly
        if fIsMatch and iStartingWordInGemara + wordCountRashi - gemaraDifferential < wordCountGemara:

            curMatch = TextMatch()
            curMatch.textToMatch = curRashi.startingText
            curMatch.textMatched = BuildPhraseFromArray(curDaf.allWords, iStartingWordInGemara,
                                                        wordCountRashi - gemaraDifferential)
            curMatch.startWord = iStartingWordInGemara
            curMatch.endWord = iStartingWordInGemara + wordCountRashi - gemaraDifferential #I added the -1 b/c there was an off-by-one error

            #if we found an abbrev in gemara, save the words which matched in the TextMatch
            curMatch.abbrev_matches = abbrev_matches
            # calculate the score, adding in the penalty for abbreviation
            totaldistance += abbreviationPenalty
            normalizedDistance = 1.0*(totaldistance + smoothingFactor) / (len(startText) + smoothingFactor) * normalizingFactor
            curMatch.score = normalizedDistance


            allMatches.append(curMatch)

        iStartingWordInGemara += 1
    return allMatches


def GetAllApproximateMatchesWithWordSkip(curDaf, curRashi, startBound, endBound,char_threshold):  # GemaraDaf, RashiUnit,int,int,double
    global normalizingFactor
    allMatches = []
    usedStartwords = []

    startText = curRashi.startingTextNormalized
    wordCount = curRashi.cvWordcount

    # No point to this unless we have at least 2 words
    if wordCount < 2:
        return []

    skipOnlyOne = wordCount == 2


    # Iterate through all the starting words within the phrase, allowing for one word to be ignored

    for iWordToIgnore in xrange(-1, wordCount):
        rashiwords = re.split(ur"\s+", startText.strip())
        cvhashes = CalculateHashes(rashiwords)

        if iWordToIgnore >= 0:
            del cvhashes[iWordToIgnore]
            alternateStartText = GetStringWithRemovedWord(startText, iWordToIgnore).strip()

        else:
            alternateStartText = startText

        # Iterate through all possible starting words within the gemara, allowing for the word afterward to be ignored
        iWord = startBound
        while iWord <= len(curDaf.allWords) - wordCount and iWord + wordCount - 1 <= endBound:

            # Start from -1 (which means the phrase as is)
            for gemaraWordToIgnore in xrange(-1, wordCount):
                # no point in skipping first word - we might as well just let the item start from the next startword
                if gemaraWordToIgnore == 0:
                    continue

                # and, choose a second word to ignore (-1 means no second word)

                skipWord2End = 0 if skipOnlyOne else wordCount
                for gemaraWord2ToIgnore in xrange(-1, skipWord2End):

                    # if not skipping first, this is not relevant unless it is also -1
                    if gemaraWordToIgnore == -1 and gemaraWord2ToIgnore != -1:
                        continue

                    # we don't need to do things both directions
                    if iWordToIgnore != -1 and gemaraWord2ToIgnore != -1:
                        continue

                    # if we are skipping a cv word, don't also skip a second word
                    if iWordToIgnore != -1 and gemaraWord2ToIgnore != -1:
                        continue

                    # if this would bring us to the end, don't do it
                    if gemaraWord2ToIgnore != -1 and iWord + wordCount >= len(curDaf.allWords):
                        continue


                    fIsMatch = False
                    distance = 0
                    totaldistance = 0

                    if wordCount >= 4:
                        nonMatchAllowance = wordCount / 2 - 1

                        initialhash = cvhashes[0]

                        if curDaf.wordhashes[iWord] == initialhash:
                            # see if the rest match up
                            offset = 0
                            fIsMatch = True

                            for icvword in xrange(1, wordCount - 1):
                                if icvword == gemaraWordToIgnore or icvword == gemaraWord2ToIgnore:
                                    offset += 1

                                # check the hash, and or first letter


                                try:
                                    temp = curDaf.allWords[iWord + icvword + offset]
                                except IndexError:
                                    print "curDaf.allWords[iWord + icvword + offset][0]"




                                if curDaf.wordhashes[iWord + icvword + offset] != cvhashes[icvword] and \
                                                curDaf.allWords[iWord + icvword + offset][0] != rashiwords[icvword][0]:
                                    nonMatchAllowance -= 1

                                    if nonMatchAllowance < 0:
                                        fIsMatch = False
                                        break
                    else:
                        # build the phrase
                        targetPhrase = BuildPhraseFromArray(curDaf.allWords, iWord, wordCount, gemaraWordToIgnore,
                                                            gemaraWord2ToIgnore)

                        # Now check if it is a match
                        distance, fIsMatch = IsStringMatch(alternateStartText, targetPhrase, char_threshold)

                    # if it is, add it in
                    if fIsMatch:
                        if iWord in usedStartwords:
                            continue
                        curMatch = TextMatch()

                        # if gemaraWordToIgnore is -1, then we didn't skip anything in the gemara.
                        # if iWordToIgnore is -1, then we didn't skip anything in the main phrase

                        # whether or not we used the two-letter shortcut, let's calculate full distance here.
                        targetPhrase = BuildPhraseFromArray(curDaf.allWords, iWord, wordCount, gemaraWordToIgnore,
                                                            gemaraWord2ToIgnore)

                        dist = ComputeLevenshteinDistanceByWord(alternateStartText, targetPhrase)

                        # add penalty for skipped words
                        if gemaraWordToIgnore >= 0:
                            dist += fullWordValue
                        if gemaraWord2ToIgnore >= 0:
                            dist += fullWordValue
                        if iWordToIgnore >= 0:
                            dist += fullWordValue

                        normalizedDistance = 1.0*(dist + smoothingFactor) / (len(startText) + smoothingFactor) * normalizingFactor
                        curMatch.score = normalizedDistance
                        curMatch.textToMatch = curRashi.startingText

                        # the "text matched" is the actual text of the gemara, including the word we skipped.
                        curMatch.textMatched = BuildPhraseFromArray(curDaf.allWords, iWord, wordCount)
                        curMatch.startWord = iWord
                        curMatch.endWord = iWord + wordCount - 1
                        curMatch.skippedWords = [gemaraWordToIgnore,gemaraWord2ToIgnore]

                        # if we skipped the last word or two words, then we should cut them out of here
                        if gemaraWordToIgnore == wordCount - 2 and gemaraWord2ToIgnore == wordCount - 1:
                            curMatch.textMatched = BuildPhraseFromArray(curDaf.allWords, iWord, wordCount - 2)
                            curMatch.endWord -= 2
                        elif gemaraWordToIgnore == wordCount - 1:
                            curMatch.textMatched = BuildPhraseFromArray(curDaf.allWords, iWord, wordCount - 1)
                            curMatch.endWord -= 1

                        allMatches.append(curMatch)
                        usedStartwords.append(iWord)
                        break

            iWord += 1
    return allMatches

#done
def GetStringWithRemovedWord(p, iWordToIgnore):  # string,int
    # remove the word specified in iWordtoIgnore
    # if -1, return word as is
    if iWordToIgnore == -1:
        return p

    words = p.split(' ')
    ret = u""

    for i in xrange(len(words)):
        if i == iWordToIgnore:
            continue

        ret += words[i] + u" "

    return ret.strip()

#done
def BuildPhraseFromArray(allWords, iWord, leng, wordToSkip=-1, word2ToSkip=-1):  # list<string>,int,int,int,int
    phrase = u""
    for jump in xrange(leng):
        if jump == wordToSkip or jump == word2ToSkip:
            continue
        phrase += allWords[iWord + jump] + u" "

    return phrase.strip()

#done
def CountWords(s):
    pattern = re.compile(ur"\S+")
    return len(re.findall(pattern, s))

#done
def IsStringMatch(orig, target, threshold):  # string,string,double,out double
    # if our threshold is 0, just compare them one to eachother.
    if threshold == 0:
        score = 0
        return (score, orig == target)

    # if equal
    if orig == target:
        score = 0
        return (score, True)

    # wait: if one is a substring of the other, then that can be considered an almost perfect match
    if orig.startswith(target) or target.startswith(orig):
        score = -1
        return (score, True)

    # Otherwise, now we need to levenshtein.
    dist = ComputeLevenshteinDistance(orig, target)

    # Now get the actual threshold
    maxDist = mathy.ceil(len(orig) * threshold)

    score = dist

    # return if it is a matchup

    return (score, dist <= maxDist)


def cleanAbbrev(str):
    str = str.replace(u"\"", u"")
    str = u"".join([sofit_swap(c) for c in str])
    return str


def isAbbrevMatch(curpos, abbrevText, unabbrevText):
    maxAbbrevLen = len(abbrevText)
    isMatch = False

    abbrevPatterns = [[],[1],[2],[1,1],[2,1]]
    for comboList in abbrevPatterns:

        numWordsCombined = sum(comboList)
        if curpos + maxAbbrevLen <= len(unabbrevText) + numWordsCombined:
            if maxAbbrevLen > numWordsCombined + 1:
                isMatch = True

                prev_combo_sum = 0
                for i_combo,currCombo in enumerate(comboList):
                    if len(unabbrevText[curpos+i_combo]) <= currCombo+1 or unabbrevText[curpos+i_combo][:currCombo+1] != abbrevText[prev_combo_sum:prev_combo_sum+currCombo+1]:
                        isMatch = False
                        break
                    prev_combo_sum += currCombo+1

                for igemaraword in xrange(curpos + len(comboList), curpos + maxAbbrevLen - numWordsCombined):
                    if unabbrevText[igemaraword][0] != abbrevText[igemaraword - curpos + numWordsCombined]:
                        isMatch = False
                        break
                if isMatch:
                    return isMatch, maxAbbrevLen - (1 + numWordsCombined)
    """
    for numWordsCombined in xrange(0, 3):
        if curpos + maxAbbrevLen <= len(unabbrevText) + numWordsCombined:
            if maxAbbrevLen > numWordsCombined + 1 and len(unabbrevText[curpos]) > numWordsCombined:
                isMatch = True

                # combine up to `numWordsCombined+1` words together at the beginning of the abbreviation
                for tempoffset in xrange(0, numWordsCombined + 1):
                    if unabbrevText[curpos][tempoffset] != abbrevText[tempoffset]:
                        isMatch = False
                        break

                for igemaraword in xrange(curpos + (numWordsCombined > 0), curpos + maxAbbrevLen - numWordsCombined):
                    if unabbrevText[igemaraword][0] != abbrevText[igemaraword - curpos + numWordsCombined]:
                        isMatch = False
                        break
                if isMatch:
                    return isMatch, maxAbbrevLen - (1 + numWordsCombined)
    """
    return isMatch, 0


def GetRashiBoundaries(allRashi, dwRashi, maxBound,boundaryFlexibility):  # List<RashiUnit>, int
    # often Rashis overlap - e.g., first שבועות שתים שהן ארבע and then שתים and then שהן ארבע
    # so we can't always close off the boundaries
    # but sometimes we want to

    # maxbound is the number of words on the amud
    startBound = 0
    endBound = maxBound - 1

    prevMatchedRashi = -1
    nextMatchedRashi = len(allRashi)

    # Okay, look as much up as you can from iRashi to find the start bound

    for iRashi in xrange(dwRashi - 1, -1, -1):
        if  allRashi[iRashi].startWord == -1:
            continue
        prevMatchedRashi = iRashi
        # // Okay, this is our closest one on top that has a value
        # // allow it to overlap
        startBound = allRashi[iRashi].startWord
        break

    # // Second part, look down as much as possible to find the end bound
    for iRashi in xrange(dwRashi + 1, len(allRashi)):
        if allRashi[iRashi].startWord == -1 or allRashi[iRashi].startWord < startBound: #added startWord < startBound condition to avoid getting endBound which might be before startBound in the case when rashis matched out of order
            continue
        # // Okay, this is the closest one below that has a value
        # // our end bound will be the startword - 1.

        nextMatchedRashi = iRashi

        # allow it to overlap
        endBound = allRashi[iRashi].startWord

        break

    # Done!
    startBound = startBound - boundaryFlexibility if startBound - boundaryFlexibility >= 0 else startBound
    endBound = endBound + boundaryFlexibility if endBound + boundaryFlexibility < maxBound else endBound
    return startBound, endBound, prevMatchedRashi, nextMatchedRashi


def CleanText(curLine):  # string
    return re.sub(ur"</?[^>]+>", u"", curLine).strip()


def ComputeLevenshteinDistanceByWord(s, t):  # s and t are strings
    global fullWordValue
    # we take it word by word, each word can be, at most, the value of a full word

    words1 = s.split(' ')
    words2 = t.split(' ')

    totaldistance = 0

    for i in xrange(len(words1)):
        if i >= len(words2):
            totaldistance += fullWordValue
        else:
            # if equal, no distance
            if s == t:
                continue

            # wait: if one is a substring of the other, then that can be considered an almost perfect match
            # note: we changed this from the original c# code which was if (s.StartsWith(t) || t.StartsWith(s))
            if s.startswith(t) or t.startswith(s):
                totaldistance += 0.5

            totaldistance += min(ComputeLevenshteinDistance(words1[i], words2[i]), fullWordValue)

    return totaldistance

def ComputeLevenshteinDistance(s, t):
    '''n = len(s)
    m = len(t)
    d = [[0 for j in range(m + 1)] for i in range(n + 1)]

    # step 1
    if n == 0:
        return m

    if m == 0:
        return n

    # Step2
    for i in range(n+1):
        d[i][0] = i
    for j in range(m+1):
        d[0][j] = j

    # Step3

    for i in range(1,n+1):
        # step4
        for j in range(1,m+1):
            # step5
            cost = 0 if t[j - 1] == s[i - 1] else 1
            # step6
            d[i][j] = min(min(d[i - 1][j] + 1, d[i][j - 1] + 1), d[i - 1][j - 1] + cost)
    # Step7
    return d[n][m]'''
    return language_tools.weighted_levenshtein(s,t,language_tools.weighted_levenshtein_cost,min_cost=0.6)


def InitializeHashTables():
    global pregeneratedKWordValues,pregeneratedKMultiwordValues
    # Populate the pregenerated K values for the polynomial hash calculation
    pregeneratedKWordValues = [GetPolynomialKValueReal(i, kForWordHash) for i in xrange(NumPregeneratedValues)]
    # pregenerated K values for the multi word
    # these need to go from higher to lower, for the rolling algorithm
    # and we know that it will always be exactly 4
    pregeneratedKMultiwordValues = [GetPolynomialKValueReal(3 - i, kForMultiWordHash) for i in xrange(4)]


def CalculateHashes(allwords):  # input list
    return [GetWordSignature(w) for w in allwords]


def GetWordSignature(word):
    # make sure there is nothing but letters
    word = re.sub(ur"[^א-ת]", u"", word)
    word = Get2LetterForm(word)

    hash = 0
    alefint = ord(u"א")
    for i, char in enumerate(word):
        chval = ord(char)
        chval = chval - alefint + 1
        hash += (chval * GetPolynomialKWordValue(i))

    return hash


def GetNormalizedLetter(ch):
    if ch == u'ם':
        return u'מ'
    elif ch == u'ן':
        return u'נ'
    elif ch == u'ך':
        return u'כ'
    elif ch == u'ף':
        return u'פ'
    elif ch == u'ץ':
        return u'צ'
    else:
        return ch


def GetPolynomialKMultiWordValue(pos):
    global kForWordHash, NumPregeneratedValues, pregeneratedKMultiwordValues
    if pos < NumPregeneratedValues:
        return pregeneratedKMultiwordValues[pos]

    return GetPolynomialKValueReal(pos, kForMultiWordHash)


def GetPolynomialKWordValue(pos):
    global kForWordHash, NumPregeneratedValues, pregeneratedKWordValues
    if (pos < NumPregeneratedValues):
        return pregeneratedKWordValues[pos]

    return GetPolynomialKValueReal(pos, kForWordHash)


def GetPolynomialKValueReal(pos, k):
    # assuming that k is 41
    return k ** pos


def Get2LetterForm(stringy):
    if stringy == u"ר":
        return u"רב"

    if len(stringy) < 3:
        return stringy

    # take a word, and keep only the two most infrequent letters

    freqchart = [(lettersInOrderOfFrequency.index(GetNormalizedLetter(tempchar)), i) for i, tempchar in
                 enumerate(stringy)]

    # sort it descending, so the higher they are the more rare they are
    freqchart.sort(key=lambda freq: -freq[0])
    letter1 = freqchart[0][1]
    letter2 = freqchart[1][1]
    # now put those two most frequent letters in order according to where they are in the words
    return u"{}{}".format(stringy[letter1], stringy[letter2]) if letter1 < letter2 else u"{}{}".format(stringy[letter2],
                                                                                                    stringy[letter1])
def sofit_swap(C):
    return sofit_map[C] if C in sofit_map else C


#if it can get this, it can get anything
#print isAbbrevMatch(0,u'בחוהמ',[u'בחול',u'המועד'])