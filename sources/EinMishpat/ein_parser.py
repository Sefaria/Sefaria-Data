# -*- coding: utf-8 -*-
from __builtin__ import enumerate

from sefaria.model import *
import codecs
import regex as re
import pygtrie
from data_utilities.util import getGematria
from data_utilities.ibid import BookIbidTracker
from sefaria.utils.hebrew import strip_nikkud
import unicodecsv as csv

class Massekhet(object):

    def __init__(self,errorfilename):
        self.ErrorFile = codecs.open(errorfilename, 'w', encoding='utf-8')
        self.test = None
        self.error_flag = False
        self.line_num = 0

    def write_shgia(self, txt):
        self.error_flag = txt
        self.ErrorFile.write(str(self.line_num) + ': ' + txt + '\n')
        print self.line_num, txt


class EM_Citation(object):
    """
    One instance per row in text file
    """
    def __init__(self, filename, line_number, orig):
        self._massekhet = filename
        self._original = orig
        self._file_line = line_number
        self._perek_counter = 0
        self._perek  = 0 # assuming all prakim in the massekhet have at least one citation of EM
        self._page_counter = 0
        self._page = 0 # a counter of pages from the begining of this perek that had ein mishpat on them
        self._mimon = None
        self._semag = None
        self._tsh = None
        self._tur = None
        self._sa = None

    def obj2dict(self,passing):
        citations = []
        if passing == 1:
            dict = self.get_dict(0)
            citations.append(dict)
        elif passing == 2:
            for i, small_letter in enumerate(self._page_counter):
                dict = self.get_dict(i)
                citations.append(dict)
        return citations

    def get_dict(self, i):
        try:
            dict = {
                u'txt file line': self._file_line,
                u'Perek running counter': self._perek_counter,
                u'page running counter': self._page_counter[i],
                u'Perek aprx': self._perek,
                u'Page aprx': self._page,
                u'Rambam': self._mimon,
                u'Semag': self._semag,
                u'Tur Shulchan Arukh': self._tsh,
                u'original': self._original,
                u'problem': None
                }
        except IndexError:
            dict = {
                u'txt file line': self._file_line,
                u'Perek running counter': self._perek_counter,
                u'page running counter':None,
                u'Perek aprx': self._perek,
                u'Page aprx': self._page,
                u'Rambam': self._mimon,
                u'Semag': self._semag,
                u'Tur Shulchan Arukh': self._tsh,
                u'original': self._original,
                u'problem': u'error missing little or big letter'
            }
            print u'error missing little or big letter'
        for key in dict.keys():
            if isinstance(dict[key], list):
                dict[key] = [ref.normal() for ref in dict[key] if (isinstance(ref, Ref))]
        return dict


    def check_double(self, variable, new):
        try:
            if vars(self)[variable]:
                vars(self)[variable].extend(new)
            else:
                vars(self)[variable] = new
        except TypeError as NoneType:
            return vars(self)[variable]


