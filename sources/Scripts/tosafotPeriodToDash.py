# -*- coding: utf-8 -*-
import regex
from sefaria.model import *
from sources import functions


"""
TODO:
1. Create Regex
2. Pull all Tosafot References from Shaas
3. Convert each Tosafot to a String
4. Decide how to isolate targeted strings using regex
5. Replace the period with a dash
6. upload them using the API

"""


def tosafotPeriodToDash():
    tosafotReferences = getCommentatorReferenceCollection("Tosafot")
    listOfFixedTosafot = removeAllPeriodTosafot(tosafotReferences)
    print(listOfFixedTosafot)


def getCommentatorReferenceCollection(commentator):
    allRefs = []
    for mesechet in library.get_indexes_in_category('Bavli'):
        print(mesechet)
        allRefs.append(library.get_index(getReferenceName(commentator,mesechet)).all_segment_refs())
    return allRefs

def getReferenceName(commentator, mesechet):
    return "{} on {}".format(commentator, mesechet)



def removeAllPeriodTosafot(tosafotReferences):
    selectedTosafot = []
    for mesechet in tosafotReferences:
        for eachComment in mesechet:
            commentary = TextChunk(eachComment,'he').as_string()
            theFirstDash = commentary.find('-')
            theFirstPeriod = commentary.find('.')
            if (theFirstDash != -1):
                if(theFirstPeriod < theFirstDash):
                    selectedTosafot.append(commentary.replace('.','-',1))
            else:
                selectedTosafot.append(commentary.replace('.','-',1))



    return selectedTosafot


tosafotPeriodToDash()