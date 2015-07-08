from myHTMLparserFile import * 
from postAPI import *
from addTags import *
import copy
import re
import csv

TOTAL_LEVELS = 6
writer = ""

def gematria_converter(num):
	num = re.sub('[^\u05d0-\u05ea]', "", num)
	gematria = 0
	for letter in num:
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
		if relativeVal > 10 and relativeVal < 20:
			relativeVal = (int(str(relativeVal)[1]) + 1) * 10
		elif relativeVal >= 20 and relativeVal < 26:
			relativeVal = (int(str(relativeVal)[1]) + 2) * 100
		gematria += relativeVal
	
	return gematria




def removeHTMLtags(text):
	parser = MyHTMLParser();
	parser.returnValue = "";
	parser.feed(text);
	return parser.returnValue;

def createHeaderCSV(title,symbol,createHeader, levelsCount, levelNumber, line, headerAttr):
	global writer
	if symbol in createHeader:
		row = [title]
		headerLevelCount = []
		for j in range(TOTAL_LEVELS):
			headerLevelCount.append(0)
		for j in range(len(levelsCount)):
			if j  < len(levelsCount) - levelNumber -1: # lower levels should be 0'ed for headers to work
				headerLevelCount[j] = 0
			elif levelsCount[len(levelsCount) - j -1] == 0: ##FIX 0's
				headerLevelCount[j] = 1
			else: #flip the level order (Sefaria Mobile goes from smallest -> largest. This goes other way).
				headerLevelCount[j] = levelsCount[len(levelsCount) - j -1]
		for j in range(len(headerLevelCount)):
			row += [headerLevelCount[j]]
		row += [line[2:]]
		row += headerAttr[createHeader.index(symbol)]
		writer.writerow(row)

		
