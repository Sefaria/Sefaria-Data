# coding=utf-8

import re
from sefaria.model import *
from sefaria.helper.text import find_and_replace_in_text
from sefaria.system.exceptions import BookNameError
from collections import defaultdict, OrderedDict

# from sefaria.local_settings import UID

def rambam_alt_names(newtitle = u'נדרים', primetitle =u'נדרים', all_table = False, remove=False):
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
        s = re.split(u''' הלכות | הלכה | הל' | הלכ''' , he)
        if len(s) > 1:
            he = s[1]
            he_names.append(he)
            name_dict[he] = en

    if all_table:
        name_dict[u'מלוה'] = name_dict[u'מלווה ולווה']
        name_dict[u'מלוה ולוה'] = name_dict[u'מלווה ולווה']
        name_dict[u'מלוה ולווה'] = name_dict[u'מלווה ולווה']
        name_dict[u'יסודי תורה'] = name_dict[u'יסודי התורה']
        name_dict[u'תפלה'] = name_dict[u'תפילה וברכת כהנים']
        name_dict[u'יו"ט'] = name_dict[u'שביתת יום טוב']
        name_dict[u'י"ט'] = name_dict[u'שביתת יום טוב']
        name_dict[u'יום טוב'] = name_dict[u'שביתת יום טוב']
        name_dict[u'ת"ת'] = name_dict[u'תלמוד תורה']
        name_dict[u'ע"ז']  = name_dict[u'עבודה זרה וחוקות הגויים']
        name_dict[u'עכו"ם'] = name_dict[u'עבודה זרה וחוקות הגויים']
        name_dict[u'ע"ג'] = name_dict[u'עבודה זרה וחוקות הגויים']
        name_dict[u'עו"ג'] = name_dict[u'עבודה זרה וחוקות הגויים']
        # name_dict[u'עבודה זרה'] = name_dict[u'עבודה זרה וחוקות הגויים']
        name_dict[u'עבודת כוכבים'] = name_dict[u'עבודה זרה וחוקות הגויים']
        name_dict[u'עבודת עכו"ם'] = name_dict[u'עבודה זרה וחוקות הגויים']
        name_dict[u'אבות הטומאה'] = name_dict[u'שאר אבות הטומאות']
        name_dict[u'שאר אבות הטומאה'] = name_dict[u'שאר אבות הטומאות']
        name_dict[u'שאר אבות הטומאות'] = name_dict[u'שאר אבות הטומאות']
        name_dict[u'אבות הטומאות'] = name_dict[u'שאר אבות הטומאות']
        name_dict[u'שאר א"ה'] = name_dict[u'שאר אבות הטומאות']
        name_dict[u'טומאת משכב ומושב'] = name_dict[u'מטמאי משכב ומושב']
        name_dict[u'מטמא משכב ומושב'] = name_dict[u'מטמאי משכב ומושב']
        name_dict[u'משכב ומושב'] = name_dict[u'מטמאי משכב ומושב']
        name_dict[u'צרעת'] = name_dict[u'טומאת צרעת']
        # name_dict[u"שכני'"] = name_dict[u'שכנים']
        # name_dict[u"שכני"] = name_dict[u'שכנים']
        name_dict[u'ס"ת'] = name_dict[u'תפילין ומזוזה וספר תורה']
        # name_dict[u'ציצית'] = name_dict[u'תפילין ומזוזה וספר תורה']
        name_dict[u'ס"ת ומזוזה'] = name_dict[u'תפילין ומזוזה וספר תורה']
        name_dict[u'ספר תורה'] = name_dict[u'תפילין ומזוזה וספר תורה']
        name_dict[u'מזוזה'] = name_dict[u'תפילין ומזוזה וספר תורה']
        name_dict[u'תפלין'] = name_dict[u'תפילין ומזוזה וספר תורה']
        name_dict[u'אבידה'] = name_dict[u'גזילה ואבידה']
        name_dict[u'גנבה'] = name_dict[u'גניבה']
        # name_dict[u'שמיטין'] = name_dict[u'שמיטה ויובל']
        name_dict[u'שמיטין ויובל'] = name_dict[u'שמיטה ויובל']
        name_dict[u'שמיטין ויובלות'] = name_dict[u'שמיטה ויובל']
        name_dict[u'שמטה ויובל'] = name_dict[u'שמיטה ויובל']
        name_dict[u'יובל'] = name_dict[u'שמיטה ויובל']
        name_dict[u'שמיטה'] = name_dict[u'שמיטה ויובל']
        name_dict[u'ביכורין'] = name_dict[u'ביכורים ושאר מתנות כהונה שבגבולין']
        name_dict[u'בכורים'] = name_dict[u'ביכורים ושאר מתנות כהונה שבגבולין']
        name_dict[u'זכיה ומתנה'] = name_dict[u'זכייה ומתנה']
        # name_dict[u"מכיר'"] = name_dict[u'מכירה']
        name_dict[u'שאר אבות הטומאה'] = name_dict[u'שאר אבות הטומאות']
        name_dict[u'מעשה קרבנות'] = name_dict[u'מעשה הקרבנות']
        name_dict[u'מעשה קרבן'] = name_dict[u'מעשה הקרבנות']
        name_dict[u'מעה"ק'] = name_dict[u'מעשה הקרבנות'] # notice when there isn't the word "הלכה" the 'ה"' seems like an indication to halachah "ק"
        name_dict[u'תענית'] = name_dict[u'תעניות']
        name_dict[u'מקוואות'] = name_dict[u'מקואות']
        name_dict[u'ערכין וחרמין'] = name_dict[u'ערכים וחרמין']
        name_dict[u'ערכין'] = name_dict[u'ערכים וחרמין']
        name_dict[u'שאלה ופקדון'] = name_dict[u'שאלה ופיקדון']
        name_dict[u"שאל' ופקדון"] = name_dict[u'שאלה ופיקדון']
        name_dict[u'פקדון'] = name_dict[u'שאלה ופיקדון']
        # name_dict[u'מעשר שני'] = name_dict[u'מעשר שני ונטע רבעי']
        name_dict[u'מעשר'] = name_dict[u'מעשרות']
        name_dict[u'מ"ש ונטע רבעי'] = name_dict[u'מעשר שני ונטע רבעי']
        name_dict[u'מעשר ונטע רבעי'] = name_dict[u'מעשר שני ונטע רבעי']
        name_dict[u'מעשר שני ונ"ר'] = name_dict[u'מעשר שני ונטע רבעי']
        # name_dict[u'מע"ש'] = name_dict[u'מעשר שני ונטע רבעי'] # is this right? קכא ג מיי׳ פ״ה מהל׳ אישות הל׳ ה ופ״ג מהל׳ מע״ש הל׳ יז (ב"ק 112)
        name_dict[u'מ"ש ונ"ר'] = name_dict[u'מעשר שני ונטע רבעי']
        name_dict[u'מ"ש'] = name_dict[u'מעשר שני ונטע רבעי']
        name_dict[u'נטע רבעי'] = name_dict[u'מעשר שני ונטע רבעי']
        name_dict[u'מתנות ענים'] = name_dict[u'מתנות עניים']
        name_dict[u'מ"ע'] = name_dict[u'מתנות עניים']
        name_dict[u'טומאת אוכלין'] = name_dict[u'טומאת אוכלים']
        name_dict[u'טומאות אוכלין'] = name_dict[u'טומאת אוכלים']
        name_dict[u'טומאות מת'] = name_dict[u'טומאת מת']
        name_dict[u'טומאת המת'] = name_dict[u'טומאת מת']
        name_dict[u'גזילה ואבדה'] = name_dict[u'גזילה ואבידה']
        name_dict[u'גזלה ואבדה'] = name_dict[u'גזילה ואבידה']
        name_dict[u'גזלה ואבידה'] = name_dict[u'גזילה ואבידה']
        name_dict[u'גזלה'] = name_dict[u'גזילה ואבידה']
        name_dict[u'אבדה'] = name_dict[u'גזילה ואבידה']
        name_dict[u'גזילה'] = name_dict[u'גזילה ואבידה']
        name_dict[u'תמידין'] = name_dict[u'תמידים ומוספין']
        name_dict[u'תמידין ומוספין'] = name_dict[u'תמידים ומוספין']
        name_dict[u'איסורי מזבח'] = name_dict[u'איסורי המזבח']
        name_dict[u'אסורי מזבח'] = name_dict[u'איסורי המזבח']
        name_dict[u'א"מ'] = name_dict[u'איסורי המזבח']
        name_dict[u'איס"ב'] = name_dict[u'איסורי ביאה']
        name_dict[u'א"ב'] = name_dict[u'איסורי ביאה']
        name_dict[u'אסורי ביאה'] = name_dict[u'איסורי ביאה']
        name_dict[u'קידוש החדש'] = name_dict[u'קידוש החודש']
        name_dict[u'קדוש החדש'] = name_dict[u'קידוש החודש']
        name_dict[u'לולב'] = name_dict[u'שופר וסוכה ולולב']
        name_dict[u'סוכה'] = name_dict[u'שופר וסוכה ולולב']
        name_dict[u'סוכה ולולב'] = name_dict[u'שופר וסוכה ולולב']
        name_dict[u'אבילות'] = name_dict[u'אבל']
        name_dict[u'אבלות'] = name_dict[u'אבל']
        name_dict[u'דיעות'] = name_dict[u'דעות']
        name_dict[u'שלוחים ושותפין'] = name_dict[u'שלוחין ושותפין']
        name_dict[u'שותפין'] = name_dict[u'שלוחין ושותפין']
        name_dict[u'כלי מקדש'] = name_dict[u'כלי המקדש והעובדין בו']
        # name_dict[u'כלי המקדש'] = name_dict[u'כלי המקדש והעובדין בו']
        name_dict[u'ביאת המקדש'] = name_dict[u'ביאת מקדש']
        name_dict[u'מ"א'] = name_dict[u'מאכלות אסורות']
        name_dict[u'מאכלות'] = name_dict[u'מאכלות אסורות']
        name_dict[u'מא"ס'] = name_dict[u'מאכלות אסורות']
        name_dict[u'אסורות'] = name_dict[u'מאכלות אסורות']
        # name_dict[u"ממרי'"] = name_dict[u'ממרים']
        # name_dict[u"שכירו'"] = name_dict[u'שכירות']
        name_dict[u"תרומה"] = name_dict[u'תרומות']
        # name_dict[u"סנהד'"] = name_dict[u'סנהדרין והעונשין המסורין להם']
        name_dict[u"סנהדרין"] = name_dict[u'סנהדרין והעונשין המסורין להם']
        name_dict[u'ק"ש'] = name_dict[u'קריאת שמע']
        name_dict[u'יום הכפורים'] = name_dict[u'עבודת יום הכפורים'] # because it makes problems with my code...can be fixed by taking it step by step
        name_dict[u'נ"כ'] = name_dict[u'תפילה וברכת כהנים']
        name_dict[u'נשיאות כפים'] = name_dict[u'תפילה וברכת כהנים']
        name_dict[u'נשיאת כפים'] = name_dict[u'תפילה וברכת כהנים']
        name_dict[u'תפלה וברכת כהנים'] = name_dict[u'תפילה וברכת כהנים']
        name_dict[u'חנוכה'] = name_dict[u'מגילה וחנוכה']
        name_dict[u'מצה'] = name_dict[u'חמץ ומצה']
        name_dict[u'חמץ'] = name_dict[u'חמץ ומצה']
        name_dict[u'חו"מ'] = name_dict[u'חמץ ומצה'] # note: this is also the r"t of חושן משפט not sopused to be a problem
        name_dict[u'גרושין'] = name_dict[u'גירושין']
        name_dict[u'נ"מ'] = name_dict[u'נזקי ממון']
        name_dict[u'פסולי מוקדשין'] = name_dict[u'פסולי המוקדשין']
        name_dict[u'פסולי המוקדשים'] = name_dict[u'פסולי המוקדשין']
        name_dict[u'ק"פ'] = name_dict[u'קרבן פסח']
        name_dict[u'רוצח וש"נ'] = name_dict[u'רוצח ושמירת נפש']
        name_dict[u'רוצח'] = name_dict[u'רוצח ושמירת נפש']
        name_dict[u'שמירת הנפש'] = name_dict[u'רוצח ושמירת נפש']
        name_dict[u'יבום'] = name_dict[u'יבום וחליצה']
        name_dict[u'חליצה'] = name_dict[u'יבום וחליצה']
        name_dict[u'מלכים'] = name_dict[u'מלכים ומלחמות']
        name_dict[u'ערובין'] = name_dict[u'עירובין']
        for name in name_dict.keys():
            first = re.split('\s', name)
            if len(first) > 1:
                name_dict[first[0]] = name_dict[name]
        del name_dict[u'איסורי']
        del name_dict[u'טומאת']
    name_dict[newtitle] = name_dict[primetitle]
    idxset = IndexSet({'title': {'$regex': '^Mishneh Torah,'}})
    rambam_alt = defaultdict(lambda: [])


    rambam_reisha = [u'רמב"ם', u'משנה תורה',u'רמב"ם,', u'משנה תורה,']
    rambam_metziata = [u'הלכות', u"הלכו'", u"הל'"]
    reishaot = []
    for r in rambam_reisha:
        for m in rambam_metziata:
            reishaot.append(u'''{} {}'''.format(r, m))

    for reisha in reishaot:
        for alt, en_title in name_dict.items():
            if alt not in he_names:
                rambam_alt[en_title].append(u'''{} {}'''.format(reisha, alt))
            elif all_table:
                rambam_alt[en_title].append(u'''{} {}'''.format(reisha, alt))
    cnt = 0
    for idx in idxset:
        cnt_idx = 0
        for newtitle in rambam_alt[idx.get_title('en')]:
            print idx, newtitle
            if remove:
                idx.nodes.remove_title(newtitle, "he")
            else:
                idx.nodes.add_title(newtitle, "he")
            idx.save(override_dependencies=True)
            cnt_idx += 1
            cnt += 1
        print cnt_idx
    print cnt
    return rambam_alt


