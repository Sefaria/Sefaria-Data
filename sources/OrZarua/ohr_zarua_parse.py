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
import re
import csv
from fuzzywuzzy import fuzz


chalek_titles=[['Volume I',u'חלק א'],['Volume II',u'חלק ב'],['Volume III',u'חלק ג'],['Volume IV',u'חלק ד']]
sub_sections=[
    [['Alpha Beta',u'אלפא ביתא'], ['Laws of Charity',u'הלכות צדקה'], []],
    [],
    [['Piskei Bava Kamma',u'פסקי בבא קמא'],['Piskei Bava Metzia',u'פסקי בבא מציעא'],['Piskei Bava Batra',u'פסקי בבא בתרא']],
    [['Piskei Sanhedrin',u'פסקי סנהדרין'],['Piskei Avodah Zarah',u'פסקי עבודה זרה'],['Piskei Shevuot',u'פסקי שבועות']]
]
archaot_header=[u'<b>הלכות ערכאות</b>']
vol_i_and_ii_link_table={"Berakhot":['Volume I, 1-109','Volume I, 117','Volume I, 127-212'],
                        "Niddah":['Volume I, 118-126', 'Volume I 338-366'],
                        "Mishnah Challah":['Volume I, 214-251'],
                        "Mishnah Kilayim":['Volume I, 252-307'],
                        "Mishnah Orlah":['Volume I, 308-325'],
                        "Chullin":['Volume I, 367-479'],
                        "Bekhorot":['Volume I, 480-530'],
                        "Menachot":['Volume I, 545-569'],
                        "Shabbat":['Volume II, 1-20', 'Volume II, 28-82','Volume II 98-108',"Volume II, 321-327"],
                        "Pesachim":['Volume II, 21-27'],
                        "Eruvin":["Volume II, 110-216"],
                        "Rosh Hashanah":['Volume II, 257-271'],
                        "Yoma":["Volume II, 277-280"],
                        "Sukkah":["Volume II, 282-320"],
                        "Beitzah":["Volume II, 329-366"],
                        "Megillah":["Volume II, 367-397"],
                        "Taanit":["Volume II, 398-416"]}

with open('Or_Zarua_Titles_-_trans_table.csv', 'r') as datafile:
    datareader = csv.reader(datafile)#, delimiter=';')
    alt_titles = []
    for row in datareader:
        alt_titles.append(map(lambda(x): x.decode('utf','replace'), row))


def remove_extra_spaces(string):
    string = re.sub(ur"\. $",u".",string)
    while u"  " in string:
        string=string.replace(u"  ",u" ")
    return string
def is_text(s):
    if len(s.strip().split())<2 and u'[' in s:
        return False
    return True
def highest_fuzz(input_list, input_item):
    highest_ratio = 0
    best_match = u''
    for item in input_list:
        if fuzz.ratio(input_item,item)>highest_ratio:
            best_match=item
            highest_ratio=fuzz.ratio(input_item,item)
    return best_match
def get_eng_title(s):
    for title in alt_titles:
        if title[1] in s:
            return title[0]
    return None     
def not_blank(s):
    while " " in s:
        s = s.replace(u" ",u"")
    return (len(s.replace(u"\n",u"").replace(u"\r",u"").replace(u"\t",u""))!=0);
def clean_line(s):
    if u'@88' in s:
        s=u'<b>'+s+u'</b>'
    elif u'@22' in s:
        s=u'<b>'+s+u'</b>'
    s = s.replace(u'@11',u'<b>').replace(u'@33',u'</b>')
    s= re.sub(ur'\(?\*\)?',u'',s)
    s=re.sub(ur'@\d+',u'',s)
    s = s.replace(u'\n',u'')
    return s
def aleph_clean_line(s):
    if u'#' in s:
        s=re.sub(ur'@\d+',u'',s)
        while u'#' in s:
            s=s[:s.index('#')]+'<b><big>'+s[s.index('#')+1]+'</b></big>'+s[s.index('#')+2:]
    else:
        s = s.replace(u'@11',u'<b>').replace(u'@33',u'</b>')
        s=re.sub(ur'@\d+',u'',s)
    s= re.sub(ur'\(?\*\)?',u'',s)
    s = s.replace(u'\n',u'')
    
    return s
        
