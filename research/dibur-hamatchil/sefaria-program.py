# -*- coding: utf-8 -*-
import re
import math as mathy
from os import listdir
from os.path import isfile, join
from sefaria.model import *

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
lettersInOrderOfFrequency = [ 'ו', 'י', 'א', 'מ', 'ה', 'ל', 'ר', 'נ', 'ב', 'ש', 'ת', 'ד', 'כ', 'ע', 'ח', 'ק', 'פ', 'ס', 'ז', 'ט', 'ג', 'צ' ]


class TextMatch:
    def __init__(self):
        self.textToMatch = ""
        self.textMatched = ""
        self.startWord = 0
        self.endWord = 0
        self.score = 0


# should be private?
class GemaraMasechet:
    def __init__(self):
        self.masechetNameEng = ""
        self.masechetNameHeb = ""
        self.allDapim = {}  # string -> GemaraDaf


# should be private?
class GemaraDaf:
    def __init__(self):
        self.dafLocation = ""
        self.gemaraText = ""
        self.allWords = []  # string
        self.wordhashes = []
        self.allRashi = []  # list of RashiUnit


class RashiUnit:
    def __init__(self):
        self.place = 0
        self.disambiguationScore = 0
        self.rashimatches = []  # list of TextMatch
        self.startingText = ""
        self.startingTextNormalized = ""
        self.fullText = ""
        self.valueText = ""
        self.startWord = -1
        self.endWord = -1
        self.lineN = 0
        self.cvWordcount = 0
        self.matchedGemaraText = ""


