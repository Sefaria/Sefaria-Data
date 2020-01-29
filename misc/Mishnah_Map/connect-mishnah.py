# -*- coding: utf-8 -*-
import urllib.request, urllib.error, urllib.parse
import re
import json
import csv
import codecs

from fm import fuzz
from sefaria.model import *


class PointerException(Exception):
    pass


class AbstractVolume(object):

    def __init__(self, title):
        self.title = title
        self.index = get_index(title)

    def get_text(self, ref):
        return TextChunk(Ref(ref), "he").text


class TalmudVolume(AbstractVolume):
    history_depth = 5

    def __init__(self, title):
        super(TalmudVolume, self).__init__(title)
        self.text = {}
        self._current_daf_index = 2
        self._next_line_pointer = 1
        self._history = []

    def get_amud_text(self, daf_amud): # daf_amud = "2a"
        if not self.text.get(daf_amud):
            raw = self.get_text(self.title + "." + str(daf_amud))
            raw1 = [re.sub(r'[,\. ]+', " ", t).strip() for t in raw]
            raw2 = [re.sub(r'א"ר','אמר רבי', t).strip() for t in raw1]
            self.text[daf_amud] = [re.sub(r'שנא\'','שנאמר', t).strip() for t in raw2]
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
        while self._next_line_pointer > len(amud): #In very rare cases, skips two pages - Nazir 33b
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

    def get_previous_lines(self, num):
        """
        Returns `num` concatenated lines, with page/line number of the last of them
        """
        (ending_daf, ending_line, foo) = self._get_from_history(1)
        joined_lines = " ".join([self._get_from_history(i)[2].strip() for i in range(num, 0, -1)])
        return ending_daf, ending_line, joined_lines

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
        if self._current_daf_index >= self.index.nodes.lengths[0] + 2:
            return False
        return True

    def has_more_lines(self):
        amud = self.get_current_amud()
        if self._next_line_pointer > len(amud):
            return False
        return True

    def has_more_pages(self):
        if self._current_daf_index >= self.index.nodes.lengths[0] + 2:
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
            self.text[num] = [re.sub(r'[,\. ]+', " ", t).strip() for t in raw]
        return self.text.get(num)

    def get_current_chapter_text(self):
        return self.get_chapter_text(self.current_chapter)

    def advance_pointer(self, chapter, mishnah=1, offset=0):
        if chapter > self.index.nodes.lengths[0]:
            raise PointerException("Reached enf of book {}".format(self.title))
        self.current_chapter = chapter

        if mishnah > 1 and mishnah > len(self.get_current_chapter_text()):
            raise PointerException("Reached end of Mishnah Chapter")
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

    def remaining_mishnah_numbers(self):
        return list(range(self.current_mishnah, len(self.get_current_chapter_text()) + 1))

