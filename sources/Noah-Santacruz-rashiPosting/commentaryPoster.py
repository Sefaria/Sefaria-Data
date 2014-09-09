#By Noah Santacruz 2014
#github username: nsantacruz

import urllib.request
from urllib.parse import urlencode
from urllib.error import HTTPError,URLError
from bs4 import BeautifulSoup
from collections import OrderedDict
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import os
import json
#NOTE: DHm = dibur hamaschil = single commentary of rashi or tosafos

#this file takes parsed rashi and tosafos commentary on gemara and posts it to the corresponding lines of gemara on sefaria.org
#problems encountered:
#1-rashis aren't necessarily in the exact order of the gemara
#2- rashi's version of the gemara often doesn't exactly match the gemara we have
#3- either rashi or the gemara will use an abbreviation, while the other won't

#solutions
#1- although rashis are not necessarily in order, they are generally in the right place, give or take 1 or 2 rashis:
        #search through the dhms linearly and find single line of gemara that seems to match
        #continue with next dhm, starting from beginning of amud
        #for next dhm, start from where first dhm was found and continue AT LEAST until second was found, if not further
        #in parallel with this search, relook at first dhm and see if any lines in this range match, if they do, add them to possible matching lines list
        #repeat. last two dhms search until the end of the amud just in case, because you will never go back to check them
#2- use a library called fuzzywuzzy, plus a little logic to determine when two strings are a close enough match to consider it significant
        #basically, you are trying to match one string with another. compare each word of one with the other and see if there are any strings that are at least a textCutoff% match
        #count up all the words that meet this criterion. if the percentage of matching words is above stringCutoff%, the lines are considered matching.
        #associate a score with each match which says how likely you think it is an actual match
        #at the end of each amud, sort the scores and weed out the ones that are below scoreCutoff (this is cutoff relative to the top score for that dhm)
        #if there's only one matching line left, congrats! you (hopefully) matched rashi to gemara!
#3- modify the text before any checking is done
        #get rid of unwantedWords
        #convert abbreviations to full words





gemara_root = "c:\\My Web Sites\\WikiGemara2\\web\\" # where wikisource-downloaded gemara files are located
parsed_root = "C:\\Users\\nss\\Desktop\\Programming\\sfaria\\rashiPosting" # file location of parsed rashi/tosafos files. Read through these and check where each dhm appears on daf
sefaria_root = "http://sefaria.org" #root of where text is located. also could be dev.sefaria.org

#here are some variables to help determine which rashi matches which line of gemara
stringCutoff = 79 
backSearchStringCutoff = 90 #
textCutoff = 0.65
scoreCutoff = 0.1 # if a score is more than 10% less than the top score for that dhm, it is not considered as a possible match for that line.
notFoundCutoff = 4 #cutoff for how many dhms are not found until we say that something else must be wrong

#a list of prefixes that either rashi or the gemara uses. If you need to remove these to get a match, deduct from the line score accordingly
listOfPrefixes = ['ב','ה','ד','מ','ו','ל']
#these words are not considered part of the DHm
unwantedWords = ["כו'","'כו","כו","וכו'",'ה"ג','גרסינן',"גמ'","וגו'"]
#convert all abbreviations to full form
abbreviations = {'אא"כ':'אלא אם כן',
                 'אע"ג':'אף על גב',
                 'אע"פ':'אף על פי',
                 'א"ר':'אמר רב',
                 'ב"ה':'בית הלל',
                 'ב"ש':'בית שמאי',
                 "ג'":"שלש",
                 "ד'":"ארבע",
                 'ה"מ':'הני מילי',
                 'ה"נ':'הכי נמי',
                 'הנ"מ':'הני מילי',
                 'ה"ק':'הכי קאמר',
                 "י'":'עשר',
                 'י"א':'יש אומרים',
                 'יו"ט':'יום טוב',
                 'למ"ד':'למאן דאמר',
                 'מ"מ':'מכל מקום',
                 'מנה"מ':'מנא הני מילי',
                 'קמ"ל':'קא משמע לן',
                 'ק"ש':'קרית שמע',
                 "ר'":'רב',
                 'ת"ש':'תא שמע',
                 'ת"ר':'תנו רבנן',
                 
                 
                 
                 
                 
                 }