def main(): #do everything
    InitializeHashTables()

    #first, set the base directory
    #note. this is obviously not right
    baseDir = "R:\\Avi\\data\\Dicta\\Sefaria-Gittin\\"

    #First, get all the masechtot with rashi.
    allMasechtot = GetAllMasechtotWithRashi(baseDir)

    sbreport = "NewMasechet: " + allMasechtot[0].masechetNameEng

    #Iterate through the dapim
    #note. change to go through all masechtot
    for curDaf in allMasechtot[0].allDapim:
        print "\n{}".format(curDaf.dafLocation)

        #calculate hashes for the gemara words
        curDaf.wordhashes = CalculateHashes(curDaf.allWords)

        #now we go through each rashi, and find all potential matches for each, with a rating
        for irashi,ru in enumerate(curDaf.allRashi):

            #give it a number so we know the order
            #note. this should be done in the constructor of RashiUnit
            ru.place = irashi

            endword = len(curDaf.allWords)
            approxMatches = GetAllApproximateMatches(curDaf,ru,0,endword,.2)
            approxAbbrevMatches = GetAllApproximateMatchesWithAbbrev(curDaf, ru, 0, endword, .2)
            approxSkipWordMatches = GetAllApproximateMatchesWithWordSkip(curDaf, ru, 0, endword, .2)

            ru.rashimatches += approxMatches + approxAbbrevMatches

            #only add skip-matches that don't overlap with existing matching
            foundpoints = []
            for tm in ru.rashimatches:
                foundpoints.append(tm.startWord)
            # for the skip words, of course, it may find items that are one-off or two-off from the actual match. Filter these out
            for tm in approxSkipWordMatches:
                startword = tm.startWord
                if startword in foundpoints or startword - 1 in foundpoints or startword + 1 in foundpoints:
                    continue
                ru.rashimatches.append(tm)

            #sort the rashis by score
            sorted(ru.rashimatches,key=lambda x: x.score) #note: check this works

            #now figure out disambiguation score
            CalculateAndFillInDisambiguity(ru)

        #let's make a list of our rashis in disambiguity order
        rashisByDisambiguity = curdDaf.allRashi[:] # note: check if this is what he wanted. List<RashiUnit> rashisByDisambiguity = new List<RashiUnit>(curDaf.allRashi);
        sorted(rashisByDisambiguity,key=lambda x: -x.disambiguationScore ) #note: check that this is sorting in the right order. rashisByDisambiguity.Sort((x, y) => y.disambiguationScore.CompareTo(x.disambiguationScore));

        #remove any rashis that have no matches at all
        for irashi,temp_rashi in enumerate(reversed(rashisByDisambiguity)):
            if len(temp_rashi.rashimatches) == 0:
                del rashisByDisambiguity[irashi]

        while len(rashisByDisambiguity) > 0:
            #take top disambiguous rashi
            topru = rashisByDisambiguity[0]

            #get its boundaries
            startBound,endBound,prevMatchedRashi,nextMatchedRashi = GetRashiBoundaries(curDaf.allRashi,topru.place,len(curDaf.allWords))

            #take the first bunch in order of disambiguity and put them in
            highestrating = topru.disambiguationScore
            #if we're up to 0 disambiguity, rate them in terms of their plac in the amud
            if (highestrating == 0):
                for curru in rashisByDisambiguity:
                    #figure out how many are tied, or at least within 5 of each other
                    topscore = curru.rashimatches[0].score
                    tobesorted = []
                    for temp_rashimatchi in curru.rashimatches:
                        if temp_rashimatchi.score == topscore:
                            #this is one of the top matches, and should be sorted
                            tobesorted.append(temp_rashimatchi)

                    #sort those top rashis by place
                    sorted(tobesorted,key=lambda x: x.startWord)
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
            sorted(ruToProcess,key=lambda x: x.place)

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
                    if best_rashi.startword < prevstartpos:
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
                            sorted(ruToProcess,key=lambda x: -x.disambiguationScore)
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
                                sorted(ruToProcess, key = lambda x: -x.disambiguationScore)
                                del ruToProcess[1]
                    else:
                        outoforder = [0 for i in range(ruToProcess)]
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
                        for irashi in reversed(range(len(ruToProcess))):
                            if outoforder[irashi] == highestDeviation and len(ruToProcess) > 1:
                                del ruToProcess[irashi]
            #TODO: deal with the case of only 2 in ruToProcess in a smarter way


            #by this point they are all in order, so we can put them all in
            for curru in ruToProcess:
                # put it in
                #TODO: if disambiguity is low, apply other criteria
                match = curru.rashimatches[0]
                curru.startWord = match.startWord
                curru.endWord = match.endWord
                curru.matchedGemaraText = match.textMatched
                # remove this guy from the disambiguities, now that it is matched up
                rashisByDisambiguity.remove(curru) #check remove
                #recalculate the disambiguities for all those who were potentially relevant, based on this one's place
                RecalculateDisambiguities(curDaf.allRashi, rashisByDisambiguity, prevMatchedRashi, nextMatchedRashi, startBound, endBound, curru)

            #resort the disambiguity array
            sorted (rashisByDisambiguity,key = lambda x: -x.disambiguationScore)

        unmatched = CountUnmatchedUpRashi(curDaf)
        #now we check for dapim that have a lot of unmatched items, and then we take items out one at a time to see if we can
        #minimize it because usually this results from one misplaced item.

        sbreport += "\n----------------------------------------------"
        sbreport += "\n{}".format(curDaf.dafLocation)
        sbreport += "\n----------------------------------------------"

        #now do a full report
        for ru in curDaf.allRashi:
            if ru.startWord == -1:
                sbreport += "\nUNMATCHED: {}".format(ru.startingText)
            else:
                sbreport += "\n{} //{}[{}-{}]".format(ru.startingText,ru.matchedGemaraText,ru.startWord,ru.endWord)

    #note. presumably we should print out sbreport here...


def RecalculateDisambiguities(allRashis, rashisByDisambiguity, prevMatchedRashi, nextMatchedRashi, startbound, endbound,
                              newlyMatchedRashiUnit):  # List<RashiUnit>,List<RashiUnit>,int,int,int,int,RashiUnit
    for irashi in range(len(rashisByDisambiguity) - 1, -1, -1):
        ru = rashisByDisambiguity[irashi]
        if ru.place <= prevMatchedRashi or ru.place >= nextMatchedRashi or ru.place == newlyMatchedRashiUnit.place:
            continue
        # this rashi falls out somewhere inside the current window, either before the newest match or after the newest match
        localstartbound = (ru.place < newlyMatchedRashiUnit.place) if startbound else newlyMatchedRashiUnit.startWord
        localendbound = (ru.place > newlyMatchedRashiUnit.place) if endbound else newlyMatchedRashiUnit.startWord

        # now remove any potential matches that are blocked by the newly matched rashi
        for imatch in range(len(ru.rashimatches) - 1, -1, -1):
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
                             threshold):  # inputs (GemaraDaf, RashiUnit, int, int, double)
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
            cvhashes = CalculateHashes(re.split(r"\s+", startText.strip()))
            initialhash = cvhashes[0]

            if curDaf.wordhashes[iWord] == initialhash:
                # see if the rest match up
                mismatches = 0

                for icvword in range(1, wordCount):
                    if curDaf.wordhashes[iWord + icvword] != cvhashes[icvword]:
                        mismatches += 1

                # now we need to decide if we can let it go
                allowedMismatches = mathy.ceil(wordCount * threshold * 1.35)
                if mismatches <= allowedMismatches:
                    distance = mismatches
                    fIsMatch = True

        else:
            # build the phrase
            targetPhrase = BuildPhraseFromArray(curDaf.allWords, iWord, wordCount)

            # now check if it is a match
            distance, fIsMatch = IsStringMatchup(startText, targetPhrase, threshold)

        # if it is, add it in
        if fIsMatch:
            curMatch = TextMatch()
            curMatch.textToMatch = curRashi.startingText;
            curMatch.textMatched = BuildPhraseFromArray(curDaf.allWords, iWord, wordCount);
            curMatch.startWord = iWord;
            curMatch.endWord = iWord + wordCount - 1;

            # calculate the score - how distant is it
            dist = ComputeLevenshteinDistanceByWord(startText, curMatch.textMatched)
            normalizedDistance = int(
                ((dist + smoothingFactor) / (len(startText) + smoothingFactor) * normalizingFactor))
            curMatch.score = normalizedDistance

            allMatches.append(curMatch)
        iWord += 1

    return allMatches


