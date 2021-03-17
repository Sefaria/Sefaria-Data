# -*- coding: utf-8 -*-

import django
django.setup()
from sefaria.model import *
import codecs
import regex as re
import pygtrie
from data_utilities.util import getGematria, multiple_replace
from data_utilities.ibid import BookIbidTracker, IbidKeyNotFoundException, IbidRefException
from sefaria.utils.hebrew import strip_nikkud
# import unicodecsv as csv
import csv
import os
import pickle

Rif = True

class Massekhet(object):

    def __init__(self,errorfilename):
        self.ErrorFile = codecs.open(errorfilename, 'w', encoding='utf-8')
        self.test = None
        self.error_flag = False
        self.line_num = 0

    def write_shgia(self, txt):
        self.error_flag = txt
        self.ErrorFile.write(str(self.line_num) + ': ' + txt + '\n')
        print(self.line_num, txt)


def resolveExceptin(tr,book, sectionList):
    '''
    This method is refactoring in the raise of Exception written in ibid (instead of print out)
    :param tr: the BookIbidTracker reffered to for this original resolve
    :param book: book name needed for the resolve function
    :param sectionList: sections list needed for the resolve function
    :return: the line ibid.py returned before the Exceptions refactor
    '''
    try:
        return tr.resolve(book, sectionList)
    except IbidKeyNotFoundException:
        return "error, couldn't find this key"
    except IbidRefException:
        return "problem with the Ref iteslf. {}.{}"


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
                'txt file line': self._file_line,
                'Perek running counter': self._perek_counter,
                'page running counter': self._page_counter[i],
                'Perek aprx': self._perek,
                'Page aprx': self._page,
                'Rambam': self._mimon,
                'Semag': self._semag,
                'Tur Shulchan Arukh': self._tsh,
                'original': self._original,
                'problem': None
                }
        except IndexError:
            dict = {
                'txt file line': self._file_line,
                'Perek running counter': self._perek_counter,
                'page running counter':None,
                'Perek aprx': self._perek,
                'Page aprx': self._page,
                'Rambam': self._mimon,
                'Semag': self._semag,
                'Tur Shulchan Arukh': self._tsh,
                'original': self._original,
                'problem': 'error missing little or big letter'
            }
            print('error missing little or big letter')
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


def parse_em(filename, passing, errorfilename, EM = True, em_list=False):
    mass = Massekhet(errorfilename)
    i = 0
    perek = 0
    page = 0
    mishneh = Rambam()  # we parse per file and create a mishne torah (Rambam) obj per file
    smg = Semag()
    tursh = TurSh()
    cit_dictionary = []
    if em_list:
        pre_lines = em_list
    else:
        with codecs.open(filename, 'r', 'utf-8') as fp:
            pre_lines = fp.readlines()
    # pattern = r'''(ו?שו?["\u05f4]ע|ו?ב?מיי['\u05f3]|ו?ב?סמ"?ג|ו?ב?טוש["\u05f4]ע|ו?ב?טור)'''
    pattern = r'''(ו?שו?["\u05f4]ע|ו?ב?מיי['\u05f3]|ו?ב?סמ"?ג|ו?ב?טוש["\u05f4]ע|ו?ב?טור|ו?ה?רמב"ם|@11)'''
    if EM == 'Rif':
        lines = []
        previous = ''
        for pl in pre_lines:
            if not pl:
                continue
            if len(pl) <= 2:
                continue
            if re.match('@11', pl):
                previous = pl
            elif not re.match('.*[:.][\s\n]*?$', pl):
                previous = previous + pl
            else:
                line = previous + pl if previous.strip() != pl.strip() else pl
                lines.append(line.replace('\n', ' '))
                previous = ''
    else:
        lines = pre_lines

    for line in lines:
        mass.error_flag = False
        i += 1
        print(i, filename)
        print(line)
        mass.line_num = i
        line = clean_line(line.strip())
        if not line:  # ignore empty lines
            continue
        cit = EM_Citation(filename, i, line)
        # flags
        split = re.split(pattern, line)
        if EM:
            sub_s = re.split('\s', split[0].strip())
            # set the counters
            cit._perek_counter = sub_s[0]
            cit._page_counter = sub_s[1:]  # since the page counters can be a list of letters
            try:
                perek_c = getGematria(cit._perek_counter)
                # check_continues
                if perek_c == 1:
                    perek += 1
                    page = 0
                elif perek_c-1 != getGematria(cit_dictionary[-1]['Perek running counter']) and cit_dictionary[-1]['problem'] != 'error, cit with the perek/page counters':
                    mass.write_shgia('error, cit with the perek/page counters')

                cit._perek = perek
                if (not cit._page_counter) or (cit._page_counter[0] == 'א'):
                    page += 1
                cit._page = page
                if list(filter(lambda x: len(x) > 3 or re.search('שם',x), cit._page_counter)):
                    mass.write_shgia('error, missing an indicator')

            except:
                mass.write_shgia('error, cit with the perek/page counters')
            # start the parsing
        else:
            counters_split = re.split('\s', split[0])
            cit._perek_counter = counters_split[0]
            cit._page_counter = counters_split[1]
        split_it = iter(split)
        for part in split_it:
            if re.search(r'''(מיי'|ו?רמב"ם)''', part):
                rambam_cit = next(split_it)
                cit.check_double('_mimon', mishneh.parse_rambam(rambam_cit, mass)) #cit._mimon = mishneh.parse_rambam(rambam_cit)
            elif re.search('ו?סמ"?ג',part):
                semag_cit = next(split_it)
                cit.check_double('_semag', smg.parse_semag(semag_cit, mass))  # cit._semag = smg.parse_semag(semag_cit)
            elif re.search('ו?טוש"ע|ש"ע|שו"ע', part):
                    tsh_cit = next(split_it)
                    cit.check_double('_tsh', tursh.parse_tsh(tsh_cit, mass))  # tursh.parse_tsh(tsh_cit)
            elif re.search(r'טור', part):
                next_part = next(split_it)
                # if next_part == r'שו?"ע':
                #     tsh_cit = next(split_it)
                #     cit._tsh = tursh.parse_tsh(tsh_cit, mass)
                # else:# basically assuming there isn't SA citation here
                #     tsh_cit = next_part
                #     cit.check_double('_tsh', tursh.parse_tsh(tsh_cit, mass, only_tur = True))#cit._tsh = tursh.parse_tsh(tsh_cit, only_tur = True)
                tsh_cit = next_part
                cit.check_double('_tsh', tursh.parse_tsh(tsh_cit, mass, only_tur=True))  # cit._tsh = tursh.parse_tsh(tsh_cit, only_tur = True)
        cit_dictionary.extend(cit.obj2dict(passing))
        if cit_dictionary[-1]['problem'] != 'error missing little or big letter' and cit_dictionary[-1]['problem'] != 'error, cit with the perek/page counters':
            cit_dictionary[-1]['problem'] = mass.error_flag
        print(cit_dictionary[-1])
    return cit_dictionary