dafLines = {}
dafDHms = []
#some stats
totalDHms = 0
notFound = 0
numAmudDHms = 0
numAmudNotFound = 0
numAmudAmbig = 0


def post_dhm(mesechta,daf,dhmObj,engComm):
        
        dhm = ''
        line = 0
        text = ''
        numOnLine = 0
        
        for prop in dhmObj:
                if prop == 'dhm':
                        dhm = dhmObj[prop]
                elif prop == 'text':
                        text = dhmObj[prop]
                elif prop == 'postable_lines':
                        if len(dhmObj[prop]) > 1 or len(dhmObj[prop]) == 0:
                                # if dhm is ambiguous, don't post it
                                return
                        line = dhmObj[prop][0]
                elif prop == 'numOnLine':
                        numOnLine = dhmObj[prop]

        #I know this url looks really crypt...Isn't it cool and dynamic!
        url = '%s/api/texts/%s_on_%s.%s.%s.%s' % (sefaria_root,engComm,mesechta,daf,line,numOnLine)
        
        index = {
                'text': text,
                'versionTitle':'Wikisource Rashi',
                'versionSource':'1.0',
                'versionUrl':"http://he.wikisource.org/wiki/%D7%AA%D7%9C%D7%9E%D7%95%D7%93_%D7%91%D7%91%D7%9C%D7%99",
                'language':"he"
        }
        indexJson = json.dumps(index)
        values = {
                'json': indexJson,
                'apikey': 'BFFjEtnWHZbbHEut6jMw9gKlXWzRlJeyMSzDUyxuw60'
                
        }

        data = urlencode(values)
        data = data.encode('utf-8')
        
        try:
                response = urllib.request.urlopen(url, data)
                #print(response.read())
        except HTTPError as e:
                print('Error code: ', e.code)


def post_amud(mesechta,daf,engComm):
        global dafDHms
        print(mesechta + " " + daf)
        numPosted = 0
        for dhmObj in dafDHms:
                post_dhm(mesechta,daf,dhmObj,engComm)
                numPosted += 1
                print('dhm posted (%d/%d)' % (numPosted,len(dafDHms)))
        
        
                        


def get_index(mesechta,daf,line,withCommentary=False):
        global sefaria_root
        
        if withCommentary:
                url = sefaria_root + '/api/texts/' + mesechta + '.' + daf + '.' + line + '?context=0'
        else:
                url = sefaria_root + '/api/texts/' + mesechta + '.' + daf + '.' + line + '?context=0&commentary=0'
        try :
                respObj = urllib.request.urlopen(url)
                decoded = respObj.read().decode("utf-8")
                jsoned = json.loads(decoded)
                
                splice = jsoned['he']
                return str(splice)
        except HTTPError as e:
                print(":( HTTP Error: ",e.code , url)
        except URLError as e:
                print(";( URL Error: ",e.reason , url)

def get_daf(mesechta,daf,withCommentary=False):
        global sefaria_root
        
        if withCommentary:
                url = sefaria_root + '/api/texts/' + mesechta + '.' + daf + '?context=0'
        else:
                url = sefaria_root + '/api/texts/' + mesechta + '.' + daf + '?context=0&commentary=0'
        try :
                respObj = urllib.request.urlopen(url)
                decoded = respObj.read().decode("utf-8")
                jsoned = json.loads(decoded)
                
                splice = jsoned['he']
                return str(splice)
        except HTTPError as e:
                print(":( HTTP Error: ",e.code , url)
        except URLError as e:
                print(";( URL Error: ",e.reason , url)
                
def get_num_lines(mesechta,daf):
        for i in range(1,1000):
                response = get_index(mesechta,daf,str(i))
                if not test_if_valid_line(response):
                        break
        return i-1
