import copy
import csv
import json
import re
import sys
from operator import attrgetter
import django
django.setup()
from sefaria.model import *
from sources.functions import getGematria, post_text
from data_utilities.text_align import CompareBreaks
from research.mesorat_hashas_sefaria.mesorat_hashas import ParallelMatcher
from data_utilities.dibur_hamatchil_matcher import match_ref


class Location():

    def __init__(self, vol=0, book='guf', pages=[1], parasha='', nex={}, **kwargs):
        self.book = book
        self.pages = pages
        self.vol = vol
        self.parasha = parasha
        self.next = nex
        for k, v in kwargs.items():
            setattr(self, k, v)

    def set_next_loc(self, **kwargs):
        error = False
        for k, v in kwargs.items():
            if k == 'book' and k in self.next and self.next[k] == 'hashmata':
                continue  # hashanata remains hashmata even if it has another title
            if k == 'book' and v == 'guf' and self.book == 'guf' and 'parasha' not in self.next:
                print('ad kan in guf', self.__dict__)
                error = True
            self.next[k] = v
        return error

    def get_next_loc(self):
        new = copy.deepcopy(self)
        for k, v in self.next.items():
            setattr(new, k, v)
        new.next = {}
        if new.book != 'hashmata' and hasattr(new, 'siman'):
            delattr(new, 'siman')
            delattr(new, 'prevbook')
        new.pages = [self.pages[-1]]
        return new


class Parapraph():

    def __init__(self, ar='', he='', loc=Location(), ref=None, prev=None, nex=None):
        self.ar = ar
        self.he = he
        self.loc = loc
        self.prev = prev
        self.next = nex

    def get_next_par(self):
        if not self.next:
            self.next = Parapraph(prev=self, loc=self.loc.get_next_loc())
        return self.next

