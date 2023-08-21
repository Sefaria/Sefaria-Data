import django
django.setup()
from sefaria.model import *
import re
from linking_utilities.dibur_hamatchil_matcher import match_ref
from sources.functions import post_link

def dh_extract_method(text, clean=True):
    dh = text.split('.')[0]
    if len(dh) > 30:
        dh = re.split(" וכו['׳] ", text)[0]
        if len(dh) > 30:
            if '<b>' in dh:
                dh = dh.split('</b>')[0]
            else:
                return
    dh = re.sub('</?b>', '', dh)
    if clean:
        dh = re.sub("(?:^| )(?:גמ['׳]|שם|מתני['׳]) ", ' ', dh)
    return dh

def tokenizer(string):
    return re.sub('<.*?>|\(.*?\)', '', string).split()

def match(ref):
    base_tref = ':'.join(ref.normal().replace("Haggahot Ya'avetz on ", '').split(':')[:-1])
    matches = match_ref(Ref(base_tref).text('he', vtitle='Wikisource Talmud Bavli'), ref.text('he'),
                        base_tokenizer=tokenizer, dh_extract_method=dh_extract_method)['matches']
    if matches:
        return matches[0]

def find_dh_comm(base, text, ref):
    def clean(string):
        string = re.sub('[\.:,\[\]\(\)]|<.*?>|^(מתני|גמ)\'', '', string).strip()
        return string
    dh = re.findall('ד[״"]ה (.*? [^\.]*)', re.sub('\(.*?\)', '', text))
    if not dh:
        return
    dh = dh[0]
    dh = clean(dh)
    base_page = Ref(f'{base} {ref.normal().split()[-1].split(":")[0]}')
    comments = base_page.all_segment_refs()
    base_text = base_page.text('he').text
    if 'Commentary of the Rosh' not in base:
        base_text = [x for y in base_text for x in y]
    base_text = [clean(x) for x in base_text]
    matches = [comm for comm in comments if comm.text('he').text and comm.text('he').text.split()[0] == dh.split()[0]]
    n = 2
    while len(matches) > 1:
        matches = [comm for comm in comments if comm.text('he').text and comm.text('he').text.split()[:n] == dh.split()[:n]]
        if len(matches) == 1:
            return matches[0]
        n += 1
        if n == 6:
            break
    if matches:
        return matches[0]

def find_base(ref):
    base = ref.normal().split(' on ')[1].split(':')[0]
    links = ref.linkset()
    links = [l for l in links if l.type=='commentary' and any(r.startswith(base) for r in l.refs)]
    if len(links) != 1:
        print(ref, len(links))
    else:
        return [r for r in links[0].refs if r.startswith(base)][0]

def link_misnah(title):
    print(title)
    masechet = title.split(" on ")[1]
    y, n = 0, 0
    links = []
    for mishna in Ref(title).all_subrefs():
        base = 'mishna'


def find_bavli_commntrator(text):
    rashi = re.search('רש[״"]י', text)
    tosfot = [re.search("תו[סם][׳']", text), re.search('תו?ד[״"]ה', text), re.search('תוספות', text)]
    tosfot_starts = [x.start() for x in tosfot if x]
    if tosfot_starts:
        tosfot = [x for x in tosfot if x and x.start() == min(tosfot_starts)][0]
    else:
        tosfot = None
    rashbam = re.search('רשב[״"]ם', text)
    ran = re.search('ר[״"]ן', text)
    rosh = re.search('רא[״"]ש', text)
    mefaresh = re.search('במפרש', text)
    commentrators = [rosh, ran, rashi, rashbam, tosfot, mefaresh]
    comm_starts = [x.start() for x in commentrators if x]
    if comm_starts:
        commentrator = [c for c in commentrators if c and c.start() == min(comm_starts)][0]
    else:
        return
    if re.search('שם|ד[״"]ה', text.split()[0]):
        return
    elif rashi is commentrator:
        return 'Rashi on '
    elif rashbam is commentrator:
        return 'Rashbam on '
    elif ran is commentrator:
        return 'Ran on '
    elif rosh is commentrator:
        return 'Commentary of the Rosh on '
    elif tosfot is commentrator:
        return 'Tosafot on '
    elif mefaresh is commentrator:
        return 'Mefaresh on '

def link_bavli(title):
    print(title)
    masechet = title.split(" on ")[1]
    y,n = 0,0
    links = []
    for page in Ref(title).all_subrefs():
        base = 'gmara'
        for comment in page.all_segment_refs():
            if comment == Ref("Haggahot Ya'avetz on Chullin 98a:1"):
                continue #unknown bug in match_ref
            text = comment.text('he').text
            dh = dh_extract_method(text, False)
            text = re.sub('<.*?>', '', text)
            if not dh:
                continue

            if  re.search('ד["״]ה|תו[סם][׳\']|רש[״"]י|רשב[״"]ם|ר[״"]ן|רא[״"]ש|תוספות', dh):
                temp = find_bavli_commntrator(text)
                if temp:
                    base = f'{temp}{masechet}'
                if base == 'gmara':
                    base = ''

            if not base:
                continue

            if re.search('^(?:שם|בא[״"]ד|בסה[״"]ד)', dh) and not re.search('^שם ד[״"]ה', text):
                pass #same base_ref
            elif base != 'gmara':
                base_ref = find_dh_comm(base, text, comment)
                if base_ref:
                    y+=1
                else:
                    n+=1
            else:
                base_ref = match(comment)
                if base_ref:
                    y+=1
                else:
                    n+=1
            if base_ref:
                links.append({
                    'refs': [base_ref.normal(), comment.normal()],
                    'type': 'commentary',
                    'ayto': True,
                    'generated_by': 'yaavetz parser'
                })
                if not base_ref.normal().startswith(masechet):
                    if 'Commentary of the Rosh on' in base_ref.normal():
                        talmud_ref = find_base(base_ref)
                    else:
                        talmud_ref = ':'.join(base_ref.normal().split(' on ')[1].split(':')[:-1])
                    links.append({
                        'refs': [talmud_ref, comment.normal()],
                        'type': 'commentary',
                        'ayto': True,
                        'generated_by': 'yaavetz parser'
                    })
    print(y/(y+n))
    server = 'https://new-shmuel.cauldron.sefaria.org'
    # server = 'http://localhost:9000'
    post_link(links, server=server, skip_lang_check=False)


for title in library.get_indices_by_collective_title("Haggahot Ya'avetz"):
    index = library.get_index(title)
    index.versionState().refresh()
    base = library.get_index(index.base_text_titles[0])
    if 'Seder' not in base.categories[-1]:
        continue
    if 'Mishnah' in base.categories:
        link_misnah(title)
    # elif 'Bavli' in base.categories:
    #     link_bavli(title)