def GetAllApproximateMatchesWithAbbrev(curDaf, curRashi, startBound, endBound,
                                       threshold):  # inputs (GemaraDaf, RashiUnit, int, int, double)
    allMatches = []
    startText = curRashi.startingTextNormalized
    wordCount = curRashi.cvWordcount
    if wordCount == 0:
        return allMatches

    # convert string into an array of words
    startTextWords = re.split(r"\s+", startText)

    # go through all possible starting words in the gemara text

    iStartingWordInGemara = startBound
    while iStartingWordInGemara <= curDaf.allWords.Count - wordCount and iStartingWordInGemara + wordCount - 1 <= endBound:
        fIsMatch = false;
        offsetWithinGemara = 0;
        offsetWithinRashiCV = 0;
        distance = 0;
        totaldistance = 0;

        # now we loop according to the number of words in the cv
        # .. keep track of how the gemara text differs from rashi length
        gemaraDifferential = 0

        for iWordWithinPhrase in range(0, wordCount - offsetWithinRashiCV):
            # first check if the cv word has a quotemark
            if "\"" in startTextWords[iWordWithinPhrase + offsetWithinRashiCV]:
                # get our ראשי תיבות word without the quote mark
                cleanRT = startTextWords[iWordWithinPhrase + offsetWithinRashiCV].replace("\"", "")
                maxlen = len(cleanRT)

                # let's see if this matches the start of the next few words
                curpos = iStartingWordInGemara + iWordWithinPhrase + offsetWithinGemara
                fIsMatch = False

                if curpos + maxlen <= len(curDaf.allWords):
                    fIsMatch = True
                    for igemaraword in range(curpos, curpos + maxlen):
                        if curDaf.allWords[igemaraword][0] != cleanRT[igemaraword - curpos]:
                            fIsMatch = False
                            break

                    if fIsMatch:
                        # we condensed maxlen words into 1. minus one, because later we'll increment one.
                        offsetWithinGemara += maxlen - 1

                # let's see if we can match by combining the first two into one word
                if curpos + maxlen <= len(curDaf.allWords) + 1:
                    if not fIsMatch and maxlen > 2:
                        fIsMatch = True
                        if len(curDaf.allWords[curpos]) < 2 or curDaf.allWords[curpos][0] != cleanRT[0] or \
                                        curDaf.allWords[curpos][1] != cleanRT[1]:
                            fIsMatch = False
                        else:
                            for igemaraword in range(curpos + 1, curpos + maxlen - 1):
                                if curDaf.allWords[igemaraword][0] != cleanRT[igemaraword - curpos + 1]:
                                    fIsMatch = False
                                    break
                        if fIsMatch:
                            # we condensed maxlen words into 1. minus one, because later we'll increment one.
                            offsetWithinGemara += maxlen - 2

                # let's see if we can match by combining the first three into one word
                if curpos + maxlen <= len(curDaf.allWords) + 2:
                    if not fIsMatch and maxlen > 3:
                        fIsMatch = True

                        if len(curDaf.allWords[curpos]) < 3 or curDaf.allWords[curpos][0] != cleanRT[0] or \
                                        curDaf.allWords[curpos][1] != cleanRT[1] or curDaf.allWords[curpos][2] != \
                                cleanRT[2]:
                            fIsMatch = False
                        else:
                            for igemaraword in range(curpos + 1, curpos + maxlen - 2):
                                if curDaf.allWords[igemaraword][0] != cleanRT[igemaraword - curpos + 2]:
                                    fIsMatch = False
                                    break
                        if fIsMatch:
                            # we condensed maxlen words into 1. minus one, because later we'll increment one.
                            offsetWithinGemara += maxlen - 3

                if not fIsMatch:
                    break

            # now increment the offset to correspond, so that we'll know we're skipping over x number of words
            elif "\"" in curDaf.allWords[iStartingWordInGemara + offsetWithinGemara + iWordWithinPhrase]:
                # get our ראשי תיבות word without the quote mark
                cleanRT = curDaf.allWords[iStartingWordInGemara + offsetWithinGemara + iWordWithinPhrase].replace("\"",
                                                                                                                  "")
                maxlen = len(cleanRT)

                # let's see if this matches the start of the next few words
                curpos = iWordWithinPhrase + offsetWithinRashiCV
                fIsMatch = False

                # note. these next three if statements can be made into a function
                if curpos + maxlen <= wordCount:
                    fIsMatch = True
                    for icvword in range(curpos, curpos + maxlen):
                        if startTextWords[icvword][0] != cleanRT[icvword - curpos]:
                            fIsMatch = False
                            break

                    if fIsMatch:
                        # we condensed maxlen words into 1. minus one, because later we'll increment one.
                        offsetWithinRashiCV += maxlen - 1

                # let's see if we can match by combining the first two into one word
                if curpos + maxlen <= wordCount + 1:
                    if not fIsMatch and maxlen > 2:
                        fIsMatch = True
                        if len(startTextWords[curpos]) < 2 or startTextWords[curpos][0] != cleanRT[0] or \
                                        startTextWords[curpos][1] != cleanRT[1]:
                            fIsMatch = False
                        else:
                            for icvword in range(curpos + 1, curpos + maxlen - 1):
                                if startTextWords[icvword][0] != cleanRT[icvword - curpos + 1]:
                                    fIsMatch = False
                                    break
                        if fIsMatch:
                            # we condensed maxlen words into 1. minus one, because later we'll increment one.
                            offsetWithinRashiCV += maxlen - 2
                # let's see if we can match by combining the first three into one word
                if curpos + maxlen <= wordCount + 2:
                    if not fIsMatch and maxlen > 3:
                        fIsMatch = True
                        if len(startTextWords[curpos]) < 3 or startTextWords[curpos][0] != cleanRT[0] or \
                                        startTextWords[curpos][1] != cleanRT[1] or startTextWords[curpos][2] != cleanRT[
                            2]:
                            fIsMatch = False
                        else:
                            for icvword in range(curpos + 1, curpos + maxlen - 2):
                                if startTextWords[icvword][0] != cleanRT[icvword - curpos + 2]:
                                    fIsMatch = False
                                    break
                        if fIsMatch:
                            # we condensed maxlen words into 1. minus one, because later we'll increment one.
                            offsetWithinRashiCV += maxlen - 3
                if not fIsMatch:
                    break
            else:
                # great, this is a basic compare.
                distance, fMatch = IsStringMatchup(startTextWords[iWordWithinPhrase + offsetWithinRashiCV],
                                                   curDaf.allWords[
                                                       iStartingWordInGemara + offsetWithinGemara + iWordWithinPhrase],
                                                   threshold)
                totaldistance += distance
                # if these words don't match, break and this isn't a match.
                if not fMatch:
                    fMatch = False
                    break
        gemaraDifferential = offsetWithinRashiCV
        gemaraDifferential -= offsetWithinGemara

        # if it is, add it in
        if fIsMatch:
            curMatch = TextMatch()
            curMatch.textToMatch = curRashi.startingText
            curMatch.textMatched = BuildPhraseFromArray(curDaf.allWords, iStartingWordInGemara,
                                                        wordCount - gemaraDifferential)
            curMatch.startWord = iStartingWordInGemara
            curMatch.endWord = iStartingWordInGemara + wordCount - gemaraDifferential

            # calculate the score, adding in the penalty for abbreviation
            totaldistance += abbreviationPenalty
            normalizedDistance = int(
                ((totaldistance + smoothingFactor) / (len(startText) + smoothingFactor) * normalizingFactor))
            curMatch.score = normalizedDistance

            allMatches.append(curMatch)

        iStartingWordInGemara += 1
    return allMatches


