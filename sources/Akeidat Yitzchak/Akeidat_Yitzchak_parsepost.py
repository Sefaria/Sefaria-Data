# -*- coding: utf-8 -*-

import sys
import os
# for a script located two directories below this file
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
from sources.functions import *
import re
import codecs

sefer_ranges=[["Genesis",1,33], ["Exodus",34,56], ["Leviticus",57,71], ["Numbers",72,86], ["Deuteronomy",87,105] ]

heb_parshiot = [u"בראשית",u"נח", u"לך לך", u"וירא", u"חיי שרה", u"תולדות", u"ויצא", u"וישלח", u"וישב", u"מקץ",
u"ויגש", u"ויחי", u"שמות", u"וארא", u"בא", u"בשלח", u"יתרו", u"משפטים", u"תרומה", u"תצוה", u"כי תשא",
u"ויקהל", u"פקודי", u"ויקרא", u"צו", u"שמיני", u"תזריע", u"מצרע", u"אחרי מות", u"קדשים", u"אמר", u"בהר",
u"בחקתי", u"במדבר", u"נשא", u"בהעלתך", u"שלח לך", u"קרח", u"חקת", u"בלק", u"פינחס", u"מטות",
u"מסעי", u"דברים", u"ואתחנן", u"עקב", u"ראה", u"שפטים", u"כי תצא", u"כי תבוא", u"נצבים",
u"וילך", u"האזינו", u"וזאת הברכה"]

eng_parshiot = ["Bereshit", "Noach", "Lech Lecha", "Vayera", "Chayei Sara", "Toldot", "Vayetzei", "Vayishlach",
"Vayeshev", "Miketz", "Vayigash", "Vayechi", "Shemot", "Vaera", "Bo", "Beshalach", "Yitro",
"Mishpatim", "Terumah", "Tetzaveh", "Ki Tisa", "Vayakhel", "Pekudei", "Vayikra", "Tzav", "Shmini",
"Tazria", "Metzora", "Achrei Mot", "Kedoshim", "Emor", "Behar", "Bechukotai", "Bamidbar", "Nasso",
"Beha'alotcha", "Sh'lach", "Korach", "Chukat", "Balak", "Pinchas", "Matot", "Masei",
"Devarim", "Vaetchanan", "Eikev", "Re'eh", "Shoftim", "Ki Teitzei", "Ki Tavo", "Nitzavim", "Vayeilech", "Ha'Azinu",
"V'Zot HaBerachah"]
def parse_haaros():
    #each sefer has its own marker...
    haarah_marker = ["2*","*","3*","*","*"]
    haaros_seforim=[]
    for index in range(1,6):
        haaros_box = []
        sefer_haaros = []
        with open("הערות"+" "+str(index)+".txt") as myfile:
            lines = myfile.readlines()
        for line_index, line in enumerate(lines):
            decode_line = line.decode('utf8','replace')
            if decode_line.count(u'{}'.format(haarah_marker[index-1]))>1.5:
                print "TOO MUCH! "+str(index)+" "+str(line_index)
                print decode_line
                print decode_line.replace(u'{}'.format(haarah_marker[index-1]),u"**מרקר**")
            #if haarah_marker[index-1] in line:
            if re.search(r"^ *"+haarah_marker[index-1].replace("*","\*"), line) is not None:
                sefer_haaros.append(haaros_box)
                haaros_box = []
            line = re.sub(r"[12*]","",line)
            if not line.isspace():
                haaros_box.append(line)
        sefer_haaros.append(haaros_box)
        haaros_seforim.append(filter(lambda(x): x is not None and len(x)!=0,sefer_haaros))
    for index,sefer in enumerate(haaros_seforim):
        print index, len(sefer)
    for sindex, sefer in enumerate(haaros_seforim):
        for hindex, haarah in enumerate(sefer):
            for pindex, paragraph in enumerate(haarah):
                print "INDEX\/ "+str(sindex)+" "+str(hindex)+" "+str(pindex)
                print paragraph
    for index in range(1,6):
        with open("הערות"+" "+str(index)+".txt") as myfile:
            lines = myfile.readlines()
        haarah_count=0
        for lindex, line in enumerate(lines):
            if haarah_marker[index-1] in line:
                haarah_count+=1
            print "HAARAHC: "+str(haarah_count)
            print "SINDEX: "+str(index)+" LINDEX: "+str(lindex)
            print line
    return haaros_seforim
