# -*- coding: utf-8 -*-
import os, sys, re
import urllib2
from urllib2 import HTTPError
from collections import namedtuple
import json
import codecs
import re
from sources.functions import post_index, post_text
from sefaria.utils.hebrew import strip_nikkud, normalize_final_letters_in_str, gematria, has_cantillation
from data_utilities.util import numToHeb
from sefaria.datatype import jagged_array
from sefaria.model import *
from sefaria.system.exceptions import BookNameError

post = False

def isGematria(txt):
    txt = normalize_final_letters_in_str(txt)
    txt = re.sub(ur'[\', ׳”״”":.\r\n)]', u'', txt)
    if txt.find(u"טו") >= 0:
        txt = txt.replace(u"טו", u"יה")
    elif txt.find(u"טז") >= 0:
        txt = txt.replace(u"טז", u"יו")

    if len(txt) == 0:
        # print "not gematria " + txt
        return False
    try:
        while txt[0] == u'ת':
            txt = txt[1:]
    except:
        return False

    if len(txt) == 1:
        if txt[0] < u'א' or txt[0] > u'ת':
            # print "not gematria " + txt
            return False
    elif len(txt) == 2:
        if txt[0] < u'י' or (txt[0] < u'ק' and txt[1] > u'ט'):
            # print "not gematria " + txt
            return False
    elif len(txt) == 3:
        if txt[0] < u'ק' or txt[1] < u'י' or txt[2] > u'ט':
            # print "not gematria " + txt
            return False
    else:
        return False
    return True
#skip (להלן|לעיל|לקמן) ((ילפ|ב|פ(\'|\")).{0,30}) (\(|\[)?((דף|ד\')(\.)? )?[א-ת]*
self_ref_words = ur'(להלן|לעיל|לקמן)'
# filler_words = u"(ילפ|ב|פ(\'|\"))"

daf_words = ur"(?P<daf_prepend>ב?\u05d3[\u05e3\u05e4\u05f3']\s+)?"
daf_number = ur'(?P<daf_number>[״”״\'ֿ׳\"א-ת]+(?![א-ת]))'
parentheses = ur'(?P<parentheses>[\(\[{]?)'
sham = ur'(?P<sham>שם\s)?'
amud_words = ur'''(?P<amud>[:.]|(\s+ע(מוד\s+|[”״”"\'׳]+)|,?\s*)[אב][\'׳]?(?![א-ת]))?'''
perek_prepend = ur"ב?(פ[רי]?['׳]|\u05e4\u05bc?\u05b6?\u05e8\u05b6?\u05e7(?:\u05d9\u05b4?\u05dd)?|[רס][\"”“״׳\']+פ|ו?ב?(סוף|ריש)|שי?להי|אית['׳א])\s*"
not_siman_words = ur'''(?!\s*ס(י?[''׳]|ימן|[”״”"\'׳]+ס))'''
filler_chars = ur'\s*[\(\[{\)\]\}\s.,:;]+'

files_dict = {}
perakim_names = ur'(?P<perek_name>'