def alt_name_dict():

    alt_names = dict({
        u"ויקרא": [u"ויק׳", u"ויק'"],
        u"במדבר": [u"במ'", u"במ׳"],
        u"דברים": [u"דב׳", u"דב'"],
        u"יהושע": [u"יהוש'", u"יהוש׳"],
        u"שופטים": [u"שופטי׳", u"שופטי'"],
        u"ישעיהו": [u"ישע'"],
        u"ירמיהו": [u"ירמ׳", u"ירמ'"],
        u"יחזקאל": [u"יחז׳", u"יחז'"],
        u"מיכה": [u"מיכ׳", u"מיכ'"],
        u"צפניה": [u"צפנ׳", u"צפנ'"],
        u"זכריה": [u"זכרי"],
        u"מלאכי": [u"מלא'"],
        u"תהילים": [u"תה׳", u"תה'"],
        u"נחמיה": [u"נחמי'"],
        u"דניאל": [u"דני׳", u"דני'"],
        u"אסתר": [u"אס׳", u"אס'"],
        u"איכה": [u"איכ׳", u"איכ'"]
    })
    alt_names[u'דברי הימים א'] = [u'''דהי"א''']
    alt_names[u'דברי הימים ב'] = [u'''דהי"ב''']
    alt_names[u"בראשית רבה"] = [u'ב"ר']
    alt_names[u"דברים רבה"] = [u'דב"ר']
    alt_names[u'''שמואל א'''] = [u'''ש''א''']
    alt_names[u'''שמואל ב'''] = [u'''ש''ב''']
    alt_names[u'''מלכים א'''] = [u'''מ''א''']
    alt_names[u'''מלכים ב'''] = [u'''מ''ב''']
    alt_names[u'''שמות רבה'''] = [u'''שמו"ר''']
    alt_names[u'''שיר השירים'''] = [u'''שה''ש''']
    alt_names[u'''בבא קמא'''] = [u'''ב''ק''']
    return alt_names



