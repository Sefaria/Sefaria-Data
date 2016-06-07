import re

import regex

from sefaria.model import *

#print(Ref('Shemot.24.1').text('he').text)

pattern = regex.compile('\((\u05dc\u05e2\u05d9\u05dc|\u05dc\u05e7\u05de\u05df).+\)')
listOfMatches = list()

#tosafotTrial = TextChunk(Ref('Tosafot on Menachot 105b'),'he').as_string()
#print(tosafotTrial)
#list = regex.findall(pattern, tosafotTrial)
#list = regex.findall('/((\u05dc\u05e2\u05d9\u05dc|\u05dc\u05e7\u05de\u05df).*/)',tosafotTrial)
#print(list)





def linkSelfReferences():
    listOfMesechtaNames = library.get_indexes_in_category('Bavli')
    isolateEachAmud(listOfMesechtaNames)


def isolateEachAmud(listOfMesechtaNames):
    for mesechet in listOfMesechtaNames:
        everyAmud = Ref(mesechet).all_subrefs()
        for amud in everyAmud:

            takeTheText(amud)

def takeTheText(amud):
    rashiCommentary = TextChunk(Ref('Rashi on '+amud.uid()),'he').as_string()
    tosafotfCommentary = TextChunk(Ref('Tosafot on '+amud.uid()),'he').as_string()
    findEverySelfReference(rashiCommentary)
    findEverySelfReference(tosafotfCommentary)

def findEverySelfReference(Commentary):
    listOfMatches.append(regex.findall(pattern, Commentary))




linkSelfReferences()
print(listOfMatches.__sizeof__())