def oz_post_index():
    # create index record
    record = SchemaNode()
    record.add_title('Ohr Zarua', 'en', primary=True, )
    record.add_title(u'אור זרוע', 'he', primary=True, )
    record.key = 'Ohr Zarua'

    # add nodes for first three parts (last one needs seperate treatment)
    for index, title in enumerate(chalek_titles):
        if len(sub_sections[index])>0:
            chelek_node = SchemaNode()
            chelek_node.add_title(title[0], 'en', primary=True, )
            chelek_node.add_title(title[1], 'he', primary=True, )
            chelek_node.key = title[0]
            for sindex, subsec in enumerate(sub_sections[index]):
                if len(subsec)>0:
                    section_node = JaggedArrayNode()
                    section_node.add_title(subsec[0], 'en', primary=True)
                    section_node.add_title(subsec[1], 'he', primary=True)
                    section_node.key = subsec[0]
                    if "Shevu" in subsec[0]:
                        section_node.depth = 1
                        section_node.addressTypes = ['Integer']
                        section_node.sectionNames = ["Siman"]
                    else:
                        section_node.depth = 2
                        section_node.addressTypes = ['Integer','Integer']
                        section_node.sectionNames = ["Siman","Paragraph"]
                    chelek_node.append(section_node)
                else:
                    default_node = JaggedArrayNode()
                    default_node.key = "default"
                    default_node.default = True
                    default_node.depth = 2
                    default_node.addressTypes = ['Integer', 'Integer']
                    default_node.sectionNames = ['Siman','Paragraph']
                    chelek_node.append(default_node)
            record.append(chelek_node)
        else:
            section_node = JaggedArrayNode()
            section_node.add_title(title[0], 'en', primary=True)
            section_node.add_title(title[1], 'he', primary=True)
            section_node.key = title[0]
            section_node.depth = 2
            section_node.addressTypes = ['Integer','Integer']
            section_node.sectionNames = ["Siman","Paragraph"]
            record.append(section_node)
    
    #alt toc
    section_nodes =SchemaNode()
    datafile = open('alt_toc_table.csv', 'r')
    datareader = csv.reader(datafile)
    alt_title_rows = []
    for row in datareader:
        alt_title_rows.append(map(lambda(x): x.decode('utf','replace'), row))
    for row in alt_title_rows:
        subsection_node = ArrayMapNode()
        subsection_node.depth = 0
        #print remove_extra_spaces("Ohr Zarua, {}, {}".format(row[2], row[3]))
        subsection_node.includeSections = True
        subsection_node.wholeRef = remove_extra_spaces("Ohr Zarua, {}, {}".format(row[2], row[3]))
        subsection_node.add_title(row[0], 'en', primary=True) 
        subsection_node.add_title(row[1], 'he', primary=True)
        section_nodes.append(subsection_node)
    record.validate()

    index = {
        "title": "Ohr Zarua",
        "alt_structs": {"Topic": section_nodes.serialize()},
        "categories": ["Halakhah"],
        "schema": record.serialize()
    }
    print "posting index..."
    post_index(index,weak_network=True)