class Semag(object):
    """
    One instance per file (massekhet)
    """
    def __init__(self):
        self._tracker = BookIbidTracker()
        self._table = {
            'שם': None,
            'לאוין': 'Sefer Mitzvot Gadol, Negative Commandments',
            'לאין': 'Sefer Mitzvot Gadol, Negative Commandments',
            'עשין': 'Sefer Mitzvot Gadol, Positive Commandments',
            'א':'Sefer Mitzvot Gadol, Rabbinic Commandments, Laws of Eruvin',
            'ב': 'Sefer Mitzvot Gadol, Rabbinic Commandments, Laws of Mourning',
            'ג': "Sefer Mitzvot Gadol, Rabbinic Commandments, Laws of Tisha B'Av",
            'ד': 'Sefer Mitzvot Gadol, Rabbinic Commandments, Laws of Megillah',
            'ה': 'Sefer Mitzvot Gadol, Rabbinic Commandments, Laws of Chanukah'
                       }

        # self._table = {
        #     'שם': None,
        #     'לאוין': 'Sefer Mitzvot Gadol, Volume One ',
        #     'לאין': 'Sefer Mitzvot Gadol, Volume One ',
        #     'עשין': 'Sefer Mitzvot Gadol, Volume Two ',
        #     'א': 'Sefer Mitzvot Gadol, Volume Two, Laws of Eruvin ',
        #     'ב': 'Sefer Mitzvot Gadol, Volume Two, Laws of Mourning ',
        #     'ג': "Sefer Mitzvot Gadol, Volume Two, Laws of Tisha B'Av ",
        #     'ד': 'Sefer Mitzvot Gadol, Volume Two, Laws of Megillah ',
        #     'ה': 'Sefer Mitzvot Gadol, Volume Two, Laws of Chanukah '
        #                }


    def parse_semag(self, str, mass):
        reg_book = re.compile('ו?ב?(עשין|שם|לאוין|לאין)')
        split = re.split(reg_book, str.strip())
        str_list = list(filter(None, [item.strip() for item in split]))
        resolveds = []
        derabanan_flag = False
        book = None
        reg_siman = "סי'?|סימן"
        reg_vav = 'ו{}'.format(reg_siman)
        for i, word in enumerate(str_list):
            if derabanan_flag:
                derabanan_flag = False
                # resolved = self._tracker.resolve(book, [1])
                resolved = resolveExceptin(self._tracker, book, [1])
                resolveds.append(resolved)
                continue
            elif re.search(reg_book, word):
                try:
                    if word != 'שם':
                        derabanan = list(filter(None, [item.strip() for item in re.split('(מד"ס|מ?דרבנן)',str_list[i+1].strip())]))
                except IndexError:
                    mass.write_shgia('error smg, no place in book notation')
                    return
                if word == 'עשין' and len(derabanan) > 1:
                    book = re.search('[א-ה]',derabanan[1])
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
                        # resolved = self._tracker.resolve(book, [None])
                        resolved = resolveExceptin(self._tracker, book, [None])
                        resolveds.append(resolved)

                    if m == 'ו?שם':
                        m = None
                    elif re.search(reg_siman, m):
                        continue
                    elif getGematriaVav(m, mass):
                        m = getGematriaVav(m, mass)
                    else:
                        m = None
                    # resolved = self._tracker.resolve(book, [m])
                    resolved = resolveExceptin(self._tracker, book, [m])
                    resolveds.append(resolved)
        if not resolveds:
            # resolved = self._tracker.resolve(book, [None])
            resolved = resolveExceptin(self._tracker, book, [None])

            resolveds.append(resolved)
        if len([item for item in resolveds if not isinstance(item, Ref)]) > 0:
            mass.write_shgia('error from ibid in Ref or table none problem')
        return resolveds


