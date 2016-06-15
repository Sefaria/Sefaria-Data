# -*- coding: utf-8 -*-
import codecs
from sefaria.model import *
from sources.functions import post_text

"""
TODO:
1. Pull all Tosafot References from Shaas
2. Convert each Tosafot to a String
3. Change all em-dashes and en-dashed to dashes
4. Replace the period with a dash
5. Replace necessary colons with a dash
6. upload them using the API

.count of period should not be equal to the number of groups with a period
.count of colon should be 2 greater than groups

first run a method only selecting those tosafot
then, run the remaining Tosafot through a changer

"""


def standardizeTosafotDivreiHamtchilToDash():
    tosafotReferences = getCommentatorReferenceCollection("Tosafot")
    listOfFixedTosafot = standardizeDashes(tosafotReferences)
    replaceTheTextsViaAPI(listOfFixedTosafot)


def getCommentatorReferenceCollection(commentator):
        allRefs = []
    #for mesechet in library.get_indexes_in_category('Bavli'):
        mesechet = 'Shevuot'
        allRefs.append(library.get_index(getReferenceName(commentator,mesechet)).all_segment_refs())
        return allRefs


def getReferenceName(commentator, mesechet):
    return "{} on {}".format(commentator, mesechet)


def standardizeDashes(tosafotReferences):
    listOfRefsAndTexts =[]
    for mesechet in tosafotReferences:
        for eachComment in mesechet:
            fixedTosafot = False
            commentary = TextChunk(eachComment,'he').as_string()
            if (commentary.find(u'\u2013') or commentary.find(u'\u2014')):
                commentary = commentary.replace(u'\u2013','-').replace(u'\u2014','-')
                fixedTosafot = True

            theFirstDash = commentary.find('-')
            theFirstPeriod = commentary.find('.')
            if (theFirstPeriod!=-1 and theFirstPeriod < 100 and (theFirstPeriod<theFirstDash or theFirstDash == -1)):
                commentary = commentary.replace('.',' -',1)
                fixedTosafot = True
            elif(commentary.count(':')>1 and commentary.find(':')<100):
                commentary = commentary.replace(':',' -',1)
                fixedTosafot = True
            if(fixedTosafot):
                listOfRefsAndTexts.append([eachComment.uid(),createTexts(commentary, eachComment)])

    return listOfRefsAndTexts


def createTexts(commentary, reference):
    return {
    "versionTitle": reference.version_list()[0]["versionTitle"],
    "versionSource": reference.version_list()[0]["versionSource"],
    "language": "he",
    "text": commentary
    }



def replaceTheTextsViaAPI(listOfFixedTosafot):
    for eachTosafot in listOfFixedTosafot:
        post_text(eachTosafot[0],eachTosafot[1])


standardizeTosafotDivreiHamtchilToDash()