def parse_em(filename, passing, errorfilename):
    mass = Massekhet(errorfilename)
    i = 0
    perek = 0
    page = 0
    mishneh = Rambam() # we parse per file and create a mishne torah (Rambam) obj per file
    smg = Semag()
    tursh = TurSh()
    cit_dictionary = []
    with codecs.open(filename, 'r', 'utf-8') as fp:
        lines = fp.readlines()
    pattern = ur'''(ו?שו?"ע|מיי'|ו?סמג|ו?טוש"ע|ו?ב?טור)'''

    for line in lines:
        mass.error_flag = False
        i += 1
        print i, filename
        print line
        mass.line_num = i
        line = clean_line(line.strip())
        cit = EM_Citation(filename, i, line)
        # flags
        split = re.split(pattern, line)
        sub_s = re.split('\s',split[0].strip())
        # set the counters
        cit._perek_counter = sub_s[0]
        cit._page_counter = sub_s[1:]  # since the page counters can be a list of letters
        try:
            perek_c = getGematria(cit._perek_counter)
            # check_continues
            if perek_c == 1:
                perek += 1
                page = 0
            elif perek_c-1 != getGematria(cit_dictionary[-1][u'Perek running counter']) and cit_dictionary[-1]['problem'] != u'error, cit with the perek/page counters':
                mass.write_shgia(u'error, cit with the perek/page counters')

            cit._perek = perek
            if (not cit._page_counter) or (cit._page_counter[0] == u'א'):
                page += 1
            cit._page = page
        except:
            mass.write_shgia(u'error, cit with the perek/page counters')
        # start the parsing
        split_it = iter(split)
        for part in split_it:
            if part == ur"מיי'":
                rambam_cit = split_it.next()
                cit.check_double(u'_mimon', mishneh.parse_rambam(rambam_cit, mass)) #cit._mimon = mishneh.parse_rambam(rambam_cit)
            elif re.search(u'ו?סמג',part):
                semag_cit = split_it.next()
                cit.check_double(u'_semag', smg.parse_semag(semag_cit, mass))  # cit._semag = smg.parse_semag(semag_cit)
            elif re.search(u'ו?טוש"ע|ש"ע|שו"ע', part):
                    tsh_cit = split_it.next()
                    cit.check_double(u'_tsh', tursh.parse_tsh(tsh_cit, mass))  # tursh.parse_tsh(tsh_cit)
            elif re.search(ur'טור', part):
                next = split_it.next()
                # if next == ur'שו?"ע':
                #     tsh_cit = split_it.next()
                #     cit._tsh = tursh.parse_tsh(tsh_cit, mass)
                # else:# basically assuming there isn't SA citation here
                #     tsh_cit = next
                #     cit.check_double('_tsh', tursh.parse_tsh(tsh_cit, mass, only_tur = True))#cit._tsh = tursh.parse_tsh(tsh_cit, only_tur = True)
                tsh_cit = next
                cit.check_double('_tsh', tursh.parse_tsh(tsh_cit, mass,
                                                             only_tur=True))  # cit._tsh = tursh.parse_tsh(tsh_cit, only_tur = True)
        cit_dictionary.extend(cit.obj2dict(passing))
        if cit_dictionary[-1][u'problem'] != u'error missing little or big letter' and cit_dictionary[-1][u'problem'] != u'error, cit with the perek/page counters':
            cit_dictionary[-1][u'problem'] = mass.error_flag
        print cit_dictionary[-1]
    return cit_dictionary