perek_to_mesechet_dict = {}
# mesechet_to_alt_titles = {}
with codecs.open('perakim.txt', 'r', encoding='utf-8') as fr:
    perakim_names_list = []
    for line in fr:
        values = line.split(u',')
        ref = Ref(values[0].strip())
        perek_title = values[2].strip()
        chapter = values[1].strip()
        hebrew_title = ref.he_book()
        all_he_titles = ref.index.all_titles('he')
        if u'?' in perek_title:
            idx = perek_title.index(u'?')
            if perek_title[:idx]+perek_title[idx+1:] in perek_to_mesechet_dict:
                print perek_title[:idx]+perek_title[idx+1:]
            perek_to_mesechet_dict[perek_title[:idx]+perek_title[idx+1:]] = (hebrew_title, chapter)
            # for hebrew_title in all_he_titles:
            #     perek_to_mesechet_dict[hebrew_title + u' ב' + perek_title[:idx]+perek_title[idx+1:]] = (hebrew_title, chapter)
            #     perek_to_mesechet_dict[hebrew_title + u' ' + perek_title[:idx]+perek_title[idx+1:]] = (hebrew_title, chapter)
            if perek_title[:idx-1]+perek_title[idx+1:] in perek_to_mesechet_dict:
                print perek_title[:idx-1]+perek_title[idx+1:]
            perek_to_mesechet_dict[perek_title[:idx-1]+perek_title[idx+1:]] = (hebrew_title, chapter)
            # for hebrew_title in all_he_titles:
            #     perek_to_mesechet_dict[hebrew_title + u' ' + perek_title[:idx-1]+perek_title[idx+1:]] = (hebrew_title, chapter)
            #     perek_to_mesechet_dict[hebrew_title + u' ב' + perek_title[:idx-1]+perek_title[idx+1:]] = (hebrew_title, chapter)
        else:
            if perek_title in perek_to_mesechet_dict:
                print perek_title
            perek_to_mesechet_dict[perek_title] = (hebrew_title, chapter)
            # for hebrew_title in all_he_titles:
            #     perek_to_mesechet_dict[hebrew_title + u' ' + perek_title] = (hebrew_title, chapter)
            #     perek_to_mesechet_dict[hebrew_title + u' ב' + perek_title] = (hebrew_title, chapter)
        # mesechet_to_alt_titles[ref.he_book()] = ref.index.all_titles('he')
        perakim_names_list.append(perek_title)
        # for hebrew_title in all_he_titles:
        #     perakim_names_list.append(hebrew_title + ur' ב?' + perek_title)
    perakim_names_list.sort(key=len, reverse=True)
    perakim_names += ur'|'.join(perakim_names_list) + ur')'
    print(perakim_names)

filler_outside_words = ur'''((ו?ב?(סוף|ריש)(\s+ה?פרק)?|ו?פ[\u059E\u201C"””״׳\']+ק\s+(ד?בתרא)?|ב?ברייתא|ד?תנן)\s+)?'''
filler_inside_words = ur'(?P<filler_inside>ו?ב?(סוף|ריש)\s+)?'

