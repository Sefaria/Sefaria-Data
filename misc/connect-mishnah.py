# -*- coding: utf-8 -*-
import urllib2
import re
import json
import csv

from fm import fuzz


class PointerException(Exception):
    pass


class AbstractVolume(object):
    def __init__(self, title):
        url = 'http://www.sefaria.org/api/index/'+ str(title)
        response = urllib2.urlopen(url)
        resp = response.read()
        self.title = title
        self.index = json.loads(resp)
        if "error" in self.index:
            raise Exception(u"Failed to get index {}: {}".format(title, self.index["error"]))

    def get_text(self, ref):
        url = 'http://www.sefaria.org/api/texts/' + str(ref)
        response = urllib2.urlopen(url)
        resp = response.read()
        return json.loads(resp)["he"]


class TalmudVolume(AbstractVolume):
    def __init__(self, title):
        super(TalmudVolume, self).__init__(title)
        self.text = {}
        self.current_daf_index = 2
        self.current_line = 1

    def get_amud_text(self, daf_amud): # daf_amud = "2a"
        if not self.text.get(daf_amud):
            raw = self.get_text(self.title + "." + str(daf_amud))
            self.text[daf_amud] = map(lambda t: re.sub(r'[,\. ]+', " ", t).strip(), raw)
        return self.text.get(daf_amud)

    def get_next_line(self):
        amud = self.get_current_amud()
        if self.current_line > len(amud):
            self.advance_page()
            amud = self.get_current_amud()
        l = amud[self.current_line - 1]
        self.current_line += 1
        return l

    def index_to_daf(self, index):
        amud = "a" if index % 2 == 0 else "b"
        daf = (index / 2) + 1
        return str(daf) + amud

    def current_daf(self):
        return self.index_to_daf(self.current_daf_index)

    def get_current_amud(self):
        return self.get_amud_text(self.current_daf())

    def advance_page(self):
        if not self.has_more_pages():
            raise PointerException("Reached end of Talmud {}")
        self.current_daf_index += 1
        self.current_line = 1

    def has_more(self):
        amud = self.get_current_amud()
        if self.current_line <= len(amud):
            return True
        if self.current_daf_index >= self.index["length"] + 2:
            return False
        return True

    def has_more_lines(self):
        amud = self.get_current_amud()
        if self.current_line > len(amud):
            return False
        return True

    def has_more_pages(self):
        if self.current_daf_index >= self.index["length"] + 2:
            return False
        return True


class MishnahVolume(AbstractVolume):
    def __init__(self, title):
        super(MishnahVolume, self).__init__(title)
        self.text = {}
        self.current_chapter = 1
        self.current_mishnah = 1
        self.current_offset = 0

    def get_chapter_text(self, num):
        if not self.text.get(num):
            raw = self.get_text(self.title + "." + str(num))
            self.text[num] = map(lambda t: re.sub(r'[,\. ]+', " ", t).strip(), raw)
        return self.text.get(num)

    def get_current_chapter_text(self):
        return self.get_chapter_text(self.current_chapter)

    def advance_pointer(self, chapter, mishnah=1, offset=0):
        self.current_chapter = chapter
        self.current_mishnah = mishnah
        self.current_offset = offset

    def advance_chapter(self):
        self.advance_pointer(self.current_chapter + 1)

    def get_current_mishnah(self):
        chapter = self.get_current_chapter_text()
        return chapter[self.current_mishnah - 1][self.current_offset:]

    def get_next_mishnah(self, num=1):
        chapter = self.get_current_chapter_text()
        requested_mishnah = self.current_mishnah + num
        if requested_mishnah > len(chapter):
            raise PointerException("Reached end of Mishnah Chapter")
        return chapter[requested_mishnah - 1]

    def number_left_in_chapter(self):
        return len(self.get_current_chapter_text()) - self.current_mishnah


#matni_re = re.compile(ur"""\u05de\u05ea\u05e0\u05d9(?:'|\u05f3|\s|\u05ea\u05d9\u05df)""")
raw_re = u"מתנ" + u"י" + u"?" + u"(?:'|\s|" + u"׳" + u"|" + u"תין" + u")"
matni_re = re.compile(raw_re)