def test_if_valid_line(string):
        if '[]' in string:
                return False
        else:
                return True


def get_line_with_text(mesechta,daf,textIndex,startIndex=1,lastDHm=False):
        originalStartIndex = startIndex #keep track because we reset it later on
        restarted = False
        dhmFound = False
        dhmJustFound = False
        text = dafDHms[textIndex]['dhm']
        if len(dafDHms[textIndex]['lines']) > 0:
                print("OH NO!")
        currIndex = textIndex
        prevText = None
        prevTextIndex = -1
        prevIndexes = []
        originalStart = startIndex
        tempList = []
        #this if statement looks back at previous dhms and tries to see where else they might appear, given that we know information about the dhms after them (a.k.a. IIs method)
        if currIndex >= 2:
                for j in range(currIndex-2,-1,-1):
                        prevList = dafDHms[j]
                        if len(prevList['lines']) > 0 and startIndex != prevList['lines'][0]:
                                prevText = prevList['dhm']
                                startIndex = prevList['lines'][0]
                                prevTextIndex = j
                                break
                        elif len(prevList['lines']) == 0:
                                prevText = prevList['dhm']
                                prevTextIndex = j
                                break
        reachedEndOfAmud = False
        i = startIndex
        while i < 200:             #arbitrary number way higher than you should ever go
                try:
                        response = dafLines[i]
                except KeyError as e:
                        
                        response = get_index(mesechta,daf,str(i))
                        response = replaceAbbrevs(response)
                        if not test_if_valid_line(response):
                                if not restarted and len(tempList) == 0:
                                        i = 1
                                        restarted = True
                                        print('restart')
                                        continue
                                elif lastDHm:
                                        reachedEndOfAmud = True
                                        break
                                else:
                                        print("REALLY NOT FOUND")
                                        print('originalStartIndex: ' + str(originalStartIndex))
                                        break

                        dafLines[i] = response

                if prevText is not None:
                        if strict_find(prevText,prevTextIndex,response,i) or fuzzy_find(prevText,prevTextIndex,response,i,True):
                                prevIndexes.append(i)
                try:
                        #see if this this dhm has already been found on this line
                        dafDHms[textIndex]['lines'].index(i)
                except ValueError as e:
                        
                        #try to combine every two lines. this will hopefully deal with dhms that span two lines yet won't give false positives
                        if i >= 2 and not dhmJustFound:
                                prevLine = dafLines[i - 1]
                                response = response + prevLine
                        if dhmJustFound:
                                dhmJustFound = False
                        if strict_find(text,textIndex,response,i) or fuzzy_find(text,textIndex,response,i):
                                #f.write("\n response long" + response + " text " + text)
                                #f.write("\n\tindex: " + str(i))
                                #just found new DHm, means that old DHm can be anywhere in range(prevIndex,startIndex)
                                #indexArray = back_search(prevIndex,startIndex,prevText,mesechta,daf)
                                tempList.append(i)
                                dhmFound = True
                                dhmJustFound = True
                                #make sure you always loop until at least the originalStartIndex. Otherwise, if you find rashi before reaching it, you'll return to soon :(
                                if dhmFound and i >= originalStartIndex:
                                        appendIndexes(tempList,textIndex,False) 
                                        if prevText is not None and len(prevIndexes) >= 1:
                                                #print(str(len(prevIndexes)) + " found!!!!!!!!!!!!")
                                        
                                                appendIndexes(prevIndexes,prevTextIndex,True)
                                                #tempList.extend(indexArray)
                                        if not lastDHm:                #if it's the last one, keep searching till the end of the daf
                                                return tempList

                i += 1
        return tempList

