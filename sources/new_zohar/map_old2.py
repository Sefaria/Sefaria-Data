import copy
import csv
import json
import re
import sys
from operator import attrgetter
import django
django.setup()
from sefaria.model import *
from sources.functions import getGematria
from linking_utilities.parallel_matcher import ParallelMatcher
from linking_utilities.dibur_hamatchil_matcher import match_ref


class Parser():

    def __init__(self):
        self.parashot = []
        self.tosafot = [{}, {}, {}]

    def parse(self):
        prev_book = ''
        old_index = library.get_index('Zohar old')
        for i in range(52):
            if i in [17, 44]:
                continue
            node = old_index.alt_structs['Parasha']['nodes'][i]
            old_ref = [node['wholeRef']]
            if i == 16:
                old_ref = ['Zohar old 2:44a:1-67a:3']
            elif i == 50:
                old_ref.append('Zohar old 3:296b:9-299b:10')
            elif i == 51:
                old_ref[0] = re.sub('\-.*', '-296b:8', old_ref[0])

            self.vol = Ref(old_ref[0]).sections[0]

            if 'sharedTitle' in node:
                p = node['sharedTitle']
            else:
                p = node['titles'][0]['text']
            print(i, p)
            self.parashot.append({})

            if p in ['Eikev', 'Shoftim', 'Ki Teitzei']:
                self.book = "Ra'ya Mehemna"
            else:
                self.book = 'guf'

            for segment in [s for ref in old_ref for s in Ref(ref).all_segment_refs()]:
                line = segment.text('he', vtitle='New Torat Emet Zohar').text

                line = line.strip()
                if not line:
                    continue

                temp_book = self.book
                if self.book != 'hashmata':
                    start = ' '.join(line.split()[:7])
                    if ('השלמה מההשמטות' in start and "עי' עליו" not in start) or segment == Ref('Zohar old 3:193b:31'):
                        self.book = 'hashmata'
                        self.sim = getGematria(re.findall('סימן ([א-ת\']{,4})', line)[0]) if 'סימן' in line else 5
                    elif any(x in line for x in ['המדרש הנעלם', 'מדרש הנעלם']) and i not in {12, 13, 20}:
                        self.book = "Midrash HaNe'elam"
                    elif 'רעיא מהימנא' in start and i != 23:
                        self.book = "Ra'ya Mehemna"
                    elif 'תּוֹסֶפְתָּא' in start:
                        self.book = 'Tosefta'
                    elif any(x in start for x in ['סִתְרֵי תּוֹרָה', 'סתרי תורה']) and i not in {1, 31, 48}:
                        self.book = 'Sitrei Torah'
                    elif 'רזא דרזין' in start and i==17:
                        self.book = 'Raza DeRazin'
                    elif 'כאן מתחיל אידרא דמשכנא' in start:
                        self.book = 'Idra DeMishkena'
                    elif 'ספרא דצניעותא' in start and i==20 and p!='Sifra DeTzniuata':
                        p = 'Sifra DeTzniuata'
                        self.parashot.append({})
                        self.book = 'guf'
                if temp_book != self.book:
                    prev_book = temp_book

                if i == 48 and self.book == 'guf':
                    continue
                if re.search('^ *<b>.*?</b> *$', line) and len(line) < 20:
                    continue

                if self.book == 'hashmata':
                    if self.sim not in self.tosafot[self.vol-1]:
                        self.tosafot[self.vol - 1][self.sim] = []
                    self.tosafot[self.vol-1][self.sim].append(segment.normal())
                else:
                    indx = -1 if i != -2 else -2
                    if self.book not in self.parashot[indx]:
                        self.parashot[indx][self.book] = []
                    self.parashot[indx][self.book].append(segment.normal())


                if re.search('עד כאן|ע"כ|ע\'\'כ.{3,20}$', line):
                    self.book = 'guf'
                if 'עֲמִיקִין רְמִיזִין ע''כ.' in line or \
                        ((re.search('עד כאן|ע"כ|ע\'\'כ.{3,20}$', line) and all(
                        x not in line for x in ['עד כאן גליון', "(ע''כ) נדמו", "עד כאן דבר אחר"])) \
                        or any(x in line for x in ["פקודא כ''ג לכבד אב וכו' פ''ג ע''א",
                                                   "ע''כ רעיא מהימנא, שלח לך דף קע''ד ע''א ראשית עריסותיכם",
                                                   "תצא דף ר''פ ע''ב כי ישבו אחיו יחדיו וכו",
                                                   "אמור פ''ט ע''א כי אם בתולה",
                                                   "פקודא ח''י לברכא ליה לקודשא בריך הוא וכו' ר''ע ע''ב",
                                                   "תצא רע''ז ע''א כי ימצא איש נערה", "ע''ח ע''א פקודא בתר דא ",
                                                   "וּמִכָּאן תֵלֵךְ ויקרא רס''ג ע''א שֵׁמַע יִשְׂרָאֵל",
                                                   "כאן חסר ותמצאהו לקמן דף רמ''ו ע''ב ד''א ויחלום וכו",
                                                   "שייך כאן פקודא לשרוף קדשים הנדפס בדף ל''ג ע''א",
                                                   "כ''ט ע''א פקודא להקריב", "כ''ד ע''ב פקודא דא המועל בהקדש וכו",
                                                   "ככתוב דף רכ''ה ע''ב אלא פגיעה בר''מ שם", " שפיר קאמר שם רט''ו ע''א",
                                                   "רעיא מהימנא רי''ג ע''א", "פנחס רמ''ב ע''א, פקודא דא להקריב",
                                                   "בִּבְנוֹי. זַכָּאָה חוּלְקֵהוֹן בְּהַאי עַלְמָא וּבְעַלְמָא דְאָתֵי",
                                                   "פקודא מ''ד למפלח כהנא וכו' ס''ג ע''",
                                                   "משפטים קי''ז לא תהיה אחרי רבים וכו", "בחבורא קדמאה קיבה רל''ד ע''ב",
                                                   "ובחבורא קדמאה אמר ר' פנחס רכ''ד ע''א שייך רל''א ע''ב",
                                                   "אמר רעיא מהימנא מילין אלין שייך כאן",
                                                   "וְסִיהֲרָא אִתְמַלְּיָיא כְּגַוְונָא דָּא. מָלֵא כָּל הָאָרֶץ כְּבוֹדוֹ. בְּקַדְמִיתָא חָסֵר, וּכְעַן"])):
                    self.book = prev_book
                    if p == 'idra raba':
                        p = 'Nasso'
                        i = -2
                if "אכי''ר. האדרא רבא קדישא" in line and p != 'idra raba':
                    p = 'idra raba'
                    self.parashot.append({})
                    self.book = 'guf'

        self.parashot += self.tosafot

    def match(self):
        name = 'Zohar'
        nodes_dict = make_nodes_dict()
        self.nones = 0
        map = {}
        for i, par in enumerate(self.parashot):
            if i<13:continue
            print(i)
            if i > 51:
                refs = [ref for s in sorted(list(par)) for ref in par[s]]
                groups = [{'oldrefs': refs, 'newrefs': [f'{name}, Addenda, Volume {"I"*(i-51)}']}]
            else:
                done = False
                node = nodes_dict[i]
                print(node)
                if len(par) == 1:
                    if 'refs' in node:
                        newrefs = node['refs']
                        done = True
                    elif len(node['nodes']) == 1:
                        newrefs = node['nodes'][0]['refs']
                        done = True
                    else:
                        print('one book but more than one node', i)
                        newrefs = node['nodes'][0]['refs']
                    groups = [{'oldrefs': list(par.values())[0], 'newrefs': newrefs}]
                if not done:
                    groups = []
                    for book in par:
                        if book == 'guf':
                            try:
                                sn = node['nodes'][0]
                            except:
                                print(4444, node)
                        else:
                            try:
                                sn = [s for s in node['nodes'] if 'titles' in s and s['titles'][0]['text']==book]
                                if len(sn) == 1:
                                    sn = sn[0]
                                else:
                                    print(f"{book} not in {[sn['titles'][0]['text'] for sn in node['nodes'] if 'titles' in sn]}")
                                    print(f' all bokks in parasha: {list(par)}')
                                    continue
                            except:
                                print(5555, node)
                        groups.append({'oldrefs': par[book], 'newrefs': sn['refs']})
            for group in groups:
                old_texts = [Ref(r).text('he').text for r in group['oldrefs']]
                if not(old_texts):
                    print('no text', group)
                    continue
                print(2, group)
                matches = match_ref([Ref(r).text('he', vtitle='Torat Emet') for r in group['newrefs']], old_texts, tokenizer,
                                    dh_extract_method=lambda x: ' '.join(tokenizer(x)[:15]),
                                    place_all=True, place_consecutively=True, chunks_list=True)['matches']
                new_node_ref = Ref(group['newrefs'][0]).index_node.ref()
                if i > 51:
                    new_node_ref = Ref(f'Zohar, Addenda, Volume {"I" * (i-51)}')
                for m, r in zip(matches, group['oldrefs']):
                    if m:
                        map[r] = m.normal()
                    else:
                        try:
                            match = match_ref(new_node_ref.text('he', vtitle='Torat Emet'), Ref(r).text('he'), tokenizer,
                                              dh_extract_method=lambda x: ' '.join(tokenizer(x)[:15]), word_threshold=0.1,
                                              char_threshold=0.1)['matches']
                        except IndexError:
                            match = None
                        if match[0]:
                            map[r] = match[0].normal()
                        else:
                            map[r] = None
                            self.nones += 1
        print('wow', self.nones)
        with open('map_old_to_new-new.json') as fp:
            old = json.load(fp)
            old.update(map)
        with open('map_old_to_new-new.json', 'w') as fp:
            json.dump(old, fp)


def make_nodes_dict():
    nodes_dict = {}
    i = 0
    alt = library.get_index('Zohar').alt_structs['Daf']['nodes']
    nodes = [node for n in alt for node in n['nodes'][:-1]]
    nodes += [n['nodes'][-1] for n in alt]
    nodes_dict = {i: node for i, node in enumerate(nodes)}
    # for x, node in enumerate(alt):
    #     if 'nodes' not in node:
    #         nodes_dict[i] = node
    #         i += 1
    #     else:
    #         for sn in node['nodes']:
    #             nodes_dict[i] = sn
    #             i += 1
    return nodes_dict

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

if __name__ == '__main__':
    parser = Parser()
    parser.parse()
    parser.match()