class TurSh(object):
    """
    One instance per file (massekhet)
    """
    def __init__(self):
        self._tracker_sa = BookIbidTracker()
        self._tracker_tur = BookIbidTracker()
        self._sa_table = {'ח"מ': 'Shulchan Arukh, Choshen Mishpat',
                          'חו"מ': 'Shulchan Arukh, Choshen Mishpat',
                          'אה"ע': 'Shulchan Arukh, Even HaEzer',
                          'א"ה': 'Shulchan Arukh, Even HaEzer',
                          'י"ד': "Shulchan Arukh, Yoreh De'ah",
                          'יד': "Shulchan Arukh, Yoreh De'ah",
                          'יו"ד': "Shulchan Arukh, Yoreh De'ah",
                          'או"ח': 'Shulchan Arukh, Orach Chayim',
                          'א"ח': 'Shulchan Arukh, Orach Chayim'
                       }
        self._tur_table = {
            None: None,
            'Shulchan Arukh, Choshen Mishpat': 'Tur, Choshen Mishpat',
            'Shulchan Arukh, Even HaEzer': 'Tur, Even HaEzer',
            "Shulchan Arukh, Yoreh De'ah": 'Tur, Yoreh Deah',
            'Shulchan Arukh, Orach Chayim': 'Tur, Orach Chaim'
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
                  133, 136, 138, 654, 655, 657, 659, 148, 149, 152, 666, 667, 156, 157, 166, 679, 683, 176, 697, 198,
                  207, 214, 598, 226, 231, 237, 241, 242, 256, 258, 556, 642, 278, 281, 283, 287, 300, 564, 342,
                  343, 347, 348, 351, 359, 367, 369, 373, 377, 383, 387, 388, 389, 395, 678, 400, 402, 403, 404,
                  406, 411, 412, 413, 417, 419, 421, 424, 427, 430, 669, 435, 449, 458, 464, 661, 469, 474, 479,
                  480, 482, 483, 484, 485, 486, 492, 596, 505, 656}
        uno_eh = {84, 72, 14, 18, 51, 52, 54, 151, 24, 57, 60, 153}
        if book == 'Shulchan Arukh, Choshen Mishpat' and siman in uno_hm:
            return True
        elif book == 'Shulchan Arukh, Even HaEzer' and siman in uno_eh:
            return True
        elif book == "Shulchan Arukh, Yoreh De'ah" and siman in uno_yd:
            return True
        elif book == 'Shulchan Arukh, Orach Chayim' and siman in uno_oc:
            return True
        return False

    def parse_tsh(self, str, mass, only_tur = False):
        ayyen = re.split(''' ובהג"ה|ועיין|ועי'?|וע"ש''', str)
        if len(ayyen) > 1:
            str = ayyen[0]
        split = re.split('\s', str.strip())
        str_list = list(filter(None, split))
        # todo: not sure what i feel about these 2 lines...
        if not str_list:
            return
        str_it = iter(str_list[1:])
        reg_siman = "סי'?|סימן"
        reg_seif = '''סעיף|סעי?'?|ס([א-ת]?"[א-ת])'''
        reg_sham = 'ו?שם'
        reg_combined = 'ס([א-ת]?"[א-ת])'
        reg_vav = 'ו({}|{}|{}|{})'.format(reg_seif, reg_siman, reg_sham, reg_combined)
        resolveds = []
        try:
            book = str_list[0]
            if re.search(reg_sham, book):
                book_sa = None
                if len(str_list) > 1 and re.search(reg_vav,str_list[1]):
                    # resolveds.append(self._tracker_sa.resolve(book_sa, [None, None]))
                    resolveds.append(resolveExceptin(self._tracker_sa, book_sa, [None, None]))
                    # resolveds.append(self._tracker_tur.resolve(self._tur_table[book_sa], [None]))
                    resolveds.append(resolveExceptin(self._tracker_tur, self._tur_table[book_sa], [None]))
            elif self._sa_table.get(book, None):
                        book_sa = self._sa_table[book]
            elif re.search(reg_siman, book) or re.search(reg_seif, book):
                book_sa = None
                str_it = iter(str_list)
            else:
                mass.write_shgia("error tsh, don't recognize book name")
                return
            flag_next = False
            gim = False
            siman = None
            seif = None
            resolved_tur = None
            hasnext = False
            for word in str_it:
                to_res = False  # a flag to say there was found a citation we want to resolve
                if re.search(reg_vav, word): # note: repeating code from lines at the end. should be a seprate function?
                    # resolved_sa = self._tracker_sa.resolve(book_sa, [siman, seif])
                    resolved_sa = resolveExceptin(self._tracker_sa , book_sa, [siman, seif])
                    # if resolved_tur != self._tracker_tur.resolve(self._tur_table[book_sa],
                    #                                              [siman]):  # self._tracker_tur._last_ref:
                    if resolved_tur != resolveExceptin(self._tracker_tur, self._tur_table[book_sa],[siman]):
                        # resolved_tur = self._tracker_tur.resolve(self._tur_table[book_sa], [siman])
                        resolved_tur = resolveExceptin(self._tracker_tur,self._tur_table[book_sa], [siman])
                        resolveds.append(resolved_tur)
                    resolveds.append(resolved_sa)
                if re.search(reg_siman, word) and not re.search(reg_seif, word):
                    to_res = True
                    siman = getGematriaVav(next(str_it), mass)
                    hasnext = True
                    try:
                        next_part = next(str_it)
                    except StopIteration:
                        hasnext = False
                    if hasnext and (re.search(reg_seif, next_part) or re.search(reg_sham, next_part)):
                        if re.search(reg_combined, next_part):
                            combined = re.search(reg_combined, next_part)
                            seif = getGematriaVav(combined.group(1), mass)
                        elif re.search(reg_sham, next_part):
                            seif = None
                        else:
                            seif = getGematriaVav(next(str_it), mass)
                    elif self.check_uno(book_sa, siman):
                        seif = 1
                    elif not only_tur:
                        mass.write_shgia('error tsh, missing seif')
                        if mass.error_flag:
                            mass.error_flag = [mass.error_flag, 'error tsh, missing seif']
                            print('error tsh, missing seif')
                            return
                elif re.search(reg_seif, word):
                    to_res = True
                    if re.search(reg_combined, word):
                        combined = re.search(reg_combined, word)
                        seif = getGematriaVav(combined.group(1), mass)
                    else:
                        seif = getGematriaVav(next(str_it), mass)
                elif len(word) <= 3:# todo: note: 3 is a bit long check that not getting gorbage, deleted: from line start re.match('''[א-ת]{1}''', word) and
                    if not re.search(reg_sham, word) and not only_tur:
                        seif = getGematriaVav(word, mass)
                        to_res = True
                    elif only_tur:
                        gim = getGematriaVav(word, mass)
                        resolved_tur = self.parse_tur(book_sa, gim)
                        resolveds.extend(resolved_tur)
                else:
                    getGematriaVav(word, mass)
                if to_res:
                    if only_tur:
                        resolved_tur = self.parse_tur(book_sa,siman)  # todo: note: might be an issue with None, None to this file
                        resolveds.extend(resolved_tur)
                        if hasnext:
                            resolved_tur = self.parse_tur(book_sa,getGematriaVav(next_part, mass))  # todo: note: might be an issue with None, None to this file
                            resolveds.extend(resolved_tur)
                    else:
                        # resolved_sa = self._tracker_sa.resolve(book_sa, [siman, seif])
                        resolved_sa = resolveExceptin(self._tracker_sa, book_sa, [siman, seif])
                        # if resolved_tur != self._tracker_tur.resolve(self._tur_table[book_sa], [siman]): # self._tracker_tur._last_ref: #
                        #     resolved_tur = self._tracker_tur.resolve(self._tur_table[book_sa], [siman])
                        #     resolveds.append(resolved_tur)
                        if resolved_tur != resolveExceptin(self._tracker_tur, self._tur_table[book_sa], [siman]): # self._tracker_tur._last_ref: #
                            resolved_tur = resolveExceptin(self._tracker_tur, self._tur_table[book_sa], [siman])
                            resolveds.append(resolved_tur)
                        resolveds.append(resolved_sa)
            if not resolveds:
                # resolveds.append(self._tracker_sa.resolve(book_sa, [siman, seif]))
                resolveds.append(resolveExceptin(self._tracker_sa, book_sa, [siman, seif]))
                #note: todo: fix! repeting code!!!
                if resolved_tur != self._tracker_tur._last_cit:  # self._tracker_tur.resolve(self._tur_table[book_sa], [siman]):
                    # resolved_tur = self._tracker_tur.resolve(self._tur_table[book_sa], [siman])
                    resolved_tur = resolveExceptin(self._tracker_tur, self._tur_table[book_sa], [siman])
                    resolveds.append(resolved_tur)
            if len([item for item in resolveds if not isinstance(item, Ref)]) > 0:
                mass.write_shgia('error from ibid in Ref or table none problem')
            return resolveds
        except KeyError:
            mass.write_shgia('error tsh, there is missing data where in the tur to look')
            return

    def parse_tur(self, book_sa = None, siman = None):
        if not book_sa:
            book_sa = self._tur_table[book_sa]
        # resolved_tur = self._tracker_tur.resolve(self._tur_table[book_sa], [siman])
        resolved_tur = resolveExceptin(self._tracker_tur, self._tur_table[book_sa], [siman])

        return [resolved_tur]


