# -*- coding: utf-8 -*-
import regex
from sefaria.model import *
from sources import functions


pattern = regex.compile(u'\((\u05dc\u05e2\u05d9\u05dc|\u05dc\u05e7\u05de\u05df)\s?([\u05d0-\u05ea]{1,3})(?:\s\u05d3\u05e3\s)?([.:])\)')
everyRashiReference = list()
everyTosafotReference = list()
listOfRashiLinks = list()
listOfTosafotLinks = list()

def linkSelfReferences():
    listOfMesechtaNames = library.get_indexes_in_category('Bavli')
    getEveryCommentReference(listOfMesechtaNames)
    findEveryRashiSelfReference()
    findEveryTosafotSelfReference()


def getEveryCommentReference(listOfMesechtaNames):
    #for mesechet in listOfMesechtaNames:
        mesechet = 'Niddah'
        print(mesechet)
        everyRashiReference.append(library.get_index('Rashi on ' + mesechet).all_segment_refs())
        everyTosafotReference.append(library.get_index('Tosafot on ' + mesechet).all_segment_refs())


def findEveryRashiSelfReference():
    for mesechet in everyRashiReference:
        print('we are in Rashi References')
        for comment in mesechet:
            rashiCommentary = TextChunk(comment,'he').as_string()
            listOfSelfReferences = pattern.findall(rashiCommentary)
            createRashiDictionaries(listOfSelfReferences,comment)


def createRashiDictionaries(listOfSelfReferences, source):
    theSource = source.uid()
    for everySelfReference in listOfSelfReferences:
        selfReference = createStringForReference(everySelfReference,theSource)
        listOfRashiLinks.append({"refs":[theSource,selfReference],
                                 "type":"commentary",
                                 "auto":False,
                                 "generate_by":"Josh's link script"})


def createStringForReference(everySelfReference,theSource):
    theDafNumber = functions.getGematria(everySelfReference[1])
    if (everySelfReference[2] == '.'):
        whichAmud = 'a'
    else:
        whichAmud = 'b'
    splitString = theSource.split(' ')
    return u'{} {} {} {}{}'.format(splitString[0],splitString[1],splitString[2],theDafNumber,whichAmud)


def findEveryTosafotSelfReference():
    for mesechet in everyTosafotReference:
        print('we are in tosafot references')
        for comment in mesechet:
            tosafotCommentary = TextChunk(comment,'he').as_string()
            listOfSelfReferences = pattern.findall(tosafotCommentary)
            createTosafotDictionaries(listOfSelfReferences,comment)


def createTosafotDictionaries(listOfSelfReferences, source):
    theSource = source.uid()
    for everySelfReference in listOfSelfReferences:
        selfReference = createStringForReference(everySelfReference,theSource)
        listOfTosafotLinks.append({"refs":[theSource,selfReference],
                                   "type":"commentary",
                                   "auto":False,
                                   "generated_by":"Josh's link script"})


linkSelfReferences()
print(listOfRashiLinks)
print(listOfTosafotLinks)