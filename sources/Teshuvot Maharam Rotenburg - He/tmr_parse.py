# -*- coding: utf-8 -*-
import os
import re
import sys
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
import django
django.setup()
from sources.functions import *
import codecs
from fuzzywuzzy import fuzz
#import re
#title_dict = {u"אורח חיים":"Orach Chaim" ,u"יורה דעה":"Yoreh Deah" ,u"אבן העזר":"Even HaEzer",u"חושן משפט":"Choshen Mishpat"} 
#title_list = [u"אורח חיים",u"יורה דעה",u"אבן העזר",u"חושן משפט"]
title_dict={"Cremona Edition":u'דפוס קרימונה',"Prague Edition":u'דפוס פראג','Lemberg Edition':u'דפוס לבוב'}
titles_in_order=["Cremona Edition","Prague Edition",'Lemberg Edition']
def not_blank(s):
    while " " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
def tmr_post_index():
    # create index record
    record = SchemaNode()
    record.add_title('Teshuvot Maharam', 'en', primary=True, )
    record.add_title(u'תשובות מהר"ם', 'he', primary=True, )
    record.key = 'Teshuvot Maharam'

    # add nodes for first three parts (last one needs seperate treatment)
    for title_key in titles_in_order:
        section_node = JaggedArrayNode()
        section_node.add_title(title_key, 'en', primary=True)
        section_node.add_title(title_dict[title_key], 'he', primary=True)
        section_node.key = title_key
        section_node.depth = 2
        section_node.addressTypes = ['Integer','Integer']
        section_node.sectionNames = ["Siman","Paragraph"]
        record.append(section_node)
    
    #Berlin Edition...
    berlin_node = SchemaNode()
    berlin_node.add_title('Berlin Edition', 'en', primary=True, )
    berlin_node.add_title(u'דפוס ברלין', 'he', primary=True, )
    berlin_node.key = 'Berlin Edition'
    
    section_node = JaggedArrayNode()
    section_node.add_title('Part I', 'en', primary=True)
    section_node.add_title(u'שער א', 'he', primary=True)
    section_node.key = 'Part I'
    section_node.depth = 2
    section_node.addressTypes = ['Integer','Integer']
    section_node.sectionNames = ["Siman","Paragraph"]
    berlin_node.append(section_node)
    
    section_node= SchemaNode()
    section_node.add_title('Part II', 'en', primary=True, )
    section_node.add_title(u'שער ב', 'he', primary=True, )
    section_node.key = 'Part II'
    
    issur_node = JaggedArrayNode()
    issur_node.add_primary_titles('Issur VeHeter',u'בעניני איסור והיתר')
    """
    issur_node.add_title('Issur VeHeter', 'en', primary=True)
    issur_node.add_title(u'בעניני איסור והיתר', 'he', primary=True)
    issur_node.key = u'Issur VeHeter'
    """
    issur_node.depth = 2
    issur_node.addressTypes = ['Integer','Integer']
    issur_node.sectionNames = ["Siman","Paragraph"]
    section_node.append(issur_node)
    
    default_node = JaggedArrayNode()
    default_node.key = "default"
    default_node.default = True
    default_node.depth = 2
    default_node.addressTypes = ['Integer', 'Integer']
    default_node.sectionNames = ['Siman','Paragraph']
    section_node.append(default_node)
    
    berlin_node.append(section_node)
    
    section_node = JaggedArrayNode()
    section_node.add_title('Part III', 'en', primary=True)
    section_node.add_title(u'שער ג', 'he', primary=True)
    section_node.key = 'Part III'
    section_node.depth = 2
    section_node.addressTypes = ['Integer','Integer']
    section_node.sectionNames = ["Siman","Paragraph"]
    berlin_node.append(section_node)
    
    record.append(berlin_node)

    record.validate()

    index = {
        "title": "Teshuvot Maharam",
        "categories": ["Responsa"],
        "schema": record.serialize()
    }
    print "posting index..."
    post_index(index,weak_network=True)
def post_cremona():
    with open('Cremona/מהרם מרוטנבורג קרמונה.txt') as myfile:
        lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
    t_box=[]
    all_ts=[]
    for line in lines:
        if u'@22' in line and len(t_box)>0:
            put_in_next=[]
            if u'$' in t_box[-1]:
                put_in_next.append(t_box.pop().replace(u'$',u''))
            all_ts.append(t_box)
            t_box=put_in_next[:]
        elif not_blank(line):
            t_box.append(lemberg_clean(line))
    all_ts.append(t_box)
    
    for tindex, t in enumerate(all_ts):
        for pindex, p in enumerate(t):
            print tindex, pindex, p
    
    version = {
        'versionTitle': 'Sefer She\'elot uTeshuvot, Kremonah, 1557',
        'versionSource': 'http://merhav.nli.org.il/primo-explore/fulldisplay?vid=NLI&docid=NNL_ALEPH001298067',
        'language': 'he',
        'text': all_ts
    }
    post_text_weak_connection("Teshuvot Maharam, Cremona Edition", version)