class Parser():

    def __init__(self):
        self.current = Parapraph()
        self.first = self.current
        self.loc = self.current.loc
        self.loc.parasha = 'הקדמה'
        self.lang = 'ar'

    def parse(self):
        for i in range(6):
            print(i)
            with open(f'torat_emet/000023_ZOHAR-VETARGUM-{i}.txt') as fp:
                data = fp.readlines()

            self.loc.vol = 1 if i < 2 else 2 if i == 2 else 3

            self.lang = 'ar'

            for line in data:
                line = line.strip()
                if not line:
                    continue
                if not re.sub('<[^>]*>', '', line).strip():
                    continue

                if line.startswith('~'):
                    if not re.search('^~ דף [א-ת\']{,5} ע(?:"|\'\')[אב]', line):
                        print('no daf', line)

                elif line.startswith('@'):
                    if 'המן' in line:
                        self.current.get_next_par().ar += f'<b>{line.replace("@", "").strip()}</b><br>'
                    else:
                        p = re.sub('@|פרשת', '', line).strip()
                        self.loc.set_next_loc(parasha=p)
                        if p in ['והיה עקב', 'שופטים', 'כי תצא']:
                            self.loc.set_next_loc(book='raya')
                        else:
                            self.loc.set_next_loc(book='guf')

                elif line in ["בָּרוּךָ יְיָ' לְעוֹלָם אָמֵן וְאָמֵן:", "בָּרוּךְ יְיָ לְעוֹלָם אָמֵן וְאָמֵן",
                              "בָּרוּךְ יְיָ' לְעוֹלָם אָמֵן וְאָמֵן. יִמְלוֹךְ יְיָ' לְעוֹלָם אָמֵן וְאָמֵן.",
                              "בָּרוּךָ ה' לְעוֹלָם אָמֵן וְאָמֵן.",
                              "בָּרוּךְ יְיָ לְעוֹלָם אָמֵן וְאָמֵן. יִמְלוֹךְ ה' לְעוֹלָם אָמֵן וְאָמֵן.",
                              "בָּרוּךְ יְיָ לְעוֹלָם אָמֵן וְאָמֵן"]:
                    self.current.ar += f'<br>{line.strip()}'

                elif re.search('^[א-ת]', strip_html(line)):
                    self.aramaic_line(line)

                elif strip_html(line).startswith('{'):
                    pass
                    if self.lang == 'ar':
                        pass
                        print('should be aramaic', line)
                    else:
                        line = handle_line(line)[1:-1]
                        line = re.sub('\{\{|\[\[', '(', line)
                        line = re.sub('\}\}|\]\]', ')', line)
                        line = re.sub('\(?(?:ע"כ|ע\'\'כ|עד כאן) מהשמטות\)?', '', line)
                        self.current.he = ' '.join(line.split())
                    self.lang = 'ar'

                elif 'השלמה מההשמטות' in line:
                    sim = getGematria(re.findall('סימן ([א-ת\']{,4})', line)[0]) if 'סימן' in line else 5
                    self.loc.set_next_loc(book='hashmata', siman=sim,
                                          prevbook=self.loc.book if self.loc.book != 'hashmata' else self.loc.prevbook)
                    self.current.ar += f'<a siman={sim}></a>'
                elif 'האדרא רבא קדישא' in line:
                    self.loc.set_next_loc(book='idra raba')
                    self.current.get_next_par().ar += '<b>האדרא רבא קדישא</b><br>'
                elif 'המדרש הנעלם' in line:
                    self.loc.set_next_loc(book='neelam')
                    self.current.get_next_par().ar += '<b>מדרש הנעלם</b><br>'
                elif 'רעיא מהימנא' in line:
                    self.loc.set_next_loc(book='raya')
                    self.aramaic_line(line)
                elif 'תּוֹסֶפְתָּא' in line:
                    self.loc.set_next_loc(book='tosefta')
                    self.aramaic_line(line)
                elif 'סִתְרֵי תּוֹרָה' in line:
                    self.loc.set_next_loc(book='sitrei')
                    self.aramaic_line(line)
                else:
                    if 'המגיה' in line:
                        self.current.get_next_par().ar += f'<small>{handle_line(line)}</small><br>'
                    elif 'ואלו החילופים מצאתי' in line:
                        self.current.ar += f'<br><small>{handle_line(line)}</small>'
                    else:
                        self.aramaic_line(line)

        self.current = self.first
        while self.current.next:
            if self.current.loc.book not in [self.current.next.loc.book, 'guf', 'hashmata'] and \
                    self.current.next.loc.book != 'hashmata' and not re.search('עד כאן|ע"כ|ע\'\'כ.{3,20}$', self.current.ar):
                print('new book without ad kan', self.current.loc.__dict__, self.current.next.loc.__dict__)
                print(self.current.ar)
            self.current = self.current.next


    def aramaic_line(self, line):
        self.loc = self.loc.get_next_loc()
        line = re.sub('</?(?:small|big|br|!--exb--)>', '', line, flags=re.IGNORECASE)
        line = re.sub('<<([א-ת].*?)>>', r'<big>\1</big>', line)
        spans = re.findall('<span[^>]*>(.*?)</span>', line, re.IGNORECASE)
        for span in spans:
            if re.search('\(עד כאן מההשמטות\)', span.strip()):
                line = re.sub(f'<span[^>]*>({re.escape(span)})</span>', '', line, flags=re.IGNORECASE)
                self.loc.set_next_loc(book=self.loc.prevbook)
            elif 'השלמה מההשמטות' in span:
                self.loc.prevbook = self.loc.book if self.loc.book != 'hashmata' else self.loc.prevbook
                self.loc.book = 'hashmata'
                sim = getGematria(re.findall('סימן ([א-ת\']{,4})', line)[0]) if 'סימן' in line else 5
                self.loc.siman = sim
                if '<B>' in line:
                    self.current.get_next_par().ar += f'<b>{re.findall("<B>(.*?)</B>", span)}</b><br>'
                line = re.sub(f'<span[^>]*>({re.escape(span)})</span>', '', line, flags=re.IGNORECASE)
                self.current.ar += f'<a siman={sim}></a>'
            else:
                line = re.sub(f'<span[^>]*>({re.escape(span)})</span>', r'\1', line, flags=re.IGNORECASE)
        line = re.sub('</?span[^>]*>', '', line, flags=re.IGNORECASE)
        bolds = re.findall('<b>(.*?)</b>', line, re.IGNORECASE)
        for bold in bolds:
            new = bold.strip()
            stripped = re.sub('[^א-ת ]', '', new)
            if new:
                line = re.sub(f'<b>{bold}</b> *', f'<b>{new}</b><br>', line, flags=re.IGNORECASE)
                if self.loc.book != 'hashmata':
                    if 'רעיא מהימנא' in stripped :
                        self.loc.book = 'raya'
                    elif stripped in ['תוספתא', "סא תוספתא"]:
                        self.loc.book = 'tosefta'
                    elif stripped == 'רזא דרזין':
                        self.loc.book = 'raza'
                    elif stripped == 'סתרי תורה':
                        self.loc.book = 'sitrei'
                    elif stripped == 'מדרש הנעלם':
                        self.loc.book = 'neelam'
                    elif stripped == 'כאן מתחיל אידרא דמשכנא':
                        self.loc.book = 'idra demishkena'
                    elif stripped == 'ספרא דצניעותא':
                        self.loc.book = 'tzniuata'
                    # else:
                    #     print(new)
            else:
                line = re.sub(f'<b>{bold}</b>', '', line, flags=re.IGNORECASE)

        if self.lang == 'he':
            pass
            # print('should be hebrew', line)
        if any(phrase in line for phrase in ['אָמְרוּ הַמָגִיהִים כָּאן מָצָאנוּ כָּתוּב פָּסוּק וַיִסָע כָּסֶדֶר כָּל אוֹת וְאוֹת בְּבַיִת אֶחָד בִּמְרוּבָּע עִם זה הַלָּשׁוֹן', 'עַד כְּאִילוּ קִיֵּים וְהָגִיתָ בּוֹ', "ואלו החילופים מצאנו בין הכתוב כאן לְבֵין הכתוב שם. דַּף ס''ג"]):
            self.current.ar += f'<br><small>{line}</small>'
        elif any(phrase in line for phrase in ['אמרו המגיהים מצאנו ראינו הפקודים האלה', "אמר רעיא מהימנא דוכתין וכו' עד על אתוון"]):
            self.current.get_next_par().ar += f'<small>{handle_line(line)}</small><br>'
        else:
            self.current = self.current.get_next_par()
            self.current.loc = self.loc
            self.current.ar += ' '.join(line.split())
            if not self.current.loc.book:
                self.current.loc.book = self.loc.book
            if not self.current.loc.book:
                self.current.loc.book = self.loc.book = 'guf'
            if not self.current.loc.pages:
                self.current.loc.pages = self.loc.pages
            if not self.current.loc.vol:
                self.current.loc.vol = self.loc.vol
            if self.current.loc.book == 'hashmata' and not hasattr(self.current.loc, 'siman'):
                self.current.loc.siman = self.loc.siman
            self.lang = 'he'

        dapim = re.findall('\(דף ([א-ת\']{1,5}) ?ע\'\'([אב])\)', line)
        for daf in dapim:
            page = getGematria(daf[0]) * 2 + getGematria(daf[1]) - 2
            if handle_line(re.split(f'\(דף {daf[0]} ?ע\'\'{daf[1]}\)', line)[0]):
                self.loc.pages.append(page)
            else:
                self.loc.pages = [page]

        if (re.search('עד כאן|ע"כ|ע\'\'כ.{3,20}$', line) and all(x not in line for x in ['עד כאן גליון', "(ע''כ) נדמו", "עד כאן דבר אחר"])) \
                or any(x in line for x in ["פקודא כ''ג לכבד אב וכו' פ''ג ע''א", "ע''כ רעיא מהימנא, שלח לך דף קע''ד ע''א ראשית עריסותיכם", "תצא דף ר''פ ע''ב כי ישבו אחיו יחדיו וכו", "אמור פ''ט ע''א כי אם בתולה", "פקודא ח''י לברכא ליה לקודשא בריך הוא וכו' ר''ע ע''ב", "תצא רע''ז ע''א כי ימצא איש נערה", "ע''ח ע''א פקודא בתר דא ", "וּמִכָּאן תֵלֵךְ ויקרא רס''ג ע''א שֵׁמַע יִשְׂרָאֵל", "כאן חסר ותמצאהו לקמן דף רמ''ו ע''ב ד''א ויחלום וכו", "שייך כאן פקודא לשרוף קדשים הנדפס בדף ל''ג ע''א", "כ''ט ע''א פקודא להקריב", "כ''ד ע''ב פקודא דא המועל בהקדש וכו", "ככתוב דף רכ''ה ע''ב אלא פגיעה בר''מ שם", " שפיר קאמר שם רט''ו ע''א", "רעיא מהימנא רי''ג ע''א", "פנחס רמ''ב ע''א, פקודא דא להקריב", "בִּבְנוֹי. זַכָּאָה חוּלְקֵהוֹן בְּהַאי עַלְמָא וּבְעַלְמָא דְאָתֵי", "פקודא מ''ד למפלח כהנא וכו' ס''ג ע''", "משפטים קי''ז לא תהיה אחרי רבים וכו", "בחבורא קדמאה קיבה רל''ד ע''ב", "ובחבורא קדמאה אמר ר' פנחס רכ''ד ע''א שייך רל''א ע''ב", "אמר רעיא מהימנא מילין אלין שייך כאן", "וְסִיהֲרָא אִתְמַלְּיָיא כְּגַוְונָא דָּא. מָלֵא כָּל הָאָרֶץ כְּבוֹדוֹ. בְּקַדְמִיתָא חָסֵר, וּכְעַן"]):
            er = self.loc.set_next_loc(book='guf')
            if er:
                print(self.current.ar)
        if 'עַד כָּאן הַאִדְרָא קַדִּישָׁא זוּטָא' in line:
            self.loc.set_next_loc(parasha='האזינו')

    def match_all(self):
        self.parashot = [[] for _ in range(55)]
        pnames = {}
        i = 0
        self.current = self.first
        while self.current.next:
            if self.current.loc.parasha == 'דברים':
                self.current = self.current.next
                continue
            if self.current.loc.parasha not in pnames:
                pnames[self.current.loc.parasha] = i
                i += 1
            if self.current.loc.book in ['idra raba', 'tzniuata'] and self.current.loc.book not in pnames:
                pnames[self.current.loc.book] = i
                i += 1

            if self.current.loc.book == 'hashmata':
                node = 51 + self.current.loc.vol
            elif self.current.loc.book in ['idra raba', 'tzniuata']:
                node = i-1
            else:
                node = pnames[self.current.loc.parasha]
            self.parashot[node].append(self.current)

            self.current = self.current.next

        self.ar = get_array()
        self.he = copy.deepcopy(self.ar)
        self.nones = 0
        for i, _ in enumerate(self.parashot):
            self.match_parasha(i)
        print('wow', self.nones)

    def match_parasha(self, i):
        pars = self.parashot[i]
        if i > 51:
            pars.sort(key=attrgetter('loc.siman'))
        books = {par.loc.book for par in pars}
        groups = []
        if len(books) == 1:
            groups = [{'pars': pars, 'refs': [Ref(f'Zohar TNG {i+1}').normal()]}]
        else:
            with open('sulam_map.json') as fp:
                sulam = json.load(fp)
            sulam = [x for x in sulam if f'TNG {i+1}:' in x['ref']]
            for s in sulam:
                if s['book'] in ['saba', 'rav metivta']:
                    s['book'] = 'guf'
            for book in books:
                groups.append({'pars': [par for par in pars if par.loc.book == book]})
                if book in ['idra raba', 'tzniuata']:
                    book = 'guf'
                groups[-1]['refs'] = [x['ref'] for x in sulam if x['book']==book]
        for group in groups:
            self.match(group['pars'], group['refs'])

    def match(self, pars, refs):
        pars = [par for par in pars if par.ar]
        te_texts = [par.ar for par in pars]
        matches = match_ref([Ref(r).text('he') for r in refs], te_texts, tokenizer, dh_extract_method=lambda x: ' '.join(tokenizer(x)[:15]),
                            place_all=True, place_consecutively=True, chunks_list=True)['matches']
        nones = len([m for m in matches if not m])
        print(nones, len(matches))
        self.nones += nones
        for m, p in zip(matches, pars):
            if m:
                self.a, self.b, self.c = m.sections
                self.a, self.b, self.c = self.a-1, self.b-1, self.c-1
                self.ar[self.a][self.b][self.c] += f'<br>{p.ar}'
                self.ar[self.a][self.b][self.c] = re.sub('^(?:<br>)*', '', self.ar[self.a][self.b][self.c])
                self.he[self.a][self.b][self.c] += f"<br>{p.he if p.he else ''}"
                self.he[self.a][self.b][self.c] = re.sub('^(?:<br>)*', '', self.he[self.a][self.b][self.c])
            else:
                if type(self.ar[self.a][self.b][self.c]) == str:
                    self.ar[self.a][self.b][self.c] = [self.ar[self.a][self.b][self.c], p.ar]
                    self.he[self.a][self.b][self.c] = [self.he[self.a][self.b][self.c], p.he]
                else:
                    self.ar[self.a][self.b][self.c].append(p.ar)
                    self.he[self.a][self.b][self.c].append(p.he)


        # sulam_texts = [Ref(ref).text('he').text for ref in refs]
        # sulam_texts = flat_array(sulam_texts)
        # sulam_texts = [re.sub('<i .*?/i>', '', t) for t in sulam_texts]
        #
        # sulam_texts = [re.sub('[^א-ת ]', '', t) for t in sulam_texts]
        # te_texts = [re.sub('[^א-ת ]', '', t) for t in te_texts]
        # text = CompareBreaks(te_texts, sulam_texts).insert_break_marks()
        # text = '<br>'.join(text)
        # text = re.split('β\d+β', text)
        # text = [re.sub('(?: *<br> *)*', '', t).strip() for t in text]

    def post(self):
        c = 1
        text_to_post = []
        server = 'http://localhost:9000'
        for text, lan in [(self.ar, ''), (self.he, ' [he]')]:
            for p, par in enumerate(text, 1):
                text_to_post.append(par)
                size = sum([sys.getsizeof(z) for x in text_to_post for y in x for z in y])
                if size > 4900000 or p == len(text):
                    text_version = {'title': 'Zohar TNG',
                                    'versionTitle': f'Torat Emet{c}{lan}',
                                    'versionSource': "",
                                    'language': 'he',
                                    'text': text_to_post
                                    }
                    c += 1
                    post_text('Zohar TNG', text_version, server=server)
                    text_to_post = [[] for _ in text_to_post]

    def make_csv(self):
        alts = library.get_index('Zohar TNG').alt_structs['Paragraph']['nodes']
        parashot = [x['text'] for x in alts[0]['titles'] if x['lang'] == 'he'][:1]
        alts.pop(0)
        parashot += [[x['text']for x in n['titles'] if x['lang'] == 'he'][0] for a in alts for n in a['nodes']]
        with open('zohar.csv', 'w') as fp:
            w = csv.DictWriter(fp, fieldnames=['ref', 'parasha', 'ot', 'sulam', 'torat emet', 'hebrew'])
            w.writeheader()
            for i in range(len(self.ar)):
                parasha = parashot[i]
                ot = 0
                if parasha == 'האדרא זוטא':
                    ot += 22
                for j in range(len(self.ar[i])):
                    for k in range(len(self.ar[i][j])):
                        ref = f'Zohar TNG {i+1}:{j+1}:{k+1}'
                        ot += 1
                        if parasha == 'האזינו' and ot == 23:
                            ot += 179
                        if parasha == 'בראשית' and ot == 483:
                            ot = 1
                            parasha = 'בראשית2'
                        torat = self.ar[i][j][k]
                        if type(torat) == str:
                            w.writerow({'ref': ref, 'parasha': parasha, 'ot': ot,
                                        'sulam': Ref(ref).text('he').text, 'torat emet': torat, 'hebrew': self.he[i][j][k]})
                        else:
                            w.writerow({'ref': ref, 'parasha': parasha, 'ot': ot,
                                        'sulam': Ref(ref).text('he').text, 'torat emet': torat.pop(0), 'hebrew': self.he[i][j][k].pop(0)})
                            for l in range(len(torat)):
                                w.writerow({'torat emet': torat[l], 'hebrew': self.he[i][j][k][l]})