class Rambam(object):
    """
    One instance per file (massekhet)
    """
    def __init__(self):
        self._tracker = BookIbidTracker()
        self._conv_table = rambam_name_table()

    def parse_rambam(self, str, mass): # these will be aoutomatic from the privates of the object (Rambam)
        str = re.sub('''יוה"כ''', 'יום הכפורים', str)
        reg1 = '''(מהל|מהלכות|מהל'|מהלכו?'|מה')'''  # מהלכות before the book name
        reg21 = ''' ו?הלכה| ו?הל'?| ו?הלכ'?| ו?דין'''
        # reg22 = ''' ה"[א-ת]'''
        reg22 = '''ו?הל?([א-ת]?"[א-ת])'''
        combi = re.search(reg22, str)

        reg2 = '''({}|{}|ו?שם)'''.format(reg21,reg22)  # before the halacha
        reg_double_cit = ''' (ופ'|ופ[א-ת]?"[א-ת]|ופרק|ושם)'''
        reg_for_book = r'''{} (.+?){}'''.format(reg1,reg2)

        # check for multiple citation
        multiple = re.search(reg_double_cit, str)
        if multiple:
            mul = re.split(reg_double_cit, str, maxsplit=1)
            a = self.parse_rambam(mul[0], mass)
            b = self.parse_rambam(mul[1] + mul[2], mass)
            return a + b


        # book
        if not re.search(reg2, str):
            reg_for_book = r'''{} (.+)'''.format(reg1)
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
                print("error mim, couldn't find this book name in table", book)
                mass.error_flag = "error mim, couldn't find this book name in table"
                mass.write_shgia("error mim, couldn't find this book name in table" + book)
        # perek
        perek = re.search('''פרק ([א-ת]"?[א-ת]?)|פ ?([א-ת]?"[א-ת])|ו?פ' ([א-ת]"?[א-ת])''', str) #'''פרק ([א-ת]"?[א-ת]?)|פ([א-ת]?"[א-ת])|ו?פ' ([א-ת]"?[א-ת]?)'''
        if perek:
            perek = perek.group(1) or perek.group(2) or perek.group(3)
            perek = getGematriaVav(perek, mass)

        if combi:
            str = re.sub(reg22, 'הלכה {}'.format(r'\1'), str)

        # halacha
        halacha = re.search('''{} (.+)'''.format(reg2), str) or re.search('''{}'''.format(reg22), str)
        if halacha:
            hal21 = re.search('''({}) (.*)'''.format(reg21), str)  # todo: important! befor it was .+ what did this change ruin
            hal22 = re.search('''הל?([א-ת]?"[א-ת])''', str)
            if hal21:
                halacha = hal21.group(2)
                if not halacha:
                    mass.write_shgia('error mim, No halacha stated')
            elif hal22:
                halacha = hal22.group(1)
            elif re.search('ו?שם', str):
                halacha = None
            # else:
            #     print 'error mim, No halcha stated'
            #     return

        # clean halacha
        if halacha:
            ayyen = re.split('''ועיין|ועי'?|וע"ש''', halacha)
            if len(ayyen)>1:
                halacha = ayyen[0]
            halacha = re.sub(reg2, '', halacha)  # todo: double check that this is not killing anything
            halacha_split = re.split('''\sו?([א-ת]?"?[א-ת]'?)''', halacha.strip())
            halacha_split = list(filter(None, halacha_split))
            halacha = [getGematriaVav(i, mass) for i in halacha_split]
            # resolved = [self._tracker.resolve(book, [perek, hal]) for hal in halacha]
            resolved = [resolveExceptin(self._tracker, book, [perek, hal]) for hal in halacha]
            if len([item for item in resolved if not isinstance(item, Ref)]) > 0:
                mass.write_shgia('error from ibid in Ref or table none problem')
        else:  # halacha was sham
            if perek and book and not re.search('ו?שם', str):
                mass.write_shgia('error mim, No halacha stated')
            # resolved = self._tracker.resolve(book, [perek, halacha])
            if Rif:
                resolved = resolveExceptin(self._tracker, book, [perek])
            else:
                resolved = resolveExceptin(self._tracker, book, [perek, halacha])


        if isinstance(resolved, list):
            return resolved
        else:
            return [resolved]