def GetAllApproximateMatchesWithWordSkip(curDaf, curRashi, startBound, endBound,
                                         threshold):  # GemaraDaf, RashiUnit,int,int,double
    allMatches = []
    usedStartwords = []

    startText = curRashi.startingTextNormalized
    wordCount = curRashi.cvWordcount

    # No point to this unless we have at least 2 words
    if wordCount < 2:
        return []

    # Iterate through all the starting words within the phrase, allowing for one word to be ignored

    for iWordToIgnore in range(-1, wordCount):
        rashiwords = re.split(r"\s+", startText.strip())
        cvhashes = CalculateHashes(rashiwords)

        alternateStartText = ""
        if iWordtoIgnore >= 0:
            del cvhashes[iWordtoIgnore]
            alternateStartText = GetStringWithRemovedWord(startText, iWordToIgnore).strip()

        else:
            alternateStartText = startText

        # Iterate through all possible starting words within the gemara, allowing for the word afterward to be ignored
        iWord = startBound
        while iWord <= len(curDaf.allWords) - wordCount and iWord + wordCount - 1 <= endBound:

            # Start from -1 (which means the phrase as is)
            for gemaraWordToIgnore in range(-1, wordCount):
                # no point in skipping first word - we might as well just let the item start from the next startword
                if gemaraWordToIgnore == 0:
                    continue

                # and, choose a second word to ignore (-1 means no second word)
                for gemaraWord2ToIgnore in range(-1, wordCount):

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

                            for icvword in range(1, wordCount - 1):
                                if icvword == gemaraWordToIgnore or icvword == gemaraWord2ToIgnore:
                                    offset += 1

                                # check the hash, and or first letter
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
                        distance, fIsMatch = IsStringMatchup(alternateStartText, targetPhrase, threshold)

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
                        if iWordtoIgnore >= 0:
                            dist += fullWordValue

                        normalizedDistance = int(
                            (dist + smoothingFactor) / (len(startText) + smoothingFactor) * normalizingFactor)
                        curMatch.score = normalizedDistance
                        curMatch.textToMatch = curRashi.startingText

                        # the "text matched" is the actual text of the gemara, including the word we skipped.
                        curMatch.textMatched = BuildPhraseFromArray(curDaf.allWords, iWord, wordCount)
                        curMatch.startWord = iWord
                        curMatch.endWord = iWord + wordCount - 1

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


