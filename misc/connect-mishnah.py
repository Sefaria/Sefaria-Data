# -*- coding: utf-8 -*-
import urllib2
import re
import json
import csv
import codecs

from fm import fuzz


class PointerException(Exception):
    pass


class AbstractVolume(object):
    server = 'http://www.sefaria.org'

    def __init__(self, title):
        url = self.server + '/api/index/'+ str(title)
        response = urllib2.urlopen(url)
        resp = response.read()
        self.title = title
        self.index = json.loads(resp)
        if "error" in self.index:
            raise Exception(u"Failed to get index {}: {}".format(title, self.index["error"]))

    def get_text(self, ref):
        url = self.server + '/api/texts/' + str(ref)
        response = urllib2.urlopen(url)
        resp = response.read()
        while True:
            try:
                return json.loads(resp)["he"]
                break
            except KeyError:
                return  ""
                #return json.loads(resp)["he"]


class TalmudVolume(AbstractVolume):
    history_depth = 3

    def __init__(self, title):
        super(TalmudVolume, self).__init__(title)
        self.text = {}
        self._current_daf_index = 2
        self._next_line_pointer = 1
        self._history = []

    def get_amud_text(self, daf_amud): # daf_amud = "2a"
        if not self.text.get(daf_amud):
            raw = self.get_text(self.title + "." + str(daf_amud))
            raw1 = map(lambda t: re.sub(r'[,\. ]+', " ", t).strip(), raw)
            raw2 = map(lambda t: re.sub(r'א"ר','אמר רבי', t).strip(), raw1)
            self.text[daf_amud] = map(lambda t: re.sub(r'שנא\'','שנאמר', t).strip(), raw2)
        return self.text.get(daf_amud)

    def _add_to_history(self, obj):
        if len(self._history) == self.history_depth:
            self._history = self._history[1:]
        self._history.append(obj)

    def _get_from_history(self, back=0):
        indx = len(self._history) - 1 - back
        return self._history[indx]

    def get_next_line(self):
        amud = self.get_current_amud()
        if self._next_line_pointer > len(amud):
            self.advance_page()
            amud = self.get_current_amud()
        l = amud[self._next_line_pointer - 1]
        self._add_to_history((self.current_daf(), self._next_line_pointer, l))
        self._next_line_pointer += 1
        return self.get_current_line()

    # Note: the signatures and behavior or get_next_line and get_current_line are different.

    def get_current_line(self):
        return self._get_from_history()

    def get_previous_line(self, back=1):
        return self._get_from_history(back)

    def index_to_daf(self, index):
        amud = "a" if index % 2 == 0 else "b"
        daf = (index / 2) + 1
        return str(daf) + amud

    def current_daf(self):
        return self.index_to_daf(self._current_daf_index)

    def get_current_amud(self):
        return self.get_amud_text(self.current_daf())

    def advance_page(self):
        if not self.has_more_pages():
            raise PointerException("Reached end of Talmud {}")
        self._current_daf_index += 1
        self._next_line_pointer = 1

    def has_more(self):
        amud = self.get_current_amud()
        if self._next_line_pointer <= len(amud):
            return True
        if self._current_daf_index >= self.index["length"] + 2:
            return False
        return True

    def has_more_lines(self):
        amud = self.get_current_amud()
        if self._next_line_pointer > len(amud):
            return False
        return True

    def has_more_pages(self):
        if self._current_daf_index >= self.index["length"] + 2:
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

log = codecs.open('mishnah.log', 'w', encoding='utf-8')

#matni_re = re.compile(ur"""\u05de\u05ea\u05e0\u05d9(?:'|\u05f3|\s|\u05ea\u05d9\u05df)""")
#raw_re = 
raw_re = ur"(^|\s+)" + u"מתנ" + u"י" + u"?" + ur"(?:'|" + u"׳" + u"|" + u"תין" + u")" + ur"(?:$|\s+)"
matni_re = re.compile(raw_re)
raw_gem = ur"(^|\s+)" + u"גמ" + ur"(" + ur"\'" + u"|" + u"רא)" + ur"(?:$|\s+)"
gemarah_re = re.compile(raw_gem)

mesechtot = [u'Mishnah Berakhot',u'Mishnah Peah',u'Mishnah Demai',u'Mishnah Kilayim',u'Mishnah Sheviit',u'Mishnah Terumot',u'Mishnah Maasrot',u'Mishnah Maaser Sheni',u'Mishnah Challah',u'Mishnah Orlah',u'Mishnah Bikkurim',u'Mishnah Shabbat',u'Mishnah Eruvin',u'Mishnah Pesachim',u'Mishnah Shekalim',u'Mishnah Yoma',u'Mishnah Sukkah',u'Mishnah Beitzah',u'Mishnah Rosh Hashanah',u'Mishnah Taanit',u'Mishnah Megillah',u'Mishnah Moed Katan',u'Mishnah Chagigah',u'Mishnah Yevamot',u'Mishnah Ketubot',u'Mishnah Nedarim',u'Mishnah Nazir',u'Mishnah Sotah',u'Mishnah Gittin',u'Mishnah Kiddushin',u'Mishnah Bava Kamma',u'Mishnah Bava Metzia',u'Mishnah Bava Batra',u'Mishnah Sanhedrin',u'Mishnah Makkot',u'Mishnah Shevuot',u'Mishnah Eduyot',u'Mishnah Avodah Zarah',u'Pirkei Avot',u'Mishnah Horayot',u'Mishnah Zevachim',u'Mishnah Menachot',u'Mishnah Chullin',u'Mishnah Bekhorot',u'Mishnah Arakhin',u'Mishnah Temurah',u'Mishnah Keritot',u'Mishnah Meilah',u'Mishnah Tamid',u'Mishnah Middot',u'Mishnah Kinnim',u'Mishnah Kelim',u'Mishnah Oholot',u'Mishnah Negaim',u'Mishnah Parah',u'Mishnah Tahorot',u'Mishnah Mikvaot',u'Mishnah Niddah',u'Mishnah Makhshirin',u'Mishnah Zavim',u'Mishnah Tevul Yom',u'Mishnah Yadayim',u'Mishnah Oktzin']