def oz_post_chelek_1():
    global make_toc_table
    global trans_table
    text_dict={'Alpha Beta':[], 'Laws of Charity':[], 'default':[]}
    #first aleph beta
    with open('files/אלפא ביתא אור זרוע.txt') as myfile:
        lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
    past_start=False
    aleph_omits =[u'@00אלפא ביתא',u'@00אור זרוע',u'@22(א)']
    siman_box=[]
    for_next=[]
    for line in lines:
        if line not in aleph_omits and not_blank(line):
            if u'@22' in line and len(siman_box)>0:
                text_dict['Alpha Beta'].append(siman_box)
                siman_box=[]
                while len(for_next)>0:
                    siman_box.append(for_next.pop(0))
            elif u'@00' in line:
                for_next.append(u'<b>'+line.replace(u'@00',u'').replace(u'\n',u'')+u'</b>')
            else:
                siman_box.append(aleph_clean_line(line))
    """
    for sindex, siman in enumerate(text_dict['Alpha Beta']):
        for pindex, paragraph in enumerate(siman):
            print sindex, pindex, paragraph
    """
                
    with open('files/אור זרוע חלק א מוכן.txt') as myfile:
        lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
    current_section='Laws of Charity'
    siman_box=[]
    past_start=False
    for line in lines:
        #print current_section
        if u'שה @33וירא כתיב גבי אברהם כי ידעתי' in line:
            past_start=True         
        if past_start and u'IGNORE' not in line:
            if u'@00' in line and (u'(א)' not in line or "Charity" in current_section):
                if len(siman_box)>0:
                    text_dict[current_section].append(siman_box)
                    siman_box=[]
            elif u"@88" in line:
                if u'@88הלכות קריאת שמע' in line:
                    if len(siman_box)>0:
                        text_dict[current_section].append(siman_box)
                        siman_box=[]
                        current_section='default'
                    past_tzeddaka=True
                if make_toc_table:
                    with open('alt_toc_table.csv','a') as fd:
                        title=line.replace(u'@88',u'').replace(u'\n',u'')
                        if get_eng_title(title):
                            fd.write('{}, {}, Volume I, {}\n'.format(get_eng_title(title), title.encode('utf8'), len(text_dict[current_section])+1))
                        else:
                            print "SKIPPED \/"
                            print line
                if trans_table:
                    with open('trans_table.csv','a') as fd:
                        fd.write('E,{}\n'.format(line.replace(u'@88',u'').replace(u'\n',u'').encode('utf8')))
                    
            elif not_blank(line) and u'@88' not in line:
                siman_box.append(clean_line(line))
    #missing siman in Charity...
    text_dict[current_section].append(siman_box)
    text_dict['Laws of Charity'].insert(27,[])
    
    """
    for sindex, siman in enumerate(text_dict['default']):
        for pindex, paragraph in enumerate(siman):
            print sindex, pindex, paragraph
    1/0
    """
    if not make_toc_table and not trans_table:
        for title in text_dict.keys():
            if len(text_dict[title])>0 and 'Alpha' not in title:
                print "posting "+title
                if 'default' not in title:
                    version = {
                        'versionTitle': 'Ohr Zarua, Zhytomyr, 1862',
                        'versionSource': 'http://aleph.nli.org.il:80/F/?func=direct&doc_number=000309285&local_base=MBI01',
                        'language': 'he',
                        'text': text_dict[title]
                    }
                    post_text_weak_connection('Ohr Zarua, Volume I, '+title, version)
                    post_text('Ohr Zarua, Volume I, '+title, version,weak_network=True, skip_links=True, index_count="on")
                    
                else:
                    version = {
                        'versionTitle': 'Ohr Zarua, Zhytomyr, 1862',
                        'versionSource': 'http://aleph.nli.org.il:80/F/?func=direct&doc_number=000309285&local_base=MBI01',
                        'language': 'he',
                        'text': text_dict[title]
                    }
                    post_text_weak_connection('Ohr Zarua, Volume I', version)
                    post_text('Ohr Zarua, Volume I', version,weak_network=True, skip_links=True, index_count="on")
                    