class TalmudMishnahMatcher(object):

    matni_re = re.compile( r"(^|\s+)" + "מתנ" + "י" + "?" + r"(?:'|" + "׳" + "|" + "תין" + ")" + r"(?:$|\s+)(.*)")
    gemarah_re = re.compile(r"(^|\s+)" + "גמ" + r"(" + r"\'" + "|" + "רא)" + r"(?:$|\s+)")
    mesechtot = ['Mishnah Berakhot','Mishnah Peah','Mishnah Demai','Mishnah Kilayim','Mishnah Sheviit','Mishnah Terumot','Mishnah Maasrot','Mishnah Maaser Sheni','Mishnah Challah','Mishnah Orlah','Mishnah Bikkurim','Mishnah Shabbat','Mishnah Eruvin','Mishnah Pesachim','Mishnah Shekalim','Mishnah Yoma','Mishnah Sukkah','Mishnah Beitzah','Mishnah Rosh Hashanah','Mishnah Taanit','Mishnah Megillah','Mishnah Moed Katan','Mishnah Chagigah','Mishnah Yevamot','Mishnah Ketubot','Mishnah Nedarim','Mishnah Nazir','Mishnah Sotah','Mishnah Gittin','Mishnah Kiddushin','Mishnah Bava Kamma','Mishnah Bava Metzia','Mishnah Bava Batra','Mishnah Sanhedrin','Mishnah Makkot','Mishnah Shevuot','Mishnah Eduyot','Mishnah Avodah Zarah','Pirkei Avot','Mishnah Horayot','Mishnah Zevachim','Mishnah Menachot','Mishnah Chullin','Mishnah Bekhorot','Mishnah Arakhin','Mishnah Temurah','Mishnah Keritot','Mishnah Meilah','Mishnah Tamid','Mishnah Middot','Mishnah Kinnim','Mishnah Kelim','Mishnah Oholot','Mishnah Negaim','Mishnah Parah','Mishnah Tahorot','Mishnah Mikvaot','Mishnah Niddah','Mishnah Makhshirin','Mishnah Zavim','Mishnah Tevul Yom','Mishnah Yadayim','Mishnah Oktzin']

    # How close to the end of the Mishnah do we have to match before we say that we matched the whole thing?
    end_of_mishnah_fudge_character_length = 12

    # mishnah_line_match_length, mishnah_line_match_threshold, max_lines
    threshold_defaults = (30, 60, 2)
    threshold_adjustments = {
            ("Yevamot", 3): (40, 70, 2),
            ("Bava_Batra", 1): (80, 80, 2),
            ("Bava_Batra", 10): (90, 70, 2),
            ("Nazir", 5): (80, 80, 3),
            ("Eruvin", 1): (60, 70, 2),
            ("Eruvin", 3): (60, 70, 2),
            ("Eruvin", 5): (60, 70, 2),
            ("Eruvin", 6): (60, 70, 2),
            ("Eruvin", 7): (60, 70, 2),
            ('Avodah_Zarah', 1): (60,70,2),
            ('Avodah_Zarah', 5): (60,70,2),
            ('Bava_Metzia', 8): (60,70,2),
            ('Berakhot', 4): (60,70,2),
            ('Chagigah', 3): (60,70,2),
            ('Gittin', 4): (60,70,2),
            ('Horayot', 2): (60,70,2),
            ('Keritot', 5): (60,70,2),
            ('Ketubot', 7): (60,70,2),
            ('Ketubot', 8): (60,70,2),
            ('Ketubot', 12): (60,70,2),
            ('Meilah', 4): (60,70,2),
            ('Menachot', 10): (60,70,2),
            ('Menachot', 13): (60,70,2),
            ('Nazir', 4): (60,70,2),
            ('Nazir', 6): (60,70,2),
            ('Nedarim', 6): (60,70,2),
            ('Nedarim', 9): (60,70,2),
            ('Nedarim', 10): (60,70,2),
            ('Shabbat', 8): (60,70,2),
            ('Shabbat', 16): (60,70,2),
            ('Shevuot', 5): (60,70,2),
            ('Sotah', 6): (60,70,2),
            ('Tamid', 6): (60,70,2),
            ('Temurah', 4): (60,70,2),
            ('Yevamot', 5): (60,70,2),
            ('Yevamot', 16): (60,70,2),
            ('Zevachim', 4): (60,70,2),
            ('Zevachim', 12): (60,70,2),
            ('Zevachim', 13): (60,70,2),

            ('Pesachim', 1): (60,90,3),
            ('Pesachim', 4): (60,70,3),
            ('Yoma', 3): (50,70,3),
            ('Rosh_Hashanah', 4): (70, 95, 2),
            ('Megillah', 1): (80, 80, 4),
            ('Kiddushin',1): (80, 80, 2),
            ('Kiddushin',3): (80, 80, 2),
            ('Kiddushin',4): (80, 80, 2),
            ("Yevamot", 4): (60, 80, 4),
            ("Yevamot", 7): (80, 80, 4),
            ("Yevamot", 13): (60, 80, 4),
            ("Yevamot", 14): (80, 90, 4),
            ("Ketubot", 1): (80, 90, 4),
            ("Ketubot", 4): (80, 80, 4),
            ("Bava_Kamma", 7): (80, 80, 4),
            ("Bava_Kamma", 2): (80, 80, 4),
            ("Bava_Kamma", 8): (40, 80, 4),
            ("Bava_Kamma", 9): (60, 90, 4),

        }

    def __init__(self):
        self.log = codecs.open('mishnah.log', 'w', encoding='utf-8')
        self.error_log = codecs.open('connect_error.log', 'w', encoding='utf-8')
        self.csv_writer = csv.writer(open('mishnah_mappings.csv', 'wb'))
        self.matched_count = 0
        self.unmatched_count = 0

    def get_next_bavli_chapter(self, title, current):
        next = current + 1
        chapters_out_of_order = {
            # Look up the mesechet and the chapter being requested (the one following the last), substitute a new position.
            # Gets confusing.  See notes.

            ("Megillah", 3): 4,  # When we get to 3, skip to 4.
            ("Megillah", 5): 3,  # After parsing 4, it asks for 5, which is beyond the end of the book, so needs to jump back to 3.
            ("Megillah", 4): 5,  # After parsing 3, jump to non-existent 5 - the end.

            ("Sanhedrin", 10): 11,
            ("Sanhedrin", 12): 10,
            ("Sanhedrin", 11): 12,

            ("Menachot", 6): 10,  # Asking for 6, jump to 10
            ("Menachot", 11): 6,  # Then at 11, go back to 6
            ("Menachot", 10): 11  # Once we get to 10, jump forward to 11.
        }
        return chapters_out_of_order.get((title, next)) or next

    @staticmethod
    def replace_roshei_tevot(s):
        # For speed, perhaps this should be flipped - iterate on words in the string
        # todo: merge with TalmudVolume.get_amud_text()
        subs = {
            'וחכ"א': 'וחכמים אומרים',
            'חכ"א': 'חכמים אומרים',

            'ור"ש': 'ורבי שמעון',
            'ר"ש': 'רבי שמעון',

            'וב"ה': 'ובית הלל',
            'ובה"א': 'ובית הלל אומרים',
            'בש"א': 'בית שמאי אומרים',
            'ב"ש': 'בית שמאי',

            # Megillah 1:1
            'בי"ב': 'בשנים עשר',
            'בי"ג': 'בשלושה עשר',
            'בי"ד': 'בארבעה עשר',
            'בי"א': 'באחד עשר',
            'בט"ו': 'בחמישה עשר',

            'ב"ד': 'בית דין'
        }

        for old, new in subs.items():
            if old in s:
                s = s.replace(old, new)

        return s

    def get_match_thresholds(self, title, chapter):
        # Returns mishnah_line_match_length, mishnah_line_match_threshold, max_lines
        return self.threshold_adjustments.get((title, chapter)) or self.threshold_defaults

    def process_all(self):

        self.csv_writer.writerow(["Book", "Mishnah Chapter", "Start Mishnah", "End Mishnah", "Start Daf", "Start Line", "End Daf", "End Line"])

        for mesechet in self.mesechtot:
            try:
                self.process_book(mesechet)
            except Exception as e:
                msg = "Failed to get objects for {}: {}".format(mesechet, e)
                print(msg)
                self.error_log.write(msg)
        self.report_results()

    def report_results(self):
        print()
        print("{} Matched".format(self.matched_count))
        print("{} Unmatched".format(self.unmatched_count))

    def process_book(self, mishnah_title):

        bavli = TalmudVolume(re.sub(" ", "_", mishnah_title[8:]))
        mishnah = MishnahVolume(re.sub(" ", "_", mishnah_title))

        perek_start = True
        mishnayot_end = False
        while bavli.has_more():
            current_mishnah = mishnah.get_current_mishnah() if not mishnayot_end else ""

            (starting_daf, starting_line, line) = bavli.get_next_line()

            m = self.matni_re.match(line)
            if m or perek_start:  # Match mishnah keyword
                self.log.write("Found Mishnah start at {}:{}\n{}\n".format(starting_daf, starting_line, line))
                ending_daf = starting_daf
                ending_line = starting_line

                if perek_start and not m:  # Perek starts with no "Mishna" - contents of `line` are fine
                    pass
                else:
                    if len(m.group(2)) == 0:  # bareword "Mishna" - get next line
                        (ending_daf, ending_line, line) = bavli.get_next_line()
                    elif len(m.group(2)) > 0: # "Mishna" followed by content, twim off "Mishna"
                        line = m.group(2)

                line = self.replace_roshei_tevot(line)
                if fuzz.partial_ratio(line, current_mishnah) > 60:
                    self.log.write("Matched a starting line in the Mishnah: {}\n{}\n".format(line, current_mishnah))

                    mishnah_line_match_length, mishnah_line_match_threshold, max_lines = self.get_match_thresholds(bavli.title, mishnah.current_chapter)

                    starting_mishnah = mishnah.current_mishnah
                    if mishnayot_end:
                        msg = "Error: Found too many mishnayot in {} {}!\n".format(bavli.title, mishnah.current_chapter)
                        print(msg)
                        self.log.write(msg)
                        self.error_log.write(msg)
                        self.csv_writer.writerow([bavli.title, mishnah.current_chapter, "?", "?", starting_daf, starting_line])

                    lines_in_match = 1
                    while not self.gemarah_re.search(line) and '\u05d4\u05d3\u05e8\u05df \u05e2\u05dc\u05da' not in line:  # Check for 'Gemara' or 'Hadran'
                        (foo, bar, line) = bavli.get_next_line()
                        lines_in_match += 1

                    lines_to_get = max_lines if max_lines <= lines_in_match else lines_in_match
                    (ending_daf, ending_line, last_bavli_segment) = bavli.get_previous_lines(lines_to_get)
                    last_bavli_segment = last_bavli_segment.strip()[-mishnah_line_match_length:]

                    # Open up Roshei Teivot
                    last_bavli_segment = self.replace_roshei_tevot(last_bavli_segment)

                    ending_mishnah = None
                    for i in range(mishnah.number_left_in_chapter() + 1):
                        m = mishnah.get_next_mishnah(i)
                        assert len(last_bavli_segment) < len(m)
                        (ratio, offset_start, offset_ending) = fuzz.partial_with_place(m, last_bavli_segment)
                        if ratio < mishnah_line_match_threshold:
                            mesg = "Failed to match last Talmud line to Mishnah: \n{}\n{}\n\n".format(last_bavli_segment, m)
                            self.log.write(mesg)
                            continue
                        self.log.write("Succeeded to match last Talmud line to Mishanh: \n{}\n{}\n\n".format(last_bavli_segment, m))
                        ending_mishnah = mishnah.current_mishnah + i
                        if offset_ending < len(m) - self.end_of_mishnah_fudge_character_length:  # Match ended in middle of a mishnah.  Number at end is close-enough-to-end fudge factor.
                            mishnah.advance_pointer(mishnah.current_chapter, ending_mishnah, offset_ending + 1)
                            self.log.write("Internal match {} in {}\n - advanced Mishnah offset: {}, {}, {}\n".format(last_bavli_segment, m, mishnah.current_chapter, ending_mishnah, offset_ending + 1))
                        else:  # match ended at end of a mishnah
                            if i == mishnah.number_left_in_chapter():  # if this is the last mishnah
                                self.log.write("Reached end of mishnayot in chapter {}.\n".format(str(mishnah.current_chapter)))
                                mishnayot_end = True
                            else:
                                mishnah.advance_pointer(mishnah.current_chapter, ending_mishnah + 1)
                                self.log.write("Advanced to next Mishnah: {}, {}\n".format(mishnah.current_chapter, ending_mishnah + 1))
                        break
                    match = [bavli.title, mishnah.current_chapter, starting_mishnah, ending_mishnah, starting_daf, starting_line, ending_daf, ending_line]

                    if ending_mishnah is None:
                        msg = "saw unmatched Mishna in Talmud: {}\n".format(", ".join([str(m) for m in match]))
                        self.log.write(msg)
                    else:
                        self.csv_writer.writerow(match)
                        self.matched_count += 1
                        msg = "Match! {}\n".format(", ".join([str(m) for m in match]))
                        #print msg
                        self.log.write(msg)
                else:
                    self.log.write("Talmud Mishna start: {}\n - did not match next Mishna: {}".format(line, current_mishnah))
            if perek_start:
                perek_start = False

            # Check for Hadran
            if '\u05d4\u05d3\u05e8\u05df \u05e2\u05dc\u05da' in line:
                if not mishnayot_end:
                    msg = 'Error: Mishna did not reach the end of chapter! ("{}", {}).\t{} remain.'.format(bavli.title, mishnah.current_chapter, mishnah.number_left_in_chapter() + 1)
                    print(msg)
                    self.log.write(msg + "\n")
                    self.error_log.write(msg + "\n")
                    for n in mishnah.remaining_mishnah_numbers():
                        self.unmatched_count += 1
                        self.csv_writer.writerow([bavli.title, mishnah.current_chapter, n])
                self.log.write("End of perek: {} {} on {} {}\n".format(bavli.title, mishnah.current_chapter, bavli.get_current_line()[0], bavli.get_current_line()[1]))
                try:
                    # Advance to next chapter, reset indicators
                    next_chapter = self.get_next_bavli_chapter(bavli.title, mishnah.current_chapter)
                    mishnah.advance_pointer(next_chapter)
                    perek_start = True
                    mishnayot_end = False
                except PointerException:
                    self.log.write("End of book: {} {} on {} {}\n".format(bavli.title, mishnah.current_chapter, bavli.get_current_line()[0], bavli.get_current_line()[1]))
                    break

tmm = TalmudMishnahMatcher()
tmm.process_all()
#tmm.process_book("Mishnah Bava_Metzia")  # Bava_Metzia
#tmm.report_results()