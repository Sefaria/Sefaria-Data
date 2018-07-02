# coding=utf-8
from sefaria.model import *
from sefaria.model.nli import ManuscriptReference, ManuscriptReferenceSet
import unicodecsv as csv

manuscript_map = {}
image_map = {}

ManuscriptReferenceSet({}).delete()

with open("Manuscripts.csv") as csvfile:
    """
    0 - Manuscript ID
    2 - EN Name
    7 - HE Name
    8 - HE Desc
    """
    next(csvfile)
    for l in csv.reader(csvfile, dialect="excel"):
        manuscript_map[l[0]] = {
            "ms_name_en": l[2],
            "ms_name_he": l[7],
            "ms_desc_he": l[8]
        }

with open("Images.csv") as csvfile:
    """
    0 - Image ID
    1 - Manuscript ID
    5 - HE Image Desc
    7 - PID
    """
    next(csvfile)
    for l in csv.reader(csvfile, dialect="excel"):
        image_map[l[0]] = {
            "ms_code": l[1],
            "img_desc_he": l[5],
            "img_pid": l[7].strip()
        }

with open("ImageMap.csv") as csvfile:
    """
    1 - Img ID
    2 - Collection ID
    3 - Tractate ID
    4 - Perek ID
    5 - Mishnah ID
    """
    next(csvfile)
    for l in csv.reader(csvfile, dialect="excel"):
        img = image_map[l[1]]
        ms_code = img["ms_code"]
        ms = manuscript_map[ms_code]

        ManuscriptReference({
            "fr_code": l[2], # Collection
            "tr_code": l[3], # Tractate
            "pe_code": l[4], # Chapter or Daf - 3 digit pad
            "mi_code": l[5], # Mishnah, Halacha, or Amud - 2 digit pad
            "img_pid": img["img_pid"], # Img ID for image server
            "ms_code": ms_code, # Manuscript Code
            "ms_name_en": ms["ms_name_en"],
            "ms_name_he": ms["ms_name_he"] + u": " + img["img_desc_he"],
            "ms_desc_he": ms["ms_desc_he"]
        }).save()