def oz_post_chelek_2():
    with open('files/אור זרוע חלק ב מוכן.txt') as myfile:
        lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
    simanim=[]
    siman_box=[]
    past_start=False
    add_to_next=[]
    for line in lines:
        if u'@00(א)' in line:
            past_start=True         
        elif past_start:
            if u'@00' in line:
                if not_blank(re.sub(ur'@00\(.*?\)',u'',line)):
                    add_to_next.append(re.sub(ur'@00\(.*?\)',u'',line).strip())
                if len(siman_box)>0:
                    simanim.append(siman_box)
                    siman_box=[]
                    if len(line.split())>3:
                        siman_box.append(clean_line(line))
            elif u'@88' in line:
                if make_toc_table:
                    with open('alt_toc_table.csv','a') as fd:
                        title=line.replace(u'@88',u'').replace(u'\n',u'')
                        if get_eng_title(title):
                            fd.write('{}, {}, Volume II, {}\n'.format(get_eng_title(title), title.encode('utf8'), len(simanim)+1))
                        else:
                            print "SKIPPED \/"
                            print line
                if trans_table:
                    with open('trans_table.csv','a') as fd:
                        fd.write('E, {}\n'.format(line.replace(u'@88',u'').replace(u'\n',u'').encode('utf8')))
            elif u'ADDHERE' in line:
                simanim.append([])
            elif not_blank(line) and u'@22' not in line and is_text(line):
                line = clean_line(line)
                while len(add_to_next)>0:
                    line=clean_line(add_to_next.pop())+u'<br>'+line
                siman_box.append(line)
    simanim.append(siman_box)
    """
    for sindex, siman in enumerate(simanim):
        for pindex, paragraph in enumerate(siman):
            print sindex, pindex, paragraph
    0/0
    """
    if not make_toc_table and not trans_table:
        print "posting volume II..."
        version = {
            'versionTitle': 'Ohr Zarua, Zhytomyr, 1862',
            'versionSource': 'http://aleph.nli.org.il:80/F/?func=direct&doc_number=000309285&local_base=MBI01',
            'language': 'he',
            'text': simanim
        }
        #post_text_weak_connection('Ohr Zarua, Volume II', version)
        post_text('Ohr Zarua, Volume II', version,weak_network=True, skip_links=True, index_count="on")
        
def oz_post_chelek_3():
    with open('files/אור זרוע חלק ג מוכן.txt') as myfile:
        lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
    text_dict={'Piskei Bava Kamma':[],'Piskei Bava Metzia':[],'Piskei Bava Batra':[]}
    
    current_section='Piskei Bava Kamma'
    siman_box=[]
    for_next_paragraph=[]
    past_start=False
    for line in lines:
        #print current_section
        if u'תשים לפניהם: ב' in line:
            past_start=True         
        elif past_start and 'SKIP' not in line:
            if u'@00' in line:
                if len(siman_box)>0:
                    text_dict[current_section].append(siman_box)
                    siman_box=[]
            else:
                if u'@88פסקי בבא מציעא פרק א' in line:
                    if len(siman_box)>0:
                        text_dict[current_section].append(siman_box)
                        siman_box=[]
                        current_section='Piskei Bava Metzia'
                if u'@88פסקי בבא בתרא פרק א' in line:
                    if len(siman_box)>0:
                        text_dict[current_section].append(siman_box)
                        siman_box=[]
                        current_section='Piskei Bava Batra'
                elif u'@22' in line:
                    for_next_paragraph.append(clean_line(line))
                elif not_blank(line) and u'SKIP' not in line:
                    line=clean_line(line)
                    while len(for_next_paragraph)>0:
                        line=for_next_paragraph.pop(0)+u'<br>'+line
                    siman_box.append(line)
    text_dict[current_section].append(siman_box)
    
    text_dict['Piskei Bava Kamma'].insert(0, archaot_header)
    #missing two simanim in Bava Batra
    text_dict['Piskei Bava Batra'].insert(255, [])
    text_dict['Piskei Bava Batra'].insert(255, [])
    #"""
    for sindex, siman in enumerate(text_dict['Piskei Bava Batra']):
        for pindex, paragraph in enumerate(siman):
            print sindex, pindex, paragraph
    1/0
    #"""
    for title in text_dict.keys():
        print "posting "+title
        if True:#len(text_dict[title])>0 and "Kam" in title:
            """
            for sindex, siman in enumerate(text_dict[title]):
                for pindex, paragraph in enumerate(siman):
                    print sindex, pindex, paragraph
            """
            #1/0
            version = {
                'versionTitle': 'Ohr Zarua, Zhytomyr, 1862',
                'versionSource': 'http://aleph.nli.org.il:80/F/?func=direct&doc_number=000309285&local_base=MBI01',
                'language': 'he',
                'text': text_dict[title]
            }
            post_text_weak_connection('Ohr Zarua, Volume III, '+title, version)