# note: should call this function only once in init
def rambam_name_table():
    names = library.get_indexes_in_category("Mishneh Torah")
    en_names = names
    he_raw = [library.get_index(name).get_title('he') for name in names]
    he_names = []
    name_dict = pygtrie.CharTrie()
    for he, en in zip(he_raw, en_names):
        s = re.split('''(?:הלכות|הלכה|הל'|הלכ)\s''', he)
        if len(s) > 1:
            he = s[1]
            he_names.append(he)
            name_dict[he] = en
    name_dict['מלוה'] = name_dict['מלווה ולווה']
    name_dict['מלוה ולוה'] = name_dict['מלווה ולווה']
    name_dict['מלוה ולווה'] = name_dict['מלווה ולווה']
    name_dict['תפלה'] = name_dict['תפילה וברכת כהנים']
    name_dict['יו"ט'] = name_dict['שביתת יום טוב']
    name_dict['י"ט'] = name_dict['שביתת יום טוב']
    name_dict['יום טוב'] = name_dict['שביתת יום טוב']
    name_dict['ת"ת'] = name_dict['תלמוד תורה']
    name_dict['ע"ז']  = name_dict['עבודה זרה וחוקות הגויים']
    name_dict['עכו"ם'] = name_dict['עבודה זרה וחוקות הגויים']
    name_dict['ע"ג'] = name_dict['עבודה זרה וחוקות הגויים']
    name_dict['עו"ג'] = name_dict['עבודה זרה וחוקות הגויים']
    # name_dict['עבודה זרה'] = name_dict['עבודה זרה וחוקות הגויים']
    name_dict['עבודת כוכבים'] = name_dict['עבודה זרה וחוקות הגויים']
    name_dict['אבות הטומאה'] = name_dict['שאר אבות הטומאות']
    name_dict['שאר אבות הטומאה'] = name_dict['שאר אבות הטומאות']
    name_dict['שאר אבות הטומאות'] = name_dict['שאר אבות הטומאות']
    name_dict['אבות הטומאות'] = name_dict['שאר אבות הטומאות']
    name_dict['שאר א"ה'] = name_dict['שאר אבות הטומאות']
    name_dict['טומאת משכב ומושב'] = name_dict['מטמאי משכב ומושב']
    name_dict['מטמא משכב ומושב'] = name_dict['מטמאי משכב ומושב']
    name_dict['משכב ומושב'] = name_dict['מטמאי משכב ומושב']
    name_dict['צרעת'] = name_dict['טומאת צרעת']
    # name_dict["שכני'"] = name_dict['שכנים']
    # name_dict["שכני"] = name_dict['שכנים']
    name_dict['ס"ת'] = name_dict['תפילין ומזוזה וספר תורה']
    # name_dict['ציצית'] = name_dict['תפילין ומזוזה וספר תורה']
    name_dict['ס"ת ומזוזה'] = name_dict['תפילין ומזוזה וספר תורה']
    name_dict['ספר תורה'] = name_dict['תפילין ומזוזה וספר תורה']
    name_dict['מזוזה'] = name_dict['תפילין ומזוזה וספר תורה']
    name_dict['תפלין'] = name_dict['תפילין ומזוזה וספר תורה']
    name_dict['תפילין וס"ת'] = name_dict['תפילין ומזוזה וספר תורה']
    name_dict['אבידה'] = name_dict['גזילה ואבידה']
    name_dict['גנבה'] = name_dict['גניבה']
    # name_dict['שמיטין'] = name_dict['שמיטה ויובל']
    name_dict['שמיטין ויובל'] = name_dict['שמיטה ויובל']
    name_dict['שמיטה ויובלות'] = name_dict['שמיטה ויובל']
    name_dict['שמיטין ויובלות'] = name_dict['שמיטה ויובל']
    name_dict['שמטה ויובל'] = name_dict['שמיטה ויובל']
    name_dict['יובל'] = name_dict['שמיטה ויובל']
    name_dict['ביכורין'] = name_dict['ביכורים ושאר מתנות כהונה שבגבולין']
    name_dict['בכורים'] = name_dict['ביכורים ושאר מתנות כהונה שבגבולין']
    name_dict['זכיה ומתנה'] = name_dict['זכייה ומתנה']
    # name_dict["מכיר'"] = name_dict['מכירה']
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
    # name_dict['מעשר שני'] = name_dict['מעשר שני ונטע רבעי']
    name_dict['מ"ש ונטע רבעי'] = name_dict['מעשר שני ונטע רבעי']
    name_dict['מעשר שני ונ"ר'] = name_dict['מעשר שני ונטע רבעי']
    # name_dict['מע"ש'] = name_dict['מעשר שני ונטע רבעי'] # is this right? קכא ג מיי׳ פ״ה מהל׳ אישות הל׳ ה ופ״ג מהל׳ מע״ש הל׳ יז (ב"ק 112)
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
    name_dict['אבדה'] = name_dict['גזילה ואבידה']
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
    # name_dict['כלי המקדש'] = name_dict['כלי המקדש והעובדין בו']
    name_dict['ביאת המקדש'] = name_dict['ביאת מקדש']
    name_dict['מ"א'] = name_dict['מאכלות אסורות']
    name_dict['מא"ס'] = name_dict['מאכלות אסורות']
    name_dict['אסורות'] = name_dict['מאכלות אסורות']
    # name_dict["ממרי'"] = name_dict['ממרים']
    # name_dict["שכירו'"] = name_dict['שכירות']
    name_dict["תרומה"] = name_dict['תרומות']
    # name_dict["סנהד'"] = name_dict['סנהדרין והעונשין המסורין להם']
    name_dict['ק"ש'] = name_dict['קריאת שמע']
    name_dict['יום הכפורים'] = name_dict['עבודת יום הכפורים'] # because it makes problems with my code...can be fixed by taking it step by step
    name_dict['נ"כ'] = name_dict['תפילה וברכת כהנים']
    name_dict['נשיאות כפים'] = name_dict['תפילה וברכת כהנים']
    name_dict['נשיאת כפים'] = name_dict['תפילה וברכת כהנים']
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
    name_dict['שמירת הנפש'] = name_dict['רוצח ושמירת נפש']
    name_dict['יבום'] = name_dict['יבום וחליצה']
    name_dict['חליצה'] = name_dict['יבום וחליצה']

    # for name in name_dict.keys():
    #     first = re.split('\s', name)
    #     if len(first) > 1:
    #         name_dict[first[0]] = name_dict[name]
    # del name_dict['איסורי']
    # del name_dict['טומאת']
    name_dict['מעשר'] = name_dict['מעשרות']
    return name_dict


