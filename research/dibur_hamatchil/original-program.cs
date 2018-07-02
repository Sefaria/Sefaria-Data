using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Net.Configuration;
using System.Net.Mime;
using System.Runtime.InteropServices;
using System.Runtime.Serialization.Formatters.Binary;
using System.Text;
using System.Threading.Tasks;
using System.IO;
using System.Text.RegularExpressions;

namespace DibburHamatchilMatcher {
	class Program {

		public const bool fdebug = false;

		// constants for generating distance score. a 0 means a perfect match, although it will never be 0, due to the smoothing.
		public const int normalizingFactor = 100;
		public const int smoothingFactor = 1;
		public const int fullWordValue = 3;
		public const int abbreviationPenalty = 1;
		public const int ImaginaryContenderPerWord = 22;


		public const bool fUseSerializedData = false;
		public const bool fSerializeData = false;


		public const int ourmod = 134217728;
		public static long[] pregeneratedKWordValues;
		public static long[] pregeneratedKMultiwordValues;
		public const int NumPregeneratedValues = 20;
		public const int kForWordHash = 41;
		public const int kForMultiWordHash = 39;
		public static List<char> lettersInOrderOfFrequency = new List<char> { 'ו', 'י', 'א', 'מ', 'ה', 'ל', 'ר', 'נ', 'ב', 'ש', 'ת', 'ד', 'כ', 'ע', 'ח', 'ק', 'פ', 'ס', 'ז', 'ט', 'ג', 'צ' };

		// debug
		public static int gdebugiteration = 0;

