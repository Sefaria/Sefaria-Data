# coding=utf-8

import re
from sefaria.model import *
from sefaria.helper.text import find_and_replace_in_text
from sefaria.system.exceptions import BookNameError
from collections import defaultdict, OrderedDict

# from sefaria.local_settings import UID

def rambam_alt_names(newtitle = 'נדרים', primetitle ='נדרים', all_table = False, remove=False):
    '''
    ATTENTION: this function can change index titles in mongo!!
    :param newtitle: he title of the book (without רמב"ם הלכות) that is to be added with the 12 start options
    :param primetitle: he prime title
    :param all_table: do we want to update all the titles possible and not only one new one, no harm in having this true since alt titles don't duplicate
    :param remove: if we actually want to remove a title (with all the 12 options) NOTE: this is the trace back option
    :return: returns a dictionary of all 88 yad books, each has a list with the titles added
    '''
    names = library.get_indexes_in_category("Mishneh Torah")
    en_names = names
    he_raw = [library.get_index(name).get_title('he') for name in names]
    he_names = []
    name_dict = {}
    for he, en in zip(he_raw, en_names):
        s = re.split(''' הלכות | הלכה | הל' | הלכ''' , he)
        if len(s) > 1:
            he = s[1]
            he_names.append(he)
            name_dict[he] = en

    if all_table:
        name_dict['מלוה'] = name_dict['מלווה ולווה']
        name_dict['מלוה ולוה'] = name_dict['מלווה ולווה']
        name_dict['מלוה ולווה'] = name_dict['מלווה ולווה']
        name_dict['יסודי תורה'] = name_dict['יסודי התורה']
        name_dict['תפלה'] = name_dict['תפילה וברכת כהנים']
        name_dict['יו"ט'] = name_dict['שביתת יום טוב']
        name_dict['שביתת יו"ט'] = name_dict['שביתת יום טוב']
        name_dict['י"ט'] = name_dict['שביתת יום טוב']
        name_dict['שביתת י"ט'] = name_dict['שביתת יום טוב']
        name_dict['יום טוב'] = name_dict['שביתת יום טוב']
        name_dict['ת"ת'] = name_dict['תלמוד תורה']
        name_dict['ע"ז']  = name_dict['עבודה זרה וחוקות הגויים']
        name_dict['עכו"ם'] = name_dict['עבודה זרה וחוקות הגויים']
        name_dict['ע"ג'] = name_dict['עבודה זרה וחוקות הגויים']
        name_dict['עו"ג'] = name_dict['עבודה זרה וחוקות הגויים']
        # name_dict[u'עבודה זרה'] = name_dict[u'עבודה זרה וחוקות הגויים']
        name_dict['עבודת כוכבים'] = name_dict['עבודה זרה וחוקות הגויים']
        name_dict['עבודת עכו"ם'] = name_dict['עבודה זרה וחוקות הגויים']
        name_dict['אבות הטומאה'] = name_dict['שאר אבות הטומאות']
        name_dict['שאר אבות הטומאה'] = name_dict['שאר אבות הטומאות']
        name_dict['שאר אבות הטומאות'] = name_dict['שאר אבות הטומאות']
        name_dict['אבות הטומאות'] = name_dict['שאר אבות הטומאות']
        name_dict['שאר א"ה'] = name_dict['שאר אבות הטומאות']
        name_dict['טומאת משכב ומושב'] = name_dict['מטמאי משכב ומושב']
        name_dict['מטמא משכב ומושב'] = name_dict['מטמאי משכב ומושב']
        name_dict['משכב ומושב'] = name_dict['מטמאי משכב ומושב']
        name_dict['צרעת'] = name_dict['טומאת צרעת']
        # name_dict[u"שכני'"] = name_dict[u'שכנים']
        # name_dict[u"שכני"] = name_dict[u'שכנים']
        name_dict['ס"ת'] = name_dict['תפילין ומזוזה וספר תורה']
        # name_dict[u'ציצית'] = name_dict[u'תפילין ומזוזה וספר תורה']
        name_dict['ס"ת ומזוזה'] = name_dict['תפילין ומזוזה וספר תורה']
        name_dict['ספר תורה'] = name_dict['תפילין ומזוזה וספר תורה']
        name_dict['מזוזה'] = name_dict['תפילין ומזוזה וספר תורה']
        name_dict['תפלין'] = name_dict['תפילין ומזוזה וספר תורה']
        name_dict['תפילין ומזוזות וספר תורה'] = name_dict['תפילין ומזוזה וספר תורה']
        name_dict['אבידה'] = name_dict['גזילה ואבידה']
        name_dict['גנבה'] = name_dict['גניבה']
        # name_dict[u'שמיטין'] = name_dict[u'שמיטה ויובל']
        name_dict['שמיטין ויובל'] = name_dict['שמיטה ויובל']
        name_dict['שמיטין ויובלות'] = name_dict['שמיטה ויובל']
        name_dict['שמטה ויובל'] = name_dict['שמיטה ויובל']
        name_dict['יובל'] = name_dict['שמיטה ויובל']
        name_dict['שמיטה'] = name_dict['שמיטה ויובל']
        name_dict['ביכורין'] = name_dict['ביכורים ושאר מתנות כהונה שבגבולין']
        name_dict['בכורים'] = name_dict['ביכורים ושאר מתנות כהונה שבגבולין']
        name_dict['זכיה ומתנה'] = name_dict['זכייה ומתנה']
        # name_dict[u"מכיר'"] = name_dict[u'מכירה']
        name_dict['שאר אבות הטומאה'] = name_dict['שאר אבות הטומאות']
        name_dict['מעשה קרבנות'] = name_dict['מעשה הקרבנות']
        name_dict['מעשה קרבן'] = name_dict['מעשה הקרבנות']
        name_dict['מעה"ק'] = name_dict['מעשה הקרבנות'] # notice when there isn't the word "הלכה" the 'ה"' seems like an indication to halachah "ק"
        name_dict['תענית'] = name_dict['תעניות']
        name_dict['מקוואות'] = name_dict['מקואות']
        name_dict['ערכין וחרמין'] = name_dict['ערכים וחרמין']
        name_dict['ערכין'] = name_dict['ערכים וחרמין']
        name_dict['שאלה ופקדון'] = name_dict['שאלה ופיקדון']
        name_dict["שאל' ופקדון"] = name_dict['שאלה ופיקדון']
        name_dict['פקדון'] = name_dict['שאלה ופיקדון']
        # name_dict[u'מעשר שני'] = name_dict[u'מעשר שני ונטע רבעי']
        name_dict['מעשר'] = name_dict['מעשרות']
        name_dict['מ"ש ונטע רבעי'] = name_dict['מעשר שני ונטע רבעי']
        name_dict['מעשר ונטע רבעי'] = name_dict['מעשר שני ונטע רבעי']
        name_dict['מעשר שני ונ"ר'] = name_dict['מעשר שני ונטע רבעי']
        # name_dict[u'מע"ש'] = name_dict[u'מעשר שני ונטע רבעי'] # is this right? קכא ג מיי׳ פ״ה מהל׳ אישות הל׳ ה ופ״ג מהל׳ מע״ש הל׳ יז (ב"ק 112)
        name_dict['מ"ש ונ"ר'] = name_dict['מעשר שני ונטע רבעי']
        name_dict['מ"ש'] = name_dict['מעשר שני ונטע רבעי']
        name_dict['נטע רבעי'] = name_dict['מעשר שני ונטע רבעי']
        name_dict['מתנות ענים'] = name_dict['מתנות עניים']
        name_dict['מ"ע'] = name_dict['מתנות עניים']
        name_dict['טומאת אוכלין'] = name_dict['טומאת אוכלים']
        name_dict['טומאות אוכלין'] = name_dict['טומאת אוכלים']
        name_dict['טומאות מת'] = name_dict['טומאת מת']
        name_dict['טומאת המת'] = name_dict['טומאת מת']
        name_dict['גזילה ואבדה'] = name_dict['גזילה ואבידה']
        name_dict['גזלה ואבדה'] = name_dict['גזילה ואבידה']
        name_dict['גזלה ואבידה'] = name_dict['גזילה ואבידה']
        name_dict['גזלה'] = name_dict['גזילה ואבידה']
        name_dict['אבדה'] = name_dict['גזילה ואבידה']
        name_dict['גזילה'] = name_dict['גזילה ואבידה']
        name_dict['תמידין'] = name_dict['תמידים ומוספין']
        name_dict['תמידין ומוספין'] = name_dict['תמידים ומוספין']
        name_dict['איסורי מזבח'] = name_dict['איסורי המזבח']
        name_dict['אסורי מזבח'] = name_dict['איסורי המזבח']
        name_dict['א"מ'] = name_dict['איסורי המזבח']
        name_dict['איס"ב'] = name_dict['איסורי ביאה']
        name_dict['א"ב'] = name_dict['איסורי ביאה']
        name_dict['אסורי ביאה'] = name_dict['איסורי ביאה']
        name_dict['קידוש החדש'] = name_dict['קידוש החודש']
        name_dict['קדוש החדש'] = name_dict['קידוש החודש']
        name_dict['לולב'] = name_dict['שופר וסוכה ולולב']
        name_dict['סוכה'] = name_dict['שופר וסוכה ולולב']
        name_dict['סוכה ולולב'] = name_dict['שופר וסוכה ולולב']
        name_dict['אבילות'] = name_dict['אבל']
        name_dict['אבלות'] = name_dict['אבל']
        name_dict['דיעות'] = name_dict['דעות']
        name_dict['שלוחים ושותפין'] = name_dict['שלוחין ושותפין']
        name_dict['שותפין'] = name_dict['שלוחין ושותפין']
        name_dict['כלי מקדש'] = name_dict['כלי המקדש והעובדין בו']
        name_dict['כלי המקדש'] = name_dict['כלי המקדש והעובדין בו']
        name_dict['ביאת המקדש'] = name_dict['ביאת מקדש']
        name_dict['מ"א'] = name_dict['מאכלות אסורות']
        name_dict['מאכלות'] = name_dict['מאכלות אסורות']
        name_dict['מא"ס'] = name_dict['מאכלות אסורות']
        name_dict['אסורות'] = name_dict['מאכלות אסורות']
        # name_dict[u"ממרי'"] = name_dict[u'ממרים']
        # name_dict[u"שכירו'"] = name_dict[u'שכירות']
        name_dict["תרומה"] = name_dict['תרומות']
        # name_dict[u"סנהד'"] = name_dict[u'סנהדרין והעונשין המסורין להם']
        name_dict["סנהדרין"] = name_dict['סנהדרין והעונשין המסורין להם']
        name_dict['ק"ש'] = name_dict['קריאת שמע']
        name_dict['יום הכפורים'] = name_dict['עבודת יום הכפורים'] # because it makes problems with my code...can be fixed by taking it step by step
        name_dict['נ"כ'] = name_dict['תפילה וברכת כהנים']
        name_dict['נשיאות כפים'] = name_dict['תפילה וברכת כהנים']
        name_dict['נשיאת כפים'] = name_dict['תפילה וברכת כהנים']
        name_dict['תפלה וברכת כהנים'] = name_dict['תפילה וברכת כהנים']
        name_dict['חנוכה'] = name_dict['מגילה וחנוכה']
        name_dict['מצה'] = name_dict['חמץ ומצה']
        name_dict['חמץ'] = name_dict['חמץ ומצה']
        name_dict['חו"מ'] = name_dict['חמץ ומצה'] # note: this is also the r"t of חושן משפט not sopused to be a problem
        name_dict['גרושין'] = name_dict['גירושין']
        name_dict['נ"מ'] = name_dict['נזקי ממון']
        name_dict['פסולי מוקדשין'] = name_dict['פסולי המוקדשין']
        name_dict['פסולי המוקדשים'] = name_dict['פסולי המוקדשין']
        name_dict['ק"פ'] = name_dict['קרבן פסח']
        name_dict['רוצח וש"נ'] = name_dict['רוצח ושמירת נפש']
        name_dict['רוצח'] = name_dict['רוצח ושמירת נפש']
        name_dict['שמירת הנפש'] = name_dict['רוצח ושמירת נפש']
        name_dict['יבום'] = name_dict['יבום וחליצה']
        name_dict['חליצה'] = name_dict['יבום וחליצה']
        name_dict['מלכים'] = name_dict['מלכים ומלחמות']
        name_dict['ערובין'] = name_dict['עירובין']
        for name in list(name_dict.keys()):
            first = re.split('\s', name)
            if len(first) > 1:
                name_dict[first[0]] = name_dict[name]
        del name_dict['איסורי']
        del name_dict['טומאת']
        del name_dict['כלי']
        del name_dict['שביתת']
    name_dict[newtitle] = name_dict[primetitle]
    idxset = IndexSet({'title': {'$regex': '^Mishneh Torah,'}})
    rambam_alt = defaultdict(lambda: [])


    rambam_reisha = ['רמב"ם', 'משנה תורה','רמב"ם,', 'משנה תורה,']
    rambam_metziata = ['הלכות', "הלכו'", "הל'"]
    reishaot = []
    for r in rambam_reisha:
        for m in rambam_metziata:
            reishaot.append('''{} {}'''.format(r, m))

    for reisha in reishaot:
        for alt, en_title in list(name_dict.items()):
            if alt not in he_names:
                rambam_alt[en_title].append('''{} {}'''.format(reisha, alt))
            elif all_table:
                rambam_alt[en_title].append('''{} {}'''.format(reisha, alt))
    cnt = 0
    for idx in idxset:
        cnt_idx = 0
        for newtitle in rambam_alt[idx.get_title('en')]:
            print(idx, newtitle)
            if remove:
                idx.nodes.remove_title(newtitle, "he")
            else:
                idx.nodes.add_title(newtitle, "he")
            idx.save(override_dependencies=True)
            cnt_idx += 1
            cnt += 1
        print(cnt_idx)
    print(cnt)
    return rambam_alt


