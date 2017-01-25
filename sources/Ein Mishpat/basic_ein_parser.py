# -*- coding: utf-8 -*-

from sefaria.model import *
import codecs
import regex as re
import pygtrie
from data_utilities.util import getGematria
from data_utilities.ibid import BookIbidTracker


class EM_Citation(object):
    """
    One instance per commentary
    """
    def __init__(self, filename, line):
        self._massekhet = filename
        self._file_line = line
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
    tursh = TurSh()
    cit_dictionary = {}
    with codecs.open(filename, 'r', 'utf-8') as fp:
        lines = fp.readlines()
    pattern = ur'''(ו?ש"ע|מיי'|ו?סמג|ו?טוש"ע|ו?ב?טור)'''
    ram_reg = re.compile(ur"(מיי')")
    semag_reg = re.compile(ur'(סמג)')
    tush_reg = re.compile(ur'(\u05d8\u05d5\u05e9\"\u05e2)')

    for line in lines:
        i += 1
        print i, filename
        print line
        line = clean_line(line)
        print line
        cit = EM_Citation(filename, i)
        # flags
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
                page += 1
            cit._page = page
        except:
            print 'error, cit with the perek/page counters'
        # start the parsing
        split_it = iter(split)
        for part in split_it:
            if part == ur"מיי'":
                # tochen = split_it.next()
                # if not tochen:
                #     tochen = u'שם'
                rambam_cit = split_it.next()
                # rambam_cit = tochen
                mishneh.cit = []
                cit._mimon = mishneh.parse_rambam(rambam_cit)
            elif re.search(u'ו?סמג',part):
                semag_cit = split_it.next()
                cit._semag = smg.parse_semag(semag_cit)
            elif re.search(u'ו?טוש"ע|ש"ע', part):
                # if not cit._tush: # i think this was in only because the tur alon but that was taken care of.
                    tush_cit = split_it.next()
                    cit._tush = tursh.parse_tush(tush_cit)
            elif re.search(ur'טור', part):
                next = split_it.next()
                if next == ur'שו?"ע':
                    tush_cit = split_it.next()
                    cit._tush = tursh.parse_tush(tush_cit)
                else:# basically assuming there isn't SA citation here
                    tush_cit = next
                    cit._tush = tursh.parse_tush(tush_cit, only_tur = True)

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
        resolveds = []
        if len(str_list) > 1:
            mitzva = str_list[1:]
            for m in mitzva:
                if m == u'שם':
                    m = None
                else:
                    m = getGematriaVav(m)
                resolved = self._tracker.resolve(book, [m])
                resolveds.append(resolved.normal())
        else:
            resolved = self._tracker.resolve(book, [None])
            resolveds.append(resolved.normal())
        print resolveds
        return resolveds