mesechtot = [u'Mishnah Berakhot',u'Mishnah Peah',u'Mishnah Demai',u'Mishnah Kilayim',u'Mishnah Sheviit',u'Mishnah Terumot',u'Mishnah Maasrot',u'Mishnah Maaser Sheni',u'Mishnah Challah',u'Mishnah Orlah',u'Mishnah Bikkurim',u'Mishnah Shabbat',u'Mishnah Eruvin',u'Mishnah Pesachim',u'Mishnah Shekalim',u'Mishnah Yoma',u'Mishnah Sukkah',u'Mishnah Beitzah',u'Mishnah Rosh Hashanah',u'Mishnah Taanit',u'Mishnah Megillah',u'Mishnah Moed Katan',u'Mishnah Chagigah',u'Mishnah Yevamot',u'Mishnah Ketubot',u'Mishnah Nedarim',u'Mishnah Nazir',u'Mishnah Sotah',u'Mishnah Gittin',u'Mishnah Kiddushin',u'Mishnah Bava Kamma',u'Mishnah Bava Metzia',u'Mishnah Bava Batra',u'Mishnah Sanhedrin',u'Mishnah Makkot',u'Mishnah Shevuot',u'Mishnah Eduyot',u'Mishnah Avodah Zarah',u'Pirkei Avot',u'Mishnah Horayot',u'Mishnah Zevachim',u'Mishnah Menachot',u'Mishnah Chullin',u'Mishnah Bekhorot',u'Mishnah Arakhin',u'Mishnah Temurah',u'Mishnah Keritot',u'Mishnah Meilah',u'Mishnah Tamid',u'Mishnah Middot',u'Mishnah Kinnim',u'Mishnah Kelim',u'Mishnah Oholot',u'Mishnah Negaim',u'Mishnah Parah',u'Mishnah Tahorot',u'Mishnah Mikvaot',u'Mishnah Niddah',u'Mishnah Makhshirin',u'Mishnah Zavim',u'Mishnah Tevul Yom',u'Mishnah Yadayim',u'Mishnah Oktzin']

def process_book(bavli, mishnah, csv_writer):
    perek_start = True

    while bavli.has_more():
        current_mishnah = mishnah.get_current_mishnah()

        line = bavli.get_next_line()

        if matni_re.search(line) or perek_start:  # Match mishnah keyword
            starting_line = bavli.current_line - 1
            starting_daf = bavli.current_daf()

            line = bavli.get_next_line()
            if fuzz.partial_ratio(line, current_mishnah) > 90:
            #if line in current_mishnah:
                starting_mishnah = mishnah.current_mishnah
                ending_daf = bavli.current_daf()
                ending_line = bavli.current_line - 1
                while ":" not in line:
                    line = bavli.get_next_line()
                    ending_daf = bavli.current_daf()
                    ending_line = bavli.current_line - 1

                last_bavli_segment = line[-20:-1]
                ending_mishnah = None
                for i in range(mishnah.number_left_in_chapter() + 1):
                    m = mishnah.get_next_mishnah(i)
                    assert len(last_bavli_segment) < len(m)
                    (ratio, offset_start, offset_ending) = fuzz.partial_with_place(m, last_bavli_segment)
                    if ratio < 70:
                        continue
                    ending_mishnah = mishnah.current_mishnah + i
                    if offset_ending < len(m):  # Match ended in middle of a mishnah
                        mishnah.advance_pointer(mishnah.current_chapter, ending_mishnah, offset_ending + 1)
                    else:  # match ended at end of a mishnah
                        if i == mishnah.number_left_in_chapter():  # if this is the last mishnah
                            pass # leave it, advance it later.
                        else:
                            mishnah.advance_pointer(mishnah.current_chapter, ending_mishnah + 1)
                    break
                match = [bavli.title, mishnah.current_chapter, starting_mishnah, ending_mishnah, starting_daf, starting_line, ending_daf, ending_line]

                if ending_mishnah is None:
                    print "Failed to Match: {}".format(", ".join([str(m) for m in match]))
                else:
                    #csv_writer.writerow(match)
                    print "Match! {}".format(", ".join([str(m) for m in match]))

        if perek_start == True:
            perek_start = False

        if u'\u05d4\u05d3\u05e8\u05df \u05e2\u05dc\u05da' in line:
            print "End of perek: {} {} on {} {}".format(bavli.title, mishnah.current_chapter, bavli.current_daf(), bavli.current_line)
            try:
                mishnah.advance_pointer(mishnah.current_chapter + 1)
                perek_start = True
            except PointerException:
                print "End of book: {} {} on {} {}".format(bavli.title, mishnah.current_chapter, bavli.current_daf(), bavli.current_line)



with open('mishnah_mappings.csv', 'wb') as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerow(["Book", "Mishnah Chapter", "Start Mishnah", "End Mishnah", "Start Daf", "Start Line", "End Daf", "End Line"])

    for mesechet in mesechtot:
#        try:
        bavli = TalmudVolume(re.sub(" ", "_", mesechet[8:]))
        mishnah = MishnahVolume(re.sub(" ", "_", mesechet))
        process_book(bavli, mishnah, csv_writer)
#        except Exception as e:
#            print "Failed to get objects for {}: {}".format(mesechet, e)