def appendIndexes(indexList,DHmIndex,backfound=False):

        for ind in indexList:
                try:
                        dafDHms[DHmIndex]['lines'].index(ind)
                except ValueError as e:
                        if ind > -1:
                                dafDHms[DHmIndex]['lines'].append(ind)
        #after appending, filter and sort
        dafDHms[DHmIndex]['postable_lines'] = list(filterLines(dafDHms[DHmIndex]['scores']).keys())
        dafDHms[DHmIndex]['lines'] = list(dafDHms[DHmIndex]['scores'].keys())
        dafDHms[DHmIndex]['lines'].sort()

#returns the number of matching words
def fuzzy_find(text,textIndex,response,line,backSearch=False):
        text = text.replace('ין','ים')
        response = response.replace('ין','ים')
        if not backSearch:
                cutoff = stringCutoff
        else:
                cutoff = backSearchStringCutoff
        words = text.split(" ")
        numMatching = 0
        lenWords = len(words)
        lowestIndex = 100 #to tell if rashi starts at (approximately) the beginning of the line of the gemara
        i = 0
        scorePenalties = 0 #give a penalty for not as exact a match
        for word in words:
                try:
                        unwantedWords.index(word)
                        #print("FOUND UNWANTED WORD")
                        lenWords -= 1
                        continue
                except ValueError as e:
                        True
                word = word.strip()
                '''try:
                        listOfPrefixes.index(word[0])
                        print("STRIPPED")
                        word = word[1:]
                except ValueError as e:
                        True'''
                if fuzz.partial_ratio(word,response) >= cutoff:
                        if i < lowestIndex:
                                lowestIndex = i
                        numMatching+=1
                elif response.find(word[1:]) != -1: #second condition tries to deal with prefixes...it's kind of a shot in the dark
                        if i < lowestIndex:
                                lowestIndex = i
                        numMatching +=1
                        scorePenalties += (1-textCutoff)/2 #you can only substitute abbrevs twice before it's not considered a match
                        
                i += 1
        if lenWords <= len(response.split(" ")):
                wordLen =  lenWords
        else:                            #meaning rashi text is longer than gemara. probably rashi doesn't actually match or goes on to next line
                if lowestIndex <= 1: #check if at least one word in the rashi is near the beginning of the line, meaning there's at least a chance it overflows to the next line
                        wordLen = len(response.split(" "))
                else:
                        return False

        try:
                percMatching = numMatching/wordLen - scorePenalties
        except ZeroDivisionError as e:
                return False
        
        #print("RATIO: " + str(percMatching))
        if percMatching >= textCutoff:
                setScore(percMatching,textIndex,line)
                return True
        else:
                return False

def strict_find(text,textIndex,response,line):
        if response.find(" " + text) > -1:
                #exact match should always win
                setScore(1,textIndex,line)
                return True
        else:
                return False

def setScore(wordPerc,DHmIndex,line):
        dafDHms[DHmIndex]['scores'][line] = wordPerc

def replaceAbbrevs(text):
        unabbrevText = text
        words = text.split(" ")
        for word in words:
                try:
                        #real abbreviations tend not to start with these letters. If they do, they are probably prefixes and are interchangeable
                        #but if SECOND letter is " than we know the letter in question is not a prefix and actually part of the abbreviation
                        if (word[0] == 'ו' or word[0] == 'ב') and word[1] != '"':
                                unabbrev = word[0] + abbreviations[word[1:]]
                        else:
                                unabbrev = abbreviations[word]
                        unabbrevText = unabbrevText.replace(word,unabbrev)
                except KeyError as e:
                        True
                except IndexError as yo:
                        True

        return unabbrevText

                      


def filterLines(scoreDict):
        _max = 0
        goodList = {}
        for i in scoreDict:
                if scoreDict[i] > _max:
                        deltaMax = abs(scoreDict[i] - _max)
                        if deltaMax >= scoreCutoff:
                                goodList = {}
                        else:
                                tempDict = {}
                                for j in goodList:
                                        if abs(goodList[j] - scoreDict[i]) < scoreCutoff:
                                                tempDict[j] = goodList[j]
                                goodList = tempDict
                        _max = scoreDict[i]
                        goodList[i] = scoreDict[i]
                elif abs(scoreDict[i] - _max) < scoreCutoff:
                        goodList[i] = scoreDict[i]
        '''if len(scoreDict) != len(goodList):
                print("NOT EQUAL------------------------------")'''
        return goodList
        
                        
                