class Semag(object):
    """
    One instance per file (massekhet)
    """
    def __init__(self):
        self._tracker = BookIbidTracker()
        self._table = {
            u'שם': None,
            u'לאוין': u'Sefer Mitzvot Gadol, Volume One',
            u'עשין': u'Sefer Mitzvot Gadol, Volume Two',
            u'א':u'Sefer Mitzvot Gadol, Volume Two, Laws of Eruvin',
            u'ב': u'Sefer Mitzvot Gadol, Volume Two, Laws of Mourning',
            u'ג': u"Sefer Mitzvot Gadol, Volume Two, Laws of Tisha B'Av",
            u'ד': u'Sefer Mitzvot Gadol, Volume Two, Laws of Megillah',
            u'ה': u'Sefer Mitzvot Gadol, Volume Two, Laws of Chanukah'
                       }



    def parse_semag(self, str, mass):
        reg_book = re.compile(u'ו?(עשין|שם|לאוין)')
        split = re.split(reg_book, str.strip())
        str_list = filter(None, [item.strip() for item in split])
        resolveds = []
        derabanan_flag = False
        book = None
        reg_siman = u"סי'?|סימן"
        reg_vav = u'ו{}'.format(reg_siman)
        for i, word in enumerate(str_list):
            if derabanan_flag:
                derabanan_flag = False
                resolved = self._tracker.resolve(book, [1])
                resolveds.append(resolved)
                continue
            elif re.search(reg_book, word):
                try:
                    if word != u'שם':
                        derabanan = filter(None, [item.strip() for item in re.split(u'(מד"ס|מ?דרבנן)',str_list[i+1].strip())])
                except IndexError:
                    mass.write_shgia('error smg, no place in book notation')
                    return
                if word == u'עשין' and len(derabanan) > 1:
                    book = re.search(u'[א-ה]',derabanan[1])
                    book = self._table[book.group(0)]
                    derabanan_flag = True
                elif re.match(reg_book, word):
                    book = self._table[word]
                else:
                    mass.write_shgia("error smg, don't recognize book name")
                    return
            else:
                mitzva = re.split('\s', word)
                for m in mitzva:
                    if re.search(reg_vav, m) and not book:
                        resolved = self._tracker.resolve(book, [None])
                        resolveds.append(resolved)
                    if m == u'שם':
                        m = None
                    elif re.search(reg_siman, m):
                        continue
                    elif getGematriaVav(m, mass):
                        m = getGematriaVav(m, mass)
                    else:
                        m = None
                    resolved = self._tracker.resolve(book, [m])
                    resolveds.append(resolved)
        if not resolveds:
            resolved = self._tracker.resolve(book, [None])
            resolveds.append(resolved)
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
                          u'א"ה': u'Shulchan Arukh, Even HaEzer',
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

    def check_uno(self, book, siman):
        # a list of all the simanim in the Shulchan Aruch that have only one Seif in them
        # todo: no need to create this static lists everytime meeting a seif, should go static, where?
        # todo: in the init of the tsh obj it will run every line... thats even more wastfull...
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
                  480, 482, 483, 484, 485, 486, 492, 596, 505, 656}
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

    def parse_tsh(self, str, mass, only_tur = False):
        ayyen = re.split(u''' ובהג"ה|ועיין|ועי'?|וע"ש''', str)
        if len(ayyen) > 1:
            str = ayyen[0]
        split = re.split('\s', str.strip())
        str_list = filter(None, split)
        # todo: not sure what i feel about these 2 lines...
        if not str_list:
            return
        str_it = iter(str_list[1:])
        reg_siman = u"סי'?|סימן"
        reg_seif = u'''סעיף|סעי?'?|ס([א-ת]?"[א-ת])'''
        reg_sham = u'שם'
        reg_combined = u'ס([א-ת]?"[א-ת])'
        reg_vav = u'ו({}|{}|{}|{})'.format(reg_seif, reg_siman, reg_sham, reg_combined)
        resolveds = []
        try:
            book = str_list[0]
            if re.search(reg_sham, book):
                book_sa = None
                if len(str_list) > 1 and re.search(reg_vav,str_list[1]):
                    resolveds.append(self._tracker_sa.resolve(book_sa, [None, None]))
                    resolveds.append(self._tracker_tur.resolve(self._tur_table[book_sa], [None]))
            elif self._sa_table.has_key(book):
                        book_sa = self._sa_table[book]
            elif re.search(reg_siman, book) or re.search(reg_seif, book):
                book_sa = None
                str_it = iter(str_list)
            else:
                mass.write_shgia(u"error tsh, don't recognize book name")
                return
            flag_next = False
            siman = None
            seif = None
            resolved_tur = None
            for word in str_it:
                to_res = False  # a flag to say there was found a citation we want to resolve
                if re.search(reg_siman, word) and not re.search(reg_seif, word):
                    to_res = True
                    siman = getGematriaVav(str_it.next(), mass)
                    hasnext = True
                    try:
                        next = str_it.next()
                    except StopIteration:
                        hasnext = False
                    if hasnext and (re.search(reg_seif,next) or re.search(reg_sham, next)):
                        if re.search(reg_combined, next):
                            combined = re.search(reg_combined, next)
                            seif = getGematriaVav(combined.group(1), mass)
                        elif re.search(reg_sham, next):
                            seif = None
                        else:
                            seif = getGematriaVav(str_it.next(), mass)
                    elif self.check_uno(book_sa, siman):
                        seif = 1
                    elif not only_tur:
                        mass.write_shgia(u'error tsh, missing seif')
                        if mass.error_flag:
                            mass.error_flag = [mass.error_flag, u'error tsh, missing seif']
                            print u'error tsh, missing seif'
                            return

                elif re.search(reg_seif, word):
                    to_res = True
                    if re.search(reg_combined, word):
                        combined = re.search(reg_combined, word)
                        seif = getGematriaVav(combined.group(1), mass)
                    else:
                        seif = getGematriaVav(str_it.next(), mass)
                elif len(word) <= 3:# todo: note: 3 is a bit long check that not getting gorbage, deleted: from line start re.match(u'''[א-ת]{1}''', word) and
                    if not re.search(reg_sham, word):
                        seif = getGematriaVav(word, mass)
                        to_res = True
                else:
                    getGematriaVav(word, mass)
                if to_res:
                    if only_tur:
                        resolved_tur = self.parse_tur(book_sa,siman)  # todo: note: might be an issue with None, None to this file
                        resolveds.extend(resolved_tur)
                    else:
                        resolved_sa = self._tracker_sa.resolve(book_sa, [siman, seif])
                        if resolved_tur != self._tracker_tur.resolve(self._tur_table[book_sa], [siman]): # self._tracker_tur._last_ref: #
                            resolved_tur = self._tracker_tur.resolve(self._tur_table[book_sa], [siman])
                            resolveds.append(resolved_tur)
                        resolveds.append(resolved_sa)
            if not resolveds:
                resolveds.append(self._tracker_sa.resolve(book_sa, [siman, seif]))
                #note: todo: fix! repeting code!!!
                if resolved_tur != self._tracker_tur._last_cit:  # self._tracker_tur.resolve(self._tur_table[book_sa], [siman]):
                    resolved_tur = self._tracker_tur.resolve(self._tur_table[book_sa], [siman])
                    resolveds.append(resolved_tur)
            return resolveds
        except KeyError:
            mass.write_shgia(u'error tsh, there is missing data where in the tur to look')
            return

    def parse_tur(self, book_sa = None, siman = None):
        if not book_sa:
            book_sa = self._tur_table[book_sa]
        resolved_tur = self._tracker_tur.resolve(self._tur_table[book_sa], [siman])
        return [resolved_tur]