def validate_alt_titles(dict):
    problem = False
    alt_titles = {}
    for anotherdict in dict:
        alt_titles.update(anotherdict)
    for k, v in alt_titles.items():
        for t in v:
            try:
                i = library.get_index(t)
                problem = True
                print u"{} -> {}".format(k, t)
            except BookNameError:
                pass
    return problem


def save_alt_titles(alt_tit_dict):

    problem = validate_alt_titles([alt_tit_dict])

    if problem:
        # raise Alt_Title_Exception
        print u'validation failed'
        return
    for origtitle, newtitles in alt_tit_dict.items():
        idx = library.get_index(origtitle)
        for nt in newtitles:
            idx.nodes.add_title(nt, "he")
            idx.save(override_dependencies=True)

def change_gershayim():
    # title, vtitle, lang - can come from the vtitle.
    # replace_dict = OrderedDict({u"\u05f3": u"'", u"(?:''|\u05f4|\u201d)": u'"'})
    replace_dict = OrderedDict({u"\u05f3": u"'", u"''": u'"', u"\u05f4": u'"', u"\u201d": u'"'})
    uid = 30044
    versions = VersionSet({"language":"he"})
    versions = VersionSet({'$and': [{"title":"Rashi on Genesis"}, {"language":"he"}]})
    titles = IndexSet({"categories":"Tanakh"})
    missing_inds = []
    for ver in versions:
        title = ver.title
        vtitle = ver.versionTitle
        try:
            library.get_index(title)
        except BookNameError:
            missing_inds.append(title)
            continue
        for old, new in replace_dict.items():
            find_and_replace_in_text(title, vtitle, u'he', old, new, uid)
    print missing_inds
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
    nodes[0].add_title(u'א"ח', 'he')
    nodes[0].add_title(u'טא"ח', 'he')
    nodes[0].add_title(u'או"ח', 'he')
    nodes[1].add_title(u'י"ד', 'he')
    nodes[1].add_title(u'יו"ד', 'he')
    nodes[2].add_title(u'ח"מ', 'he')
    nodes[2].add_title(u'חו"מ', 'he')
    nodes[3].add_title(u'א"ה', 'he')
    nodes[3].add_title(u'א"ע', 'he')
    nodes[3].add_title(u'אה"ע', 'he')
    tur_ind.save()

def change_gershayim_in_titles():
    pass


if __name__ == "__main__":
    rambam_alt = rambam_alt_names(u'ערובין', u'עירובין')
    # tur_alt_titles()
    # more_titles = alt_name_dict()
    # save_alt_titles(more_titles)
    # change_gershayim()
    print 'done'