def lcs(a, b):
        lengths = [[0 for j in range(len(b)+1)] for i in range(len(a)+1)]
        # row 0 and column 0 are initialized to 0 already
        for i, x in enumerate(a):
                for j, y in enumerate(b):
                        if x == y:
                                lengths[i+1][j+1] = lengths[i][j] + 1
                        else:
                                lengths[i+1][j+1] = max(lengths[i+1][j], lengths[i][j+1])
        result = ""
        x, y = len(a), len(b)
        while x != 0 and y != 0:
                if lengths[x][y] == lengths[x-1][y]:
                        x -= 1
                elif lengths[x][y] == lengths[x][y-1]:
                        y -= 1
                else:
                        assert a[x-1] == b[y-1]
                        result = a[x-1] + result
                        x -= 1
                        y -= 1
        return result

def get_commentary(filename,commentary,outputfile):
        engComm = commentary_translator(commentary)
        fileHasError = False
        commErr = False
        
        f = open(engComm + '\\' + outputfile,'w',encoding='utf-8')
                
        #filePath = gemara_root + mesechta + '_' + daf + '_' + amud + ".html"
        filePath = gemara_root + filename
        try:
                amud = open(filePath,"r",encoding='utf-8')
        except IOError as e:
                #print(e)
                print('ERROR opening local amud')
                return []
        soupAmud = BeautifulSoup(amud)
        #print(soupAmud.prettify().encode('utf-8'))
        rashi_h2 = None
        for h2 in soupAmud.find_all('h2'):
                if str(h2.contents) is not None and (str(h2.contents).find(commentary)) is not -1: #or .find("rashi") is not -1):
                        rashi_h2 = h2
                        print('found')
                        break
                else:
                        fileHasError = True
        if rashi_h2 is not None:
                currSib = rashi_h2
                for i in range(1001):
                        nextSib = currSib.next_sibling
                        currSib = nextSib
                        
                        if nextSib is None:
                                break
                        if nextSib.find('<b>') is -1:
                                continue
                        #print(type(nextSib))
                        #f.write(str(nextSib) + '\n')
                        reachedFirstRashi = False
                        if nextSib.find('b') is not None:
                                #found some rashi or tosfos!
                                #print(str(nextSib.find('b')).encode('utf-8'))
                                #print(nextSib.get_text().encode('utf-8'))
                                reachedFirstRashi = True
                                #f.write(nextSib.find('b').get_text().replace('\n','') + '\n' + nextSib.get_text() + '\n')
                                
                        elif reachedFirstRashi and nextSib.get_text() is not '':
                                fileHasError = True
                                print('no b tag')
                                break
                        
        else:
                print('commentary not found!')
                fileHasError = True
                commErr = True
        #commentaryDict['yo'] = 7
        #f.write(str(commentaryDict))
        f.close()
        amud.close()
        if fileHasError:
                errors = open('errors.txt','a',encoding='utf-8')
                #errors.write(engComm + '\\' + filename + ' ' + str(commErr) + '\n')
                errors.close()
def get_all_commentary(commentary):
        i = 0
        for filename in os.listdir(gemara_root):
                '''i+=1
                if i > 10:
                        break'''
                get_commentary(filename,commentary,(filename.split('.html')[0] + '.txt'))

