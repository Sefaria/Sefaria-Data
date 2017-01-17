# -*- coding: utf-8 -*-

from sefaria.model import *
import codecs
import re
import pygtrie
from data_utilities.util import getGematria
from data_utilities.ibid import BookIbidTracker

class EM_Citation(object):
    """
    One instance per commentary
    """
    def __init__(self):
        self._massekhet = None
        self._file_line = 0
        self._perek_counter = 0
        self._perek  = 0 # assuming all prakim in the massekhet have at least one citation of EM
        self._page_counter = 0
        self._page = 0 # a counter of pages from the begining of this perek that had ein mishpat on them
        self._mimon = None
        self._semag = None
        self._tush = None



def parse_em(filename):
    i = 0
    perek = 0
    page = 0
    mishneh = Rambam() # we parse per file and create a mishne torah (Rambam) obj per file
    smg = Semag()
    cit_dictionary = {}
    with codecs.open(filename, 'r', 'utf-8') as fp:
        lines = fp.readlines()
    pattern = ur'''(ש"ע|מיי'|ו?סמג|טוש"ע|טור)'''
    ram_reg = re.compile(ur"(מיי')")
    semag_reg = re.compile(ur'(סמג)')
    tush_reg = re.compile(ur'(\u05d8\u05d5\u05e9\"\u05e2)')

    for line in lines:
        i += 1
        print i
        print line
        line = clean_line(line)
        cit = EM_Citation()
        cit._file_line = i
        # flags
        rambam = False
        semag = False
        tush = False
        split = re.split(pattern, line.strip())
        sub_s = re.split('\s',split[0].strip())
        # set the counters
        cit._perek_counter = sub_s[0]
        cit._page_counter = sub_s[1:] # the page counters can be a list of letters
        try:
            if getGematria(cit._perek_counter) == 1:
            # if cit._perek_counter == u'א':
                perek +=1
                page = 0
            cit._perek = perek
            if (not cit._page_counter) or (cit._page_counter[0] == u'א'):
                page +=1
            cit._page = page
        except:
            print 'error, cit with the perek/page counters'
        # start the parsing
        split_it = iter(split)
        for part in split_it:
            if part == ur"מיי'":
                rambam_cit = split_it.next()  # todo: what happens when it says מיי' וסמג שם?
                mishneh.cit = []
                cit._mimon = mishneh.parse_rambam(rambam_cit)
            elif part == ur'סמג':
                semag_cit = split_it.next()
                cit._semag = smg.parse_semag(semag_cit)
            elif part == ur'טוש"ע' or part == ur'טור' or part == u'ש"ע':
                tush_cit = split_it.next()

        cit_dictionary[i] = cit
        # print 'perek', perek_counter, 'page', page_counter
        # if rambam: print 'rambam',rambam_cit
        # if semag: print 'smg', semag_cit
        # if tush: print 'tursh', tush_cit
    return cit_dictionary
class Semag(object):
    """
    One instance per file (massekhet)
    """
    def __init__(self):
        self._tracker = BookIbidTracker()


    def parse_semag(self, str):
        split = re.split('\s', str.strip())
        str_list = filter(None, split)
        book = str_list[0]
        if book == u'שם':
            book = None
        elif book == u'לאוין':
            book = u'Sefer Mitzvot Gadol, Volume One'  # todo: maybe should take this out of the refs?
        elif book == u'עשין':
            book = u'Sefer Mitzvot Gadol, Volume Two'  # todo: maybe should take this out of the refs?
        else:
            print "error smg, don't recognize book name", book
            return

        if len(str_list) > 1:
            mitzva = str_list[1:]
            for m in mitzva:
                resolved = self._tracker.resolve(book, [getGematria(m)])
        else:
            resolved = self._tracker.resolve(book, [None])
        print resolved.normal()