def get_haara_refs():
    ay_text = get_parsed_text()
    all_indices = []
    #need to break up by sefer, since that's how the haaras are broken up
    sefer_breaks=[]
    for x in range(1,5):
        sefer_breaks.append(sefer_ranges[x][1])
    sefer_box = []    
    for sindex, shaar in enumerate(ay_text):
        if sindex in sefer_breaks:
            all_indices.append(sefer_box)
            sefer_box=[]
        for cindex, chapter in enumerate(shaar):
            for pindex, paragraph in enumerate(chapter):
                paragraph = paragraph.replace("**","")
                for x in range(0,paragraph.count("*")):
                    sefer_box.append([sindex,cindex,pindex])
    all_indices.append(sefer_box)
    return all_indices
def get_haaras_by_shaarim():
    return_list = [[] for x in range(105)]
    for sefer_haara_refs, sefer_haaras in zip(get_haara_refs(),parse_haaros()):
        for haara_ref, haara in zip(sefer_haara_refs, sefer_haaras):
            for paragraph in haara:
                return_list[haara_ref[0]].append(paragraph)
    return return_list
#after is was decided to change format of text, we changed approach to haarah parsing
def parse_haaras2():
    #each sefer has its own marker...
    haarah_marker = [u"2*",u"*",u"3*",u"*",u"*"]
    haaros_final=[]
    haarah_sefer_counts=[]
    for index in range(1,6):
        sefer_count=0
        haaros_box = []
        with open("הערות"+" "+str(index)+".txt") as myfile:
            lines = myfile.readlines()
        for line_index, line in enumerate(lines):
            #
            decode_line = line.decode('utf8','replace')
            if decode_line.count(u'{}'.format(haarah_marker[index-1]))>1.5:
                print str(decode_line.count(u'{}'.format(haarah_marker[index-1]))),"TOO MUCH! "+str(index)+" "+str(line_index)
                print decode_line
                print decode_line.replace(u'{}'.format(haarah_marker[index-1]),u"**מרקר**")
            if haarah_marker[index-1] in decode_line and len(haaros_box)>0:
                haaros_final.append(haaros_box)
                haaros_box = []
                sefer_count+=1
            line = re.sub(ur"[123*]","",line)
            if not line.isspace():
                haaros_box.append(line)
        sefer_count+=1
        haarah_sefer_counts.append(sefer_count)
        haaros_final.append(haaros_box)
    haaros_final= filter(lambda(x): x is not None and len(x)!=0,haaros_final)
    return haaros_final
def get_text_with_haaras(akeida_text, haaras):
    haara_index = 0
    for sindex, shaar in enumerate(akeida_text):
        for cindex, chapter in enumerate(shaar):
            for pindex,paragraph in enumerate(chapter):
                    """
                    star_indices= [i for i, ltr in enumerate(paragraph) if ltr == "*"]
                    offset = 0
                    new_paragraph = paragraph
                    for star_index in star_indices:
                        haara_string = '<br>'.join(haaras[haara_index])
                        new_paragraph = paragraph[star_index+offset:]+"<sup>*</sup><i class=\"footnote\">"+haara_string+"</i>"+paragraph[:star_index+offset+1]
                        offset+=len(haara_string)
                    """
                    new_paragraph = paragraph
                    while "*" in new_paragraph:
                        star_index = new_paragraph.index("*")
                        new_paragraph = new_paragraph[:star_index]+"<sup>STARPLACE</sup><i class=\"footnote\">"+'<br>'.join(haaras[haara_index])+"</i>"+new_paragraph[star_index+1:]
                        haara_index+=1
                    new_paragraph=new_paragraph.replace("STARPLACE","*")
                    akeida_text[sindex][cindex][pindex]=new_paragraph
    return akeida_text
def get_1D_text_with_haaras(text, haaras):
    haara_index = 0
    for pindex,paragraph in enumerate(text):
            new_paragraph = paragraph
            while "*" in new_paragraph:
                star_index = new_paragraph.index("*")
                new_paragraph = new_paragraph[:star_index]+"<sup>STARPLACE</sup><i class=\"footnote\">"+'<br>'.join(haaras[haara_index])+"</i>"+new_paragraph[star_index+1:]
                haara_index+=1
            new_paragraph=new_paragraph.replace("STARPLACE","*")
            text[pindex]=new_paragraph
    return text
def get_2D_text_with_haaras(text, haaras):
    haara_index = 0
    for cindex, chapter in enumerate(text):
        for pindex,paragraph in enumerate(chapter):
                new_paragraph = paragraph
                while "*" in new_paragraph:
                    star_index = new_paragraph.index("*")
                    new_paragraph = new_paragraph[:star_index]+"<sup>STARPLACE</sup><i class=\"footnote\">"+haaras[haara_index]+"</i>"+new_paragraph[star_index+1:]
                    haara_index+=1
                new_paragraph=new_paragraph.replace("STARPLACE","*")
                text[cindex][pindex]=new_paragraph
    return text