def oz_post_chelek_4():
    with open('files/אור זרוע חלק ד מוכן.txt') as myfile:
        lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
    text_dict={'Piskei Sanhedrin': [], 'Piskei Avodah Zarah':[[] for x in range(95)], 'Piskei Shevuot':[]}
    #""""
    current_section='Piskei Sanhedrin'
    siman_box=[]
    for_next_paragraph=[]
    past_start=False
    for line in lines:
        #print current_section
        if u'דף ג' in line:
            past_start=True         
        elif past_start and u'SKIP' not in line:
            if u'@00' in line:
                if u'?' not in line and len(siman_box)>0:
                    text_dict[current_section].append(siman_box)
                    siman_box=[]
            else:
                if u'@88פסקי עבודה זרה' in line:
                    if len(siman_box)>0:
                        text_dict[current_section].append(siman_box)
                        siman_box=[]
                        current_section='Piskei Avodah Zarah'
                elif u'@22' in line:
                    for_next_paragraph.append(clean_line(line))
                elif not_blank(line) and u'SKIP' not in line:
                    line=clean_line(line)
                    while len(for_next_paragraph)>0:
                        line=for_next_paragraph.pop(0)+u'<br>'+line
                    siman_box.append(line)
    text_dict[current_section].append(siman_box)
    
    #fix align issue
    text_dict['Piskei Avodah Zarah'].insert(144,[])
    
    #"""
    
    
    """              
    for sindex, siman in enumerate(text_dict['Piskei Avodah Zarah']):
        for pindex, paragraph in enumerate(siman):
            print sindex, pindex, paragraph
    1/0
    """
    #Shevuot needs special treatment
    with open('files/אור זרוע למסכת שבועות.txt') as myfile:
        lines = list(map(lambda(x): x.decode('utf','replace'), myfile.readlines()))
    for_next_paragraph=[]
    
    for line in lines:
        if u'@22' in line:
            for_next_paragraph.append(clean_line(line))
        elif not_blank(line) and u'SKIP' not in line:
            line=clean_line(line)
            while len(for_next_paragraph)>0:
                line=for_next_paragraph.pop(0)+u'<br>'+line
            text_dict['Piskei Shevuot'].append(line)
    """"
    for pindex, paragraph in enumerate(text_dict['Piskei Shevuot']):
        print "SHAVUOT",pindex, paragraph
    #1/0
    """
    for title in text_dict.keys():
        if len(text_dict[title])>0 and "Shev" not in title:
            print "posting "+title
            version = {
                'versionTitle': 'Ohr Zarua, Zhytomyr, 1862',
                'versionSource': 'http://aleph.nli.org.il:80/F/?func=direct&doc_number=000309285&local_base=MBI01',
                'language': 'he',
                'text': text_dict[title]
            }
            if "local" in SEFARIA_SERVER:
                post_text('Ohr Zarua, Volume IV, '+title, version,weak_network=True, skip_links=True, index_count="on")
            else:
                post_text_weak_connection('Ohr Zarua, Volume IV, '+title, version)
def finish_file():
    datafile = open('alt_toc_table.csv', 'r')
    datareader = csv.reader(datafile)
    alt_title_rows = []
    for row in datareader:
        alt_title_rows.append(map(lambda(x): x.decode('utf','replace'), row))
    f = open('alt_toc_table.csv','w')
    next_row=None
    for index, row in enumerate(alt_title_rows):
        row=map(lambda(x): x.encode('utf','replace'),row)
        if next_row:
            f.write(', '.join(next_row)+'-'+str(int(row[-1])-1)+'\n')
        if index==len(alt_title_rows)-1:
            f.write(', '.join(next_row)+'-465\n')
        next_row=row
        
    f.close()