def postFile2(filename, index, textIndex, symbolList, actuallyPost = True, useRealSite = False, postBookIndex = True, displayHeaderSymbols = [], createHeader = [], headerAttr = [], useAsNumberForLocation = [], postSifKatans = False, commentary = False):
	
	
	if((not postSifKatans and len(index["sectionNames"]) != len(symbolList)) or (postSifKatans and len(index["sectionNames"]) != len(symbolList) )):
		print("ERROR: The lengths of sectionNames and symbolList don't match!!!")
		return
	if len(createHeader) != len(headerAttr):
		print("ERROR: lengths of createHeader and headerAttr don't match!!!")
		return
		
	title = index["title"];
	
	allLinks = []
	originalBookTitle =""
	if commentary:
		originalBookTitle = title.split(" on ",1)[1]
	
	if len(createHeader)  > 0:
		global writer
		ofile = open("header_" + title + ".csv",'w', newline='')
		writer = csv.writer(ofile)
		
	print(filename);
	file = open(filename, 'r');
	outfilename = "outs/out_"  + title + '.txt';
	output = open(outfilename, 'w');
	
	lines = file.readlines();
	
	levelsCount = [];
	for i in range(len(symbolList)):
		levelsCount.append(0)
	
	uploadedTexts = set()
	
	symbolLine = ""
	prevFoundSym = False
	post_index(index, useRealSite, actuallyPost, postBookIndex);#POSTING BOOK INFO # create/edit Sefer Info

	validSymbolsNotPartOfList = [ '~','^', '@', '$', '!', '#']
	for tempSymbol in symbolList:
		validSymbolsNotPartOfList.remove(tempSymbol)
		
	####PARSING INPUT FILE####
	
	for i in range(2, len(lines)): # start at 2 b/c the first lines have other random ToratEmet MetaData
		line = lines[i];
		
		#if(i +1 == 8062):
		#	import pdb
		#	pdb.set_trace()
		
		###skip dumb lines:
		if line.find("**INDEX_WRITE=") > -1: #skip this ugly line
			continue
		
		continueThisLoop = False
		for tempSymbol in validSymbolsNotPartOfList:
			if ( line.find(tempSymbol) == 0):  # skip title, and other ignored symbols
				continueThisLoop = True
		if(continueThisLoop):
			continue
		line = removeHTMLtags(line)
		if len(re.sub('\s',"", line)) < 1:#skip blank line
			continue
		if len(re.sub('\s',"", removeHTMLtags(addTags(line, False)))) < 1:#skip lines that only have HTML and no real text
			addTags(line, True) #update the info about the smallBox
			continue

		###determine levelNumber
		foundSymbol = False
		for levelNumber in range(len(symbolList)): 
			symbol = symbolList[levelNumber];
			if(symbol == 'NL'): #it's a new line that's the level that we aren't talking about.
				foundSymbol = True
				break;
			if line.find(symbol) == 0:  #you found a symbol and thus the levelNumber (it's a new book/chap/paragraph/etc).
				symbolLine = line
				foundSymbol = True
				break;
		
		if symbolLine == "": #never found a symbol yet, so don't do any posting
			continue
		
		if foundSymbol:
			
			if(symbol in useAsNumberForLocation):		
				levelsCount[levelNumber] = gematria_converter(line[1:])
			else:
				levelsCount[levelNumber] += 1
					
			if not (prevFoundSym and (symbolList[prevLevelNumber] in displayHeaderSymbols)):
				for k in range(levelNumber + 1, len(levelsCount)): #reset all previous levels
					levelsCount[k] = 0;
					
			if prevFoundSym and (symbolList[prevLevelNumber] in displayHeaderSymbols):
				#output.write("\n___FOUND PREVOUS SYMBOL__" + str(levelNumber) + "\n" + str(levelsCount))
				levelsCount[levelNumber] -= 1 # return value
				if(symbol in displayHeaderSymbols) or symbol == symbolList[-1]:
					levelsCount[-1] += 1 #this is the line that you are going to want to add to
				#output.write("\n" + str(levelsCount) + "\n")

			#create Header csv
			createHeaderCSV(title,symbol,createHeader, levelsCount, levelNumber, line, headerAttr)
				
			if(symbol in displayHeaderSymbols): #add this header:
				line = "[[[[[[" + line[2:] + "]]]]]]"
			elif symbol == "NL":
				x = 1	##display the line as is
			else:
				continue
			
		textOutPut = removeHTMLtags(line)
		if(postSifKatans): #sifKatan stuff
			pattern = '{{{{[\u05d0-\u05ea]+}}}}'
			sifKatanLines = re.split(pattern, textOutPut)
			sifKatanNums = re.findall(pattern, textOutPut)
			sifKatanLines.remove("")
			if(len(sifKatanLines) != len(sifKatanNums)):
				dummy = input("The number of sifKatanLines and Nums don't match")
		else:
			textOutPut = addTags(textOutPut, True)
		
		
		
		if len(re.sub('\s',"", textOutPut)) < 1: #don't post empty lines
			dummy = input("It's ignoring a line that was filtered out... Make sure there are no errors. (click enter to continue)")
			output.write("__IGNORING LINE__\n");
			levelsCount[levelNumber] -= 1 #return the value to what it was when we thought it was a real line
			try:
				prevLevelNumber = prevLevelNumber #maybe this should say something... this seems pretty dumb
			except: #that should just mean that prevLevelNumber hasn't been assigned yet
				dummyVar =1
			continue;
			
		#FIX levels that are accidentally still 0
		for k in range(len(levelsCount)):
			if levelsCount[k] == 0:
				print("FIXING 0's")
				output.write("FIXING 0's\n")
				levelsCount[k] = 1
				
		levelString = "";
		for k in range(len(levelsCount)):
			levelString += "." +  str(levelsCount[k])
		
		prevFoundSym = foundSymbol
		prevLevelNumber = levelNumber
		
		if i > len(lines) - 5:
			setCountTo0 = False;
		else:
			setCountTo0 = True;
		
		if(postSifKatans):
			lengthOfPosts = len(sifKatanNums)
		else:
			lengthOfPosts = 1

		for k in range(lengthOfPosts):
			if(postSifKatans):
				sifNum = "." + str(gematria_converter(sifKatanNums[k]))
				textOutPut = sifKatanLines[k] + "\n"
				textOutPut = addTags(textOutPut, True)
				if len(re.sub('\s',"", textOutPut)) < 1: #don't post empty lines
					dummy = input("It's ignoring a line that was filtered out... Make sure there are no errors. (click enter to continue)")
					output.write("__IGNORING LINE__\n");
					continue
				levelString = "";
				for k in range(len(levelsCount)-1):
					levelString += "." +  str(levelsCount[k])

			else:
				sifNum = ""
		
			levelInformation = title + levelString + sifNum
			output.write(str(i+1) + ". " + levelInformation +   " "  + symbolLine);
			output.write(textOutPut);
					
			
			
			if levelInformation not in uploadedTexts:
				uploadedTexts.add(levelInformation)
			else:
				dummy = input("ERROR: YOU'RE TRYING TO REUPLOAD TO THE SAME LOCATION:\n" + levelInformation)
				
			
			if commentary: ##add links
				source1 = (levelInformation).replace(" ", "_")
				source2 = (originalBookTitle + makeLevelString2(levelsCount,postSifKatans)).replace(" ", "_")
				#print(source1,source2)
				allLinks.append(createSingleLink(source1,source2))
			
			#POSTING#################### 1 line at a time.
			postTorah(levelInformation, textOutPut, textIndex, useRealSite,setCountTo0, actuallyPost);
			############################
	if actuallyPost and commentary:
		print("uploading links...")
		postLink(allLinks, useRealSite) #post all the links
		print("finished uploading links.")
		
	if len(createHeader)  > 0:
		ofile.close()
	
def makeLevelString2(levelsCount,postSifKatans):
	if postSifKatans:
		num = len(levelsCount) 
	else:
		num = len(levelsCount) - 1
	levelString2 = "";
	for k in range(num):
		levelString2 += "." +  str(levelsCount[k])
	return levelString2