def clean_line(line):
    line = strip_nikkud(line)
    replace_dict = {'[.:\?]': '', '[”״]': '"', '[’׳]': "'"} #note put \. in the file/ how can i check if it is right?
    line = multiple_replace(line, replace_dict, using_regex=True)
    # line = re.sub('[:\?]', '', line)
    # line = re.sub('”', '"', line)
    reg_parentheses = re.compile('\((.*?)\)')
    reg_brackets = re.compile('\[(.*?)\]')
    in_per = reg_parentheses.search(line)
    in_bra = reg_brackets.search(line)
    reg_ayyen_tur = re.compile('''ו?(עיין|עי'|ע"ש) בטור''')
    reg_lo_manu = re.compile('''(?P<a>(\u05d0\u05da )?\u05dc\u05d0 \u05de\u05e0(.*?))(\u05e1\u05de"?\u05d2|\u05e8\u05de\u05d1"?\u05dd|\u05d8\u05d5\u05e8|\n)''')
    line = re.sub('\[.*?אלפס.*?\]', '', line)
    line = re.sub('טור ו?שו"ע', 'טוש"ע', line)
    f_ayyen = re.search(reg_ayyen_tur, line)
    f_lo_manu = re.search(reg_lo_manu, line)

    if f_ayyen:
        line = line[:f_ayyen.start()]
    if f_lo_manu:
        line = re.sub(f_lo_manu.group('a'), "", line)
    if in_per:
        if in_bra:
            clean = re.sub(reg_brackets, r'\1', line)  # brackets are always correct
            clean = re.sub(reg_parentheses, '', clean)
        else:
            clean = re.sub(reg_parentheses, r'\1', line)
    elif in_bra:
        clean = re.sub(reg_brackets, r'\1', line)  # brackets are always correct
    else:
        clean = line
    return clean