class Rambam(object):
    """
    One instance per file (massekhet)
    """
    def __init__(self):
        self._tracker = BookIbidTracker()
        self._conv_table = rambam_name_table()

    def parse_rambam(self, str, mass): # these will be aoutomatic from the privates of the object (Rambam)
        re.sub(u'''יוה"כ''', u'יום הכיפורים', str)
        reg1 = u'''(מהל|מהלכות|מהל'|מהלכו'|מה')'''  # מהלכות before the book name
        reg21 = u''' ו?הלכה| ו?הל'?| ו?הלכ'?| ו?דין'''
        # reg22 = u''' ה"[א-ת]'''
        reg22 = u'''ו?הל?([א-ת]?"[א-ת])'''
        combi = re.search(reg22, str)

        reg2 = u'''({}|{}|שם)'''.format(reg21,reg22)  # before the halacha
        reg_double_cit = u''' (ופ'|ופ[א-ת]?"[א-ת]|ופרק)'''
        reg_for_book = ur'''{} (.+?){}'''.format(reg1,reg2)

        # check for multiple citation
        multiple = re.search(reg_double_cit, str)
        if multiple:
            mul = re.split(reg_double_cit, str, maxsplit=1)
            a = self.parse_rambam(mul[0], mass)
            b = self.parse_rambam(mul[1] + mul[2], mass)
            return a + b


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
                mass.error_flag = "error mim, couldn't find this book name in table"
                mass.write_shgia("error mim, couldn't find this book name in table" + book)
        # perek
        perek = re.search(u'''פרק ([א-ת]"?[א-ת]?)|פ([א-ת]?"[א-ת])|ופ' ([א-ת]"?[א-ת]?)''', str)
        if perek:
            perek = perek.group(1) or perek.group(2) or perek.group(3)
            perek = getGematriaVav(perek, mass)

        if combi:
            str = re.sub(reg22, u'הלכה {}'.format(ur'\1'), str)

        # halacha
        halacha = re.search(u'''{} (.+)'''.format(reg2), str) or re.search(u'''{}'''.format(reg22), str)
        if halacha:
            hal21 = re.search(u'''({}) (.*)'''.format(reg21), str)  # todo: important! befor it was .+ what did this change ruin
            hal22 = re.search(u'''הל?([א-ת]?"[א-ת])''', str)
            if hal21:
                halacha = hal21.group(2)
                if not halacha:
                    mass.write_shgia(u'error mim, No halacha stated')
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
            halacha = re.sub(reg2, u'', halacha)  # todo: double check that this is not killing anything
            halacha_split = re.split(u'''\sו?([א-ת]?"?[א-ת]'?)''', halacha.strip())
            halacha_split = filter(None, halacha_split)
            halacha = [getGematriaVav(i, mass) for i in halacha_split]
            resolved = [self._tracker.resolve(book, [perek, hal]) for hal in halacha]
            if len([item for item in resolved if not isinstance(item, Ref)]) > 0:
                mass.write_shgia(u'error from ibid in Ref or table none problem')
        else:  # halacha was sham
            if perek and book and not re.search(u'שם', str):
                mass.write_shgia('error mim, No halacha stated')
            resolved = self._tracker.resolve(book, [perek, halacha])

        if isinstance(resolved, list):
            return resolved
        else:
            return [resolved]