def alt_name_dict():

    alt_names = dict({
        "ויקרא": ["ויק׳", "ויק'"],
        "במדבר": ["במ'", "במ׳"],
        "דברים": ["דב׳", "דב'"],
        "יהושע": ["יהוש'", "יהוש׳"],
        "שופטים": ["שופטי׳", "שופטי'"],
        "ישעיהו": ["ישע'"],
        "ירמיהו": ["ירמ׳", "ירמ'"],
        "יחזקאל": ["יחז׳", "יחז'"],
        "מיכה": ["מיכ׳", "מיכ'"],
        "צפניה": ["צפנ׳", "צפנ'"],
        "זכריה": ["זכרי"],
        "מלאכי": ["מלא'"],
        "תהילים": ["תה׳", "תה'"],
        "נחמיה": ["נחמי'"],
        "דניאל": ["דני׳", "דני'"],
        "אסתר": ["אס׳", "אס'"],
        "איכה": ["איכ׳", "איכ'"]
    })
    alt_names['דברי הימים א'] = ['''דהי"א''']
    alt_names['דברי הימים ב'] = ['''דהי"ב''']
    alt_names["בראשית רבה"] = ['ב"ר']
    alt_names["דברים רבה"] = ['דב"ר']
    alt_names['''שמואל א'''] = ['''ש''א''']
    alt_names['''שמואל ב'''] = ['''ש''ב''']
    alt_names['''מלכים א'''] = ['''מ''א''']
    alt_names['''מלכים ב'''] = ['''מ''ב''']
    alt_names['''שמות רבה'''] = ['''שמו"ר''']
    alt_names['''שיר השירים'''] = ['''שה''ש''']
    alt_names['''בבא קמא'''] = ['''ב''ק''']
    return alt_names



