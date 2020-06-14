import django
django.setup()
from sefaria.model import *
from sefaria.system.database import db
import re

def numToHeb(engnum=""):
    engnum = str(engnum)
    numdig = len(engnum)
    hebnum = ""
    letters = [["" for i in range(3)] for j in range(10)]
    letters[0]=["", "א", "ב", "ג", "ד", "ה", "ו", "ז", "ח", "ט"]
    letters[1]=["", "י", "כ", "ל", "מ", "נ", "ס", "ע", "פ", "צ"]
    letters[2]=["", "ק", "ר", "ש", "ת", "תק", "תר", "תש", "תת", "תתק"]
    if (numdig > 3):
        print("We currently can't handle numbers larger than 999")
        exit()
    for count in range(numdig):
        hebnum += letters[numdig-count-1][int(engnum[count])]
    hebnum = re.sub('יה', 'טו', hebnum)
    hebnum = re.sub('יו', 'טז', hebnum)
    return hebnum

def modify_text(str, he=False):
    ref = str.replace(".", ":")
    sections = ref.split()[-1].split(":")
    chapter_to_gate = {"1": "Gate I", "2": "Gate II", "3": "Gate III", "4": "Chapters", "5": "Gate IV"}
    he_chapter_to_gate = {"1": "שער א", "2": "שער ב", "3": "שער ג", "4": "פרקים", "5": "שער ד"}
    use_dict = chapter_to_gate if not he else he_chapter_to_gate
    title = "Nefesh HaChayim" if not he else "נפש החיים"
    if len(sections) in [2, 3]:
        num = sections[1] if not he else numToHeb(sections[1])
        return "{}, {} {}".format(title, use_dict[sections[0]], num)
    elif len(sections) == 1:
        return "{}, {}".format(title, use_dict[sections[0]])
    
    
for sheet in db.sheets.find({"sources.ref": {"$regex": "^Nefesh HaChaim"}}):
    main_ref = None
    print(sheet["id"])
    included = sheet["includedRefs"] if "includedRefs" in sheet else []
    if sheet["title"].startswith("Nefesh HaChaim"):
        sheet["title"] = modify_text(sheet["title"])

    for source in sheet["sources"]:
        if "ref" in source and source["ref"].startswith("Nefesh HaChaim"):
            main_ref = source["ref"]
            main_ref = modify_text(main_ref)
            source["heRef"] = modify_text(source["ref"], True)
            source["ref"] = main_ref
            included.append(main_ref)
            Ref(source["heRef"])

    sheet["includedRefs"] = []
    for ref in included:
        try:
            Ref(ref)
            sheet["includedRefs"] += ref
        except:
            print(ref)
    db.sheets.save(sheet)