# note: should call this function only once in init
def rambam_name_table():
    names = library.get_indexes_in_category("Mishneh Torah")
    en_names = names
    he_raw = [library.get_index(name).all_titles('he')[0] for name in names]
    he_names = []
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
    name_dict[u'עכו"ם'] = name_dict[u'עבודה זרה וחוקות הגויים']
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
    name_dict[u'מטמא משכב ומושב'] = name_dict[u'מטמאי משכב ומושב']
    name_dict[u'משכב ומושב'] = name_dict[u'מטמאי משכב ומושב']
    name_dict[u'צרעת'] = name_dict[u'טומאת צרעת']
    # name_dict[u"שכני'"] = name_dict[u'שכנים']
    # name_dict[u"שכני"] = name_dict[u'שכנים']
    name_dict[u'ס"ת'] = name_dict[u'תפילין ומזוזה וספר תורה']
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
    name_dict[u'ביכורין'] = name_dict[u'ביכורים ושאר מתנות כהונה שבגבולין']
    name_dict[u'בכורים'] = name_dict[u'ביכורים ושאר מתנות כהונה שבגבולין']
    name_dict[u'זכיה ומתנה'] = name_dict[u'זכייה ומתנה']
    # name_dict[u"מכיר'"] = name_dict[u'מכירה']
    name_dict[u'שאר אבות הטומאה'] = name_dict[u'שאר אבות הטומאות']
    name_dict[u'מעשה קרבנות'] = name_dict[u'מעשה הקרבנות']
    name_dict[u'מעשה קרבן'] = name_dict[u'מעשה הקרבנות']
    name_dict[u'תענית'] = name_dict[u'תעניות']
    name_dict[u'מקוואות'] = name_dict[u'מקואות']
    name_dict[u'ערכין וחרמין'] = name_dict[u'ערכים וחרמין']
    name_dict[u'ערכין'] = name_dict[u'ערכים וחרמין']
    name_dict[u'שאלה ופקדון'] = name_dict[u'שאלה ופיקדון']
    name_dict[u"שאל' ופקדון"] = name_dict[u'שאלה ופיקדון']
    name_dict[u'פקדון'] = name_dict[u'שאלה ופיקדון']
    # name_dict[u'מעשר שני'] = name_dict[u'מעשר שני ונטע רבעי']
    name_dict[u'מ"ש ונטע רבעי'] = name_dict[u'מעשר שני ונטע רבעי']
    name_dict[u'מעשר שני ונ"ר'] = name_dict[u'מעשר שני ונטע רבעי']
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
    name_dict[u'אבדה'] = name_dict[u'גזילה ואבידה']
    name_dict[u'תמידין'] = name_dict[u'תמידים ומוספין']
    name_dict[u'תמידין ומוספין'] = name_dict[u'תמידים ומוספין']
    name_dict[u'איסורי מזבח'] = name_dict[u'איסורי המזבח']
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
    name_dict[u'מא"ס'] = name_dict[u'מאכלות אסורות']
    name_dict[u'אסורות'] = name_dict[u'מאכלות אסורות']
    # name_dict[u"ממרי'"] = name_dict[u'ממרים']
    # name_dict[u"שכירו'"] = name_dict[u'שכירות']
    name_dict[u"תרומה"] = name_dict[u'תרומות']
    # name_dict[u"סנהד'"] = name_dict[u'סנהדרין והעונשין המסורין להם']
    name_dict[u'ק"ש'] = name_dict[u'קריאת שמע']
    # name_dict[u'עבודת יה"כ'] = name_dict[u'עבודת יום הכפורים'] # because it makes problems with my code...can be fixed by taking it step by step
    name_dict[u'נ"כ'] = name_dict[u'תפילה וברכת כהנים']
    name_dict[u'נשיאות כפים'] = name_dict[u'תפילה וברכת כהנים']
    name_dict[u'נשיאת כפים'] = name_dict[u'תפילה וברכת כהנים']
    name_dict[u'חנוכה'] = name_dict[u'מגילה וחנוכה']
    name_dict[u'מצה'] = name_dict[u'חמץ ומצה']
    name_dict[u'גרושין'] = name_dict[u'גירושין']
    name_dict[u'נ"מ'] = name_dict[u'נזקי ממון']
    name_dict[u'פסולי מוקדשין'] = name_dict[u'פסולי המוקדשין']
    name_dict[u'פסולי המוקדשים'] = name_dict[u'פסולי המוקדשין']
    name_dict[u'ק"פ'] = name_dict[u'קרבן פסח']
    name_dict[u'רוצח וש"נ'] = name_dict[u'רוצח ושמירת נפש']
    name_dict[u'שמירת הנפש'] = name_dict[u'רוצח ושמירת נפש']

    # for name in name_dict.keys():
    #     first = re.split('\s', name)
    #     if len(first) > 1:
    #         name_dict[first[0]] = name_dict[name]
    # del name_dict[u'איסורי']
    # del name_dict[u'טומאת']
    name_dict[u'מעשר'] = name_dict[u'מעשרות']
    return name_dict