def get_parsha_index():
    parsha_count=0
    shaar_count = 0
    book_files = ["בראשית.txt","שמות.txt","ויקרא.txt","במדבר.txt","דברים.txt"]
    parsha_index = []
    for index, file in enumerate(book_files):
        with open(file) as myfile:
            text = myfile.readlines()
        for line in text:
            if "IGNORE" not in line:
                if "@22" in line:
                    shaar_count+=1
                if "@11" in line:
                    if len(parsha_index)>0:
                        parsha_index[-1].append(shaar_count-1 if parsha_index[-1][-1]!=shaar_count else shaar_count)
                    parsha_index.append([heb_parshiot[parsha_count],shaar_count])
                    parsha_count+=1
                #introduction to parshas shemos requires it's own implementation, since it breaks from the parsha pattern
                if "@232" in line:
                    parsha_index[-1].append(shaar_count-1)
                    parsha_index.append([u"הקדמת ספר שמות",shaar_count])
    parsha_index[-1].append(shaar_count)
    return parsha_index
def get_parsed_text():
    book_files = ["בראשית.txt","שמות.txt","ויקרא.txt","במדבר.txt","דברים.txt"]
    final_text = []
    parsha_index = []
    for index, file in enumerate(book_files):
        with open(file) as myfile:
            text = myfile.readlines()
        #first parse the shaarim, the most detailed level of structure:
        shaar_box = []
        chapter_box=[]
        mistakes =[]
        for line in text:
            if "@77נעילת שערים" in line:
                break
            line = remove_unused_tags(line)
            if "IGNORE" not in line:
                line = fix_bold_lines(line)
                line = line.replace("@05","").replace("**","")
                if "@" in line:
                    if "@22" in line and len(chapter_box)!=0:
                        shaar_box.append(chapter_box)
                        chapter_box=[]
                        final_text.append(shaar_box)
                        shaar_box = []
                    elif "@33" in line and len(chapter_box)!=0:
                        shaar_box.append(chapter_box)
                        chapter_box=[]
                    elif "@11" not in line and "@00" not in line:
                        mistakes.append(file+" EXTRA@ "+ line)
                else:
                    if "השער" in line and len(line)<50:
                        mistakes.append(file+" SHAAR "+line)
                    chapter_box.append(line)
        shaar_box.append(chapter_box)
        final_text.append(shaar_box)
    for mistake in mistakes:
        print mistake
    return get_text_with_haaras(final_text, parse_haaras2())
def remove_unused_tags(s):
    unused_tags = ["@05","**","@01","@02","@04","@03","@50","@88"]
    for tag in unused_tags:
        s = s.replace(tag,"")
    return s
def remove_unused_tags_intro(s):
    unused_tags = ["@11","22","@66","@77","@88","@44","@55","@99","@"]
    for tag in unused_tags:
        s = s.replace(tag,"")
    return s
def bold_intro_lines(s):
    return s.replace("@33","<b>").replace("@43","</b>")
def get_parsed_intro():
    with open("הקדמה עקידת יצחק.txt") as myfile:
        lines = myfile.readlines()
    final_intro = []
    section_box = []
    for line in lines:
        #line=line.replace("@66","<b>").replace("@77","</b>")
        #line = re.sub("@[")
        if "@00" in line and len(section_box)!=0:
            final_intro.append(section_box)
            section_box = []
        else:
            line = remove_unused_tags_intro(bold_intro_lines(line))
            #some paragraphs end in the wrong place, so we make sure each paragraph ends with a ":"
            if len(section_box)>0:
                if ":" not in section_box[-1]:
                    section_box[-1] = (section_box[-1]+line).replace("\n","")
                else:
                    section_box.append(line)
            else:
                section_box.append(line)
    final_intro.append(section_box)
    #now add haaras
    with open("הערות הקדמה ומבוא שערים.txt") as myfile:
        h_lines = myfile.readlines()
    for line in h_lines:
        print line
    intro_haaras = list(map(lambda(x): x.replace("2*",""),h_lines))
    return get_2D_text_with_haaras(final_intro[1:], intro_haaras)
def get_parsed_neilah():
    with open("דברים.txt") as myfile:
        lines = myfile.readlines()
    neilah_index=0
    for index, line in enumerate(lines):
        if "@77נעילת שערים" in line:
            break
        neilah_index+=1
    neilah_return = []
    for line in lines[neilah_index+1:]:
        line = re.sub("@[\d]+","",line)
        line = line.replace("**","")
        neilah_return.append(line)

    #now add haaras. The last 5 haaras belong the neilah:
    neilah_haaras = parse_haaras2()[-5:]

    return get_1D_text_with_haaras(neilah_return, neilah_haaras)

