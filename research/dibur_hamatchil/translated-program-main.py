

fdebug = False
# constants for generating distance score. a 0 means a perfect match, although it will never be 0, due to the smoothing.
normalizingFactor = 100
smoothingFactor = 1
fullWordValue = 3
abbreviationPenalty = 1
ImaginaryContenderPerWord = 22

fUseSerializedData = False
fSerializeData = False

ourmod = 134217728
pregeneratedKWordValues = []
pregeneratedKMultiwordValues = []
NumPregeneratedValues = 20
kForWordHash = 41
kForMultiWordHash = 39
lettersInOrderOfFrequency = [ 'ו', 'י', 'א', 'מ', 'ה', 'ל', 'ר', 'נ', 'ב', 'ש', 'ת', 'ד', 'כ', 'ע', 'ח', 'ק', 'פ', 'ס', 'ז', 'ט', 'ג', 'צ' ]

def main(): #do everything
	#initialization
	InitializeHashTables()

	#first, set the base directory
	#note. this is obviously not right
	baseDir = "R:\\Avi\\data\\Dicta\\Sefaria-Gittin\\" 

	#First, get all the masechtot with rashi.
	allMasechtot = []
	if fUseSerializedData:
		allMasechtot = GetAllMasechtotWithRashiFromSerializedData(baseDir)
	else:
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
									elif temp_irashi.rashimatches[0].startWord == temp_jrashi.rashimatches[0].startWord):
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





'''

static void Main(string[] args) {

	// Iterate through the dapim
	foreach (GemaraDaf curDaf in allMasechtot[0].allDapim.Values) {

		while (rashisByDisambiguity.Count > 0) {

		sbreport.AppendLine("----------------------------------------------");
		sbreport.AppendLine(curDaf.dafLocation);
		sbreport.AppendLine("----------------------------------------------");
		// now do a full report
		for (int i = 0; i < curDaf.allRashi.Count; i++) {
			RashiUnit ru = curDaf.allRashi[i];
			if (ru.startWord == -1) {
				sbreport.AppendLine("UNMATCHED: " + ru.startingText);
			}
			else {
				sbreport.AppendLine(ru.startingText + " //" + ru.matchedGemaraText + "[" + ru.startWord + "-" + ru.endWord + "]");
			}
		}
	}
	string s = sbreport.ToString();
}








'''