def GetStringWithRemovedWord(p, iWordToIgnore):  # string,int
    # remove the word specified in iWordtoIgnore
    # if -1, return word as is
    if iWordtoIgnore == -1:
        return p

    words = p.split(' ')
    ret = ""

    for i in range(len(words)):
        if i == iWordToIgnore:
            continue

        ret += words[i] + " "

    return ret.strip()


def BuildPhraseFromArray(allWords, iWord, leng, wordToSkip=-1, word2ToSkip=-1):  # list<string>,int,int,int,int
    phrase = ""
    for jump in range(leng):
        if jump == wordToSkip or jump == word2ToSkip:
            continue
        phrase += allWords[iWord + jump] + " "

    return phrase.strip()


def CountWords(s):
    pattern = re.compile(r"\S+")
    return len(re.findall(pattern, s))


def IsStringMatchup(orig, target, threshold):  # string,string,double,out double
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


def GetRashiBoundaries(allRashi, dwRashi, maxBound):  # List<RashiUnit>, int
    # often Rashis overlap - e.g., first שבועות שתים שהן ארבע and then שתים and then שהן ארבע
    # so we can't always close off the boundaries
    # but sometimes we want to

    # maxbound is the number of words on the amud
    startBound = 0
    endBound = maxBound - 1

    prevMatchedRashi = -1
    nextMatchedRashi = len(allRashi)

    # Okay, look as much up as you can from iRashi to find the start bound

    for iRashi in range(dwRashi - 1, -1, -1):
        if allRashi[iRashi].startWord == -1:
            continue
        prevMatchedRashi = iRashi
        # // Okay, this is our closest one on top that has a value
        # // allow it to overlap
        startBound = allRashi[iRashi].startWord
        break

    # // Second part, look down as much as possible to find the end bound
    for iRashi in range(dwRashi + 1, len(allRashi)):
        if allRashi[iRashi].startWord == -1:
            continue
        # // Okay, this is the closest one below that has a value
        # // our end bound will be the startword - 1.

        nextMatchedRashi = iRashi

        # allow it to overlap
        endBound = allRashi[iRashi].startWord

        break

    # Done!
    return startBound, endBound, prevMatchedRashi, nextMatchedRashi