class TurSh(object):
    """
    One instance per file (massekhet)
    """
    def __init__(self):
        self._tracker_sa = BookIbidTracker()
        self._tracker_tur = BookIbidTracker()
        self._sa_table = {u'ח"מ': u'Shulchan Arukh, Choshen Mishpat',
                          u'חו"מ': u'Shulchan Arukh, Choshen Mishpat',
                          u'אה"ע': u'Shulchan Arukh, Even HaEzer',
                          u'י"ד': u"Shulchan Arukh, Yoreh De'ah",
                          u'יד': u"Shulchan Arukh, Yoreh De'ah",
                          u'יו"ד': u"Shulchan Arukh, Yoreh De'ah",
                          u'או"ח': u'Shulchan Arukh, Orach Chayim',
                          u'א"ח': u'Shulchan Arukh, Orach Chayim'
                       }
        self._tur_table = {
            None: None,
            u'Shulchan Arukh, Choshen Mishpat': u'Tur, Choshen Mishpat',
            u'Shulchan Arukh, Even HaEzer': u'Tur, Even HaEzer',
            u"Shulchan Arukh, Yoreh De'ah": u'Tur, Yoreh Deah',
            u'Shulchan Arukh, Orach Chayim': u'Tur, Orach Chaim'
            }
            # {
            #            u'ח"מ': u'Tur, Choshen Mishpat',
            #            u'חו"מ': u'Tur, Choshen Mishpat',
            #            u'אה"ע': u'Tur, Even HaEzer',
            #            u'י"ד': u'Tur, Yoreh Deah',
            #            u'יד': u'Tur, Yoreh Deah',
            #            u'יו"ד': u'Tur, Yoreh Deah',
            #            u'או"ח': u'Tur, Orach Chaim',
            #            u'א"ח': u'Tur, Orach Chaim',
            #            }

    def check_uno(self, book, siman):
        # a list of all the simanim in the Shulchan Aruch that have only one Seif in them
        # todo: no need to create this static lists everytime meeting a seif, should go static, where?
        # todo: in the init of the tush obj it will run every line... thats even more wastfull...
        uno_hm = {2, 4, 6, 20, 21, 23, 24, 38, 48, 50, 53, 59, 62, 64, 124, 152, 165, 166, 179, 180, 189, 193, 208, 221,
                  233, 244, 254, 265, 274, 282, 297, 299, 318, 319, 323, 324, 325, 326, 329, 342, 347, 350, 351, 352, 368, 376, 377,
                  381, 382, 387, 392, 395, 402, 416, 426}
        uno_yd = {386, 3, 260, 261, 7, 8, 9, 140, 337, 277, 27, 29, 290, 165, 167, 171, 304, 136, 350, 183, 191,
                  193, 323, 200, 74, 311, 332, 77, 78, 207, 209, 212, 398, 346, 93, 222, 224, 225, 354, 355, 356,
                  230, 231, 360, 233, 369, 370, 117}
        uno_oc = {5, 520, 16, 530, 22, 29, 35, 41, 44, 557, 558, 49, 50, 563, 52, 573, 577, 578, 67, 68, 78, 80, 594,
                  595, 84, 86, 599, 88, 603, 605, 609, 100, 105, 620, 625, 115, 116, 118, 120, 635, 641, 130,
                  133, 136, 138, 654, 655, 657, 659, 148, 149, 152, 666, 667, 157, 166, 679, 683, 176, 697, 198,
                  207, 214, 598, 226, 231, 237, 241, 242, 256, 258, 556, 642, 278, 281, 283, 287, 300, 564, 342,
                  343, 347, 348, 351, 359, 367, 369, 373, 377, 383, 387, 388, 389, 395, 678, 400, 402, 403, 404,
                  406, 411, 412, 413, 417, 419, 421, 424, 427, 430, 669, 435, 449, 458, 464, 661, 469, 474, 479,
                  480, 482, 483, 484, 485, 486, 492, 596, 505}
        uno_eh = {84, 72, 14, 18, 51, 52, 54, 151, 24, 57, 60, 153}
        if book == u'Shulchan Arukh, Choshen Mishpat' and siman in uno_hm:
            return True
        elif book == u'Shulchan Arukh, Even HaEzer' and siman in uno_eh:
            return True
        elif book == u"Shulchan Arukh, Yoreh De'ah" and siman in uno_yd:
            return True
        elif book == u'Shulchan Arukh, Orach Chayim' and siman in uno_oc:
            return True
        return False

    def parse_tush(self, str, only_tur = False):
        ayyen = re.split(u''' ובהג"ה|ועיין|ועי'?|וע"ש''', str)
        if len(ayyen) > 1:
            str = ayyen[0]
        split = re.split('\s', str.strip())
        str_list = filter(None, split)
        # todo: not sure what i feel about these 2 lines...
        if not str_list:
            return
        str_it = iter(str_list[1:])
        reg_siman = re.compile(u"סי'?|סימן")
        reg_seif = re.compile(u'''סעי'?|סעיף|ס([א-ת]?"[א-ת])''')
        reg_sham = u'שם'
        reg_combined = u'ס([א-ת]?"[א-ת])'
        resolveds = []
        try:
            book = str_list[0]
            if re.search(reg_sham, book):
                book_sa = None
            elif self._sa_table.has_key(book):
                        book_sa = self._sa_table[book]
            elif re.search(reg_siman, book) or re.search(reg_seif, book):
                book_sa = None
                str_it = iter(str_list)
            else:
                print "error tush, don't recognize book name", book
                return

            # else:
            #     try:
            #         if self._sa_table.has_key(book):
            #             book_sa = self._sa_table[book]
            #     except KeyError:
            #         print "error tush, don't recognize book name", book
            #         return

            siman = None
            seif = None
            resolved_tur = None
            for word in str_it:
                to_res = False  # a flag to say there was found a citation we want to resolve
                if re.search(reg_siman, word):
                    to_res = True
                    siman = getGematriaVav(str_it.next())
                    hasnext = True
                    try:
                        next = str_it.next()
                    except StopIteration:
                        hasnext = False
                    if hasnext and (re.search(reg_seif,next) or re.search(reg_sham, next)):
                        if re.search(reg_combined, next):
                            combined = re.search(reg_combined, next)
                            seif = getGematriaVav(combined.group(1))
                        elif re.search(reg_sham, next):
                            seif = None
                        else:
                            seif = getGematriaVav(str_it.next())
                    elif self.check_uno(book_sa, siman):
                        seif = 1
                    else:
                        if only_tur:
                            resolved_tur = self.parse_tur(book_sa, siman) #todo: note: might be an issue with None, None to this file
                            print resolved_tur
                            return resolved_tur
                        else:
                            print 'error tush, missing seif'
                elif re.search(reg_seif, word):
                    to_res = True
                    if re.search(reg_combined, word):
                        combined = re.search(reg_combined, word)
                        seif = getGematriaVav(combined.group(1))
                    else:
                        seif = getGematriaVav(str_it.next())
                elif len(word) <= 3: # todo: note: 3 is a bit long check that not getting gorbage, deleted: from line start re.match(u'''[א-ת]{1}''', word) and
                    seif = getGematriaVav(word)
                    to_res = True
                if to_res:
                    resolved_sa = self._tracker_sa.resolve(book_sa, [siman, seif])
                    # don't type in the same resolved tur twice... (when there is citations to 2 seifim in the same siman it is twice one citation in the tur, no need)
                    if resolved_tur != self._tracker_tur.resolve(self._tur_table[book_sa], [siman]):
                        resolved_tur = self._tracker_tur.resolve(self._tur_table[book_sa], [siman])
                        resolveds.append(resolved_tur)

                    resolveds.append(resolved_sa)

            # for word in str_it:
            #     if re.search(reg_siman, word):
            #         if not siman:
            #             siman = getGematria(str_it.next())
            #             siman1 = siman
            #         else:
            #             siman1 = getGematria(str_it.next())
            #     elif re.search(reg_seif, word):
            #         if not seif:
            #             seif = getGematria(str_it.next())
            #         else:
            #             seif1 = getGematria(str_it.next())
            # if not seif:
            #    if self.check_uno(book_sa, siman):
            #        seif = 1
            #    else:
            #        seif = None
            # resolved_sa = self._tracker_sa.resolve(book_sa, [siman, seif])
            # resolved_tur = self._tracker_tur.resolve(book_tur, [siman])
            # print resolved_tur
            # print resolved_sa
            # if siman1!= siman or seif1:
            #     resolved_sa1 = self._tracker_sa.resolve(book_sa, [siman1, seif1])
            #     resolved_tur1 = self._tracker_tur.resolve(book_tur, [siman1])
            #     if not seif:
            #         if self.check_uno(book_sa, siman1):
            #             seif = 1
            #         else:
            #             seif = None
            #     print resolved_tur1
            #     print resolved_sa1
            #     return [resolved_sa, resolved_tur, resolved_sa1, resolved_tur1]
            # else:
            #     return [resolved_sa, resolved_tur]
            print resolveds
            return resolveds
        except KeyError:
            print 'error tush, there is missing data where in the tur to look'
            return

    def parse_tur(self, book_sa = None, siman = None):
        # if book_sa == 'None':
        #     book_sa = None
        # if siman == 'None':
        #     siman = None
        if not book_sa:
            book_sa = self._tur_table[book_sa]
        resolved_tur = self._tracker_tur.resolve(book_sa, [siman])
        return resolved_tur


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
            perek = getGematriaVav(perek)

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
            halacha_split = re.split(u'\sו?([א-ת]?"?[א-ת])', halacha.strip())
            halacha_split = filter(None, halacha_split)
            halacha = [getGematriaVav(i) for i in halacha_split]
            # halacha = filter(lambda x:x!=0,halacha)

        # print book, (perek, halacha)
        # resolved = self._tracker.resolve(book, [perek, halacha])
            resolved = [self._tracker.resolve(book, [perek, hal]) for hal in halacha]
        else:  # halacha was sham
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
    line = re.sub(u':', '', line)
    line = re.sub(u':', '', line)
    reg_parentheses = re.compile(u'\((.*?)\)')
    reg_brackets = re.compile(u'\[(.*?)\]')
    in_per = reg_parentheses.search(line)
    in_bra = reg_brackets.search(line)
    reg_ayyen_tur = re.compile(u'''(ו?עיין|ו?עי') בטור''')
    line = re.sub(u'\[.*?אלפס.*?\]', u'', line)
    line = re.sub(u'טור ו?שו"ע', u'טוש"ע', line)
    pos = re.search(reg_ayyen_tur, line)

    if pos:
        line = line[:pos.start()]

    if in_per:
        if in_bra:
            clean = re.sub(reg_brackets, ur'\1', line)  # brackets are always correct
            clean = re.sub(reg_parentheses, '', clean)
        else:
            clean = re.sub(reg_parentheses, ur'\1', line)
    elif in_bra:
        clean = re.sub(reg_brackets, ur'\1', line)  # brackets are always correct
    else:
        clean = line
    return clean