# perek_str = perek_prepend + perakim_names + filler_outside_words + parentheses + filler_inside_words + daf_words + daf_number + amud_words + not_siman_words
perek_str = ur'[\(\[]?' + perek_prepend + perakim_names + filler_chars + filler_outside_words + filler_chars + sham + filler_inside_words + daf_words + daf_number + amud_words
# ur"(פ['']|פרק|[רס][\"””״]פ) (?P<perek_name>הורו בית דין|הורה כהן משיח|כהן משיח|לפני אי?די?הן|אין מעמי?דין|כל הצלמים|רבי ישמעאל|ה?שוכר את הפועל|מגילה נקראת|ה?קו?רא למפרע|ה?קו?רא עו?מד|בני ה?עיר|שבועות שתים( קמא)?|ידי?עו?ת ה?טו?מאה|שבו?עו?ת שתים בתרא|שבועת( העדות)?|שבועת הפקדון|שבועת הדייני?ן|כל הנשבעי?ן|ארבעה שו?מרי?ן|מאימתי|היה קורא|מי שמתו|תפלת השחר|אין עו?מדי?ן|כיצד מברכי?ן|שלשה שאכלו|אלו דברים|ה?רואה|הלוקח( עובר חמורו)?|הלוקח עובר פרתו|הלו?קח בהמה|עד כמה|כל פסולי המו?קדשי?ן|על אלו מו?מי?ן|מו?מי?ן אלו|יש בכור|מעשר בהמה|דיני ממונות|כהן גדול|זה בורר|אחד דיני ממונות|היו בודקין|נגמר הדין|ארבע מיתות|בן סורר ומורה|הנשרפין|אלו הן הנחנקין|ה?חלק|כל כנויי נזירות|הריני נזיר|מי שאמר( קמא)?|מי שאמר בתרא|בית שמאי|שלשה מינין|כהן גדול|שני נזירים|הכותים אין להם נזירות|ארבעה אבות|כיצד רגל|המניח|שור שנגח( ד' וה')?|שור שנגח את הפרה|הכונס|מרובה|החובל|הגוזל עצים|הגוזל בתרא|המקנא|היה מביא|היה נוטל|ארוסה|כשם שהמים|מי שקינא|אלו נאמרין|משוח מלחמה|עגלה ערופה|השותפין|לא יחפור|חזקת הבתים|המוכר את הבית|המוכר את הספינה|המוכר פירות|בית כור|יש נוחלין|מי שמת|גט פשוט|שבעת ימים|בראשונה|אמר להם הממונה|טרף בקלפי|הוציאו לו|שני שעירי|בא לו|יום ה?כפורים|קדשי קדשים|חטאת העוף|ולד חטאת|קדשי מזבח|הנהנה מן ההקדש|השליח שעשה שליחותו|שלשים ושש|ארבעה מחוסרי כפרה|אמרו לו|ספק אכל חלב|דם שחיטה|המביא אשם|בשלשה מקומות|ראוהו אחיו|אמר להם הממונה בואו|לא היו כופתין|אמר להם הממונה ברכו|החלו עולים|בזמן שכהן גדול|ה?כל מעריכין|אין נערכין|יש בערכין|השג יד|ה?אומר משקלי עלי|שום היתו?מים|אין מקדי?שין|ה?מקדיש שדהו|ה?מוכר שדהו|שמאי אומר|כל היד|ה?מפלת חתיכה|בנות כותים|יוצא דופן|בא סימן|דם ה?נדה|ה?רואה כתם|ה?אשה שהיא עושה|תינוקת|ה?מביא קמא|ה?מביא בתרא|כל הגט|ה?שולח|הניזקין|ה?אומר התקבל|מי שאחזו|הזורק גט|המגרש|חמש עשרה נשים|כיצד אשת אחיו|ארבעה אחין|החולץ|רבן גמליאל|הבא על יבמתו|אלמנה לכהן גדול|הערל|יש מותרות|האישה רבה|נושאין על האנוסה|מצות חליצה|בית שמאי|חרש שנשא|האשה שלום|האשה בתרא|משקין בית השלחין|מי שהפך|ואלו מגלחין|הכל חייבין|אין דורשין|חומר בקודש|יציאות השבת|במה מדליקין|כירה|במה טומנין|במה בהמה|במה אשה|כלל גדול|המוציא יין|אמר רבי עקיבא|המצניע|הזורק|הבונה|האורג|שמנה שרצים|ואלו קשרים|כל כתבי|כל הכלים|מפנין|רבי אליעזר דמילה|תולין|נוטל אדם את בנו|חבית|שואל|מי שהחשיך|מבוי|עו?שין פסין|ב?כל מערבין|מי שהוציאוהו|כיצד מעברין|הדר|חלון|כיצד משתתפין|כל גגות|ה?מוצא תפילין|שנים אוחזין|אלו מציאות|המפקיד|הזהב|איזהו נשך|ה?שוכר את האומנין|ה?שוכר את הפועלים|השואל את הפרה|ה?מקבל שדה מחבירו|ה?בית והעלייה|כל הזבחים|כל הזבחים שקבלו דמן|כל הפסולין|בית שמאי|איזהו מקומן|קדשי קדשים|חטאת העוף|כל הזבחים שנתערבו|המזבח מקדש|כל התדיר|דם חטאת|טבול יום|ה?שוחט והמעלה|פרת חטאת|ה?אשה נקנית|ה?איש מקדש|ה?אומר לחברו|עשרה יוחסין|ה?כל שוחטין|ה?שוחט|אלו טרי?פות|בהמה המקשה|או?תו ואת בנו|כסוי הדם|גיד הנשה|כל הבשר|ה?עור והרוטב|ה?זרוע והלחיים|ראשית הגז|שילוח הקן|הכל ממי?רין|יש בקרבנות|אלו קדשים|ולד חטאת|כיצד מערי?מין|כל האסו?רין|יש בקדשי מזבח|מאימתי מזכירין|סדר תעניות כיצד|סדר תעניות( אלו)?|ב?שלשה פרקים|יום טוב|אין צדין|המביא כדי יין|משילין|ארבעה ראשי שנים|אם אינן מכירין|ראוהו בית דין|יום טוב|כל כנויי|ו?אלו מו?תרין|ארבעה נדרים|אין בין המודר|השו?תפין שנדרו|ה?נודר( מן המבושל)?|ה?נודר מן הירק|קונם יין|רבי אליעזר|נערה המאורסה|ו?אלו נדרים|כל המנחות|ה?קומץ את ה?מנחה|ה?קומץ רבה|ה?תכלת|כל ה?מנחות באות מצה|רבי ישמעאל|אלו מנחות נקמצות|התודה היתה באה|כל קרבנות ציבור|שתי מדות|שתי הלחם|המנחות והנסכים|הרי עלי עשרון|אור לארבעה עשר|כל שעה|אלו עוברין|מקום שנהגו|תמיד נשחט|אלו דברים|כיצד צולין|האשה|מי שהיה טמא|ערבי פסחים|בתולה נשאת|ה?אשה שנתארמלה|אלו נערות|נערה שנתפתתה|אף על פי|מציאת האשה|ה?מדיר|ה?אשה שנפלו|ה?כותב לאשתו|מי שהיה נשוי|אלמנה ניזונת|ה?נושא את ה?אשה|שני דייני גזירות|הישן|לולב ה?גזול|לולב וערבה|ה?חליל|כיצד העדים|אלו הן הגולין|אלו הן הלוקין).?.?.{4, 15}((ו?ב?(סוף|ריש)( הפרק)?|ופ[\"””״]ק דבתרא|בברייתא|תנן) )?(?P<parentheses>[\(\[{])(?P<filler_inside>ו?ב?(סוף|ריש) )?(?P<daf_prepend>(ב?ד[פף]?\'?)\.? )?(?P<daf_number>[״”״\'\"א-ת]+)(?P<amud>[:.]|(ע(מוד |[”״”\"\']+)|,? )[אב])?"
links_added = 0
base_text = None

