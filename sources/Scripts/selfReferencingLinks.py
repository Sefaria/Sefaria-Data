# -*- coding: utf-8 -*-
import regex
from sefaria.model import *
from sources import functions

pattern = regex.compile(
        u'\((\u05dc\u05e2\u05d9\u05dc|\u05dc\u05e7\u05de\u05df)\s?([\u05d0-\u05ea]{1,3})(?:\s?\u05d3\u05e3\s?)?([.:])\)')


def linkSelfReferences():
    rashiRefs = getCommentatorReferenceCollection("Rashi")
    tosRefs = getCommentatorReferenceCollection("Tosafot")
    listOfRashiRefsWithSource = findEverySelfReference(rashiRefs)
    listOfTosafotRefWithSource = findEverySelfReference(tosRefs)
    listOfRashiLinks = createLinks(listOfRashiRefsWithSource)
    listOfTosafotLinks = createLinks(listOfTosafotRefWithSource)
    brokenLinks = open('BrokenLinks.txt', 'w')
    goodLinks = open('goodLink.txt', 'w')
    postLinks(listOfRashiLinks, brokenLinks, goodLinks)
    postLinks(listOfTosafotLinks, brokenLinks, goodLinks)
    brokenLinks.close()
    goodLinks.close()


def getCommentatorReferenceCollection(commentator):
    allRefs = []
    for mesechet in library.get_indexes_in_category('Bavli'):
        print(mesechet)
        allRefs.append(library.get_index(getReferenceName(commentator, mesechet)).all_segment_refs())
    return allRefs


def getReferenceName(commentator, mesechet):
    return "{} on {}".format(commentator, mesechet)


def findEverySelfReference(listOfRefs):
    referenceWithSource = []
    for mesechet in listOfRefs:
        for eachCommentRef in mesechet:
            commentary = TextChunk(eachCommentRef, 'he').as_string()
            listOfAllSelfRefs = (pattern.findall(commentary))
            referenceWithSource.append((listOfAllSelfRefs, eachCommentRef))
    return referenceWithSource


def createLinks(listOfRefsWithSources):
    dictList = []
    for eachSourceWithRef in listOfRefsWithSources:
        theSource = eachSourceWithRef[1].uid()
        for eachSelfReference in eachSourceWithRef[0]:
            selfReference = createStringForReference(eachSelfReference, theSource)
            dictList.append({"refs": [theSource, selfReference],
                             "type": "commentary",
                             "auto": False,
                             "generate_by": "Josh's link script"})
    return dictList


def validDafReference(eachSelfReference):
    singles = regex.compile(u'[\u05d0\u05d1\u05d2\u05d3\u05d4\u05d5\u05d6\u05d7\u05d8]')
    fifteen = regex.compile(u'(\u05d8\u05d5)')
    sixteen = regex.compile(u'(\u05d8\u05d6)')
    tens = regex.compile(u'[\u05d9\u05db\u05dc\u05de\u05e0\u05e1\u05e2\u05e4\u05e6]')
    if len(singles.findall(eachSelfReference)) > 1 and \
                            len(fifteen.findall(eachSelfReference)) + len(sixteen.findall(eachSelfReference)) == 0:
        return False
    if len(tens.findall(eachSelfReference)) > 1:
        return False
    return True


def createStringForReference(everySelfReference, theSource):
    theDafNumber = functions.getGematria(everySelfReference[1])
    if (everySelfReference[2] == '.'):
        whichAmud = 'a'
    else:
        whichAmud = 'b'
    splitString = theSource.split(' ')
    if (splitString[3].isalpha()):
        return u'{} {} {}{}'.format(splitString[2], splitString[3], theDafNumber, whichAmud)
    return u'{} {}{}'.format(splitString[2], theDafNumber, whichAmud)


def postLinks(listOfPotentialLink, badLinksFile, goodLinksFile):
    for eachLink in listOfPotentialLink:
        if Ref.is_ref(eachLink['refs'][1]):
            functions.post_link(eachLink)
            goodLinksFile.write(eachLink['refs'][0] + ' linked with ' + eachLink['refs'][1] + '\r\n')
        else:
            badLinksFile.write(eachLink['refs'][0] + ' linked with ' + eachLink['refs'][1] + '\r\n')


linkSelfReferences()