def GetAllMasechtotWithRashi():  # string input
    allMesechtot = {}
    return allMasechtot.keys()


def CleanText(curLine):  # string
    return re.sub("</?[^>]+>", "", curLine)


def ComputeLevenshteinDistanceByWord(s, t):  # s and t are strings

    # we take it word by word, each word can be, at most, the value of a full word

    words1 = s.split(' ')
    words2 = t.split(' ')

    totaldistance = 0

    for i in range(len(words1)):
        if i >= len(words2):
            totaldistance += fullWordValue
        else:
            # if equal, no distance
            if s == t:
                continue

            # wait: if one is a substring of the other, then that can be considered an almost perfect match
            # note: we changed this from the original c# code which was if (s.StartsWith(t) || t.StartsWith(s))
            if s in t or t in s:
                totaldistance += 0.5

            totaldistance += min(ComputeLevenshteinDistance(words1[i], words2[i]), fullWordValue)

    return totaldistance


def ComputeLevenshteinDistance(s, t):
    n = len(s)
    m = len(t)
    d = [[0 for j in range(m + 1)] for i in range(n + 1)]

    # step 1
    if n == 0:
        return m

    if m == 0:
        return n

    # Step2
    for i in range(n):
        d[i][0] = i
    for j in range(m):
        d[0][j] = j

    # Step3

    for i in range(n):
        # step4
        for j in range(m):
            # step5
            cost = 0 if t[j - 1] == s[i - 1] else 1
            # step6
            d[i][j] = min(min(d[i - 1][j] + 1, d[i][j - 1] + 1), d[i - 1][j - 1] + cost)
    # Step7
    return d[n][m]


def InitializeHashTables():
    # Populate the pregenerated K values for the polynomial hash calculation
    pregeneratedKWordValues = [GetPolynomialKValueReal(i, kForWordHash) for i in range(NumPregeneratedValues)]
    # pregenerated K values for the multi word
    # these need to go from higher to lower, for the rolling algorithm
    # and we know that it will always be exactly 4
    pregeneratedKMultiwordValues = [GetPolynomialKValueReal(3 - i, kForMultiWordHash) for i in range(4)]


def CalculateHashes(allwords):  # input list
    return [GetWordSignature(w) for w in allwords]


def GetWordSignature(word):
    # make sure there is nothing but letters
    word = re.sub(r"[^א-ת]", "", word)
    word = Get2LetterForm(word)

    hash = 0
    alefint = ord("א".decode('utf-8'))
    for i, char in enumerate(word):
        chval = ord(char.decode('utf-8'))
        chval = chaval - alefint + 1
        hash += (chval * GetPolynomialKWordValue(i))

    return hash


def GetNormalizedLetter(ch):
    if ch == 'ם':
        return 'מ'
    elif ch == 'ן':
        return 'נ'
    elif ch == 'ך':
        return 'כ'
    elif ch == 'ף':
        return 'פ'
    elif ch == 'ץ':
        return 'צ'
    else:
        return ch


def GetPolynomialKMultiWordValue(pos):
    if pos < NumPregeneratedValues:
        return pregeneratedKMultiwordValues[pos]

    return GetPolynomialKValueReal(pos, kForMultiWordHash)


def GetPolynomialKWordValue(pos):
    if (pos < NumPregeneratedValues):
        return pregeneratedKWordValues[pos]

    return GetPolynomialKValueReal(pos, kForWordHash)


def GetPolynomialKValueReal(pos, k):
    if pos == 0:
        return 1
    # assuming that k is 41

    ret = (k ** 2) ** (pos - 1) if k > 1 else k
    return ret


def Get2LetterForm(stringy):
    if string == "ר":
        return "רב"

    if len(stringy) < 3:
        return stringy

    # take a word, and keep only the two most infrequent letters

    freqchart = [(lettersInOrderOfFrequency.index(GetNormalizedLetter(tempchar)), i) for i, tempchar in
                 enumerate(stringy)]

    # sort it descending, so the higher they are the more rare they are
    sorted(freqchart, key=lambda freq: -freq[0])
    letter1 = freqchart[0][1]
    letter2 = freqchart[1][1]
    # now put those two most frequent letters in order according to where they are in the words
    return "{}{}".format(stringy[letter1], string[letter2]) if letter1 < letter2 else "{}{}".format(stringy[letter2],
                                                                                                    string[letter1])