def clean_line(line):
    line = strip_nikkud(line)
    line = re.sub(u':', '', line)
    reg_parentheses = re.compile(u'\((.*?)\)')
    reg_brackets = re.compile(u'\[(.*?)\]')
    in_per = reg_parentheses.search(line)
    in_bra = reg_brackets.search(line)
    reg_ayyen_tur = re.compile(u'''ו?(עיין|עי'|ע"ש) בטור''')
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
def getGematriaVav(str, mass):
    str = str.strip()
    str = re.sub(u'''"|''', u'', str)
    case_set = {270,272,274,275,298,304,344,670,672,698,744} # from trello card 'Letter transpositions'
    if str[0] == u'ו' and (is_hebrew_number(str[1:]) or (getGematria(str[1:]) in case_set)):
        return getGematria(str[1:])
    elif is_hebrew_number(str) or getGematria(str) in case_set: # and not re.search(u'''מד"ס'''): or re.search(u'''('|")''', str)
        return getGematria(str)
    elif re.search(u'בהגהה?', str): # this is not gimatria but there is no need to send an error about it each time...
        return
    else:
        mass.write_shgia('error in pointer, not Gimatria...'+ str)
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


def toCSV(filename, obj_list):
    list_dict = obj_list
    with open(u'{}.csv'.format(filename), 'w') as csv_file:
        writer = csv.DictWriter(csv_file, [u'txt file line', u'Perek running counter',u'page running counter',
                                u'Perek aprx', u'Page aprx', u'Rambam', u'Semag', u'Tur Shulchan Arukh', u'original', u'problem']) #fieldnames = obj_list[0].keys())
        writer.writeheader()
        writer.writerows(list_dict)


def fromCSV(fromcsv, newfile):
    f = codecs.open(newfile, 'w', encoding = 'utf-8')
    with open(fromcsv, 'r') as csvfile:
        file_reader = csv.DictReader(csvfile)
        for i, row in enumerate(file_reader):
            f.write(row[u'original'].strip() + u'\n')


#  run to create csv for QA
def run1(massechet_he = None, massechet_en = None):
    parse1 = parse_em(u'{}.txt'.format(massechet_he), 1, u'{}_error'.format(massechet_en))  # reades from ביצה.txt to screen output
    toCSV(massechet_he, parse1)  # writes to ביצה.csv
    return parse1


#  run to create the csv after first run of QA to get talmud matching
def run2(massechet_he=None, massechet_en=None):
    fromCSV(u'{}.csv'.format(massechet_he), u'{}.txt'.format(massechet_en))  # reads from fixed ביצה.csv to egg.txt
    parse2 = parse_em(u'{}.txt'.format(massechet_en),2, u'{}_error'.format(massechet_en))  # egg.txt to screen output
    toCSV(u'{}_done'.format(massechet_en), parse2)  # write final to egg_done.csv
    return parse2

def run15(massechet_he=None, massechet_en=None):
    fromCSV(u'{}.csv'.format(massechet_he), u'{}.txt'.format(massechet_he))  # reads from fixed ביצה.csv to egg.txt
    parse1 = parse_em(u'{}.txt'.format(massechet_he),1, u'{}_error'.format(massechet_en))  # egg.txt to screen output
    toCSV(u'{}1'.format(massechet_he), parse1)
    return parse1