def get_chapter_range_ref(talmud_title, chapter):
    range = Ref(talmud_title).index.alt_structs['Chapters']['nodes'][int(chapter)-1]['wholeRef']
    range = re.sub(ur'b:', u'a:', range[:range.index(u'-')]) + range[range.index(u'-'):]
    try:
        # try to extend range for pages without amudim and slightly bad refs by authours
        return Ref(range[:range.index(u'-')] + re.sub(ur'a:', u'b:', range[range.index(u'-'):]))
    except:
        return Ref(range)
    

def walk_thru_action(s, tref, heVersionTitle, heVersionSource):
    global base_text
    global links_added
    global csvfile
    seg_text = u''
    test_seg_text = u''
    pre_idx = 0
    test_pre_idx = 0
    offset = 0
    text_changed_perek = False
    text_changed_quotes = False
    # if re.search(ur'[\u0590-\u05FF]([\u2018\u2019\u0027][\u2018\u2019\u0027]|[\"“”])[\u0590-\u05FF]', s):
    s = re.sub(ur'([\u0590-\u05FF])([\u2018\u2019\u0027][\u2018\u2019\u0027]|[“”])([\u0590-\u05FF])', ur'\1״\3', s)
        # text_changed_quotes = True
    # if re.search(ur'[\u2018\u2019\u0027][\u2018\u2019\u0027]', s):
    s = re.sub(ur'([\u2018\u2019\u0027][\u2018\u2019\u0027]|[“”])', ur'"', s)
        # print u"quotes replace {} ref: {}".format(s, tref)
        # text_changed_quotes = True
    # if re.search(ur'([\u0590-\u05FF])([\u2018\u2019\u0027])([\u0590-\u05FF])', s):
    s = re.sub(ur'([\u0590-\u05FF])[\u2018\u2019]([\u0590-\u05FF])', ur'\1׳\2', s)
        # text_changed_quotes = True'
    # if re.search(ur'[\u2018\u2019]', s):
    s = re.sub(ur'[\u2018\u2019]', ur"'", s)
        # text_changed_quotes = True
    # if has_cantillation(s, detect_vowels=True):
    if True:
        # s_nikud = s
        # s = strip_nikkud(s)
        for match in re.finditer(perek_str, s):  
            try:
                daf = match.group('daf_number')
                amud = match.group('amud')
                talmud_title, chapter = perek_to_mesechet_dict[match.group('perek_name')]
                # alt_titles = mesechet_to_alt_titles[talmud_title]
                ref = talmud_title + u' ' + daf + amud if amud else talmud_title + u' ' + daf
                if isGematria(daf) and Ref().is_ref(ref) and ((match.group()[0] != u'[') and (match.group()[0] != u'(')):
                    if not Ref(ref).overlaps(get_chapter_range_ref(talmud_title, chapter)):
                        if u'ישמעאל' in match.group('perek_name'):
                            talmud_title = u'מנחות'
                            chapter = 6
                            ref = talmud_title + u' ' + daf + amud if amud else talmud_title + u' ' + daf
                            if not Ref(ref).overlaps(get_chapter_range_ref(talmud_title, chapter)):
                                continue
                        elif u'נערה' == match.group('perek_name'):
                            talmud_title = u'נדרים'
                            chapter = 10
                            ref = talmud_title + u' ' + daf + amud if amud else talmud_title + u' ' + daf
                            if not Ref(ref).overlaps(get_chapter_range_ref(talmud_title, chapter)):
                                continue 
                        elif u'שבועות שתים' in match.group('perek_name'):
                            chapter = 1
                            ref = talmud_title + u' ' + daf + amud if amud else talmud_title + u' ' + daf
                            if not Ref(ref).overlaps(get_chapter_range_ref(talmud_title, chapter)):
                                continue  
                        elif u'זורק' in match.group('perek_name'):
                            talmud_title = u'גיטין'
                            chapter = 8
                            ref = talmud_title + u' ' + daf + amud if amud else talmud_title + u' ' + daf
                            if not Ref(ref).overlaps(get_chapter_range_ref(talmud_title, chapter)):
                                continue
                        elif u'ה?שוחט' in match.group('perek_name'):
                            talmud_title = u'זבחים'
                            chapter = 13
                            ref = talmud_title + u' ' + daf + amud if amud else talmud_title + u' ' + daf
                            if not Ref(ref).overlaps(get_chapter_range_ref(talmud_title, chapter)):
                                continue
                        elif u'כהן גדול' in match.group('perek_name'):
                            talmud_title = u'נזיר'
                            chapter = 7
                            ref = talmud_title + u' ' + daf + amud if amud else talmud_title + u' ' + daf
                            if not Ref(ref).overlaps(get_chapter_range_ref(talmud_title, chapter)):
                                continue
                        elif u'כל המנחות' in match.group('perek_name'):
                            chapter = 5
                            ref = talmud_title + u' ' + daf + amud if amud else talmud_title + u' ' + daf
                            if not Ref(ref).overlaps(get_chapter_range_ref(talmud_title, chapter)):
                                continue
                        elif u'נודר' in match.group('perek_name'):
                            talmud_title = u'נדרים'
                            chapter = 6
                            ref = talmud_title + u' ' + daf + amud if amud else talmud_title + u' ' + daf
                            if not Ref(ref).overlaps(get_chapter_range_ref(talmud_title, chapter)):
                                continue
                        # elif u'האשה' in match.group('perek_name'):
                        #     talmud_title = u'נידה'
                        #     chapter = 9
                        #     ref = talmud_title + u' ' + daf + amud if amud else talmud_title + u' ' + daf
                        #     range = Ref(talmud_title).index.alt_structs['Chapters']['nodes'][int(chapter)-1]['wholeRef']
                        #     # extend range for pages without amudim and slightly bad refs by authours
                        #     range = re.sub(ur'b:', u'a:', range[:range.index(u'-')]) + re.sub(ur'a:', u'b:', range[range.index(u'-'):])
                        #     if not Ref(ref).overlaps(Ref(range)):
                        #         continue
                        elif u'שותפין' in match.group('perek_name'):
                            talmud_title = u'נדרים'
                            chapter = 5
                            ref = talmud_title + u' ' + daf + amud if amud else talmud_title + u' ' + daf
                            if not Ref(ref).overlaps(get_chapter_range_ref(talmud_title, chapter)):
                                continue
                        elif u'מי שאמר' in match.group('perek_name'):
                            talmud_title = u'נזיר'
                            chapter = 3
                            ref = talmud_title + u' ' + daf + amud if amud else talmud_title + u' ' + daf
                            if not Ref(ref).overlaps(get_chapter_range_ref(talmud_title, chapter)):
                                continue
                        elif u'גוזל' in match.group('perek_name'):
                            talmud_title = u'בבא קמא'
                            chapter = 10
                            ref = talmud_title + u' ' + daf + amud if amud else talmud_title + u' ' + daf
                            if not Ref(ref).overlaps(get_chapter_range_ref(talmud_title, chapter)):
                                continue
                        elif u'ולד חטאת' in match.group('perek_name'):
                            talmud_title = u'תמורה'
                            chapter = 4
                            ref = talmud_title + u' ' + daf + amud if amud else talmud_title + u' ' + daf
                            if not Ref(ref).overlaps(get_chapter_range_ref(talmud_title, chapter)):
                                continue
                        elif u'חטאת העוף' in match.group('perek_name'):
                            talmud_title = u'מעילה'
                            chapter = 2
                            ref = talmud_title + u' ' + daf + amud if amud else talmud_title + u' ' + daf
                            if not Ref(ref).overlaps(get_chapter_range_ref(talmud_title, chapter)):
                                continue
                        elif u'קדשי קדשים' in match.group('perek_name'):
                            talmud_title = u'מעילה'
                            chapter = 1
                            ref = talmud_title + u' ' + daf + amud if amud else talmud_title + u' ' + daf
                            if not Ref(ref).overlaps(get_chapter_range_ref(talmud_title, chapter)):
                                continue
                        elif u'אלו דברים' in match.group('perek_name'):
                            talmud_title = u'ברכות'
                            chapter = 8
                            ref = talmud_title + u' ' + daf + amud if amud else talmud_title + u' ' + daf
                            if not Ref(ref).overlaps(get_chapter_range_ref(talmud_title, chapter)):
                                continue
                        elif u'יום טוב' in match.group('perek_name') or u'יו״ט' in match.group('perek_name') or u'יו"ט' in match.group('perek_name'):
                            talmud_title = u'ראש השנה'
                            chapter = 4
                            ref = talmud_title + u' ' + daf + amud if amud else talmud_title + u' ' + daf
                            if not Ref(ref).overlaps(get_chapter_range_ref(talmud_title, chapter)):
                                continue
                        elif u'הקורא' in match.group('perek_name'):
                            chapter = 3
                            ref = talmud_title + u' ' + daf + amud if amud else talmud_title + u' ' + daf
                            if not Ref(ref).overlaps(get_chapter_range_ref(talmud_title, chapter)):
                                continue
                        elif u'כל הזבחים' in match.group('perek_name'):
                            chapter = 2
                            ref = talmud_title + u' ' + daf + amud if amud else talmud_title + u' ' + daf
                            if not Ref(ref).overlaps(get_chapter_range_ref(talmud_title, chapter)):
                                chapter = 8
                                ref = talmud_title + u' ' + daf + amud if amud else talmud_title + u' ' + daf
                                if not Ref(ref).overlaps(get_chapter_range_ref(talmud_title, chapter)):
                                    continue
                        elif u'בית שמאי' in match.group('perek_name') or u'ב"ש' in match.group('perek_name') or u'ב״ש' in match.group('perek_name'):
                            talmud_title = u'יבמות'
                            chapter = 13 
                            ref = talmud_title + u' ' + daf + amud if amud else talmud_title + u' ' + daf
                            if not Ref(ref).overlaps(get_chapter_range_ref(talmud_title, chapter)):
                                talmud_title = u'נזיר'
                                chapter = 5
                                ref = talmud_title + u' ' + daf + amud if amud else talmud_title + u' ' + daf
                                if not Ref(ref).overlaps(get_chapter_range_ref(talmud_title, chapter)):
                                    continue
                        else:
                            print u"{} : {} not in perek".format(tref, s[match.start():match.end()])
                            # print s 
                            continue
                        
                    if match.group("sham"):
                        if u'(' in match.group():
                            seg_text += s[pre_idx:match.start('sham')] + talmud_title + u' ' + s[match.end('sham'):match.end()]
                            test_seg_text += s[pre_idx:match.start('sham')] + talmud_title + u' ' + s[match.end('sham'):match.end()+3]
                            test_pre_idx = match.end() + 6
                            pre_idx = match.end() # subtract length of sham and space and add whats added to end
                            text_changed_perek = True
                    else:
                        for group in ["filler_inside", "daf_prepend", 'daf_number']:
                            if match.group(group):
                                if re.search(ur'[(\[{]', match.group()):
                                    if (s[match.end()] == u']') and (u'[' in match.group()):
                                        seg_text += s[pre_idx:s.index(u'[', match.start())] + u'(' + s[s.index(u'[', match.start())+1:match.start(group)] + talmud_title + u' ' + s[match.start(group):match.end()] + u')'
                                        test_seg_text += s[test_pre_idx:s.index(u'[', match.start())] + u'(' + s[s.index(u'[', match.start())+1:match.start(group)] + talmud_title + u' ' + s[match.start(group):match.end()] + u')'
                                        test_pre_idx = match.end() + 1
                                        pre_idx = match.end() + 1
                                        text_changed_perek = False
                                    elif match.group('daf_prepend') or match.group('amud'):
                                        text_changed_perek = False
                                        front_p_idx = re.search(ur'[(\[{]', match.group()) 
                                        if front_p_idx and (front_p_idx.end() < (match.start(group) - match.start())):
                                            seg_text += s[pre_idx:match.start(group)] + u'(' + talmud_title + u' ' + s[match.start(group):match.end()] + u')'
                                            print u"paren before:" + seg_text[pre_idx:]
                                            pre_idx = match.end()
                                            test_seg_text += s[test_pre_idx:match.start(group)] + u'(' + talmud_title + u' ' + s[match.start(group):match.end()] + u')'
                                            test_pre_idx = match.end()
                                        else:
                                            seg_text += s[pre_idx:match.start(group)] + talmud_title + u' ' + s[match.start(group):match.end()]
                                            pre_idx = match.end()
                                            test_seg_text += s[test_pre_idx:match.start(group)] + talmud_title + u' ' + s[match.start(group):match.end()]
                                            test_pre_idx = match.end()
                                        
                                else:
                                    if match.group('daf_prepend') or match.group('amud'):
                                        seg_text += s[pre_idx:match.start(group)] + u'(' + talmud_title + u' ' + s[match.start(group):match.end()] + u')'
                                        pre_idx = match.end()
                                        test_seg_text += s[test_pre_idx:match.start(group)] + u'(' + talmud_title + u' ' + s[match.start(group):match.end()] + u')'
                                        test_pre_idx = match.end()
                                        text_changed_perek = False
                                break
                                        
                            # if (u'(' not in s[match.start():match.end()]) and (u'[' not in s[match.start():match.end()]):
                    #      print u"{} : {} no front parentheses".format(tref, s[match.start():match.end()])
                        if text_changed_perek:
                            links_added += 1
                            csvfile.write(u'{}\t{}\t{}\n'.format(tref, 
                                                                 s[match.start():match.end()].strip(), 
                                                                 seg_text[match.start()+offset:].strip()))
                            offset += len(talmud_title)+2
                        if text_changed_quotes and (not text_changed_perek):
                            print "only changed quotes for {}".format(tref)
                else:
                    pass
                    # print tref
            except Exception as e:
                print u"{} in {} for {}".format(e, tref, ref)
    seg_text += s[pre_idx:]
    test_seg_text += s[test_pre_idx:]
    if re.search(ur'ֿֿ[\(\[](ריש|סוף)', seg_text):
        print u"SEG TEXT: {}".format(seg_text) 
    # if (text_changed_quotes or text_changed_perek) and post:
    if text_changed_perek:
        try:
            text_version = {
                'versionTitle': heVersionTitle,
                'versionSource': heVersionSource,
                'language': 'he',
                'text': seg_text,
            }
            section = Ref(tref).sections[-1]
            response = urllib2.urlopen('https://www.sefaria.org/api/texts/{}?lang=he'.format(tref))
            resp = json.loads(response.read())
            prod_text = resp['he'][section-1]
            if prod_text == seg_text:
                return True
            elif prod_text != test_seg_text:
                # if "Tosafot" in tref:
                post_text(tref, text_version)
                return True
            #     else:
            #         print "{} doesnt match".format(tref)
            #         return False
            elif post:
                print post_text(tref, text_version)
                return True
        except:
            print u"Issue posting: {}".format(tref)
    return None

