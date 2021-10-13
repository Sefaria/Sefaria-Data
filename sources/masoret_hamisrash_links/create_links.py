import json
import django
django.setup()
from sefaria.model import *
import re
from sefaria.system.exceptions import InputError
from sources.functions import getGematria, post_link
from sefaria.model.text import logger
from data_utilities.dibur_hamatchil_matcher import match_ref

N,Y=0,0

class MidrashSegmentLinks():

    def __init__(self, ref):
        self.ref = ref
        self.midrash_text = Ref(ref).text('he', 'Midrash Rabbah, Vilna, 1878').text
        self.refs = []
        self.mm = 'Masoret HaMidrash'
        self.links = []

    def find_refs_segment(self):

        def clean_string(s):
            return re.sub('[^א-ת]', '', s)

        def check_ref(ref, verbose=True):
            try:
                if Ref(ref).text('he').text:
                    return 1
                if verbose:
                    print('no text', ref)
            except InputError:
                if verbose:
                    print('problem with ref', ref)

        def add_refs_by_tiltle(text, title):
            refs = []
            text = '(' + re.sub("[\(\)]", "", text) + ')'
            try:
                res = library._build_all_refs_from_string(title, text)
                for r in res:
                    if r.text('he').text:
                        refs.append(r)
                    else:
                        print(f'empty ref to {title}. in {text}. ref is {r}')
            except AssertionError as e:
                logger.info("Skipping Schema Node: {}".format(title))
            except TypeError as e:
                print(title,text)
                logger.error("Error finding ref for {} in: {}".format(title, text))
            return refs

        comment = ' '.join(self.comment.split())
        #yalkut shimoni
        yalkut = 'ילקוט'
        remez = '(?:רמ[זו.]|סימן)'
        if not comment:
            return
        if yalkut in comment:
            found = re.findall(f'{yalkut} ((?:[^ ]* ){{1,3}}?){remez} ([^ ]*)', comment)
            #if len(found) != comment.count(yalkut):
            #    print(comment, len(found))
            for occurence in found:
                book, siman = occurence
                siman = getGematria(siman)
                if any(parsh in book for parsh in ['פרשה', 'סדר']):
                    book = 'Torah'
                elif 'כאן' in book:
                    if 'Torah' in Ref(self.ref.split(' Rabbah')[0]).index.categories:
                        book = 'Torah'
                    else:
                        book = 'Nach'
                else:
                    try:
                        if 'Torah' in Ref(book+'א').index.categories:
                            book = 'Torah'
                        else:
                            book = 'Nach'
                    except InputError:
                        if any(nach in book for nach in ['ד"ה', 'דה"י', 'דניאל', 'נ"ך,']):
                            book = 'Nach'
                        elif 'שם' in book:
                            continue
                        else:
                            book = 'Torah'
                ref = f'Yalkut Shimoni on {book} {siman}'
                if not check_ref(ref, verbose=False):
                    continue
                self.refs.append(ref)
        #rabbah
        rabbah = 'רבה'
        reg = f'(\\b[^ ]*) רבה ([^ ]*) ([^ ]*)'
        found = re.findall(reg, comment)
        for f in found:
            if not f[0]:
                continue
            try:
                book = Ref(f[0]).index.get_title('he')
            except InputError:
                try:
                    book = re.sub('^(?:ו?ב|ד)', '', f[0])
                    if not book:
                        continue
                    book = Ref(book).index.get_title('he')
                except InputError:
                    continue
            if f[1] in ['פרשה', "פרש'"]:
                p = f[2]
            elif f[1].startswith('פ') and '"' in f[1]:
                p = f[1].replace('פ', '', 1)
            else:
                continue
            p = clean_string(p)
            if p == 'יוד':
                p = 'י'
            try:
                if Ref(f'{book} {rabbah} {p}').text('he').text:
                    self.refs.append(f'{book} {rabbah} {p}')
                else:
                    #print('no text', f'{book} {rabbah} {p}')
                    pass
            except InputError:
                #print('input error', f'{book} {rabbah} {p}')
                pass
        #pdra, tnda, pdrk, pr, seder olam, adrn
        for title in ["פרקי דר' אליעזר", "תנא דבי אליהו רבה", 'פסיקתא דרב כהנא', 'פסיקתא רבתי', 'סדר עולם רבה', 'סדר עולם זוטא']\
                + [index.get_title('he') for index in library.get_indexes_in_category('Minor Tractates', full_records=True)]: #zuta doesn't work
            temp = comment.replace('רבא', 'רבה').replace("תנא דבי אליהו זוטא", "תנא דבי אליהו זוטא, סדר אליהו זוטא").replace('פרק', '').replace('.','')
            if title in temp:
                if 'פסיקתא' in title:
                    temp = re.sub(" [פס]'? ", '', temp)
                self.refs += add_refs_by_tiltle(temp, title)
        #tanchuma
        tan = 'תנחומא'
        sed = 'ב?ס[דר]ר'
        par = 'פרשה'
        sim = "ב?סי(?:'|מן)"
        daf = 'דף'
        perek = 'פרק'
        tenp = comment.replace(' סוף ', ' ')
        found = re.findall(f'{tan} (?:{sed} |{par} )?([^ ]*) ([^ ]*)?', tenp)
        for f in found:
            seder = f[0].replace(".", "").replace('חוקת', 'חקת').replace('פינחס', 'פנחס')
            seder = re.sub('בחו?קו?תי', 'בחוקתי', seder)
            try:
                Ref(f'{tan}, {seder}')
            except InputError:
                try:
                    Ref(f'{tan}, כי {seder}')
                    seder = f'כי s{seder}'
                except InputError:
                    try:
                        seder = f'{seder} {f[1]}'
                        Ref(f'{tan}, {seder}')
                    except InputError:
                        continue
            siman = re.findall(f'{tan} (?:{sed} |{par} )?{seder} ([^ ]*)( [^ ]*)?', temp)
            for s in siman:
               if re.findall(sim, s[0]):
                    cleaned = clean_string(s[1])
                    if cleaned == 'יוד':
                        cleaned = 'י'
               elif s[0].startswith('ס') and '"' in  s[0]:
                   cleaned = clean_string(s[0].replace('ס', '', 1))
               else:
                   continue
               ref = f'{tan}, {seder} {cleaned}'
               if check_ref(ref, verbose=False):
                   self.refs.append(ref)
        #mishnah like
        masechtot = ['כלים ב"ק', 'כלים ב"מ', 'כלים ב"ב'] + [index.get_title('he').replace('משנה ', '') for index in
                    library.get_indexes_in_category("Mishnah", full_records=True)][:-1] + ['ב"ק', 'ב"מ', 'ב"ב', 'ר"ה', 'מו"ק', 'עוקצין', 'קדושין']
        temp = re.sub('סוף|ריש', '', comment)
        for m in masechtot:
            found = re.findall(f'([^ ]* )?({m})', comment)
            for f in found:
                if 'תוספתא' in f[0]:
                    per = "(?:פרק|פ')"
                    reg = f'{f[0]}{f[1]}(?: {per}) ([^ ]*)'
                    for tos in re.findall(reg, temp):
                        ref = f'תוספתא {m} {clean_string(tos[1])}'
                        if check_ref(ref, verbose=False):
                            self.refs.append(ref)
                elif 'ירוש' in f[0]:
                    continue
                else:
                    if Ref(f[1]).is_bavli():
                        reg = f'{f[0]}{f[1]}(?: {daf})? ([^ ]*)'
                        if f[0] == '':
                            reg = f'^{reg}'
                        for talmud in re.findall(reg, temp):
                            ref = f'{m} {clean_string(talmud).replace("יוד", "י")}'
                            if check_ref(ref, verbose=False):
                                self.refs.append(ref)
                    else:
                        reg = f'{f[0]}{f[1]}(?: {perek})? ([^ ]*)'
                        if f[0] == '':
                            reg = f'^{reg}'
                        for mish in re.findall(reg, temp):
                            ref = f'{m} {clean_string(mish).replace("יוד", "י")}'
                            if check_ref(ref, verbose=False):
                                self.refs.append(ref)
        #sifrei
        parashot_terms = TermSet({'category':"Torah Portions"})
        bamidbar = [t for t in parashot_terms if getattr(t, 'ref', False) and 'Numbers' in t.ref]
        devarim = [t for t in parashot_terms if getattr(t, 'ref', False) and 'Deuteronomy' in t.ref]
        bamidbar = '|'.join([tit for t in bamidbar for tit in t.get_titles('he') if 'פרשת' not in tit]) + '|ח"א'
        devarim = '|'.join([tit for t in devarim for tit in t.get_titles('he') if 'פרשת' not in tit]) + '|ח"ב'
        temp = comment
        while 'ספרי ' in temp:
            temp = temp.split('ספרי ', 1)[1].replace('פינחס', 'פנחס').replace('תצא', 'כי תצא').replace('חוקת', 'חקת')
            temp = re.sub('^סוף', '', temp)
            temp = re.sub("^(?:פרשה|פ'|סדר) ", '', temp)
            temp = re.sub('^ה?ברכה', 'וזאת הברכה', temp)
            if re.search(f'^({bamidbar})', temp):
                temp = re.sub(f'^({bamidbar})', '', temp).strip()
                ref = 'ספרי במדבר '
            elif re.search(f'^({devarim})', temp):
                temp = re.sub(f'^({devarim})', '', temp).strip()
                ref = 'ספרי דברים '
            elif re.search('^(?:פיסקא|כאן)', temp):
                if 'Bamidbar' in self.ref:
                    ref = 'ספרי במדבר '
                elif 'Devarim' in self.ref:
                    ref = 'ספרי דברים '
                else:
                    print(temp.split()[0])
                    continue
                temp = re.sub('^כאן', '', temp).strip()
            else:
                continue
            temp = re.sub('^(?:סוף |\.)', '', temp).strip()
            if not re.search("^(?:|פי?סקא|פיס'|פי'?|פ') ", temp):
                continue
            ref += clean_string(temp.split()[1])
            if check_ref(ref, verbose=False):
                self.refs.append(ref)

    def find_dh(self, segment, tag):
        segment = segment.replace('%', '').replace(tag, '%')
        segment = re.sub('<[^>]*>', '', segment)
        return segment.split('%')[1].split()[:7]

    def accurate_refs(self):
        global Y, N
        for ref in self.refs:
            if type(ref) == str:
                ref = Ref(ref)
            ref = ref.normal()
            if not Ref(ref).is_segment_level():
                ver = 'Wikisource Talmud Bavli' if Ref(ref).is_bavli() else 'Mishnah, ed. Romm, Vilna 1913' if 'Mishnah' in ref else 'Tsel Midrash Tanchuma' if 'Tanchuma' in ref else None
                if 'Rabbah' in ref:
                    base_tokenizer = lambda x: x.split()
                else:
                    base_tokenizer = lambda x: re.sub('[^\'" א-ת]', '', x).split()
                if not Ref(ref).text('he', ver).text:
                    ver = None
                match = match_ref(Ref(ref).text('he', ver), [self.dh], base_tokenizer=base_tokenizer, word_threshold=0.55, char_threshold=0.52)["matches"][0]
                if match:
                    Y += 1
                    ref = match.tref
                else:
                    N += 1
            self.links.append({'refs': [ref, self.ref],
                        'generated_by': 'masoret hamidrash',
                        'type': 'related',
                        'auto': True})


    def find_refs(self):
        tag_regex = f'<i data-commentator="{self.mm}" data-label="..?" data-order="..?">'
        for n, tag in enumerate(re.findall(tag_regex, self.midrash_text)):
            self.dh = ' '.join(self.find_dh(self.midrash_text, tag))
            mm_ref = f'{self.mm} on {self.ref}:{n+1}'.replace('Bereishit', 'Bereshit')
            self.comment = Ref(mm_ref).text('he').text
            self.find_refs_segment()
        self.accurate_refs()

links = []
for index in library.get_indexes_in_category('Midrash Rabbah', full_records=True):
    print(index)
    refs = index.all_segment_refs()
    for ref in refs:
        finder = MidrashSegmentLinks(ref.tref)
        finder.find_refs()
        links += finder.links
print(len(links))
print(N,Y)
with open('links.json', 'w') as fp:
    json.dump(links, fp)
#server = 'http://localhost:9000'
server = 'https://ezradev.cauldron.sefaria.org'
post_link(links, server=server, VERBOSE=False)