		static void Main(string[] args) {

			// Initialization
			InitializeHashTables();

			// first, set the base directory
			//string baseDir = @"R:\Avi\data\Dicta\Searia\";
			string baseDir = @"R:\Avi\data\Dicta\Sefaria-Gittin\";

			// First, get all the masechtot with rashi.
			List<GemaraMasechet> allMasechtot;
			if (fUseSerializedData)
				allMasechtot = GetAllMasechtotWithRashiFromSerializedData(baseDir);
			else
				allMasechtot = GetAllMasechtotWithRashi(baseDir);

			StringBuilder sbreport = new StringBuilder();
			sbreport.AppendLine("NewMasechet: " + allMasechtot[0].masechetNameEng);

			// Iterate through the dapim
			foreach (GemaraDaf curDaf in allMasechtot[0].allDapim.Values) {

				Console.Write("\r" + curDaf.dafLocation);

				// calculate hashes for the gemara words
				curDaf.wordhashes = CalculateHashes(curDaf.allWords);

				// now we go through each rashi, and find all potential matches for each, with a rating
				for (int irashi = 0; irashi < curDaf.allRashi.Count; irashi++) {
					RashiUnit ru = curDaf.allRashi[irashi];

					// give it a number so we know the order
					ru.place = irashi;

					int endword = curDaf.allWords.Count;

					List<TextMatch> approxMatches = GetAllApproximateMatches(curDaf, ru, 0, endword, .2);
					List<TextMatch> approxAbbrevMatches = GetAllApproximateMatchesWithAbbrev(curDaf, ru, 0, endword, .2);
					List<TextMatch> approxSkipWordMatches = GetAllApproximateMatchesWithWordSkip(curDaf, ru, 0, endword, .2);

					ru.rashimatches.AddRange(approxMatches);
					ru.rashimatches.AddRange(approxAbbrevMatches);
					
					// only add skip-matches that don't overlap with existing matching
					List<int> foundpoints = new List<int>();
					foreach (TextMatch tm in ru.rashimatches) {
						foundpoints.Add(tm.startWord);
					}

					// for the skip words, of course, it may find items that are one-off or two-off from the actual match. Filter these out
					foreach (TextMatch tm in approxSkipWordMatches) {
						int startword = tm.startWord;
						if (foundpoints.Contains(startword) || foundpoints.Contains(startword - 1) || foundpoints.Contains(startword + 1))
							continue;
						ru.rashimatches.Add(tm);
					}

					// sort the rashis by score
					ru.rashimatches.Sort((x, y) => x.score.CompareTo(y.score));

					// now figure out disambiguation score
					CalculateAndFillInDisambiguity(ru);
				}

				// let's make a list of our rashis in disambiguity order
				List<RashiUnit> rashisByDisambiguity = new List<RashiUnit>(curDaf.allRashi);
				rashisByDisambiguity.Sort((x, y) => y.disambiguationScore.CompareTo(x.disambiguationScore));

				// remove any rashis that have no matches at all
				for (int irashi = rashisByDisambiguity.Count - 1; irashi >= 0; irashi--) {
					if (rashisByDisambiguity[irashi].rashimatches.Count == 0)
						rashisByDisambiguity.RemoveAt(irashi);
				}

				while (rashisByDisambiguity.Count > 0) {

					gdebugiteration++;
					if (gdebugiteration == 50) {
					}

					// take top disambiguous rashi
					RashiUnit topru = rashisByDisambiguity[0];

					// get its boundaries
					int startBound = -1, endBound = -1, prevMatchedRashi = -1, nextMatchedRashi = -1;
					GetRashiBoundaries(curDaf.allRashi, topru.place, ref startBound, ref endBound, ref prevMatchedRashi, ref nextMatchedRashi, maxBound: curDaf.allWords.Count);

					// take the first bunch in order of disambiguity and put them in

					int highestrating = topru.disambiguationScore;
					if (highestrating < 0) {
						
					}

					// if we're up to 0 disambiguity, rate them in terms of their place in the amud
					if (highestrating == 0) {

						for (int irashi = 0; irashi < rashisByDisambiguity.Count; irashi++) {

							RashiUnit curru = rashisByDisambiguity[irashi];

							// figure out how many are tied, or at least within 5 of each other
							int topscore = rashisByDisambiguity[irashi].rashimatches[0].score;
							//int thresholdlocal = topscore + 5;

							List<TextMatch> tobesorted = new List<TextMatch>();
							for (int imatch = 0; imatch < curru.rashimatches.Count; imatch++) {
								if (curru.rashimatches[imatch].score == topscore) {
									// this is one of the top matches, and should be sorted
									tobesorted.Add(curru.rashimatches[imatch]);
								}
							}

							// sort those top rashis by place
							tobesorted.Sort((x,y) => x.startWord.CompareTo(y.startWord));

							// now add in the rest
							for (int imatch = tobesorted.Count; imatch < curru.rashimatches.Count; imatch++) {
								tobesorted.Add(curru.rashimatches[imatch]);
							}

							// put them all in
							curru.rashimatches = tobesorted;
						}
					}



					// .. debuggigng
					int lowestrating = -1;
					List<RashiUnit> rashiUnitsCandidates = new List<RashiUnit>();
					//List<RashiUnit> ruToProcess = new List<RashiUnit>();
					for (int irashi = 0; irashi < rashisByDisambiguity.Count; irashi++) {

						RashiUnit ru = rashisByDisambiguity[irashi];

						// if this is outside the region, chuck it
						// the rashi are coming in in a completely diff order, hence we need to check each one
						if (ru.place <= prevMatchedRashi || ru.place >= nextMatchedRashi)
							continue;


						//if (ru.disambiguationScore < (highestrating/2))
						//	break;

						rashiUnitsCandidates.Add(ru);
						//if (ruToProcess.Count == 5)
						//	break;
					}

					// now we figure out how many of these we want to process
					// we want to take the top three at the least, seven at most, and anything that fits into the current threshold.
					
					List<RashiUnit> ruToProcess = new List<RashiUnit>();
					int threshold = Math.Max(rashiUnitsCandidates[0].disambiguationScore - 5, rashiUnitsCandidates[0].disambiguationScore/2);
					int thresholdBediavad = rashiUnitsCandidates[0].disambiguationScore / 2;
					for (int irashi = 0; irashi < rashiUnitsCandidates.Count; irashi++) {
						RashiUnit ru = rashiUnitsCandidates[irashi];
						int curScore = rashiUnitsCandidates[irashi].disambiguationScore;

						if (curScore >= threshold || (ruToProcess.Count < 3 && curScore >= thresholdBediavad)) {
							ruToProcess.Add(rashiUnitsCandidates[irashi]);

							if (highestrating == -1 || ru.disambiguationScore > highestrating)
								highestrating = ru.disambiguationScore;
							if (lowestrating == -1 || ru.disambiguationScore < lowestrating)
								lowestrating = ru.disambiguationScore;
						}
						else {
							break;
						}

						if (ruToProcess.Count == 7)
							break;
					}
					

					// are these in order?
					// .. order them by place in the rashi order
					ruToProcess.Sort((x, y) => x.place.CompareTo(y.place));

					// .. see if they are in order
					bool fAllInOrder = true;
					bool fFirstTime = true;
					while (!fAllInOrder || fFirstTime) {

						// if there are ties, allow for those
						// **


						fFirstTime = false;
						fAllInOrder = true;
						int prevstartpos = -1;
						int prevendpos = -1;
						for (int irashi = 0; irashi < ruToProcess.Count; irashi++) {

							// if this one is prior to the current position, break
							if (ruToProcess[irashi].rashimatches[0].startWord < prevstartpos) {
								fAllInOrder = false;
								break;
							}

							// if this one is the same as curpos, only ok if it is shorter
							if (ruToProcess[irashi].rashimatches[0].startWord == prevstartpos) {
								if (ruToProcess[irashi].rashimatches[0].endWord >= prevendpos) {
									fAllInOrder = false;
									break;
								}
							}

							prevstartpos = ruToProcess[irashi].rashimatches[0].startWord;
							prevendpos = ruToProcess[irashi].rashimatches[0].endWord;
						}

						// if they are not in order, then we need to figure out which ones are causing trouble and throw them out
						if (!fAllInOrder) {

							if (ruToProcess.Count == 2) {

								// there are only 2

								// if the top one is much higher in its disambig score than the next one, then don't try to reverse; just take the top score
								if (Math.Abs(ruToProcess[0].disambiguationScore - ruToProcess[1].disambiguationScore) > 10) {
									ruToProcess.Sort((x, y) => y.disambiguationScore.CompareTo(x.disambiguationScore));
									ruToProcess.RemoveAt(1);
								}
								else {

									// if there are only 2, see if we can reverse them by going to the secondary matches
									// .. try the first
									bool ffixed = false;
									if (ruToProcess[0].rashimatches.Count > 1) {
										if (ruToProcess[0].rashimatches[1].startWord < ruToProcess[1].rashimatches[0].startWord) {

											// make sure they are reasonably close
											if (ruToProcess[0].disambiguationScore < 10) {
												ruToProcess[0].rashimatches.RemoveAt(0);
												ffixed = true;
											}
										}
									}

									if (!ffixed) {
										// .. try the second
										ffixed = false;
										if (ruToProcess[1].rashimatches.Count > 1) {
											if (ruToProcess[1].rashimatches[1].startWord > ruToProcess[0].rashimatches[0].startWord) {

												if (ruToProcess[1].disambiguationScore < 10) {
													ruToProcess[1].rashimatches.RemoveAt(0);
													ffixed = true;
												}
											}
										}
									}

									if (!ffixed) {
										// .. try the second of both
										ffixed = false;
										if (ruToProcess[0].rashimatches.Count > 1 && ruToProcess[1].rashimatches.Count > 1) {
											if (ruToProcess[1].rashimatches[1].startWord > ruToProcess[0].rashimatches[1].startWord) {
												if (ruToProcess[1].disambiguationScore < 10 && ruToProcess[0].disambiguationScore < 10) {

													ruToProcess[0].rashimatches.RemoveAt(0);
													ruToProcess[1].rashimatches.RemoveAt(0);
													ffixed = true;
												}
											}
										}
									}

									// if not, take the one with the highest score
									if (!ffixed) {
										ruToProcess.Sort((x, y) => y.disambiguationScore.CompareTo(x.disambiguationScore));
										ruToProcess.RemoveAt(1);
									}
								}
							}
							else {
								int[] outoforder = new int[ruToProcess.Count];
								for (int irashi = 0; irashi < ruToProcess.Count; irashi++) {
									outoforder[irashi] = 0;
								}
								int highestDeviation = 0;
								for (int irashi = 0; irashi < ruToProcess.Count; irashi++) {

									// how many are out of order vis-a-vis this one?
									for (int jrashi = 0; jrashi < ruToProcess.Count; jrashi++) {

										if (jrashi == irashi) continue;

										if (irashi < jrashi) {

											// easy case: they start at diff places
											if (ruToProcess[irashi].rashimatches[0].startWord > ruToProcess[jrashi].rashimatches[0].startWord)
												outoforder[irashi]++;

												// deal with case of same starting word. only ok if irashi is of greater length
											else if (ruToProcess[irashi].rashimatches[0].startWord == ruToProcess[jrashi].rashimatches[0].startWord) {
												if (ruToProcess[irashi].rashimatches[0].endWord <= ruToProcess[jrashi].rashimatches[0].endWord) {
													outoforder[irashi]++;
												}
											}
										}
										else {

											// in this case, irashi is after jrashi

											if (ruToProcess[irashi].rashimatches[0].startWord < ruToProcess[jrashi].rashimatches[0].startWord)
												outoforder[irashi]++;

												// deal with case of same starting word. only ok if jrashi is of greater length
											else if (ruToProcess[irashi].rashimatches[0].startWord == ruToProcess[jrashi].rashimatches[0].startWord) {
												if (ruToProcess[irashi].rashimatches[0].endWord >= ruToProcess[jrashi].rashimatches[0].endWord) {
													outoforder[irashi]++;
												}
											}
										}
									}
									if (outoforder[irashi] > highestDeviation)
										highestDeviation = outoforder[irashi];
								}
								// now throw out all those that have the highest out-of-order ranking
								for (int irashi = ruToProcess.Count - 1; irashi >= 0; irashi--) {
									if (outoforder[irashi] == highestDeviation && ruToProcess.Count > 1) {
										ruToProcess.RemoveAt(irashi);
									}
								}
							}
						}
					}


					// TODO: deal with the case of only 2 in ruToProcess in a smarter way

					for (int irashi = 0; irashi < ruToProcess.Count; irashi++) {
						if (ruToProcess[irashi].startingText == "והא") {

						}

					}

					// by this point they are all in order, so we can put them all in
					for (int irashi = 0; irashi < ruToProcess.Count; irashi++) {

						RashiUnit curru = ruToProcess[irashi];

						// put it in


						// TODO: if disambiguity is low, apply other criteria
						TextMatch match = curru.rashimatches[0];
						curru.startWord = match.startWord;
						curru.endWord = match.endWord;
						curru.matchedGemaraText = match.textMatched;

						// remove this guy from the disambiguities, now that it is matched up 
						rashisByDisambiguity.Remove(curru);
						if (curru.startingText.Contains("מאי לאו בהא קמיפלגי")) {
							
						}

						// recalculate the disambiguities for all those who were potentially relevant, based on this one's place
						RecalculateDisambiguities(curDaf.allRashi, rashisByDisambiguity, prevMatchedRashi, nextMatchedRashi, startBound, endBound, curru);
					}

					// resort the disambiguity array
					rashisByDisambiguity.Sort((x, y) => y.disambiguationScore.CompareTo(x.disambiguationScore));
				}
				
				int unmatched = CountUnmatchedUpRashi(curDaf);

				// now we check for dapim that have a lot of unmatched items, and then we take items out one at a time to see if we can 
				// minimize it
				// because usually this results from one misplaced item.

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

		private static void RecalculateDisambiguities(List<RashiUnit> allRashis, List<RashiUnit> rashisByDisambiguity, int prevMatchedRashi, int nextMatchedRashi, int startbound, int endbound, RashiUnit newlyMatchedRashiUnit) {

			for (int irashi = rashisByDisambiguity.Count-1; irashi >= 0; irashi--) {

				RashiUnit ru = rashisByDisambiguity[irashi];
				if (ru.place <= prevMatchedRashi || ru.place >= nextMatchedRashi || ru.place == newlyMatchedRashiUnit.place)
					continue;

				// this rashi falls out somewhere inside the current window, either before the newest match or after the newest match
				int localstartbound = (ru.place < newlyMatchedRashiUnit.place) ? startbound : newlyMatchedRashiUnit.startWord;
				int localendbound = (ru.place > newlyMatchedRashiUnit.place) ? endbound : newlyMatchedRashiUnit.startWord;

				// now remove any potential matches that are blocked by the newly matched rashi
				for (int imatch = ru.rashimatches.Count-1; imatch >= 0; imatch--) {
					TextMatch tm = ru.rashimatches[imatch];
					if (tm.startWord < localstartbound || tm.startWord > localendbound) {
						if (ru.startingText == "והא") {
							
						}
						ru.rashimatches.RemoveAt(imatch);
					}
				}

				// special shift: if there are two close items, and one is an overlap with a current anchor and one is not, switch and their scores
				int endOfPrevRashi = prevMatchedRashi == -1 ? -1 : allRashis[prevMatchedRashi].endWord;
				int startOfNextRashi = nextMatchedRashi == allRashis.Count ? 9999 : allRashis[nextMatchedRashi].startWord;

				if (ru.rashimatches.Count >= 2) {
					// if the top one overlaps
					if (ru.rashimatches[0].startWord <= endOfPrevRashi || ru.rashimatches[0].endWord >= startOfNextRashi) {
						// and if the next one does not overlap
						if (ru.rashimatches[1].startWord > endOfPrevRashi && ru.rashimatches[1].endWord < startOfNextRashi) {

							if (ru.rashimatches[1].score - ru.rashimatches[0].score < 20) {

								// let's switch them
								
								TextMatch temp = ru.rashimatches[1];
								ru.rashimatches[1] = ru.rashimatches[0];
								ru.rashimatches[0] = temp;

								int tempscore = ru.rashimatches[1].score;
								ru.rashimatches[0].score = ru.rashimatches[1].score;
								ru.rashimatches[1].score = tempscore;
								
							}
						}
					}
				}

				// if there are none left, remove it altogether
				if (ru.rashimatches.Count == 0) {
					rashisByDisambiguity.RemoveAt(irashi);
				}
				else {
					// now recalculate the disambiguity
					CalculateAndFillInDisambiguity(ru);
				}
			}
		}

		private static void CalculateAndFillInDisambiguity(RashiUnit ru) {

			// if just one, it is close to perfect. Although could be that there is no match...
			if (ru.rashimatches.Count == 1) {
				// calculate it vis-a-vis blank
				ru.disambiguationScore = (ImaginaryContenderPerWord * ru.cvWordcount) - ru.rashimatches[0].score;
				if (ru.disambiguationScore < 0)
					ru.disambiguationScore = 0;
			}
			else if (ru.rashimatches.Count == 0)
				ru.disambiguationScore = 0xFFFF;
			else {
				ru.disambiguationScore = ru.rashimatches[1].score - ru.rashimatches[0].score;
				if (ru.disambiguationScore == -44) {
					
				}
			}

			if (ru.startingText == "והא") {
				
			}
		}

		private static int CountUnmatchedUpRashi(GemaraDaf curDaf) {
			/// This function counts all the Rashi's in a given daf and 
			/// return the amount of rashi's that still don't have a location within
			/// the gemara text.
			int toRet = 0;
			foreach (RashiUnit rashi in curDaf.allRashi) {
				if (rashi.startWord == -1)
					toRet++;
			}
			return toRet;
		}


		private static List<TextMatch> GetAllApproximateMatches(GemaraDaf curDaf, RashiUnit curRashi, int startBound, int endBound, double threshold) {
			List<TextMatch> allMatches = new List<TextMatch>();

			string startText = curRashi.startingTextNormalized;
			int wordCount = curRashi.cvWordcount;
			if (wordCount == 0) return allMatches;
			
			// Okay, start going through all the permutations..
			double distance = 0;
			for (int iWord = startBound; iWord <= curDaf.allWords.Count - wordCount && iWord + wordCount - 1 <= endBound; iWord++) {

				bool fIsMatch = false;
				// if phrase is 4 or more words, use the 2-letter hashes
				if (wordCount >= 4) {
					// get the hashes for the starting text
					List<long> cvhashes = CalculateHashes(Regex.Split(startText.Trim(), @"\s+").ToList());

					long initialhash = cvhashes[0];
					if (curDaf.wordhashes[iWord] == initialhash) {

						// see if the rest match up
						int mismatches = 0;
						for (int icvword = 1; icvword < wordCount; icvword++) {
							if (curDaf.wordhashes[iWord + icvword] != cvhashes[icvword]) {
								mismatches++;
							}
						}

						// now we need to decide if we can let it go
						int allowedMismatches = (int)Math.Ceiling(wordCount * threshold * 1.35);
						if (mismatches <= allowedMismatches) {
							distance = mismatches;
							fIsMatch = true;
						}
					}
				}
				else {
					// build the phrase
					string targetPhrase = BuildPhraseFromArray(curDaf.allWords, iWord, wordCount);

					// Now check if it is a match.
					fIsMatch = IsStringMatchup(startText, targetPhrase, threshold, out distance);
				}
				// If it is, add it in.
				if (fIsMatch) {
					TextMatch curMatch = new TextMatch();
					curMatch.textToMatch = curRashi.startingText;
					curMatch.textMatched = BuildPhraseFromArray(curDaf.allWords, iWord, wordCount);
					curMatch.startWord = iWord;
					curMatch.endWord = iWord + wordCount - 1;

					// calculate the score - how distant is it
					double dist = ComputeLevenshteinDistanceByWord(startText, curMatch.textMatched);
					int normalizedDistance = (int)((dist + smoothingFactor) / (startText.Length + smoothingFactor) * normalizingFactor);
					curMatch.score = normalizedDistance;

					allMatches.Add(curMatch);
				}
			}

			return allMatches;
		}

		private static List<TextMatch> GetAllApproximateMatchesWithAbbrev(GemaraDaf curDaf, RashiUnit curRashi, int startBound, int endBound, double threshold) {
			List<TextMatch> allMatches = new List<TextMatch>();

			string startText = curRashi.startingTextNormalized;
			int wordCount = curRashi.cvWordcount;
			if (wordCount == 0) return allMatches;

			if (startText.Contains("חוצה")) {
				
			}

			// convert string into an array of words
			string[] startTextWords = Regex.Split(startText, @"\s+");


			// go through all possible starting words in the gemara text
			for (int iStartingWordInGemara = startBound; iStartingWordInGemara <= curDaf.allWords.Count - wordCount && iStartingWordInGemara + wordCount - 1 <= endBound; iStartingWordInGemara++) {

				bool fIsMatch = false;
				int offsetWithinGemara = 0;
				int offsetWithinRashiCV = 0;
				double distance = 0;
				double totaldistance = 0;

				// now we loop according to the number of words in the cv

				// .. keep track of how the gemara text differs from rashi length
				int gemaraDifferential = 0;

				for (int iWordWithinPhrase = 0; iWordWithinPhrase + offsetWithinRashiCV < wordCount; iWordWithinPhrase++) {

					// first check if the cv word has a quotemark
					if (startTextWords[iWordWithinPhrase + offsetWithinRashiCV].Contains("\"")) {

						// get our ראשי תיבות word without the quote mark
						string cleanRT = startTextWords[iWordWithinPhrase + offsetWithinRashiCV].Replace("\"", "");
						int maxlen = cleanRT.Length;

						// let's see if this matches the start of the next few words
						int curpos = iStartingWordInGemara + iWordWithinPhrase + offsetWithinGemara;
						fIsMatch = false;

						if (curpos + maxlen <= curDaf.allWords.Count) {
							fIsMatch = true;
							for (int igemaraword = curpos; igemaraword < curpos + maxlen; igemaraword++) {
								if (curDaf.allWords[igemaraword][0] != cleanRT[igemaraword - curpos]) {
									fIsMatch = false;
									break;
								}
							}
							if (fIsMatch) {
								// we condensed maxlen words into 1. minus one, because later we'll increment one.
								offsetWithinGemara += maxlen - 1;
							}
						}


						// let's see if we can match by combining the first two into one word
						if (curpos + maxlen <= curDaf.allWords.Count + 1) {

							if (!fIsMatch && maxlen > 2) {

								fIsMatch = true;
								if (curDaf.allWords[curpos].Length < 2 || curDaf.allWords[curpos][0] != cleanRT[0] || curDaf.allWords[curpos][1] != cleanRT[1]) {
									fIsMatch = false;
								}
								else {
									for (int igemaraword = curpos + 1; igemaraword < curpos + maxlen - 1; igemaraword++) {
										if (curDaf.allWords[igemaraword][0] != cleanRT[igemaraword - curpos + 1]) {
											fIsMatch = false;
											break;
										}
									}
								}
								if (fIsMatch) {
									// we condensed maxlen words into 1. minus one, because later we'll increment one.
									offsetWithinGemara += maxlen - 2;
								}
							}
						}

						// let's see if we can match by combining the first three into one word
						if (curpos + maxlen <= curDaf.allWords.Count + 2) {

							if (!fIsMatch && maxlen > 3) {

								fIsMatch = true;
								if (curDaf.allWords[curpos].Length < 3 || curDaf.allWords[curpos][0] != cleanRT[0] || curDaf.allWords[curpos][1] != cleanRT[1] ||
								    curDaf.allWords[curpos][2] != cleanRT[2]) {
									fIsMatch = false;
								}
								else {
									for (int igemaraword = curpos + 1; igemaraword < curpos + maxlen - 2; igemaraword++) {
										if (curDaf.allWords[igemaraword][0] != cleanRT[igemaraword - curpos + 2]) {
											fIsMatch = false;
											break;
										}
									}
								}
								if (fIsMatch) {
									// we condensed maxlen words into 1. minus one, because later we'll increment one.
									offsetWithinGemara += maxlen - 3;
								}
							}
						}

						if (!fIsMatch) break;

						// now increment the offset to correspond, so that we'll know we're skipping over x number of words
					}
					else if (curDaf.allWords[iStartingWordInGemara + offsetWithinGemara + iWordWithinPhrase].Contains("\"")) {
						
						// get our ראשי תיבות word without the quote mark
						string cleanRT = curDaf.allWords[iStartingWordInGemara + offsetWithinGemara + iWordWithinPhrase].Replace("\"", "");
						int maxlen = cleanRT.Length;

						// let's see if this matches the start of the next few words
						int curpos = iWordWithinPhrase + offsetWithinRashiCV;
						fIsMatch = false;

						if (curpos + maxlen <= wordCount) {
							fIsMatch = true;
							for (int icvword = curpos; icvword < curpos + maxlen; icvword++) {
								if (startTextWords[icvword][0] != cleanRT[icvword - curpos]) {
									fIsMatch = false;
									break;
								}
							}
							if (fIsMatch) {
								// we condensed maxlen words into 1. minus one, because later we'll increment one.
								offsetWithinRashiCV += maxlen - 1;
							}
						}


						// let's see if we can match by combining the first two into one word
						if (curpos + maxlen <= wordCount + 1) {
							if (!fIsMatch && maxlen > 2) {

								fIsMatch = true;
								if (startTextWords[curpos].Length < 2 || startTextWords[curpos][0] != cleanRT[0] || startTextWords[curpos][1] != cleanRT[1]) {
									fIsMatch = false;
								}
								else {
									for (int icvword = curpos + 1; icvword < curpos + maxlen - 1; icvword++) {
										if (startTextWords[icvword][0] != cleanRT[icvword - curpos + 1]) {
											fIsMatch = false;
											break;
										}
									}
								}
								if (fIsMatch) {
									// we condensed maxlen words into 1. minus one, because later we'll increment one.
									offsetWithinRashiCV += maxlen - 2;
								}
							}
						}

						// let's see if we can match by combining the first three into one word
						if (curpos + maxlen <= wordCount + 2) {

							if (!fIsMatch && maxlen > 3) {

								fIsMatch = true;
								if (startTextWords[curpos].Length < 3 || startTextWords[curpos][0] != cleanRT[0] || startTextWords[curpos][1] != cleanRT[1] ||
								    startTextWords[curpos][2] != cleanRT[2]) {
									fIsMatch = false;
								}
								else {
									for (int icvword = curpos + 1; icvword < curpos + maxlen - 2; icvword++) {
										if (startTextWords[icvword][0] != cleanRT[icvword - curpos + 2]) {
											fIsMatch = false;
											break;
										}
									}
								}
								if (fIsMatch) {
									// we condensed maxlen words into 1. minus one, because later we'll increment one.
									offsetWithinRashiCV += maxlen - 3;
								}
							}
						}

						if (!fIsMatch) break;
					}
					else {
						// great, this is a basic compare.
						bool fMatch = IsStringMatchup(startTextWords[iWordWithinPhrase + offsetWithinRashiCV], curDaf.allWords[iStartingWordInGemara + offsetWithinGemara + iWordWithinPhrase], threshold, out distance);
						totaldistance += distance;
						// if these words don't match, break and this isn't a match.
						if (!fMatch) {
							fIsMatch = false; break;
						}
					}
				}

				gemaraDifferential = offsetWithinRashiCV;
				gemaraDifferential -= offsetWithinGemara;

				// If it is, add it in.
				if (fIsMatch) {
					TextMatch curMatch = new TextMatch();
					curMatch.textToMatch = curRashi.startingText;
					curMatch.textMatched = BuildPhraseFromArray(curDaf.allWords, iStartingWordInGemara, wordCount - gemaraDifferential);
					curMatch.startWord = iStartingWordInGemara;
					curMatch.endWord = iStartingWordInGemara + wordCount - gemaraDifferential;

					// calculate the score, adding in the penalty for abbreviation
					totaldistance += abbreviationPenalty;
					int normalizedDistance = (int)((totaldistance + smoothingFactor) / (startText.Length + smoothingFactor) * normalizingFactor);
					curMatch.score = normalizedDistance;

					allMatches.Add(curMatch);
				}
			}


			return allMatches;
		}

		private static List<TextMatch> GetAllApproximateMatchesWithWordSkip(GemaraDaf curDaf, RashiUnit curRashi, int startBound, int endBound, double threshold) {
			List<TextMatch> allMatches = new List<TextMatch>();
			List<int> usedStartwords = new List<int>();

			if (curRashi.startingTextNormalized.Contains("אלא סיד")) {
				
			}

			string startText = curRashi.startingTextNormalized;
			int wordCount = curRashi.cvWordcount;

			// No point to this unless we have at least 2 words
			if (wordCount < 2) return new List<TextMatch>();

			// Iterate through all the starting words within the phrase, allowing for one word to be ignored
			for (int iWordToIgnore = -1; iWordToIgnore < wordCount; iWordToIgnore++) {

				List<string> rashiwords = Regex.Split(startText.Trim(), @"\s+").ToList();
				List<long> cvhashes = CalculateHashes(rashiwords);

				string alternateStartText = "";
				if (iWordToIgnore >= 0) {
					cvhashes.RemoveAt(iWordToIgnore);
					alternateStartText = GetStringWithRemovedWord(startText, iWordToIgnore).Trim();
				}
				else {
					alternateStartText = startText;
				}
				
				// Iterate through all possible starting words within the gemara, allowing for the word afterward to be ignored
				for (int iWord = startBound; iWord <= curDaf.allWords.Count - wordCount && iWord + wordCount - 1 <= endBound; iWord++) {

					// Start from -1 (which means the phrase as is)
					for (int gemaraWordToIgnore = -1; gemaraWordToIgnore < wordCount; gemaraWordToIgnore++) {

						// no point in skipping first word - we might as well just let the item start from the next startword
						if (gemaraWordToIgnore == 0) continue;

						// and, choose a second word to ignore (-1 means no second word)
						for (int gemaraWord2ToIgnore = -1; gemaraWord2ToIgnore < wordCount; gemaraWord2ToIgnore++) {

							// if not skipping first, this is not relevant unless it is also -1
							if (gemaraWordToIgnore == -1 && gemaraWord2ToIgnore != -1)
								continue;
							
							// we don't need to do things both directions
							if (gemaraWord2ToIgnore != -1 && gemaraWord2ToIgnore < gemaraWordToIgnore)
								continue;

							// if we are skipping a cv word, don't also skip a second word
							if (iWordToIgnore != -1 && gemaraWord2ToIgnore != -1) {
								continue;
							}

							// if this would bring us to the end, don't do it
							if (gemaraWord2ToIgnore != -1 && iWord + wordCount >= curDaf.allWords.Count)
								continue;

							bool fIsMatch = false;
							double distance = 0;
							double totaldistance = 0;


							if (wordCount >= 4) {

								int nonMatchAllowance = wordCount/2 - 1;

								long initialhash = cvhashes[0];
								if (curDaf.wordhashes[iWord] == initialhash) {
									// see if the rest match up
									int offset = 0;
									fIsMatch = true;
									for (int icvword = 1; icvword < wordCount - 1; icvword++) {
										if (icvword == gemaraWordToIgnore || icvword == gemaraWord2ToIgnore) {
											offset++;
										}

										// check the hash, and or first letter
										if (curDaf.wordhashes[iWord + icvword + offset] != cvhashes[icvword] &&
										    curDaf.allWords[iWord + icvword + offset][0] != rashiwords[icvword][0]) {

												nonMatchAllowance--;

												if (nonMatchAllowance < 0) {
												fIsMatch = false;
												break;
											}
										}
									}
								}
							}
							else {
								// build the phrase
								string targetPhrase = BuildPhraseFromArray(curDaf.allWords, iWord, wordCount, gemaraWordToIgnore, gemaraWord2ToIgnore);

								// Now check if it is a match
								fIsMatch = IsStringMatchup(alternateStartText, targetPhrase, threshold, out distance);
							}
							// If it is, add it in.
							if (fIsMatch) {

								if (usedStartwords.Contains(iWord)) continue;
								TextMatch curMatch = new TextMatch();

								// if gemaraWordToIgnore is -1, then we didn't skip anything in the gemara.
								// if iWordToIgnore is -1, then we didn't skip anything in the main phrase

								// whether or not we used the two-letter shortcut, let's calculate full distance here.
								string targetPhrase = BuildPhraseFromArray(curDaf.allWords, iWord, wordCount, gemaraWordToIgnore, gemaraWord2ToIgnore);
								double dist = ComputeLevenshteinDistanceByWord(alternateStartText, targetPhrase);

								// add penalty for skipped words
								if (gemaraWordToIgnore >= 0)
									dist += fullWordValue;
								if (gemaraWord2ToIgnore >= 0)
									dist += fullWordValue;
								if (iWordToIgnore >= 0)
									dist += fullWordValue;

								int normalizedDistance = (int) ((dist + smoothingFactor)/(startText.Length + smoothingFactor)*normalizingFactor);
								curMatch.score = normalizedDistance;
								curMatch.textToMatch = curRashi.startingText;

								// the "text matched" is the actual text of the gemara, including the word we skipped.
								curMatch.textMatched = BuildPhraseFromArray(curDaf.allWords, iWord, wordCount);
								curMatch.startWord = iWord;
								curMatch.endWord = iWord + wordCount - 1;

								// if we skipped the last word or two words, then we should cut them out of here
								if (gemaraWordToIgnore == wordCount - 2 && gemaraWord2ToIgnore == wordCount -1) {
									curMatch.textMatched = BuildPhraseFromArray(curDaf.allWords, iWord, wordCount - 2);
									curMatch.endWord-=2;
								}
								else if (gemaraWordToIgnore == wordCount - 1) {
									curMatch.textMatched = BuildPhraseFromArray(curDaf.allWords, iWord, wordCount - 1);
									curMatch.endWord--;
								}

								allMatches.Add(curMatch);

								usedStartwords.Add(iWord);
								break;
							}
						}
					}
				}
			}
			return allMatches;
		}

		private static string GetStringWithRemovedWord(string p, int iWordToIgnore) {
			// remove the word specified in iWordToIgnore
			// if -1, return word as is
			if (iWordToIgnore == -1)
				return p;

			string[] words = p.Split(' ');
			string ret = "";
			for (int i = 0; i < words.Length; i++) {
				if (i == iWordToIgnore)
					continue;

				ret += words[i] + " ";
			}
			return ret.Trim();
		}

		private static string BuildPhraseFromArray(List<string> allWords, int iWord, int len, int wordToSkip = -1, int word2ToSkip = -1) {
			string phrase = "";
			for (int jump = 0; jump < len; jump++) {
				if (jump == wordToSkip || jump == word2ToSkip) continue;
				phrase += allWords[iWord + jump] + " ";
			}
			return phrase.Trim();
		}
		private static int CountWords(string s) {
			MatchCollection mc = Regex.Matches(s, @"\S+");
			return mc.Count;
		}
		private static bool IsStringMatchup(string orig, string target, double threshold, out double score) {

			// if our threshold is 0, just compare them one to eachother.
			if (threshold == 0) {
				score = 0;
				return orig == target;
			}

			// if equal
			if (orig == target) {
				score = 0;
				return true;
			}

			// wait: if one is a substring of the other, then that can be considered an almost perfect match
			if (orig.StartsWith(target) || target.StartsWith(orig)) {
				score = 1;
				return true;
			}


			// Otherwise, now we need to levenshtein.
			double dist = ComputeLevenshteinDistance(orig, target);

			// Now get the actual threshold
			double maxDist = Math.Ceiling(orig.Length * threshold);

			score = dist;

			// return if it is a matchup
			return dist <= maxDist;
		}
		private static void GetRashiBoundaries(List<RashiUnit> allRashi, int dwRashi, ref int startBound, ref int endBound, ref int prevMatchedRashi, ref int nextMatchedRashi, int maxBound) {

			// often Rashis overlap - e.g., first שבועות שתים שהן ארבע and then שתים and then שהן ארבע
			// so we can't always close off the boundaries
			// but sometimes we want to

			// maxbound is the number of words on the amud
			startBound = 0;
			endBound = maxBound - 1;

			prevMatchedRashi = -1;
			nextMatchedRashi = allRashi.Count;

			// Okay, look as much up as you can from iRashi to find the start bound
			for (int iRashi = dwRashi - 1; iRashi >= 0; iRashi--) {
				if (allRashi[iRashi].startWord == -1) continue;

				prevMatchedRashi = iRashi;

				// Okay, this is our closest one on top that has a value
				// allow it to overlap
				startBound = allRashi[iRashi].startWord;
				break;
			}

			// Second part, look down as much as possible to find the end bound
			for (int iRashi = dwRashi + 1; iRashi < allRashi.Count; iRashi++) {
				if (allRashi[iRashi].startWord == -1) continue;
				// Okay, this is the closest one below that has a value
				// our end bound will be the startword - 1.

				nextMatchedRashi = iRashi;

				// allow it to overlap
				endBound = allRashi[iRashi].startWord;

				break;
			}
			// Done!!
		}

		public class TextMatch {
			public string textToMatch;
			public string textMatched;
			public int startWord;
			public int endWord;
			public int score;
		}

		private static List<GemaraMasechet> GetAllMasechtotWithRashiFromSerializedData(string baseDir) {
			FileStream fs = new FileStream(baseDir + "szdata.bin", FileMode.Open);
			BinaryFormatter bf = new BinaryFormatter();
			object toRet = bf.Deserialize(fs);
			fs.Close();

			return (List<GemaraMasechet>)toRet;
		}
		private static List<GemaraMasechet> GetAllMasechtotWithRashi(string baseDir) {
			string baseGemaraDir = baseDir + "Talmud\\";
			string baseRashiDir = baseDir + "Rashi\\";

			Dictionary<string, GemaraMasechet> allMasechtot = new Dictionary<string, GemaraMasechet>();
			// OK, so first we want to get all the gemara text by daf.
			string[] allFiles = Directory.GetFiles(baseGemaraDir, "*.txt");
			for (int iFile = 0; iFile < allFiles.Length; iFile++) {
				string file = allFiles[iFile];
				Console.Write("\rProcessing gemara file " + (iFile + 1) + " out of " + allFiles.Length + "       ");
				// now get the text.
				string[] allLines = File.ReadAllLines(file);
				// create our gemara masechet unit
				GemaraMasechet gm = new GemaraMasechet();
				gm.masechetNameEng = allLines[0];
				gm.masechetNameHeb = allLines[1];

				// OK, so now we iterate through all the lines
				GemaraDaf gd = new GemaraDaf();
				foreach (string curLine in allLines) {
					if (curLine.Trim() == "") continue;
					// first check if this is a daf heading.
					if (curLine.StartsWith("Daf ")) {
						// it is! put it in!
						if (gd.dafLocation != null && gd.gemaraText.Trim() != "") {
							gm.allDapim.Add(gd.dafLocation, gd);
						}
						// reset..
						gd = new GemaraDaf();
						gd.dafLocation = curLine;
						gd.gemaraText = "";

						if (fdebug) {
							if (gd.dafLocation.Contains("10a"))
								break;
						}

						continue;
					}
					// if we haven't reached the first daf yet..
					if (gd.dafLocation == null) continue;
					// yay add the text!
					string cleanGemaraText = CleanText(curLine);

					// now generate the lists of bad words to ignore
					MatchCollection mcWordToIgnore = Regex.Matches(cleanGemaraText, @"\([^)]+\)");

					int startWord = gd.allWords.Count;
					// now get all the words.
					MatchCollection mcWords = Regex.Matches(cleanGemaraText, @"\S+");
					foreach (Match m in mcWords) {
						string curVal = Regex.Replace(m.Value, "[^א-ת \"]", "");
						// first, make sure there is stuff that isn't punc
						if (curVal.Trim() == "") continue;
						// secondly, make sure this isn't from the ignored text
						bool fIgnore = false;
						foreach (Match mToIgnore in mcWordToIgnore) {
							if (m.Index >= mToIgnore.Index && (m.Index + m.Length) <= (mToIgnore.Index + mToIgnore.Length))
								fIgnore = true;
						}
						if (fIgnore) continue;

						// now put this into the dictionary
						gd.iWordToOrigChar.Add(gd.allWords.Count, gd.gemaraText.Length + m.Index);
						// now put it into all words
						gd.allWords.Add(curVal);
					}
					int endWord = gd.allWords.Count - 1;

					gd.lineStartingWordPointers.Add(new Tuple<int, int>(startWord, endWord));
					gd.gemaraText += cleanGemaraText + " ";
				}
				if (gd.dafLocation != null && gd.gemaraText.Trim() != "") {
					gm.allDapim.Add(gd.dafLocation, gd);
				}

				allMasechtot.Add(gm.masechetNameEng, gm);
			}


			// now rashi!
			allFiles = Directory.GetFiles(baseRashiDir, "*.txt");
			for (int iFile = 0; iFile < allFiles.Length; iFile++) {
				string file = allFiles[iFile];
				Console.Write("\rProcessing rashi file " + (iFile + 1) + " out of " + allFiles.Length + "       ");
				// now get the text.
				string[] allLines = File.ReadAllLines(file);
				// get the masechet
				string masechet = allLines[0].Replace("Rashi on ", "");

				// now traverse!
				string curDaf = ""; int curLineN = 0;
				for (int iLine = 0; iLine < allLines.Length; iLine++) {
					string curLine = allLines[iLine];
					if (curLine.Trim() == "") continue;
					if (curLine.StartsWith("Line ")) {
						curLineN = int.Parse(curLine.Replace("Line ", "")) - 1; continue;
					}

					// is this a daf heading?
					if (curLine.StartsWith("Daf ")) {
						curDaf = curLine; continue;
					}
					if (curDaf.Trim() == "") continue;

					// first of all, remove גמ' and מתני' declerations beginnign parens
					curLine = Regex.Replace(curLine, @"\s*\([^)]+\)\s*", " ");
					// check if after the colon there is one word and then it ends
					curLine = Regex.Replace(curLine, @":\s*\S+$", ":");

					// now split by ":"
					string[] allUnits = Regex.Split(curLine, ": ");
					for (int iUnit = 0; iUnit < allUnits.Length; iUnit++) {
						string unitStr = allUnits[iUnit];
						if (unitStr.Trim() == "") continue;

						// if this isn't saved the regular way..
						if (!Regex.IsMatch(unitStr, " [-‒–—] ")) {
							unitStr = Regex.Replace(unitStr, @"^([^.]+)\. ", "$1 - ");
						}

						RashiUnit curUnit = new RashiUnit();
						Match m = Regex.Match(unitStr, "(.*?) [-‒–—] (.*)");
						curUnit.startingText = m.Groups[1].Value.Trim();
						curUnit.fullText = unitStr;
						curUnit.valueText = m.Groups[2].Value;
						curUnit.lineN = curLineN;

						string normalizedCV = Regex.Replace(curUnit.startingText, " ו" + "?" + "כו" + "'?" + "$", "").Trim();
						normalizedCV = Regex.Replace(normalizedCV, "^(גמ|גמרא|מתני|מתניתין|משנה)'? ", "").Trim();

						// if it starts with a הג, then take just 3 words afterward
						if (curUnit.startingText.StartsWith("ה\"ג")) {
							normalizedCV = Regex.Match(normalizedCV, "[^ ]+ ([^ ]+( [^ ]+)?( [^ ]+)?)").Groups[1].Value;
						}

						// now remove all non-letters, allowing just quotes
						normalizedCV = Regex.Replace(normalizedCV, "[^א-ת \"]", "").Trim();

						curUnit.startingTextNormalized = normalizedCV;
						curUnit.cvWordcount = CountWords(normalizedCV);

						if (!allMasechtot[masechet].allDapim.ContainsKey(curDaf)) continue;
						if (curUnit.startingText == "" || curUnit.valueText == "") continue;
						if (curUnit.lineN >= allMasechtot[masechet].allDapim[curDaf].lineStartingWordPointers.Count) continue;
						allMasechtot[masechet].allDapim[curDaf].allRashi.Add(curUnit);
					}
				}
			}
			//////// Serialize //////////////////
			if (fSerializeData) {
				FileStream fs = new FileStream(baseDir + "szdata.bin", FileMode.Create);
				BinaryFormatter bf = new BinaryFormatter();
				bf.Serialize(fs, allMasechtot.Values.ToList());
				fs.Close();
			}
			/////////////////////////////////////

			Console.WriteLine("\n");
			return allMasechtot.Values.ToList();
		}
		private static string CleanText(string curLine) {
			curLine = Regex.Replace(curLine, "</?[^>]+>", "").Trim();
			return curLine;
		}
		[Serializable]
		private class GemaraMasechet {
			public string masechetNameEng;
			public string masechetNameHeb;
			public Dictionary<string, GemaraDaf> allDapim;
			public GemaraMasechet() {
				allDapim = new Dictionary<string, GemaraDaf>();
			}
		}
		[Serializable]
		private class GemaraDaf {
			public string dafLocation;
			public string gemaraText;
			public List<string> allWords;
			public Dictionary<int, int> iWordToOrigChar;
			public List<Tuple<int, int>> lineStartingWordPointers;
			public List<long> wordhashes;
			public List<RashiUnit> allRashi;
			public GemaraDaf() {
				allWords = new List<string>();
				allRashi = new List<RashiUnit>();
				lineStartingWordPointers = new List<Tuple<int, int>>();
				wordhashes = new List<long>();
				iWordToOrigChar = new Dictionary<int, int>();
			}
		}
		[Serializable]
		public class RashiUnit {
			public int place;
			public int disambiguationScore;
			public List<TextMatch> rashimatches;
			public string startingText;
			public string startingTextNormalized;
			public string fullText;
			public string valueText;
			public int startWord;
			public int endWord;
			public int lineN;
			public int cvWordcount;
			public string matchedGemaraText;
			public RashiUnit() {
				startWord = -1;
				endWord = -1;
				rashimatches = new List<TextMatch>();
			}
		}

		private static int ComputeLevenshteinDistanceByWord(string s, string t) {

			// we take it word by word
			// each word can be, at most, the value of a full word

			string[] words1 = s.Split(' ');
			string[] words2 = t.Split(' ');

			double totaldistance = 0;

			for (int i = 0; i < words1.Length; i++) {
				if (i >= words2.Length)
					totaldistance += fullWordValue;
				else {

					// if equal, no distance
					if (s == t) {
						continue;
					}

					// wait: if one is a substring of the other, then that can be considered an almost perfect match
					if (s.StartsWith(t) || t.StartsWith(s)) {
						totaldistance += 0.5;
					}

					totaldistance += Math.Min(ComputeLevenshteinDistance(words1[i], words2[i]), fullWordValue);
				}
			}

			return (int) totaldistance;
		}
		
		/// <summary>
		/// Compute the distance between two strings.
		/// </summary>
		private static int ComputeLevenshteinDistance(string s, string t) {

			int n = s.Length;
			int m = t.Length;
			int[,] d = new int[n + 1, m + 1];

			// Step 1
			if (n == 0) {
				return m;
			}

			if (m == 0) {
				return n;
			}
			// Step 2
			for (int i = 0; i <= n; d[i, 0] = i++) {
			}

			for (int j = 0; j <= m; d[0, j] = j++) {
			}
			// Step 3
			for (int i = 1; i <= n; i++) {
				//Step 4
				for (int j = 1; j <= m; j++) {
					// Step 5
					int cost = (t[j - 1] == s[i - 1]) ? 0 : 1;

					// Step 6
					d[i, j] = Math.Min(
						Math.Min(d[i - 1, j] + 1, d[i, j - 1] + 1),
						d[i - 1, j - 1] + cost);
				}
			}
			// Step 7
			return d[n, m];
		}

		public static void InitializeHashTables() {
			////////////////////////////////////////////////////////
			// Populate the pregenerated K values for the polynomial hash calculation
			pregeneratedKWordValues = new long[NumPregeneratedValues];
			pregeneratedKMultiwordValues = new long[NumPregeneratedValues];
			for (int i = 0; i < NumPregeneratedValues; i++) {
				pregeneratedKWordValues[i] = GetPolynomialKValueReal(i, kForWordHash);
			}

			// pregenerated K values for the multi word
			// these need to go from higher to lower, for the rolling algorithm
			// and we know that it will always be exactly 4
			for (int i = 0; i < 4; i++) {
				pregeneratedKMultiwordValues[i] = GetPolynomialKValueReal(3 - i, kForMultiWordHash);
			}
		}
		public static List<long> CalculateHashes(List<string> allwords) {

			List<long> dafHashes = new List<long>();

			for (int iword = 0; iword < allwords.Count; iword++) {
				long hash = GetWordSignature(allwords[iword]);
				dafHashes.Add(hash);
			}

			return dafHashes;
		}

		static long GetWordSignature(string word) {

			// make sure there is nothing but letters
			word = Regex.Replace(word, "[^א-ת]", "");
			word = Get2LetterForm(word);

			long hash = 0;

			for (int i = 0; i < word.Length; i++) {
				int chval = (int)word[i];
				chval = chval - 'א' + 1;
				hash += (chval * GetPolynomialKWordValue(i));
			}

			return hash;
		}

		static char GetNormalizedLetter(char ch) {
			switch (ch) {
				case 'ם':
					return 'מ';
				case 'ן':
					return 'נ';
				case 'ך':
					return 'כ';
				case 'ף':
					return 'פ';
				case 'ץ':
					return 'צ';
				default:
					return ch;
			}
		}

		static long GetPolynomialKMultiWordValue(int pos) {

			if (pos < NumPregeneratedValues) {
				return pregeneratedKMultiwordValues[pos];
			}

			return GetPolynomialKValueReal(pos, kForMultiWordHash);

		}

		static long GetPolynomialKWordValue(int pos) {

			if (pos < NumPregeneratedValues) {
				return pregeneratedKWordValues[pos];
			}

			return GetPolynomialKValueReal(pos, kForWordHash);

		}

		static long GetPolynomialKValueReal(int pos, int k) {

			int ret = k;

			if (pos == 0)
				return 1;

			// assuming that k is 41

			for (int i = 1; i < pos; i++) {
				ret = ret * k;
			}

			return ret;

		}

		static string Get2LetterForm(string s) {

			if (s == "ר")
				return "רב";

			if (s.Length < 3)
				return s;

			// take a word, and keep only the two most infrequent letters
			List<Tuple<int, int>> freqchart = new List<Tuple<int, int>>();

			for (int ichar = 0; ichar < s.Length; ichar++) {
				char ch = GetNormalizedLetter(s[ichar]);
				freqchart.Add(new Tuple<int, int>(lettersInOrderOfFrequency.IndexOf(ch), ichar));
			}

			// sort it descending, so the higher they are the more rare they are
			freqchart.Sort((x, y) => y.Item1.CompareTo(x.Item1));
			int letter1 = freqchart[0].Item2;
			int letter2 = freqchart[1].Item2;

			// now put those two most frequent letters in order according to where they are in the words
			if (letter1 < letter2) {
				return "" + s[letter1] + s[letter2];
			}
			else {
				return "" + s[letter2] + s[letter1];
			}
		}



	}
}
