from postFile2 import *

def postBook(title, filename, heTitle,categories):
	index = {
	"title": title,
	"titleVariants": [],
	#"heTitle" : heTitle,
	"heTitleVariants" : [],
	"sectionNames": ["Chapter","Halacha"],
	"categories": categories
	}
	textIndex = {
		"versionTitle": "Torat Emet 361",
		"versionSource":  "http://www.toratemetfreeware.com/index.html?downloads",
		"language": "he",	
	}
	actuallyPost = False; # False=> outputting file; True=> post to site
	useRealSite = False; # False=> dev site; True=> real site
	postBookIndex = False; #do False for old book in their DB, and do True for new book.
	symbolAtLevel = ['~', '!'] #put symbols where 'NL' means that NL is the lowest level. COMMON symbols: [ '~','^', '@', '$', '!', '#'] that start a new Chapter/Paragraph/etc in ToratEmet
	displayHeaderSymbols = []	# Put symbols (but not NL) that you want to display header into displayHeaderSymbol with bigger first. ex. displayHeaderSymbol = [ '@', '~']	
	createHeader = [] #these are the headers for which you want to create a headers.csv with
	headerAttr = [] # put in the attributes for the headers in the format: [displayNum , displayLevelType (ex. daf)] . ex. if using 2 header syms = [[1,0], [0,0]]
	useAsNumberForLocation = ['!'] #typically used for commentary (usually ['!']), where not every line is there but there is only a commentary on some lines.
	postSifKatans = False # if you want to post Sif Katans (which are contained within a line of TE)
	commentary = False #if this is a commentary on something make it true. <book title> on <thing it's a comment on> is assumed to be the title of this book
	postFile2(filename, index, textIndex,symbolAtLevel, actuallyPost, useRealSite,postBookIndex, displayHeaderSymbols, createHeader, headerAttr, useAsNumberForLocation, postSifKatans, commentary)
	
	


titleList = []
fileA = open('rambam.txt' , 'r')
bookTitles = fileA.readlines() 
for bookTitle in bookTitles:
	split = bookTitle.rsplit(',',1)
	titleList.append([split[1].replace('\n',''),split[0].replace('\n','')])


def findEnInTitleList(word):
	global titleList
	for item in titleList:
		if(item[0] == word):
			return item[1]
	return ""

def findHeInTitleList(word):
	global titleList
	for item in titleList:
		if(item[1] == word):
			return item[0]
	return ""
	
	
def divideBook(filename, outpath):
	file = open(filename, 'r');
	
	booksList = open(outpath + 'booksList.txt', 'w');
	lines = file.readlines();

	bookCount =0
	output = open(outpath + 'dummy.txt', 'w');
	for line in lines:
		if(line.find('#') ==0): #start new books
			output.close()
			newFileName = outpath + str(bookCount) + ".txt"
			output = open(newFileName, 'w') 
			output.write('\n\n\n\n')
			booksList.write(newFileName + "$$$$" + line[2:]) #.replace(" ","_")
			bookCount = bookCount +1
			
		else:
			output.write(line)
	
	
def uploadSefer(sefer,originalFileName):
	divideBook('files/' + originalFileName, 'divided/' + sefer + '_')

	booksListFile = open('divided/' + sefer + "_booksList.txt" , 'r')
	booksList = booksListFile.readlines()
	i = 0 
	for bookName in booksList:
		split = bookName.split("$$$$")
		filename = split[0]
		heTitle = split[1].replace('\n','')
		enTitle = findEnInTitleList(heTitle)
		heTitle = findHeInTitleList(enTitle)
		print(str(i) + enTitle + ' ' + heTitle)
		if(enTitle == ''):
			dummy = input('couldnt find the enTitle of this book: ' + filename)
		testLetter = '' ##this is only for testing
		title = "Mishneh Torah, " + enTitle + testLetter
		heTitle = '' #"משנה תורה," + " "  + heTitle + testLetter
		categories = ['Halacha', "Mishneh Torah" , "Sefer " + sefer]
		
		postBook(title,  filename, heTitle,categories)
		
		i +=1

sefers = ["Madda", "Ahavah", "Zemanim", "Nashim", "Kedushah", "Haflaah", \
"Zeraim", "Avodah", "Korbanot", "Taharah", "Nezikim", "Kinyan", \
"Mishpatim", "Shoftim"]
originalFileNames = ['90002_מדע.txt', "90003_אהבה.txt", "90004_זמנים.txt",\
 "90005_נשים.txt", "90006_קדושה.txt", "90007_הפלאה.txt",\
 "90008_זרעים.txt", "90009_עבודה.txt", "90010_קרבנות.txt", "90011_טהרה.txt",\
 "90012_נזיקין.txt", "90013_קנין.txt", "90014_משפטים.txt", "90015_שופטים.txt"]

for i in range(len(sefers)):
	number = i
	sefer = sefers[number]
	originalFileName = originalFileNames[number]
	uploadSefer(sefer, originalFileName)


"""
Comments/Changes/Problems:
Changed some of the tags

"""
