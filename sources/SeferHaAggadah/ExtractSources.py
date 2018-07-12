# -*- coding: utf-8 -*-
#Extracting the sources of Sefer Agada by Ben Kozuch Spring 2016

#############################################################
####Remove lines from the xml file that represent nekudot####
#############################################################

'''
any unicode value starts with a '05d' or '05e' its a hebrew letter. 
If it starts with '05' and the next letter is a 9,a,b,c or f then its some type of Nekuda or Ta'am
http://unicode.org/charts/PDF/U0590.pdf 
'''
'''
import re
Fout = open("part1_withoutVow.xml","w") 
with open("part1.xml") as Fin:                                  #Rax XML file from ghostscript
    for line in Fin:
        
        matchObj = re.match(r"""<char bbox="\d+ \d+ \d+ \d+" c="(&#x5.*)"/>""",line,re.M|re.I)
        
        if matchObj:                                            # (i.e. if the unicode value starts with a '05')
            
            unicodeVal = matchObj.group(1)
                                                                #only write to file a unicode like that starts with 05 
            if unicodeVal[4:5]=='d' or unicodeVal[4:5]=='e':    #AND the next letter is a 'D' or 'C'

                Fout.write(line)
        else:

            Fout.write(line)
                                                                #if it doesnt start with '05' then print it no matter what
Fin.close()
Fout.close()
'''

#####################################################   
####Create regular Hebrew text file from xml file####
#####################################################

'''
Things to know:
------------------------------------------------------------------ 
The pdf is like the first quadrant of an XY plane flipped on its head. 
Meaning 0,0 is on the top left and as you go towards the right side 
the x value gets bigger and as you go down the y value gets bigger.
X goes from 0 to around 550
Y goes from 0 to around 750
------------------------------------------------------------------
'''

def printHeb(letter,fileObj):
    
    letters = {'&#x5d0;': 'א', '&#x5d1;': 'ב', '&#x5d2;': 'ג', '&#x5d3;': 'ד', '&#x5d4;': 'ה', '&#x5d5;': 'ו', '&#x5d6;': 'ז', '&#x5d7;': 'ח', '&#x5d8;': 'ט', '&#x5d9;': 'י', '&#x5da;': 'ך', '&#x5db;': 'כ', '&#x5dc;': 'ל', '&#x5dd;': 'ם', '&#x5de;': 'מ', '&#x5df;': 'ן', '&#x5e0;': 'נ', '&#x5e1;': 'ס', '&#x5e2;': 'ע', '&#x5e3;': 'ף', '&#x5e4;': 'פ', '&#x5e5;': 'ץ', '&#x5e6;': 'צ', '&#x5e7;': 'ק', '&#x5e8;': 'ר', '&#x5e9;': 'ש', '&#x5ea;': 'ת','&apos;':'^','&#x2014;':' ','&quot;':'"'};
    
    if letter in letters:
        tmpletter = letters[letter]
        tmpletter = tmpletter.decode('utf-8')
        fileObj.write(tmpletter.encode('utf-8'))
    else:
        fileObj.write(letter)


#global variable to fix exploding number problem
lastSmallestXposValue = 50
def extractXYcoord(fourNums):
   
    listOfFourNums = fourNums.split(" ")
    
    global lastSmallestXposValue

    if int(listOfFourNums[0]) > 600:
        listOfFourNums[0] = lastSmallestXposValue
    else:
        lastSmallestXposValue = listOfFourNums[0]

    return int( listOfFourNums[0] ), int( listOfFourNums[1] ) #This is the x and Y coordinate of each letter on the pdf


def determinePageStructure(page):

    fourthLineOnPage = page.split("\n")[4] # the first three lines are <page>\n<block>\n<line>
    matchObj = re.match(r"""<.* bbox="(\d+ \d+ \d+ \d+)" .*>""",fourthLineOnPage,re.M|re.I)
    if matchObj:
        Xpos,Ypos = extractXYcoord(matchObj.group(1))
        if Ypos > 70:
            return True #This page is the beginning of a chapter
        else:
            return False #Not beginning of chapter


import re
Fin = open("part1_withoutVow.xml")
Fout = open("part1_normalHebrew",'w')

Wholefile = Fin.read()

#Some pages in the pdf are completelety empty (i.e. the beginning of a new Chelek is all blank and can through errors)
Wholefile.replace("<page>\n<block>\n</block>\n</page>\n", "") 

pages = Wholefile.split("</page>")

#remove empty last element
pages.pop(len(pages)-1)