class Rambam(object):
    """
    One instance per file (massekhet)
    """
    def __init__(self):
        self._tracker = BookIbidTracker()
        self._conv_table = rambam_name_table()
        self.cit = []


    def parse_rambam(self, str): # these will be aoutomatic from the privates of the object (Rambam)
        reg1 = u'''(מהל|מהלכות|מהל'|מהלכו'|מה')'''  # מהלכות before the book name
        reg21 = u''' הלכה| הל'?| הלכ'?| דין'''
        # reg22 = u''' ה"[א-ת]'''
        reg22 = u'''הל?([א-ת]?"[א-ת])'''
        reg2 = u'''({}|{}|שם)'''.format(reg21,reg22)  # before the halacha
        reg_double_cit = u''' (ופ[א-ת]?"[א-ת])'''
        reg_for_book = ur'''{} (.+?){}'''.format(reg1,reg2)

        # check for multiple citation
        multiple = re.search(reg_double_cit, str)
        if multiple:
            mul = re.split(reg_double_cit, str, maxsplit=1)
            self.parse_rambam(mul[0])
            self.parse_rambam(mul[1] + mul[2])
            return

        # book
        if not re.search(reg2, str):
            reg_for_book = ur'''{} (.+)'''.format(reg1)
        book = re.search(reg_for_book, str)
        if book:
            book = book.group(2).strip()
            book = re.sub("'",'',book)

        if book:
            try:
                if self._conv_table.has_key(book):
                    book = self._conv_table[book]
                elif self._conv_table.keys(book):
                    key = self._conv_table.keys(book)
                    book = self._conv_table[key[0]]
            except:
                print "error mim, couldn't find this book name in table", book
                return
        # perek
        perek = re.search(u'פרק ([א-ת]"?[א-ת]?)|פ([א-ת]?"[א-ת])', str)
        if perek:
            perek = perek.group(1) or perek.group(2)
            perek = getGematria(perek)

        # halacha
        halacha = re.search(u'''{} (.+)'''.format(reg2), str) or re.search(u'''{}'''.format(reg22), str)
        if halacha:
            hal21 = re.search(u'''({}) (.+)'''.format(reg21), str)
            hal22 = re.search(u'''הל?([א-ת]?"[א-ת])''', str)
            if hal21:
                halacha = hal21.group(2)
            elif hal22:
                halacha = hal22.group(1)
            elif re.search(u'שם', str):
                halacha = None
            # else:
            #     print 'error mim, No halcha stated'
            #     return

        # clean halacha
        if halacha:
            ayyen = re.split(u'''ועיין|ועי'?|וע"ש''', halacha)
            if len(ayyen)>1:
                halacha = ayyen[0]
            halacha_split = re.split(u'\s([א-ת]?"?[א-ת])', halacha.strip())
            halacha_split = filter(None, halacha_split)
            halacha = [getGematria(i) for i in halacha_split]
            # halacha = filter(lambda x:x!=0,halacha)

        # print book, (perek, halacha)
        # resolved = self._tracker.resolve(book, [perek, halacha])
            resolved = [self._tracker.resolve(book, [perek, hal]) for hal in halacha]
        else: # halacha was sham
            if perek and book and not re.search(u'שם', str):
                print 'error mim, No halacha stated'
            resolved = self._tracker.resolve(book, [perek, halacha])
        print resolved
        # return (book,(perek, halacha))
        self.cit.append(resolved)
        return self.cit


