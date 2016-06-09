# -*- coding: utf-8 -*-
import regex
from sefaria.model import *
from sources import functions

"TODO: fix the multi name mesechtas and eminate Global Variables"

pattern = regex.compile(u'\((\u05dc\u05e2\u05d9\u05dc|\u05dc\u05e7\u05de\u05df)\s?([\u05d0-\u05ea]{1,3})(?:\s\u05d3\u05e3\s)?([.:])\)')

def linkSelfReferences():
    rashiRefs = getCommentatorReferenceCollection("Rashi")
    tosRefs = getCommentatorReferenceCollection("Tosafot")
    listOfRashiRefsWithSource = findEverySelfReference(rashiRefs)
    listOfTosafotRefWithSource = findEverySelfReference(tosRefs)
    listOfRashiLinks = createLinks(listOfRashiRefsWithSource)
    listOfTosafotLinks = createLinks(listOfTosafotRefWithSource)
    functions.post_link(listOfRashiLinks)
    functions.post_link(listOfTosafotLinks)

    # print(listOfRashiLinks)
    # print(listOfTosafotLinks)
    # print(len(listOfRashiLinks))
    # print(len(listOfTosafotLinks))


def getCommentatorReferenceCollection(commentator):
    allRefs = []
    for mesechet in library.get_indexes_in_category('Bavli'):
        print(mesechet)
        allRefs.append(library.get_index(getReferenceName(commentator,mesechet)).all_segment_refs())
    return allRefs

def getReferenceName(commentator, mesechet):
    return "{} on {}".format(commentator, mesechet)

def findEverySelfReference(listOfRefs):
    referenceWithSource = []
    for mesechet in listOfRefs:
        for eachComment in mesechet:
            commentary = TextChunk(eachComment,'he').as_string()
            listOfAllSelfRefs = (pattern.findall(commentary))
            referenceWithSource.append((listOfAllSelfRefs,eachComment))
    return referenceWithSource

def createLinks(listOfRefsWithSources):
    dictList = []
    for eachSourceWithRef in listOfRefsWithSources:
        theSource = eachSourceWithRef[1].uid()
        for eachSelfReference in eachSourceWithRef[0]:
            selfReference = createStringForReference(eachSelfReference, theSource)
            dictList.append({"refs":[theSource,selfReference],
                                 "type":"commentary",
                                 "auto":False,
                                 "generate_by":"Josh's link script"})
    return dictList


def createStringForReference(everySelfReference,theSource):
    theDafNumber = functions.getGematria(everySelfReference[1])
    if (everySelfReference[2] == '.'):
        whichAmud = 'a'
    else:
        whichAmud = 'b'
    splitString = theSource.split(' ')
    if (splitString[3].isalpha()):
        return u'{} {} {} {} {}{}'.format(splitString[0],splitString[1],splitString[2],splitString[3],theDafNumber,whichAmud)
    return u'{} {} {} {}{}'.format(splitString[0],splitString[1],splitString[2],theDafNumber,whichAmud)

linkSelfReferences()