def clean_prague(s):
    return s.replace(u'@',u'')
def post_prague():
    all_ts=[]
    for title in ['',' 2',' 3',' 4']:
        with open('Budapest/תשובות מהר_ם{}.txt'.format(title)) as myfile:
            lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
        past_start=False if len(title)==0 else True
        t_box=[]
        for_next=[]
        for line in lines:
            if u'START' in line:
                past_start=True
            elif past_start:
                if u'#' in line:
                    for_next.append(line.replace(u'#',u''))
                else:
                    if u'@' in line and len(t_box)>0:
                        all_ts.append(t_box)
                        t_box=[]
                        while len(for_next)>0:
                            t_box.append(clean_prague(for_next.pop(0)))
                    if not_blank(line):
                        t_box.append(clean_prague(line))
        #if there's no next it's for the last one
        while len(for_next)>0:
            t_box.append(for_next.pop(0))
        all_ts.append(t_box)
    
    for tindex, t in enumerate(all_ts):
        for pindex, p in enumerate(t):
            print tindex, pindex, p
    version = {
        'versionTitle': 'Teshuvot Maharam bar Barukh, Budapest, 1895',
        'versionSource': 'http://merhav.nli.org.il/primo-explore/fulldisplay?vid=NLI&docid=NNL_ALEPH001298073',
        'language': 'he',
        'text': all_ts
    }
    post_text_weak_connection("Teshuvot Maharam, Prague Edition", version)
    #post_text("Malbim on Leviticus",  version,weak_network=True, skip_links=True, index_count="on")
def lemberg_clean(s):
    s = s.replace(u'@11',u'<b>').replace(u'@33',u'</b>')
    return s
    #return re.sub(ur"@\d{1,4}",u"",s)
def post_lemberg():
    with open('Lemberg/מהרם בן ברוך הערות.txt') as myfile:
        lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
    notes=[]
    for line in lines:
        #print line
        if u'@22' not in line and not_blank(line):
            notes.append(line.replace(u'@11',u'<b>').replace(u'@33',u'</b>'))
    """
    for note in notes:
        print note
    """
    #for Lemberg, first 56 are missing...
    #all_ts=[[] for x in range(0,56)]
    all_ts=[]
    t_box=[]
    last_t=1
    with open('Lemberg/מהרם בן ברוך ללא הערות.txt') as myfile:
        lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))         
    for line in lines:
        if u'@00' in line:
            if len(t_box)>0:
                #print line
                #print last_t
                for x in range(0,getGematria(line.replace(u'סימן',u''))-last_t-1):
                    all_ts.append([])
                all_ts.append(t_box)
                last_t=getGematria(line.replace(u'סימן',u''))
                t_box=[]
        elif not_blank(line):
            newline=line
            for match in re.findall(ur'@77\(\S+?\)',line):
                newline = newline.replace(match, u'<sup>'+re.findall(ur'(?<=\()\S+(?=\))',match)[0]+u'</sup><i class=\"footnote\">'+notes.pop(0)+u'</i>')
            #print newline
            t_box.append(lemberg_clean(newline))
    all_ts.append(t_box)
    for tindex, t in enumerate(all_ts):
        for pindex, p in enumerate(t):
            print tindex, pindex, p
    #print "NOTES",len(notes)
    version = {
        'versionTitle': 'Teshuvot Maharam bar Barukh, Lemberg, 1860',
        'versionSource': 'http://merhav.nli.org.il/primo-explore/fulldisplay?vid=NLI&docid=NNL_ALEPH001298071',
        'language': 'he',
        'text': all_ts
    }
    post_text_weak_connection("Teshuvot Maharam, Lemberg Edition", version)
def clean_berlin(s):
    s = re.sub(ur'@\S{1,4}\.\s*',ur'',s)
    return s