# putting in casses of switching the letter order
def getGematriaVav(str):
    case_set = {270,272,274,275,298,304,344,670,672,698,744} # from trello card 'Letter transpositions'
    if str[0] == u'ו' and (is_hebrew_number(str[1:]) or (getGematria(str[1:]) in case_set)):
        return getGematria(str[1:])
    else:
        return getGematria(str)

#  Noahs code checking that the hundreds, tens, ones, are in the right order
def is_hebrew_number(str):
    matches = re.findall(hebrew_number_regex(), str)
    if len(matches) == 0:
        return False
    return matches[0] == str


def hebrew_number_regex():
    """
    Regular expression component to capture a number expressed in Hebrew letters
    :return string:
    \p{Hebrew} ~= [\u05d0–\u05ea]
    """
    rx = ur"""                                    # 1 of 3 styles:
    ((?=[\u05d0-\u05ea]+(?:"|\u05f4|'')[\u05d0-\u05ea])    # (1: ") Lookahead:  At least one letter, followed by double-quote, two single quotes, or gershayim, followed by  one letter
            \u05ea*(?:"|\u05f4|'')?                    # Many Tavs (400), maybe dbl quote
            [\u05e7-\u05ea]?(?:"|\u05f4|'')?        # One or zero kuf-tav (100-400), maybe dbl quote
            [\u05d8-\u05e6]?(?:"|\u05f4|'')?        # One or zero tet-tzaddi (9-90), maybe dbl quote
            [\u05d0-\u05d8]?                        # One or zero alef-tet (1-9)                                                            #
        |[\u05d0-\u05ea]['\u05f3]                    # (2: ') single letter, followed by a single quote or geresh
        |(?=[\u05d0-\u05ea])                        # (3: no punc) Lookahead: at least one Hebrew letter
            \u05ea*                                    # Many Tavs (400)
            [\u05e7-\u05ea]?                        # One or zero kuf-tav (100-400)
            [\u05d8-\u05e6]?                        # One or zero tet-tzaddi (9-90)
            [\u05d0-\u05d8]?                        # One or zero alef-tet (1-9)
    )"""

    return re.compile(rx, re.VERBOSE)

if __name__ == "__main__":
    ein_mishpat = parse_em('בבא מציעא.txt')
    # ein_mishpat = parse_em('בבא בתרא.txt')
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
    # # parse_em('נדרים.txt')
    # parse_em('נזיר.txt')
    # parse_em('סוטה.txt')
    # parse_em('סוכה.txt')
    # parse_em('סנהדרין.txt')
    # parse_em('עירובין.txt')
    # parse_em('פסחים.txt')
    # parse_em('קידושין.txt')
    # parse_em('שבועות.txt')
    # parse_em('שבת.txt')