def push_commentary(mesechta,daf,amud,commentary):
        global dafDHms
        engComm = commentary_translator(commentary)
        engMesechta = mesechta_translator(mesechta.replace('_',' '))
        engDaf = daf_translator(daf,amud)
        print(engMesechta,engDaf,engComm)
        commFile = open(engComm + '\\' + mesechta + '_' + daf + '_' + amud + '.txt','r',encoding='utf-8')
        commText = commFile.read()
        commFile.close()
        #update dafDHms
        parseCommentary(commText,engComm)

        #num_lines = get_num_lines(engMesechta,engDaf.replace('.',''))
        currIndex = 1
        numMissingInARow = 0
        lastDHmFound = -1 #index of last dhm found. In case I think there was a problem with it later on...
        lastIndexFound = -1
        i = 0
        while i < len(dafDHms):
                isLastDHm = False
                if i >= len(dafDHms)-2:
                        isLastDHm = True
                '''if numMissingInARow == notFoundCutoff:
                        numMissingInARow = 0
                        dafDHms[lastDHmFound]['lines'] = []
                        dafDHms[lastDHmFound]['scores'] = {}
                        
                        if lastDHmFound >= 1: 
                                print(i-notFoundCutoff-1)
                                currIndex = lastIndexFound-1 #start searching at a line before this bad dhm
                                i = i - notFoundCutoff #and return index so that you re-search the 'missing' dhms
                        else:
                                currIndex = 1
                                i = 1

                        
                        continue'''
                tempIndex = get_line_with_text(engMesechta.replace(' ','_'),engDaf,i,currIndex,isLastDHm)
                print(str(tempIndex))
                
                
                
                if tempIndex != [-1] and len(tempIndex) != 0:
                        currIndex = tempIndex[0]
                        lastDHmFound = i
                        lastIndexFound = currIndex
                        numMissingInARow = 0
                else:
                        #f.write("\nNOT FOUND!!!  " + engMesechta + " " + engDaf + " " + dafDHms[i]['dhm'] + " " + str(currIndex) + " ")
                        numMissingInARow += 1


                i+=1
                
        f.write("\n"+ engMesechta + " AMUD " + daf + " " + amud + " " + engComm + " -------------------------------------")
        eFile.write("\n"+ engMesechta + " AMUD " + daf + " " + amud + " " + engComm + " -------------------------------------")
        aFile.write("\n"+ engMesechta + " AMUD " + daf + " " + amud + " " + engComm + " -------------------------------------")
        postRashiProcessing()
        printDafDHms()
        post_amud(engMesechta,engDaf,engComm)
        if numAmudDHms >= 1:
                print("AMUD STATS: not found percentage = " + str(round(numAmudNotFound/numAmudDHms * 10000)/100) + "%")
                print("AMUD STATS: ambiguous percentage = " + str(round(numAmudAmbig/numAmudDHms * 10000)/100) + "%")

def push_mesechta(mesechta,commentary):
        global dafLines, notFound, totalDHms
        i = 0
        hebMes = mesechta_translator(mesechta,False)
        hebCommentary = commentary_translator(commentary)
        for filename in os.listdir(parsed_root + '\\' + 'test'):
                #loop through all amudim, but only amudim in the mesechta you want to post
                if filename.find(hebMes) != -1:
                        nameList = filename.split('_')
                        
                        dafLines = {}
                        if len(nameList) == 3:
                                push_commentary(nameList[0],nameList[1],nameList[2].replace('.txt',''),hebCommentary)
                        elif len(nameList) == 4:
                                push_commentary(nameList[0] + "_" + nameList[1],nameList[2],nameList[3].replace('.txt',''),hebCommentary)

        print("STATS: not found percentage = " + str(round(notFound/totalDHms * 10000)/100) + "%")
        