def link_talmud_sections():
    talmud_sections=[
        'Ohr Zarua, Volume III, Piskei Bava Kamma',
        'Ohr Zarua, Volume III, Piskei Bava Metzia',
        'Ohr Zarua, Volume III, Piskei Bava Batra',
        'Ohr Zarua, Volume IV, Piskei Sanhedrin',
        'Ohr Zarua, Volume IV, Piskei Avodah Zarah',
        'Ohr Zarua, Volume IV, Piskei Shevuot'
    ]
    ranges=generate_range_tables()
    for talmud_section in talmud_sections:
        if "Kamma" not in talmud_section and "Met" not in talmud_section:
            tractate = talmud_section.split('Piskei ')[-1]
            for range_group in ranges[tractate]:
                tractate_chunk=TextChunk(Ref('{} {}'.format(tractate, range_group[0])),'he')
                ohr_chunk = TextChunk(Ref('{},{}-{}'.format(talmud_section,range_group[1],range_group[2])),'he')
                matches = match_ref(tractate_chunk,ohr_chunk,
                    base_tokenizer,dh_extract_method=dh_extract_method,rashi_filter=_filter,verbose=True)
                if "comment_refs" in matches:
                    for link_index, (base, comment) in enumerate(zip(matches["matches"],matches["comment_refs"])):
                        print "B",base,"C", comment
                        if base:
                            link = (
                                    {
                                    "refs": [
                                             base.normal(),
                                             comment.normal(),
                                             ],
                                    "type": "commentary",
                                    "auto": True,
                                    "generated_by": "sterling_ohrzarua_linker"
                                    })
                            post_link(link, weak_network=True)
        
def _filter(some_string):
    return not_blank(some_string)
def dh_extract_method(some_string):
    some_string=re.sub(ur'<.*?>',u'',some_string)
    some_string=re.sub(ur'\[.*?\]',u'',some_string)
    some_string=some_string.replace(u'מתני\'',u'')
    #print "DH!:",some_string
    if len(some_string.split(u'.')[0].split(u' '))<8:
        return some_string.split(u'.')[0]
    else:
        return u' '.join(some_string.split(u' ')[:8])

def base_tokenizer(some_string):
    some_string=re.sub(ur'<.*?>',u'',some_string)
    return filter(lambda(x): x!=u'',remove_extra_spaces(some_string.replace(u"<b>",u"").replace(u"</b>",u"").replace(u".",u"")).split(" "))
    
def extract_daf(s):
    sections=s.split(u' ')
    if len(sections)==3:
        amud='a' if u'א' in sections[2] else 'b'
        daf = getGematria(sections[1]) if getGematria(sections[1])!=300 else "SHAM"
        return '{}{}'.format(daf,amud)
    if len(sections)==2:
        amud='a' if u'א' in sections[1] else 'b'
        daf = getGematria(sections[0]) if getGematria(sections[0])!=300 else "SHAM"
        return '{}{}'.format(daf,amud)
def generate_range_tables():
    
    #we need range tables to direct the linking, since the structure here does not follow the dapim
    talmud_sections=[
        'Ohr Zarua, Volume III, Piskei Bava Kamma',
        'Ohr Zarua, Volume III, Piskei Bava Metzia',
        'Ohr Zarua, Volume III, Piskei Bava Batra',
        'Ohr Zarua, Volume IV, Piskei Sanhedrin',
        'Ohr Zarua, Volume IV, Piskei Avodah Zarah'
    ]
    ranges={}
    
    for talmud_section in talmud_sections:
        tractate = talmud_section.split('Piskei ')[-1]
        ranges[tractate]=[]
        for sindex, siman in enumerate(TextChunk(Ref(talmud_section),'he').text):
            for pindex, paragraph in enumerate(siman):
                if re.search(ur'\[דף.*?[אב]\]',paragraph):
                    #print tractate,re.search(ur'\[דף.*?[אב]\]',paragraph).group()
                    #print re.search(ur'\[דף.*?[אב]\]',paragraph).group()
                    #"""
                    if len(ranges[tractate])>0:
                        ranges[tractate][-1].append(last_location)
                    ranges[tractate].append([extract_daf(re.search(ur'\[דף.*?[אב]\]',paragraph).group()),'{}:{}'.format(sindex+1,pindex+1)])
                    #"""
                last_location='{}:{}'.format(sindex+1,pindex+1)
        ranges[tractate][-1].append(last_location)
    
    #Shevuot Seperate...
    talmud_section='Ohr Zarua, Volume IV, Piskei Shevuot'
    old_daf_ref=''
    tractate = talmud_section.split('Piskei ')[-1]
    #print tractate
    ranges[tractate]=[]
    for pindex, paragraph in enumerate(TextChunk(Ref(talmud_section),'he').text):
        #print paragraph
        if re.search(ur'<b>\[.*?[םאב]\]',paragraph):
            if len(re.search(ur'<b>\[.*?[אבם]\]',paragraph).group().split(u' '))>1:
                #print re.search(ur'<b>\[.*?[אבם]\]',paragraph).group()
                if len(ranges[tractate])>0:
                    ranges[tractate][-1].append(last_location)
                new_daf_ref=extract_daf(re.search(ur'<b>\[.*?[םאב]\]',paragraph).group())
                new_daf_ref=new_daf_ref.replace("SHAM",re.search(ur'\d*',old_daf_ref).group())
                ranges[tractate].append([new_daf_ref,str(pindex+1)])
                old_daf_ref=new_daf_ref
        last_location=str(pindex+1)
    ranges[tractate][-1].append(last_location)
    """
    for key in ranges.keys():
        for ref in ranges[key]:
            print key,ref[0],ref[1],ref[2]
    """
    return ranges
