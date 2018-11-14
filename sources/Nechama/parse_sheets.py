#encoding=utf-8

import django
django.setup()

from sheets import *
from research.mesorat_hashas_sefaria.mesorat_hashas import ParallelMatcher
import unicodedata
from sefaria.utils.hebrew import strip_cantillation
from collections import OrderedDict
from segments import *
from data_utilities.util import WeightedLevenshtein



class Nechama_parser(object):

    def __init__(self):
        self.sheets = OrderedDict()
        self.sheet = None
        self.levenshtein = WeightedLevenshtein()



    def bs4_reader(self, file_list_names):
        """
        The main BeautifulSoup reader function, that etrates on all sheets and creates the obj, probably should be in it's own file
        :param self:
        :return:
        """
        for html_sheet in file_list_names:
            content = BeautifulSoup(open("{}".format(html_sheet)), "lxml")
            print html_sheet
            top_dict = self.dict_from_html_attrs(content.find('div', {'id': "contentTop"}).contents)
            # print 'len_content type ', len(top_dict.keys())
            self.sheet = Sheet(html_sheet, top_dict["paging"].text, top_dict["h1"].text, top_dict["year"].text, top_dict["pasuk"].text)
            self.sheets[html_sheet] = self.sheet
            body_dict = self.dict_from_html_attrs(content.find('div', {'id': "contentBody"}))
            self.sheet.sections.extend([v for k, v in body_dict.items() if re.search(u'ContentSection_\d', k)]) # check that these come in in the right order
            self.sheet.sheet_remark = body_dict['sheetRemark'].text
            pass
        return self.sheets

    def dict_from_html_attrs(self, contents):
        d = OrderedDict()
        for e in [e for e in contents if isinstance(e, element.Tag)]:
            if "id" in e.attrs.keys():
                d[e.attrs['id']] = e
            else:
                d[e.name] = e
        return d

    def get_score(self, words_a, words_b):
        normalizingFactor = 100
        smoothingFactor = 1
        ImaginaryContenderPerWord = 22
        str_a = u" ".join(words_a)
        str_b = u" ".join(words_b)
        dist = self.levenshtein.calculate(str_a, str_b,normalize=False)
        score = 1.0 * (dist + smoothingFactor) / (len(str_a) + smoothingFactor) * normalizingFactor

        dumb_score = (ImaginaryContenderPerWord * len(words_a)) - score
        return dumb_score

    def clean(self, s):
        s = unicodedata.normalize("NFD", s)
        s = strip_cantillation(s, strip_vowels=True)
        s = re.sub(u"(^|\s)(?:\u05d4['\u05f3])($|\s)", u"\1יהוה\2", s)
        s = re.sub(ur"[,'\":?.!;־״׳]", u" ", s)
        s = re.sub(ur"\([^)]+\)", u" ", s)
        # s = re.sub(ur"\((?:\d{1,3}|[\u05d0-\u05ea]{1,3})\)", u" ", s)  # sefaria automatically adds pasuk markers. remove them
        s = bleach.clean(s, strip=True, tags=()).strip()
        s = u" ".join(s.split())
        return s

    def tokenizer(self, s):
        return self.clean(s).split()

    def get_score(self, words_a, words_b):
        normalizingFactor = 100
        smoothingFactor = 1
        ImaginaryContenderPerWord = 22
        str_a = u" ".join(words_a)
        str_b = u" ".join(words_b)
        dist = self.levenshtein.calculate(str_a, str_b,normalize=False)
        score = 1.0 * (dist + smoothingFactor) / (len(str_a) + smoothingFactor) * normalizingFactor

        dumb_score = (ImaginaryContenderPerWord * len(words_a)) - score
        return dumb_score

    def check_reduce_sources(self, comment, ref):
        n = len(re.split(u'\s+', comment))
        pm = ParallelMatcher(self.tokenizer, dh_extract_method = None, ngram_size=3, max_words_between=4, min_words_in_match =int(round(n*0.8)),
        min_distance_between_matches=0, all_to_all=False, parallelize = False, verbose = False, calculate_score = self.get_score)
        new_ref = pm.match(tc_list=[ref.text('he'), (comment, 1)], return_obj=True)
        return new_ref


if __name__ == "__main__":
    # Ref(u"בראשית פרק ג פסוק ד - פרק ה פסוק י")
    # Ref(u"u'דברים פרק ט, ז-כט - פרק י, א-י'")
    np = Nechama_parser()

    # sheets = bs4_reader(['html_sheets/{}.html'.format(x) for x in ["1", "2", "30", "62", "84", "148","212","274","302","378","451","488","527","563","570","581","750","787","820","844","894","929","1021","1034","1125","1183","1229","1291","1351","1420"]])
    # sheets = np.bs4_reader(["html_sheets/{}".format(fn) for fn in os.listdir("html_sheets") if fn != 'errors.html'])
    pass