def validate_alt_titles(dict):
    problem = False
    alt_titles = {}
    for anotherdict in dict:
        alt_titles.update(anotherdict)
    for k, v in list(alt_titles.items()):
        for t in v:
            try:
                i = library.get_index(t)
                problem = True
                print("{} -> {}".format(k, t))
            except BookNameError:
                pass
    return problem


def save_alt_titles(alt_tit_dict):

    problem = validate_alt_titles([alt_tit_dict])

    if problem:
        # raise Alt_Title_Exception
        print('validation failed')
        return
    for origtitle, newtitles in list(alt_tit_dict.items()):
        idx = library.get_index(origtitle)
        for nt in newtitles:
            idx.nodes.add_title(nt, "he")
            idx.save(override_dependencies=True)

def change_gershayim():
    ''''
    an outline of how to change this:
    # indxs = library.all_index_records()
    # library.get_index('bereshit')
    # Index().load({'title': 'Genesis'})
    # indx = library.get_index('bereshit')
    # indx.all_segment_refs()[0]
    # Ref('Genesis 1:1')
    # indx.all_segment_refs()[0].text('he')
    # TextChunk(Genesis
    # 1:1, he)
    # r = indx.all_segment_refs()[0]
    # r.versionset('he')
    # TextChunk(r, 'he', r.versionset('he')[0].versionTitle).text
    # u'\\u05d1\\u05bc\\u05b0\\u05e8\\u05b5\\u05d0\\u05e9\\u05c1\\u05b4\\u0596\\u05d9\\u05ea \\u05d1\\u05bc\\u05b8\\u05e8\\u05b8\\u05a3\\u05d0 \\u05d0\\u05b1\\u05dc\\u05b9\\u05d4\\u05b4\\u0591\\u05d9\\u05dd \\u05d0\\u05b5\\u05a5\\u05ea \\u05d4\\u05b7\\u05e9\\u05c1\\u05bc\\u05b8\\u05de\\u05b7\\u0596\\u05d9\\u05b4\\u05dd \\u05d5\\u05b0\\u05d0\\u05b5\\u05a5\\u05ea \\u05d4\\u05b8\\u05d0\\u05b8\\u05bd\\u05e8\\u05b6\\u05e5\\u05c3'
    '''
    # title, vtitle, lang - can come from the vtitle.
    # replace_dict = OrderedDict({u"\u05f3": u"'", u"(?:''|\u05f4|\u201d)": u'"'})
    replace_dict = OrderedDict({"\u05f3": "'", "''": '"', "\u05f4": '"', "\u201d": '"'})
    uid = 30044
    versions = VersionSet({"language": "he"})
    versions = VersionSet({'$and': [{"title": "Rashi on Genesis"}, {"language":"he"}]})
    titles = IndexSet({"categories": "Tanakh"})
    missing_inds = []
    for ver in versions:
        title = ver.title
        vtitle = ver.versionTitle
        try:
            library.get_index(title)
        except BookNameError:
            missing_inds.append(title)
            continue
        for old, new in list(replace_dict.items()):
            find_and_replace_in_text(title, vtitle, 'he', old, new, uid)
    print(missing_inds)
    # inds = library.get_indexes_in_category(catagory, include_dependant=True, full_records=True)
    # for ind in inds:
    #     vSet = ind.versionSet().array()
    #     vSet = VersionSet({"title": ind.title, la}, )
    #     for v in vSet:
    #         vtitle = v.versionTitle
    #         for frm, to in replace_dict.items():
    #             find_and_replace_in_text(title, vtitle, u'he', frm, to, 30044)
def tur_alt_titles():
    tur_ind = library.get_index("Tur")
    nodes = tur_ind.nodes.children
    nodes[0].add_title('א"ח', 'he')
    nodes[0].add_title('או"ח', 'he')
    nodes[1].add_title('י"ד', 'he')
    nodes[1].add_title('יו"ד', 'he')
    nodes[2].add_title('א"ה', 'he')
    nodes[2].add_title('א"ע', 'he')
    nodes[2].add_title('אה"ע', 'he')
    nodes[3].add_title('ח"מ', 'he')
    nodes[3].add_title('חו"מ', 'he')
    tur_ind.save()

def change_gershayim_in_titles():
    pass


if __name__ == "__main__":
    rambam_alt = rambam_alt_names('תפילין ומזוזות וספר תורה', 'תפילין ומזוזה וספר תורה')
    # tur_alt_titles()
    # more_titles = alt_name_dict()
    # save_alt_titles(more_titles)
    # change_gershayim()
    print('done')