def printDafDHms():
        global notFound, totalDHms,numAmudDHms, numAmudNotFound, numAmudAmbig
        numAmudDHms = 0
        numAmudNotFound = 0
        numAmudAmbig = 0
        for i in range(len(dafDHms)):
                f.write('\n' + dafDHms[i]['dhm'])
                for stuff in dafDHms[i]:
                        if stuff != 'dhm':
                                f.write('\n\t' + stuff + ": " + str(dafDHms[i][stuff]))
                                if stuff == 'lines' and len(dafDHms[i]['lines']) == 0:
                                        eFile.write('\n' + dafDHms[i]['dhm'])
                                        eFile.write('\n\ttext: ' + str(dafDHms[i]['text']))
                                        numAmudNotFound += 1
                                        notFound+=1
                                if stuff == 'postable_lines' and len(dafDHms[i]['postable_lines']) > 1:
                                        aFile.write('\n' + dafDHms[i]['dhm'])
                                        aFile.write('\n\t' + stuff + ": " + str(dafDHms[i][stuff]))
                                        aFile.write('\n\ttext: ' + str(dafDHms[i]['text']))
                                        numAmudAmbig += 1
                totalDHms+=1
                numAmudDHms+=1
        if numAmudDHms >= 1:
                f.write("\nAMUD STATS: not found percentage = " + str(round(numAmudNotFound/numAmudDHms * 10000)/100) + "%")
        else:
                f.write("\n AMUD STATS: not found percentage = 0% (b/c there were no rashis)")
        f.write("\n-----------------------------------------------")
        

def parseCommentary(commText,engCommentary):
        global dafDHms
        dafDHms = []
        commList = commText.split('\n')
        tempDHm = ''
        tempComm = ''
        for line in commList:
                if tempDHm == '':
                        tempDHm = line.strip()
                elif tempComm == '':
                        tempComm = line.strip()
                        #because of the way tosfos was parsed from wikisource, the real dhm is actually in the text
                        if engCommentary == 'Tosafot' and tempComm != '':
                                tempDHm = tempComm.split('.')[0]
                        
                        
                if tempDHm != '' and tempComm != '':
                        tempDHm = replaceAbbrevs(tempDHm)
                        #each dhmObj has a bunch of useful properties.
                        #dhm - the dibur hamaschil
                        #text- the text of the rashi. includes dibur hamaschil
                        #lines - all relevant lines with the dhm. these are local to where the rashis around it were found
                        #scores - each line is given a corresponding percentage 'score' that says how likely the rashi is actually on that line
                        #postable_lines - contains only the lines that are the most likely to be correct. hopefully this narrows it down to one line most of the time
                        #numOnLine - need to know which rashi this one is on its line. this is just for posting to sefaria and otherwise has no meaning
                        dafDHms.append(OrderedDict({'dhm':tempDHm,'text':tempComm,'lines':[],'scores':{},'postable_lines':[],'numOnLine':0}))
                        tempDHm = ''
                        tempComm = ''

        #print(str(commDict).encode('utf-8'))

#for now, this gets the number of rashis on any given line and then sets the 'numOnLine' property for each one accordingly, so that they have unique numbers
def postRashiProcessing():
        global dafDHms
        lineReps = {}
        for i in range(len(dafDHms)):
                if len(dafDHms[i]['postable_lines']) == 1:
                        line = dafDHms[i]['postable_lines'][0]
                        try:
                                numReps = len(lineReps[line].keys())
                                lineReps[line][i] = numReps + 1
                        except KeyError as e:
                                #if it doesn't exist, value is initialized to 1
                                lineReps[line] = OrderedDict({i:1})

        for line in lineReps:
                for index in lineReps[line]:
                        dafDHms[index]['numOnLine'] = lineReps[line][index]
        

def mesechta_translator(inp,hebToEng=True):
        try:
                
                transDict = {'ברכות':'Berakhot','שבת':'Shabbat','עירובין':'Eruvin','פסחים':'Pesachim','יומא':'Yoma','ראש השנה':'Rosh Hashanah','תענית':'Taanit','ביצה':'Beitzah','מועד קטן':'Moed Katan','סוכה':'Sukkah','מגילה':'Megillah','חגיגה':'Chagigah','יבמות':'Yevamot','כתובות':'Ketubot','נדרים':'Nedarim','נזיר':'Nazir','סוטה':'Sotah','גיטין':'Gittin','קידושין':'Kiddushin','בבא קמה':'Bava Kamma','בבא מציעה':'Bava Metzia','בבא בתרא':'Bava Batra','סנהדרין':'Sanhedrin','מכות':'Makkot','שבועות':'Shevuot','עבודה זרה':'Avoda Zarah','הוריות':'Horayot','זבחים':'Zevachim','מנחות':'Menachot','חולין':'Chullin','בכורות':'Bekhorot','ערכין':'Arakhin','כריתות':'Keritot','תמיד':'Tamid','נידה':'Niddah'}
                if hebToEng:
                        return transDict[inp]
                else: #we want to translate from english to hebrew
                        for hebMes in transDict:
                                if transDict[hebMes] == inp:
                                        return hebMes
                        print('INPUT ERROR: Please check your spelling for the mesechta and try again...')
        except KeyError as e:
                print('KEY ERROR ' + inp.encode('utf-8'))