with codecs.open('Inserting Perek name results - שם results.tsv', 'rb', 'utf-8') as tsvfile: 
    with codecs.open('new_sham_2' + '.tsv', 'wb+', 'utf-8') as tsvfile_write:
        for line in tsvfile:
            ref = Ref(line.split('\t')[0])
            ref_url = ref.url()
            # opener = urllib2.build_opener()
            # opener.addheaders = [('User-agent', 'Mozilla/5.0')]
            try:
                response = urllib2.urlopen('http://ste.sandbox.sefaria.org/api/texts/{}?lang=he'.format(ref_url))
                values = json.loads(response.read())
                matched = walk_thru_action(values['he'][ref.sections[-1]-1], ref_url, values['heVersionTitle'], values['heVersionSource'])
                if matched:
                    tsvfile_write.write("matched\t{}\n".format(ref_url))
                else:
                    tsvfile_write.write("didn't match\t{}\n".format(ref_url))
            except HTTPError, e:
                print 'Error code: ', e.code, " because ", e.reason


# with codecs.open('newest' + '.tsv', 'wb+', 'utf-8') as csvfile:
#         # s is the segment string
#         # tref is the segment's english ref
#         # heTref is the hebrew ref
#         # version is the segment's version object. use it to get the version title and language```
#     
#     # vs = VersionSet({"title": "Siftei Kohen on Shulchan Arukh, Choshen Mishpat"})
#     vs = VersionSet({"language": "he"})
#     start_posting = True
#     for v in vs:
#             try:
#                 i = v.get_index()
#                 if (u'Chesed LeAvraham' not in i.get_title()) and (u'Rav Pealim' not in i.get_title()):
#                     # if u'Tosafot Yom Tov on Mishnah Oholot' in i.get_title():
#                     #     start_posting = True
#                     if start_posting:
#                         v.walk_thru_contents(walk_thru_action, heTref=i.get_title('he'), schema=i.schema)
#                         # if (u"B'Mareh HaBazak Volume VII" in i.get_title()):
#                         #     start_posting = False
#             except BookNameError:
#                 print u"Skipping {}, {}".format(v.title, v.versionTitle)
#                 continue
#             except Exception as e:
#                 print e, v.title, v.versionTitle
#                 continue
#     print u"Links Added: {}".format(links_added)
    