#Go through each page and read in the left column the right column
for i in range (1,len(pages)):
    #Each page has a different structure which will dictate how to read in from that page
    beginningOfPerek = determinePageStructure(pages[i])
    
    #initialize variables to be used to read in
    leftColumn = [""]
    rightColumn = [""]
    tmpLineLeft=[]
    tmpLineRight=[]
    YposPrev=0
    latestYposOfChapter = 0


    #Read in left column of this page
    for line in pages[i].split('\n'):

        matchObj = re.match(r"""<char bbox="(\d+ \d+ \d+ \d+)" c="(.*)"/>""",line,re.M|re.I)        
        
        #Only process a line from the XML file if its a letter
        if matchObj:

            Xpos,Ypos = extractXYcoord(matchObj.group(1))
            unicodeVal = (matchObj.group(2)) 
            
            #This if statements assures that we're only reading in letters that are content
            #and not something like a "chelek Rishon" or "perek aleph" which is centered and not on the left or right side
            # Xpos < 300 means its on the left side of the pdf
            #...structure of if statement is ( (x and y) or (a and b) ) and (z)
            if (  (  ((beginningOfPerek)and(Ypos>200)) or ((beginningOfPerek==False)and(Ypos>70)) ) and (Xpos<300) ): 

                #This means we've moved to the next line in the pdf and we need to process the previous line that was read in
                if Ypos - YposPrev > 10:

                    #Flip Line becuase its Hebrew!
                    tmpLineLeft=list(reversed(tmpLineLeft))
                    leftColumn.extend(tmpLineLeft)

                    #Clear Line to get it ready for the next line to be read in
                    tmpLineLeft=[]
 
                    #Update YposPrev
                    YposPrev = Ypos

                tmpLineLeft.append(unicodeVal)
        
        # If its not a letter then it has the following format which just specifies the font
        # <span bbox="495 60 539 60" font="DDJSZK+FbHadasaNewBook-Light" size="11.0000">
        # If it has a font of 13 then its the start of a new section and we need to mark that spot
        # in order to know which sources belong to which section

        else: 

            matchObj2 = re.match(r"""<span bbox="(\d+ \d+ \d+ \d+)".*size="13.*">""",line,re.M|re.I) 

            if matchObj2:

                Xpos,Ypos = extractXYcoord(matchObj2.group(1)) 
                
                #Only consider content and not headers at the top of the page...same as before
                if (  (  ((beginningOfPerek)and(Ypos>200)) or ((beginningOfPerek==False)and(Ypos>70)) ) and(Xpos<300) ):

                    #make sure this is the first time we are placing a "NEWCHAPTER" for this y coordinate
                    #because sometimes there can be multiple lines with this format:
                    # <span bbox="495 60 539 60" font="DDJSZK+FbHadasaNewBook-Light" size="11.0000">
                    # for just one section header
                    if Ypos - latestYposOfChapter > 5:

                        #place NEWCHAPTER symbol    
                        tmpLineLeft.append("NEWCHAPTER")
                        
                        #Update latestYposOfChapter
                        latestYposOfChapter = Ypos


    #Reset Variables for right column
    YposPrev=0
    latestYposOfChapter = 0

    # Read in Right column of this page...
    # same comments as the left column
    for line in pages[i].split('\n'):
        matchObj = re.match(r"""<char bbox="(\d+ \d+ \d+ \d+)" c="(.*)"/>""",line,re.M|re.I)        
        
        if matchObj:
            
            Xpos,Ypos = extractXYcoord(matchObj.group(1))
            unicodeVal = (matchObj.group(2))

            #Notice this time its "Xpos > 300" because its the right side
            if (  (  ((beginningOfPerek)and(Ypos>200)) or ((beginningOfPerek==False)and(Ypos>70)) )   and   (Xpos>300) ):
                if Ypos - YposPrev > 10:
                    tmpLineRight=list(reversed(tmpLineRight))
                    rightColumn.extend(tmpLineRight)
                    tmpLineRight=[]
                    YposPrev = Ypos

                tmpLineRight.append(unicodeVal)
        else:

            matchObj2 = re.match(r"""<span bbox="(\d+ \d+ \d+ \d+)".*size="13.*">""",line,re.M|re.I) 
            
            if matchObj2:

                Xpos,Ypos = extractXYcoord(matchObj2.group(1)) 

                if (  (  ((beginningOfPerek)and(Ypos>200)) or ((beginningOfPerek==False)and(Ypos>70)) ) and(Xpos>300) ):
                    
                    if Ypos - latestYposOfChapter > 5:
                    
                        tmpLineRight.append("NEWCHAPTER")
                        latestYposOfChapter = Ypos

    #Remove all '' from the list of letters because it causes errors
    i=0
    if len(leftColumn)>5:
        while i != len(leftColumn):
            if leftColumn[i]=='':
                leftColumn.pop(i)
            i+=1

        i=0
        while i != len(rightColumn):
            if rightColumn[i]=='':
                rightColumn.pop(i)
            i+=1

        for x in rightColumn:
            printHeb(x,Fout)

        printHeb("\n\n\n\n\n",Fout)
        for x in leftColumn:
            printHeb(x,Fout)

        printHeb("\n\n\n\n\n",Fout)

Fin.close()
Fout.close()



###############################################
####Extract sources and organize by chapter####
###############################################



import codecs
import re
Fin = codecs.open("part1_normalHebrew",'rb',encoding='UTF-8')
Fout = open("part1_SourcesBySection.txt","w") 

wholeFile = Fin.read()
wholeFile = wholeFile.encode('utf-8')
chapters = wholeFile.split("NEWCHAPTER")

numChapter = 0
allSourcesByChapter = []

for chapter in chapters:
    
    Fout.write("Chapter: " + str(numChapter) )

    sources = re.findall('\(.*?\)',chapter)
    
    sourcestmp = []
    for source in sources:

        #Filter out things that have parenthesis but are not sources
        #This is not perfect and should be enhanced
        if len(source) < 80 and (("," in source)or("לפסוק" in source)or("\"" in source)):
            sourcestmp.append(source)
            Fout.write("\n" + source)
    
    Fout.write("\n\n")
    
    allSourcesByChapter.append(sourcestmp)
    
    numChapter+=1

Fin.close()
Fout.close()