def get_array():
    array = Ref('Zohar TNG').text('he').text
    return [[['' for _ in y] for y in x] for x in array]

with open('abbr.csv') as fp:
    ABBR = sorted(list(csv.DictReader(fp)), key=lambda x: len(x['abbr']), reverse=True)
def tokenizer(string):
    for ab in ABBR:
        rab = ab['abbr'].replace('"', '(?:"|\'\')')
        string = re.sub(rab, ab['full'], string)
    string = re.sub('<i .*?/i>', '', string)
    string = re.sub('<[^>]*>', '', string)
    string = re.sub('\([^\)]*\)', '', string)
    string = re.sub('\[[^\]]*\]', '', string)
    string = re.sub("'\"", ' ', string)
    string = re.sub('[^א-ת ]', '', string)
    return string.split()

def flat_array(array):
    new = []
    for x in array:
        if type(x) == list:
            new += flat_array(x)
        else:
            new.append(x)
    return new

def strip_html(text):
    tags = ['small', 'span', 'b', 'big']
    for tag in tags:
        text = re.sub(f'<{tag}.*?</{tag}>', '', text, flags=re.IGNORECASE)
        text = re.sub(f'</?{tag}[^>]*>', '', text, flags=re.IGNORECASE)
    text = re.sub('<!.*?>', '', text)
    while re.search('^ *[\.,]', text):
        text = re.sub('^ *[\.,]', '', text)
    return text.strip()

def handle_line(line):
    return ' '.join(strip_html(line).split())

def page(line):
    daf = re.findall('^\(דף ([א-ת\']{1,5}) ?ע\'\'([אב])\)$', line)
    if not daf:
        return
    global AMUD
    daf, amud = daf[0]
    old_amud = AMUD
    AMUD = getGematria(daf) * 2 + getGematria(amud) - 2
    if AMUD - old_amud != 1:
        print(f'going from page {old_amud} to {AMUD}')

if __name__ == '__main__':
    parser = Parser()
    parser.parse()
    parser.match_all()
    # parser.post()
    parser.make_csv()