def get_star_count(shaar):
    #used to confirm that footnote division went smoothly
    star_count = 0
    for chapter in shaar:
        for paragraph in chapter:
            for x in range(paragraph.count("*")):
                star_count+=1
    return star_count

def fix_bold_lines(input_line):
    #we decided later not to bold these tags
    """
    if "@01" in input_line:
        input_line = input_line.replace("@01","<b>")
        if "@02" in input_line:
            input_line= input_line.replace("@02","</b>")
        else:
            input_line+="</b>"
    input_line = input_line.replace("@04","<b>").replace("@03","</b>")
    """
    if "@44" in input_line:
        input_line = "<b>"+input_line.replace("@44","")+"</b>"
    return input_line
def main():
    pass
if __name__ == "__main__":
    """
    #for MAIN TEXT
  
    text = get_parsed_text()
    for bindex, book in enumerate(text):
        for cindex,chapter in enumerate(book):
            for pindex, paragraph in enumerate(chapter):
                print str(bindex)+" "+str(cindex)+" "+str(pindex)+" "+paragraph
    
    
    version = {
        'versionTitle': 'Akeidat Yitzchak, Pressburg 1849',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002034858',
        'language': 'he',
        'text': text
    }

    post_text('Akeidat Yitzchak', version,weak_network=True)
    """
"""
    #for INTROS
    print "this is an intro"
    for sindex, section in enumerate(get_parsed_intro()):
        for pindex, paragraph in enumerate( section):
            print str(sindex)+" "+str(pindex)+" "+paragraph
    
    parshadex = get_parsha_index()
    for parsha in parshadex:
        print parsha[0]+u" ",parsha[1]," ",parsha[2]," end"
    intro_titles = ["Index","Author's Introduction","Mavo Shearim"]
    intro_text = get_parsed_intro()
    for index, title in enumerate(intro_titles):
        version = {
            'versionTitle': 'Akeidat Yitzchak, Pressburg 1849',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002034858',
            'language': 'he',
            'text': intro_text[index]
        }

        post_text('Akeidat Yitzchak, '+title, version, weak_network=True)

    #for NEILAH
    n = get_parsed_neilah()
    for line in n:
        print line
    version = {
        'versionTitle': 'Akeidat Yitzchak, Pressburg 1849',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002034858',
        'language': 'he',
        'text': n
    }

    post_text('Akeidat Yitzchak, Neilat Shearim', version, weak_network=True)
    """
"""

for index, section in enumerate(get_parsed_intro()):
    for paragraph in section:
        print str(index)+" "+paragraph
        """
#for b in get_parsed_text():
#    print "BOOK: "+b
"""
    @00 - Book
    @44 - Gate/Chapter (should be reorganized to sperate the two)
    @99 - Verse quote
    @22 @55 - Introductory Midrash
    @11 @33 - regular paragraph
    5<>6 bold
    * first level footnotes (we have them)
    **) second level footnotes (we haven't got them)
"""
                
            
            
    """
    for sindex, shaar in enumerate(text):
        for pindex, paragraph in enumerate(shaar):
            for sefer[dh_sefer_index] in haaros_dh[dh_sefer_index:]:
                if dh in paragraph:
                    dh_index = haaros_dh.index(dh)
                    matches.append([str(sindex)+" "+str(pindex),str(new_dh)])
                    break

    for sindex, sefer in enumerate(get_haara_refs()):
        for iindex, index, in enumerate(sefer):
            print "FOR "+str(sindex)+" "+str(iindex)+":"
            print str(index[0])+" "+str(index[1])+" "+str(index[2])
    print "AY Haaras by Shaar:"
    for sindex, shaar in enumerate(get_haaras_by_shaarim()):
        for hindex, haarah in enumerate(shaar):
            for pindex, paragraph in enumerate(haarah):
                print str(sindex)+" "+str(hindex)+" "+str(pindex)
                print paragraph
    """
    1/0

    for sindex, shaar in enumerate(get_text_with_haaras()):
        for cindex, chapter in enumerate(shaar):
            for pindex, paragraph in enumerate(chapter):
                print sindex,pindex,paragraph

    for index, (haarah_shaar, akeida_shaar) in enumerate(zip(get_haaras_by_shaarim(), get_parsed_text())):
        if len(haarah_shaar)!=get_star_count(akeida_shaar):
            print "OOPS! "+str(index)
            print "HA: "+str(len(haarah_shaar))
            print "AK: "+str(get_star_count(akeida_shaar))
    #adding shaarim: 104+107+108+139+172=630
    main()