# note: should call this function only once in init
def rambam_name_table():
    names = library.get_indexes_in_category("Mishneh Torah")
    en_names = names
    he_raw = [library.get_index(name).all_titles('he')[0] for name in names]
    he_names = []
    # name_dict = {}
    name_dict = pygtrie.CharTrie()
    for he, en in zip(he_raw, en_names):
        s = re.split(u''' הלכות | הלכה | הל' | הלכ''' , he)
        if len(s)>1:
            he = s[1]
            he_names.append(he)
            name_dict[he] = en
    name_dict[u'מלוה'] = name_dict[u'מלווה ולווה']
    name_dict[u'מלוה ולוה'] = name_dict[u'מלווה ולווה']
    name_dict[u'מלוה ולווה'] = name_dict[u'מלווה ולווה']
    name_dict[u'תפלה'] = name_dict[u'תפילה וברכת כהנים']
    name_dict[u'יו"ט'] = name_dict[u'שביתת יום טוב']
    name_dict[u'י"ט'] = name_dict[u'שביתת יום טוב']
    name_dict[u'יום טוב'] = name_dict[u'שביתת יום טוב']
    name_dict[u'ת"ת'] = name_dict[u'תלמוד תורה']
    name_dict[u'ע"ז']  = name_dict[u'עבודה זרה וחוקות הגויים']
    name_dict[u'ע"ג'] = name_dict[u'עבודה זרה וחוקות הגויים']
    name_dict[u'עו"ג'] = name_dict[u'עבודה זרה וחוקות הגויים']
    # name_dict[u'עבודה זרה'] = name_dict[u'עבודה זרה וחוקות הגויים']
    name_dict[u'עבודת כוכבים'] = name_dict[u'עבודה זרה וחוקות הגויים']
    name_dict[u'אבות הטומאה'] = name_dict[u'שאר אבות הטומאות']
    name_dict[u'שאר אבות הטומאה'] = name_dict[u'שאר אבות הטומאות']
    name_dict[u'שאר אבות הטומאות'] = name_dict[u'שאר אבות הטומאות']
    name_dict[u'אבות הטומאות'] = name_dict[u'שאר אבות הטומאות']
    name_dict[u'שאר א"ה'] = name_dict[u'שאר אבות הטומאות']
    name_dict[u'טומאת משכב ומושב'] = name_dict[u'מטמאי משכב ומושב']
    name_dict[u'משכב ומושב'] = name_dict[u'מטמאי משכב ומושב']
    # name_dict[u"שכני'"] = name_dict[u'שכנים']
    # name_dict[u"שכני"] = name_dict[u'שכנים']
    name_dict[u'ס"ת'] = name_dict[u'תפילין ומזוזה וספר תורה']
    name_dict[u'ספר תורה'] = name_dict[u'תפילין ומזוזה וספר תורה']
    name_dict[u'מזוזה'] = name_dict[u'תפילין ומזוזה וספר תורה']
    name_dict[u'תפלין'] = name_dict[u'תפילין ומזוזה וספר תורה']
    name_dict[u'אבידה'] = name_dict[u'גזילה ואבידה']
    # name_dict[u'שמיטין'] = name_dict[u'שמיטה ויובל']
    name_dict[u'שמיטין ויובל'] = name_dict[u'שמיטה ויובל']
    name_dict[u'שמיטין ויובלות'] = name_dict[u'שמיטה ויובל']
    name_dict[u'שמטה ויובל'] = name_dict[u'שמיטה ויובל']
    name_dict[u'יובל'] = name_dict[u'שמיטה ויובל']
    name_dict[u'ביכורין'] = name_dict[u'ביכורים ושאר מתנות כהונה שבגבולין']
    name_dict[u'בכורים'] = name_dict[u'ביכורים ושאר מתנות כהונה שבגבולין']
    name_dict[u'זכיה ומתנה'] = name_dict[u'זכייה ומתנה']
    # name_dict[u"מכיר'"] = name_dict[u'מכירה']
    name_dict[u'שאר אבות הטומאה'] = name_dict[u'שאר אבות הטומאות']
    name_dict[u'מעשה קרבנות'] = name_dict[u'מעשה הקרבנות']
    name_dict[u'תענית'] = name_dict[u'תעניות']
    name_dict[u'מקוואות'] = name_dict[u'מקואות']
    name_dict[u'ערכין וחרמין'] = name_dict[u'ערכים וחרמין']
    name_dict[u'ערכין'] = name_dict[u'ערכים וחרמין']
    name_dict[u'שאלה ופקדון'] = name_dict[u'שאלה ופיקדון']
    name_dict[u"שאל' ופקדון"] = name_dict[u'שאלה ופיקדון']
    name_dict[u'פקדון'] = name_dict[u'שאלה ופיקדון']
    # name_dict[u'מעשר שני'] = name_dict[u'מעשר שני ונטע רבעי']
    name_dict[u'מ"ש'] = name_dict[u'מעשר שני ונטע רבעי']
    name_dict[u'נטע רבעי'] = name_dict[u'מעשר שני ונטע רבעי']
    name_dict[u'מתנות ענים'] = name_dict[u'מתנות עניים']
    name_dict[u'מ"ע'] = name_dict[u'מתנות עניים']
    name_dict[u'טומאת אוכלין'] = name_dict[u'טומאת אוכלים']
    name_dict[u'טומאות אוכלין'] = name_dict[u'טומאת אוכלים']
    name_dict[u'טומאת המת'] = name_dict[u'טומאת מת']
    name_dict[u'גזילה ואבדה'] = name_dict[u'גזילה ואבידה']
    name_dict[u'גזלה ואבדה'] = name_dict[u'גזילה ואבידה']
    name_dict[u'גזלה ואבידה'] = name_dict[u'גזילה ואבידה']
    name_dict[u'אבדה'] = name_dict[u'גזילה ואבידה']
    name_dict[u'תמידין'] = name_dict[u'תמידים ומוספין']
    name_dict[u'תמידין ומוספין'] = name_dict[u'תמידים ומוספין']
    name_dict[u'איסורי מזבח'] = name_dict[u'איסורי המזבח']
    name_dict[u'א"מ'] = name_dict[u'איסורי המזבח']
    name_dict[u'איס"ב'] = name_dict[u'איסורי ביאה']
    name_dict[u'א"ב'] = name_dict[u'איסורי ביאה']
    name_dict[u'קידוש החדש'] = name_dict[u'קידוש החודש']
    name_dict[u'קדוש החדש'] = name_dict[u'קידוש החודש']
    name_dict[u'לולב'] = name_dict[u'שופר וסוכה ולולב']
    name_dict[u'סוכה'] = name_dict[u'שופר וסוכה ולולב']
    name_dict[u'אבילות'] = name_dict[u'אבל']
    name_dict[u'אבלות'] = name_dict[u'אבל']
    name_dict[u'דיעות'] = name_dict[u'דעות']
    name_dict[u'שלוחים ושותפין'] = name_dict[u'שלוחין ושותפין']
    name_dict[u'שותפין'] = name_dict[u'שלוחין ושותפין']
    name_dict[u'כלי מקדש'] = name_dict[u'כלי המקדש והעובדין בו']
    # name_dict[u'כלי המקדש'] = name_dict[u'כלי המקדש והעובדין בו']
    name_dict[u'ביאת המקדש'] = name_dict[u'ביאת מקדש']
    name_dict[u'מ"א'] = name_dict[u'מאכלות אסורות']
    name_dict[u'מא"ס'] = name_dict[u'מאכלות אסורות']
    # name_dict[u"ממרי'"] = name_dict[u'ממרים']
    # name_dict[u"שכירו'"] = name_dict[u'שכירות']
    name_dict[u"תרומה"] = name_dict[u'תרומות']
    # name_dict[u"סנהד'"] = name_dict[u'סנהדרין והעונשין המסורין להם']
    name_dict[u'ק"ש'] = name_dict[u'קריאת שמע']
    # name_dict[u'עבודת יה"כ'] = name_dict[u'עבודת יום הכפורים'] # because it makes problems with my code...can be fixed by taking it step by step
    name_dict[u'נשיאות כפים'] = name_dict[u'תפילה וברכת כהנים']
    name_dict[u'חנוכה'] = name_dict[u'מגילה וחנוכה']
    name_dict[u'מצה'] = name_dict[u'חמץ ומצה']
    name_dict[u'גרושין'] = name_dict[u'גירושין']
    name_dict[u'נ"מ'] = name_dict[u'נזקי ממון']
    name_dict[u'פסולי מוקדשין'] = name_dict[u'פסולי המוקדשין']
    name_dict[u'ק"פ'] = name_dict[u'קרבן פסח']
    name_dict[u'רוצח וש"נ'] = name_dict[u'רוצח ושמירת נפש']

    # for name in name_dict.keys():
    #     first = re.split('\s', name)
    #     if len(first) > 1:
    #         name_dict[first[0]] = name_dict[name]
    # del name_dict[u'איסורי']
    # del name_dict[u'טומאת']
    name_dict[u'מעשר'] = name_dict[u'מעשרות']
    return name_dict