def process_book(bavli, mishnah, csv_writer):
    perek_start = True
    mishnayot_end = False
    while bavli.has_more():
        current_mishnah = mishnah.get_current_mishnah() if not mishnayot_end else ""

        (starting_daf, starting_line, line) = bavli.get_next_line()

        if matni_re.search(line) or perek_start:  # Match mishnah keyword
            log.write(u"Found Mishnah start at {}:{}\n{}\n".format(starting_daf, starting_line, line))
            if mishnayot_end:
                msg = u"Error: Found too many mishnayot in {} {}!\n".format(bavli.title, mishnah.current_chapter)
                print msg
                log.write(msg)
            (ending_daf, ending_line, line) = bavli.get_next_line()
            if fuzz.partial_ratio(line, current_mishnah) > 60:
                log.write(u"Matched a starting line in the Mishnah: {}\n{}\n".format(line, current_mishnah))
                starting_mishnah = mishnah.current_mishnah
                while not gemarah_re.search(line):
                    (foo, bar, line) = bavli.get_next_line()

                (ending_daf, ending_line, previous_line) = bavli.get_previous_line()
                (foo, bar, previous_previous_line) = bavli.get_previous_line(2)
                last_bavli_segment = previous_previous_line.strip() + u" " + previous_line.strip()
                last_bavli_segment = last_bavli_segment[-30:-1]
                ending_mishnah = None
                for i in range(mishnah.number_left_in_chapter() + 1):
                    m = mishnah.get_next_mishnah(i)
                    assert len(last_bavli_segment) < len(m)
                    (ratio, offset_start, offset_ending) = fuzz.partial_with_place(m, last_bavli_segment)
                    if ratio < 60:
                        log.write(u"Failed to match last Talmud line to Mishnah: {}\n{}\n".format(last_bavli_segment, m))
                        continue
                    log.write(u"Succeeded to match last Talmud line to Mishanh: {}\n{}\n".format(last_bavli_segment, m))
                    ending_mishnah = mishnah.current_mishnah + i
                    if offset_ending < len(m) - 10:  # Match ended in middle of a mishnah.  Number at end is close-enough-to-end fudge factor.
                        mishnah.advance_pointer(mishnah.current_chapter, ending_mishnah, offset_ending + 1)
                        log.write(u"Advanced Mishnah offset: {}, {}, {}\n".format(mishnah.current_chapter, ending_mishnah, offset_ending + 1))
                    else:  # match ended at end of a mishnah
                        if i == mishnah.number_left_in_chapter():  # if this is the last mishnah
                            log.write(u"Reached end of mishnayot in chapter {} is {}\n".format(str(mishnah.current_chapter), str(len(mishnah.get_current_chapter_text()))))
                            mishnayot_end = True
                        else:
                            mishnah.advance_pointer(mishnah.current_chapter, ending_mishnah + 1)
                            log.write(u"Advanced to next Mishnah: {}, {}\n".format(mishnah.current_chapter, ending_mishnah + 1))
                    break
                match = [bavli.title, mishnah.current_chapter, starting_mishnah, ending_mishnah, starting_daf, starting_line, ending_daf, ending_line]

                if ending_mishnah is None:
                    msg = u"Error: Failed to Match: {}\n".format(", ".join([str(m) for m in match]))
                    print msg
                    log.write(msg)
                else:
                    print
                    csv_writer.writerow(match)
                    msg = u"Match! {}\n".format(", ".join([str(m) for m in match]))
                    print msg
                    log.write(msg)

        if perek_start == True:
            perek_start = False

        if u'\u05d4\u05d3\u05e8\u05df \u05e2\u05dc\u05da' in line:
            if mishnayot_end == False:
                msg = u"Error: Mishna did not reach the end of chapter!\n"
                print msg
                log.write(msg)
            log.write(u"End of perek: {} {} on {} {}\n".format(bavli.title, mishnah.current_chapter, bavli.get_current_line()[0], bavli.get_current_line()[1]))
            try:
                mishnah.advance_pointer(mishnah.current_chapter + 1)
                perek_start = True
                mishnayot_end = False
            except PointerException:
                log.write(u"End of book: {} {} on {} {}\n".format(bavli.title, mishnah.current_chapter, bavli.get_current_line()[0], bavli.get_current_line()[1]))



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