def post_berlin():
    shaar1=True
    iAndH=True
    default=True
    shaar3=True
    if shaar1:
        #first shaar rishon
        all_ts=[]
        t_box=[]
        past_start=False
        with open('Berlin/ספר שערי תשובות.txt') as myfile:
            lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
        for line in lines:
            if u'@' in line:
                past_start=True
            if not_blank(line) and past_start:
                if u'@' in line and len(t_box)>0:
                    all_ts.append(t_box)
                    t_box=[]
                t_box.append(clean_berlin(line))        
        all_ts.append(t_box)
        t_box=[]
          
        with open('Berlin/ספר שערי תשובות2.txt') as myfile:
            lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
        for line in lines:
            if not_blank(line):
                if u'#' in line:
                    break
                if u'@' in line and len(t_box)>0:
                    all_ts.append(t_box)
                    t_box=[]
                t_box.append(clean_berlin(line))

        all_ts.append(t_box)
        
        for tindex, t, in enumerate(all_ts):
            for pindex, p in enumerate(t):
                print tindex, pindex, p
        
        version = {
            'versionTitle': 'Shaarei Teshuvot, Maharam bar Barukh, Berlin, 1891',
            'versionSource': 'http://merhav.nli.org.il/primo-explore/fulldisplay?vid=NLI&docid=NNL_ALEPH001298074',
            'language': 'he',
            'text': all_ts
        }
        post_text_weak_connection("Teshuvot Maharam, Berlin Edition, Part I", version)        
    if iAndH:
        with open('Berlin/ספר שערי תשובות3.txt') as myfile:
            lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
        
        t_box=[]
        all_ts=[]
        last_t=1
        default_box=[]
        past_start=False
        in_default=False
        for line in lines:
            if not_blank(line):
                if u'@' in line:
                    past_start=True
                if in_default:
                    if u'@' in line and len(t_box)>0:
                        default_box.append(t_box)
                        t_box=[]
                    t_box.append(clean_berlin(line))
                elif past_start:
                    if u'@' in line and len(t_box)>0:
                        for x in range(0,getGematria(re.findall(ur'@\S{1,4}\.\s*',line)[0])-last_t-1):
                            all_ts.append([])
                        all_ts.append(t_box)
                        last_t=getGematria(re.findall(ur'@\S{1,4}\.\s*',line)[0])
                        t_box=[]
                    t_box.append(clean_berlin(line))
                if u'ש בהגהות באיזה מקומות עוד אי' in line:
                    all_ts.append(t_box)
                    t_box=[]
                    in_default=True
        
        default_box.append(t_box)
        
        #default needs a blank section for missing teshuva
        default_box.insert(124,[])
        
        """
        for tindex, t in enumerate(all_ts):
            for pindex, p in enumerate(t):
                print "IH", tindex, pindex, p
                if re.findall(ur'@\S{1,4}\.\s*',p):
                    if getGematria(re.findall(ur'@\S{1,4}\.\s*',p)[0])!=tindex+1:
                        print "NOT MAYCH"
        for tindex, t in enumerate(default_box):
            for pindex, p in enumerate(t):
                print "DEFAULT", tindex, pindex, p
                if re.findall(ur'@\S{1,4}\.\s*',p):
                    if getGematria(re.findall(ur'@\S{1,4}\.\s*',p)[0])!=tindex+1:
                        print "NOT MAYCH"
        """
        version = {
            'versionTitle': 'Shaarei Teshuvot, Maharam bar Barukh, Berlin, 1891',
            'versionSource': 'http://merhav.nli.org.il/primo-explore/fulldisplay?vid=NLI&docid=NNL_ALEPH001298074',
            'language': 'he',
            'text': all_ts
        }
        post_text_weak_connection("Teshuvot Maharam, Berlin Edition, Part II, Issur VeHeter", version)
        
        version = {
            'versionTitle': 'Shaarei Teshuvot, Maharam bar Barukh, Berlin, 1891',
            'versionSource': 'http://merhav.nli.org.il/primo-explore/fulldisplay?vid=NLI&docid=NNL_ALEPH001298074',
            'language': 'he',
            'text': default_box
        }
        post_text_weak_connection("Teshuvot Maharam, Berlin Edition, Part II", version)
    if shaar3:
        t_box=[]
        all_ts=[]
        past_start=False
        last_t=1
        with open('Berlin/ספר שערי תשובות 4.txt') as myfile:
            lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
        for line in lines:
            if u'פסקי ברכות של מו' in line:
                break
            if past_start and not_blank(line):
                if u'@' in line and len(t_box)>0:
                    print line
                    for x in range(0,getGematria(re.findall(ur'@\S{1,4}\.\s*',line)[0])-last_t-1):
                        all_ts.append([])
                    all_ts.append(t_box)
                    last_t=getGematria(re.findall(ur'@\S{1,4}\.\s*',line)[0])
                    t_box=[]
                t_box.append(clean_berlin(line))
                #t_box.append(line)
            if u'#שער שלישי' in line:
                past_start=True
        all_ts.append(t_box)
        """
        for tindex, t in enumerate(all_ts):
            for pindex, p in enumerate(t):
                print tindex, pindex, p
        """
        version = {
            'versionTitle': 'Shaarei Teshuvot, Maharam bar Barukh, Berlin, 1891',
            'versionSource': 'http://merhav.nli.org.il/primo-explore/fulldisplay?vid=NLI&docid=NNL_ALEPH001298074',
            'language': 'he',
            'text': all_ts
        }
        post_text_weak_connection("Teshuvot Maharam, Berlin Edition, Part III", version)
                
                
        
        
    
            
tmr_post_index()
post_cremona()
post_prague()
post_lemberg()
post_berlin()