def link_first_two_volumes():
    for mesechet in vol_i_and_ii_link_table.keys():
        if True:
            f = open('Ohr Zarua {} links.tsv'.format(mesechet),'w')
            f.write('OZ location\tTalmud Location\tDH Text\tOZ Full Text\tfull talmud line\n')
            f.close()
            with open('Ohr Zarua {} links.tsv'.format(mesechet),'a') as mf:
                for oz_range in vol_i_and_ii_link_table[mesechet]:
                    tractate_chunk=TextChunk(Ref(mesechet),'he')
                    ohr_chunk = TextChunk(Ref('Ohr Zarua, {}'.format(oz_range)),'he')
                    print "LINKING {} TO {}".format(mesechet, oz_range)
                    matches = match_ref(tractate_chunk,ohr_chunk,
                        base_tokenizer,dh_extract_method=dh_extract_method,rashi_filter=_filter,verbose=True,boundaryFlexibility=1000000, word_threshold=0.1,char_threshold=0.2)
                    if "comment_refs" in matches:
                        for link_index, (base, comment) in enumerate(zip(matches["matches"],matches["comment_refs"])):
                            for key in matches.keys():
                                print key
                            print "B",base,"C", comment
                            if base:
                                mf.write(u'{}\t{}\t{}\t{}\t{}\n'.format(comment,base, dh_extract_method(TextChunk(comment,'he').text),TextChunk(comment,'he').text, TextChunk(base,'he').text).encode('utf','replace'))
                            else:
                                mf.write(u'{}\tNULL\t{}\t{}\tNULL\n'.format(comment, dh_extract_method(TextChunk(comment,'he').text),TextChunk(comment,'he').text).encode('utf','replace'))
                                

make_toc_table=False
trans_table=False
if make_toc_table:
    f = open('alt_toc_table.csv','w')
    f.close()   
if trans_table:
    f = open('trans_table.csv','w')
    f.close()
#oz_post_index()
#oz_post_chelek_1()
#oz_post_chelek_2()
link_first_two_volumes()
#finish_file()
#oz_post_chelek_3()
#oz_post_chelek_4()
#generate_range_tables()
#link_talmud_sections()
#721
"""
datafile = open('Or_Zarua_Titles_-_trans_table.csv', 'r')
datareader = csv.reader(datafile)#, delimiter=';')
alt_titles = []
for row in datareader:
    alt_titles.append(map(lambda(x): x.decode('utf','replace'), row))

                                link = (
                                        {
                                        "refs": [
                                                 base.normal(),
                                                 comment.normal(),
                                                 ],
                                        "type": "commentary",
                                        "auto": True,
                                        "generated_by": "sterling_ohrzarua_linker"
                                        })
                                #post_link(link, weak_network=True)
"""