'''
מקרא ילפינן לה במנחות בפרק שתי הלחם (דף צט.):
כדאמרינן בגיטין (פ"ב דף יז:)
במסכת ע"ז (פ"ק דף יז)
שדרשו ז"ל בכתובות (פ"ז דף ע"ז:) ר'
הוא שאמרו (קידושין פ"ק דף לא) מאכיל 
שאמר ר"ע (סנהדרין פי"א דף קא) 
לא תלבש שעטנז גדילים תעשה לך (מנחות פ"ד לט.):
במסכת ביצה בגמרא דיום טוב (דף כב.):
פסק דהלכה כרבי יהודה (בפרק גיד הנשה ק' ע"ב) דאמר 
בנדרים ריש פרק השותפין
look for not in perek for כל המנחות
בשבת פרק אמר רבי עקיבא (ט ב)
ביבמות פרק האשה (דף קטז.)
 בנדה פרק האשה (דף סב.)
  ובשבת פרק שואל (דף קנ.)
  דאמר בנדה פרק האשה דף סא: 
  כן בנדה פ' האשה (ס"ב ע"א)
  וב"ק ד' צ"ו ע"א, וע"ב
   והא דאמ"ר יוסף (שם [סנהדרין] פ"ק ט ע"ב)
   במנחות רפ"ט (פ"ג:)
   לעיל בפרקין הנטמא ביום מלאת אינו סותר אלא שלשים יום
   ובמסכת זבחים פרק שני (כה, ב)
    בהמפלת (כ"ב א')
    בשבת פ"א (שבת י"א א')
    ובנדה פ' האשה (ס"ג ג') וביבמות פ' כיצד (כ"ג א')
חולין סוף (דף קמ"א)
נדה סוף פרק ראשון
(דף מ') ראש הפרק יוצא דופן

'''

"""
MISHNAH:

  דמסכת שביעית פ"ז (מ"ג)

RESEARCH:
(בסו״פ כל הכלים) דתנור וכירים מחוברים לקרקע עיי״ש
ובפסחים (פרק אלו דברים) תניא הרי הוא אומר עבודת מתנה

כדאמרי' בפ' קמא (דף י:)

skip Kinaat_Sofrim_on_Sefer_HaMitzvot%2C_Shorashim.9.5
בסוטה בשילהי פרק שני

"""