def daf_translator(daf,amud):
        gematria = 0
        for letter in daf:
                relativeVal = int.from_bytes(letter.encode('utf-8'),byteorder='big') - int.from_bytes('א'.encode('utf-8'),byteorder='big') + 1
                if relativeVal >= 12 and relativeVal <= 13:
                        relativeVal -= 1
                if relativeVal == 15:
                        relativeVal -= 2
                if relativeVal >= 17 and relativeVal <= 19:
                        relativeVal -= 3
                if relativeVal == 21:
                        relativeVal -= 4
                if relativeVal >= 23:
                        relativeVal -= 5
                print('original: ' + str(relativeVal))
                if relativeVal > 10 and relativeVal < 20:
                        relativeVal = (int(str(relativeVal)[1]) + 1) * 10
                elif relativeVal >= 20 and relativeVal < 26:
                        relativeVal = (int(str(relativeVal)[1]) + 2) * 100
                print('after: ' + str(relativeVal))
                gematria += relativeVal

        if amud == 'א':
                amud = 'a'
        elif amud == 'ב':
                amud = 'b'
        return str(gematria) + '' + amud

def commentary_translator(commentary):
        engComm = ''
        if commentary == ('רש"י'):
                engComm = 'Rashi'
        elif commentary == 'תוספות':
                engComm = 'Tosafot'
        elif commentary == 'ר"ן':
                engComm = 'Ran'
        elif commentary == 'רשב"ם':
                engComm = 'Rashbam'
        elif commentary == 'Rashi':
                engComm = 'רש"י'
        elif commentary == 'Tosafot':
                engComm = 'תוספות'
        elif commentary == 'Ran':
                engComm = 'ר"ן'
        elif commentary == 'Rashbam':
                engComm = 'רשב"ם'
        return engComm

#get_index('Sukkah','2','100')
#print(get_num_lines('Berakhot','8a'))
#num_lines = get_num_lines('Berakhot','8a')
#print(get_line_with_text('Berakhot','8a',"כל מי שיש",num_lines))
#get_commentary("שבת_כג_א.html",'רש"י','aaaaaa.txt' )
#get_all_commentary('ר"ן')
#print(mesechta_translator('ברכות').encode('utf-8'))
#print(mesechta_translator('Berakhot',False).encode('utf-8'))
#print(daf_translator('קלד','א'))
#parseCommentary('yo\n\t\nthis i afd')
f = open('logFileAll.txt','a',encoding='utf-8')
eFile = open('logFileNotFound.txt','a',encoding='utf-8')
aFile = open('logFileAmbiguous.txt','a',encoding='utf-8')
#push_commentary('סוכה','מא','א','רש"י')
#push_all_commentary()

#f.write(replaceAbbrevs('אע"פ ששגכךשףגחכש שגכךלח גכש שגכךלח גכש ר\''))
#print(str(filterLines({28:1,27:0.75})))
#post_dhm('Sukkah','4b',{'dhm':'test','text':'קוורטי','postable_lines':[1],'numOnLine':1})

selectedMesechta = input('please type (in english exactly like sefaria\'s naming scheme) the name of the mesechta whose commentary you would like to post\n')
selectedCommentary = input('Thanks! now type (in english lower-case) the commentary you\'d like to post\n')
push_mesechta(selectedMesechta,selectedCommentary)