def clean_line(line):
    line = re.sub(u':','', line)
    line = re.sub(u':','', line)
    reg_parentheses = re.compile(u'\((.*?)\)')
    reg_brackets = re.compile(u'\[(.*?)\]')
    in_per = reg_parentheses.search(line)
    in_bra = reg_brackets.search(line)

    if in_per:
        if in_bra:
            clean = re.sub(reg_brackets, in_bra.group(1), line)  # brackets are always correct
            clean = re.sub(reg_parentheses, '', clean)
        else:
            clean = re.sub(reg_parentheses, in_per.group(1), line)
    elif in_bra:
        clean = re.sub(reg_brackets, in_bra.group(1), line)  # brackets are always correct
    else:
        clean = line
    return clean

if __name__ == "__main__":
    # ein_mishpat = parse_em('בבא מציעא.txt')
    ein_mishpat = parse_em('בבא בתרא.txt')
    # parse_em('ראש השנה.txt')
    # parse_em('ביצה.txt')
    # parse_em('ברכות.txt')
    # parse_em('גיטין.txt')
    # parse_em('חגיגה.txt')
    # parse_em('יבמות.txt')
    # parse_em('יומא.txt')
    # parse_em('כתובות.txt')
    # parse_em('מועד קטן.txt')
    # parse_em('מכות.txt')
    # parse_em('נדרים.txt')
    # parse_em('נזיר.txt')
    # parse_em('סוטה.txt')
    # parse_em('סוכה.txt')
    # parse_em('סנהדרין.txt')
    # parse_em('עירובין.txt')
    # parse_em('פסחים.txt')
    # parse_em('קידושין.txt')
    # parse_em('שבועות.txt')
    # parse_em('שבת.txt')