def last_algo_run(withSegments, parsedData):
    pass


def write_errfile(filename):
    error = codecs.open(u'error_{}.txt'.format(filename), 'w', encoding = 'utf-8')
    with codecs.open(u'error_main.txt', 'r', 'utf-8') as fp:
        lines = fp.readlines()
        # it = iter(lines)
        e = enumerate(lines)
        for i, line in e:
            if re.search(u'error', line):
                j, k = i, i
                while not re.search(u'.txt', lines[j]):
                    j -= 1
                while (j < i):
                    error.write(lines[j])
                    j+=1
                while not re.search(u'.txt', lines[k]):
                    error.write(lines[k])
                    k+=1
                    e.next()

# from csv to txt
def reverse_collapse(fromcsv, collapsed_file):
    f = codecs.open(u'{}.txt'.format(collapsed_file), 'w', encoding='utf-8')
    with open(fromcsv, 'r') as csvfile:
        file_reader = csv.DictReader(csvfile)
        prev = None
        for i, row in enumerate(file_reader):
            if prev != (row[u'original'].strip() + u'\n'):
                f.write(row[u'original'].strip() + u'\n')
            prev = (row[u'original'].strip() + u'\n')
    run1(u'{}'.format(collapsed_file),u'{}'.format(collapsed_file))

def segment_column(segmentfile, reffile, massekhet):
    final_list = []
    with open(segmentfile, 'r') as csvfile:
        seg_reader = csv.DictReader(csvfile)
        with open(reffile, 'r') as csvfile:
            ref_reader = csv.DictReader(csvfile)
            for segrow, refrow in zip(seg_reader, ref_reader):
                letter_dict = {u'Segment': u'{}.{}.{}'.format(massekhet, segrow[u'Daf'],segrow[u'Line']),
                              u'Rambam': refrow[u'Rambam'],
                              u'Semag': refrow[u'Semag'],
                              u'Tur Shulchan Arukh':refrow[u'Tur Shulchan Arukh']}
                final_list.append(letter_dict)
    return final_list

if __name__ == "__main__":
    # test = parse_em('test.txt')
    # filenames_he = [u'בבא מציעא', u'בבא בתרא', u'ראש השנה', u'ברכות', u'גיטין',  u'יבמות', u'יומא',
    #              u'כתובות', u'מועד קטן',  u'נדרים',   u'סנהדרין', u'עירובין', u'פסחים',
    #              u'קידושין',u'ראש השנה', u'שבועות', u'שבת']  #
    # filenames_he = [u'נזיר', u'ביצה', u'סוכה',u'מכות',u'סוטה']
    # filenames_eg = [u'bm', u'bb', u'rh',  u'brachot', u'gittin',  u'yevamot', u'yoma',
    #              u'ktobot', u'moed',  u'nedarim', u'sanhedrim', u'eruvin', u'pesachim',
    #              u'kidushin',u'rh', u'shvuot', u'shabbat']  # u'nazir', u'egg', u'hagiga', u'sukka', u'makot', u'sota'
    # filenames_eg = [u'nazir', u'beitza', u'sukka', u'makot', u'sota']
    # for m_en, m_he in zip(filenames_eg, filenames_he):
    #     parsed = run15(massechet_he=m_he, massechet_en= m_en)
        # parsed = run2(massechet_he=m_he, massechet_en= m_en)
    # parsed = run2(massechet_he=u'מועד קטן', massechet_en= u'mk_test')
    # test = run2(massechet_he=u'Ein Mishpat - Moed Katan.csv', massechet_en=u'mk - test')

    # # final lines to get a dict
    # reverse_collapse(u'hagiga_done.csv', u'hagiga_collapsed')
    # parsed = run2(massechet_he=u'hagiga_collapsed', massechet_en=u'hg_test')
    # reverse_collapse(u'hagiga_done.csv', u'hagiga_collapsed')
    # parsed = run2(massechet_he=u'hagiga_collapsed', massechet_en=u'hg_test')
    final_list = segment_column('Ein Mishpat - Moed Katan.csv', 'mk_test_done.csv','Moed_Katan')
    print 'done'