# putting in casses of switching the letter order
def getGematriaVav(str, mass):
    str = str.strip()
    str = re.sub('''"|''', '', str)
    case_set = {270,272,274,275,298,304,344,670,672,698,744} # from trello card 'Letter transpositions'
    if str[0] == 'ו' and (is_hebrew_number(str[1:]) or (getGematria(str[1:]) in case_set)):
        return getGematria(str[1:])
    elif is_hebrew_number(str) or getGematria(str) in case_set: # and not re.search('''מד"ס'''): or re.search('''('|")''', str)
        return getGematria(str)
    elif re.search('בהגהה?', str): # this is not gimatria but there is no need to send an error about it each time...
        return
    else:
        mass.write_shgia('error in pointer, not Gimatria...'+ str)

#  Noahs code checking that the hundreds, tens, ones, are in the right order
def is_hebrew_number(str):
    matches = re.findall(hebrew_number_regex(), str)
    if len(matches) == 0:
        return False
    if str == 'שם':
        return False
    return matches[0] == str


def hebrew_number_regex():
    """
    Regular expression component to capture a number expressed in Hebrew letters
    :return string:
    \p{Hebrew} ~= [\u05d0–\u05ea]
    """
    rx = r"""                                    # 1 of 3 styles:
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
    for row in list_dict:
        # erasing the error codes related to letters count
        if row['problem'] == 'error missing little or big letter' or row['problem'] == 'error, cit with the perek/page counters':
            row['problem'] = False
    with open('{}.csv'.format(filename), 'w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames = ['txt file line', 'Perek running counter', 'page running counter',
                                'Perek aprx', 'Page aprx', 'Rambam', 'Semag', 'Tur Shulchan Arukh', 'original', 'problem']) #fieldnames = obj_list[0].keys())
        writer.writeheader()
        writer.writerows(list_dict)


def fromCSV(fromcsv, newfile):
    f = codecs.open(newfile, 'w', encoding = 'utf-8')
    with open(fromcsv, 'r') as csvfile:
        file_reader = csv.DictReader(csvfile)
        for i, row in enumerate(file_reader):
            if not row:
                continue
            f.write(row['original'].strip() + '\n')


#  run to create csv from txt file for QA
def run1(massechet_he = None, massechet_en = None, EM = True):
    parse1 = parse_em('{}.txt'.format(massechet_he), 1, '{}_error'.format(massechet_en), EM = EM)
    toCSV(massechet_he, parse1)
    return parse1


#  run to create the csv to get talmud matching
def run2(massechet_he=None, massechet_en=None):
    fromCSV('{}.csv'.format(massechet_he), '{}.txt'.format(massechet_en))
    parse2 = parse_em('{}.txt'.format(massechet_en), 2, '{}_error'.format(massechet_en))
    toCSV('{}_little_letters'.format(massechet_en), parse2)
    return parse2


def run15(massechet_he=None, massechet_en=None):
    fromCSV('{}.csv'.format(massechet_he), '{}.txt'.format(massechet_he))  # reads from fixed ביצה.csv to egg.txt
    parse1 = parse_em('{}.txt'.format(massechet_he), 1, '{}_error'.format(massechet_en))  # egg.txt to screen output
    toCSV('{}'.format(massechet_en), parse1)
    return parse1


def last_algo_run(withSegments, parsedData):
    pass


def write_errfile(filename):
    error = codecs.open('error_{}.txt'.format(filename), 'w', encoding = 'utf-8')
    with codecs.open('error_main.txt', 'r', 'utf-8') as fp:
        lines = fp.readlines()
        # it = iter(lines)
        e = enumerate(lines)
        for i, line in e:
            if re.search('error', line):
                j, k = i, i
                while not re.search('.txt', lines[j]):
                    j -= 1
                while (j < i):
                    error.write(lines[j])
                    j+=1
                while not re.search('.txt', lines[k]):
                    error.write(lines[k])
                    k+=1
                    next(e)


# from csv to txt
def reverse_collapse(fromcsv, collapsed_file):
    f = codecs.open('{}.txt'.format(collapsed_file), 'w', encoding='utf-8')
    with open(fromcsv, 'r') as csvfile:
        file_reader = csv.DictReader(csvfile)
        prev = None
        for i, row in enumerate(file_reader):
            if prev != (row['original'].strip() + '\n'):
                f.write(row['original'].strip() + '\n')
            prev = (row['original'].strip() + '\n')
    run1('{}'.format(collapsed_file), '{}'.format(collapsed_file))


def segment_column(segmentfile, reffile, massekhet, wikitext=False):
    final_list = []
    i = 0
    with open(segmentfile, 'r') as csvfile:
        seg_reader = csv.DictReader(csvfile)
        with open(reffile, 'r') as csvfile:
            ref_reader = csv.DictReader(csvfile)
            for segrow, refrow in zip(seg_reader, ref_reader):
                i += 1
                if not wikitext:
                    daf, daf_line = segrow['Daf'], segrow['Line']
                else:
                    split = re.split('[\s:]', segrow['full line'])
                    daf, daf_line = split[1], split[2]
                smg = convert_smg(refrow['Semag'])
                letter_dict = {'Segment': '{}.{}.{}'.format(massekhet, daf, daf_line),
                          'Rambam': refrow['Rambam'],
                          'Semag': smg,
                          'Tur Shulchan Arukh': refrow['Tur Shulchan Arukh']}
                final_list.append(letter_dict)
    return final_list


def convert_smg(smg_str):
    conv_table = {
    'Sefer Mitzvot Gadol, Volume One ' : 'Sefer Mitzvot Gadol, Negative Commandments ',
    'Sefer Mitzvot Gadol, Volume Two ':'Sefer Mitzvot Gadol, Positive Commandments ',
    'Sefer Mitzvot Gadol, Volume Two, Laws of Eruvin ': 'Sefer Mitzvot Gadol, Rabbinic Commandments, Laws of Eruvin ',
    'Sefer Mitzvot Gadol, Volume Two, Laws of Mourning ': 'Sefer Mitzvot Gadol, Rabbinic Commandments, Laws of Mourning ',
    "Sefer Mitzvot Gadol, Volume Two, Laws of Tisha B'Av ": "Sefer Mitzvot Gadol, Rabbinic Commandments, Laws of Tisha B'Av ",
    'Sefer Mitzvot Gadol, Volume Two, Laws of Megillah ': 'Sefer Mitzvot Gadol, Rabbinic Commandments, Laws of Megillah ',
    'Sefer Mitzvot Gadol, Volume Two, Laws of Chanukah ': 'Sefer Mitzvot Gadol, Rabbinic Commandments, Laws of Chanukah '
    }

    return multiple_replace(smg_str, conv_table, using_regex=True)


def needs_another_cycle(txtfile, mass_name):
    if os.stat(txtfile).st_size == 0:
        print('\n' + mass_name + ' is empty from errors')
    else:
        with codecs.open(txtfile, 'r', 'utf-8') as fp:
            lines = fp.readlines()
        reg_letter_error = '((error missing little or big letter)|(error, cit with the perek/page counters)|(error, missing))'
        reg_missing_indicator = 'error, missing an indicator'
        needs_c = 0
        indicator_c = 0
        for line in lines:
            if not re.search(reg_letter_error, line):
                needs_c += 1
            if re.search(reg_missing_indicator, line):
                indicator_c  += 1
        if not needs_c and not indicator_c:
            print('\n' + mass_name + ' is empty from errors')
        else:
            print('\n' + mass_name + '\n' \
            +" indicator count " + str(indicator_c)\
            +" other problem " + str(needs_c))

if __name__ == "__main__":
    run1('EM_Bava Batra', 'Rif', EM='Rif')
    i = 1
    #run15('EM_Rif_{}'.format(i), 'EM_Rif_{}'.format(i+1))
