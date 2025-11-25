import re
from collections import Counter, defaultdict
import django
django.setup()
from sefaria.utils.hebrew import gematria
from sefaria.model import *
from sources.functions import int_to_roman, post_index, post_text

def first_data_manipulation(data):
    data = re.sub('[‪‬‫]', '', data)
    data = data.replace('\t', ' ')
    data = data.replace("'", '׳').replace('"', '״').replace('׳׳', '״').replace('„', '״')
    data = data.replace('־', '-')
    data = data.replace('(', '*').replace(')', '(').replace('*', ')')
    data = data.replace('[', '*').replace(']', '[').replace('*', ']')
    data = '\n'.join([' '.join(l.split()) for l in data.split('\n')])
    data = re.sub(' ([.,:!?)\]])', r'\1 ', data)
    data = re.sub('([([]) ', r' \1', data)
    return data

def make_next_word_counter(lines):
    b=Counter()
    for l, line in enumerate(lines):
        if len(line) > 49 and re.search('[.:!]$', line):
            next_word = f'{lines[l+1]} '.split(' ')[0]
            b[next_word] += 1
    return b


def handle_paragraph(par):
    return par.strip()


def make_paragraphs(lines):
    next_word_counter = make_next_word_counter(lines)
    paragraphs = defaultdict(list)
    par = ''

    def append_par():
        nonlocal par
        paragraphs[key].append(handle_paragraph(par))
        par = ''

    for l, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        last = False
        length = len(line)
        # if length > 70:
        #     print(line, length)
        if line == "עיקר ב׳ השחיטה מתרת מיד והנחירה אחר יציאת נפש":
            if par:
                append_par()
            key = line
            continue
        if length < 45 and re.search('[^.:!]$', line):
            if length < 5 or line == 'רביעי' or re.search('^(חולין )?פרק', line): #garbage
                continue
            if re.search('^(<b>|הדרן עלך|כ״ד אביך|ה״ק משה שמואל|ת׳ ו׳ ש׳ ל׳)', line): #regular line that is end of paragraph
                last = True
            else: #structural title (but principle 2 is imssing)
                if par:
                    append_par()
                if line not in paragraphs:
                    key = line
                continue
        elif length > 49 and re.search('[.:!]$', line):
            next_word = f'{lines[l+1]} '.split(' ')[0]
            if next_word_counter[next_word] > 1: #assume this is end of paragraph
                last = True
            else: #assume same paragraph (after checking some cases)
                pass
        elif re.search('[.:!]$', line):
            last = True
        par = f'{par} {line}'
        if last:
            append_par()
    return paragraphs


def handle_main(paragraphs):
    new = [[],[],[]]
    new_word = ['ע״ש', 'תוס׳', 'רש״י', 'משנה', 'באו״ד', 'גמר׳', 'בא״ד', 'גמרא', 'ד״ה', 'במשנה', 'שם', 'בד״ה', 'עוד שם']
    for par in paragraphs:
        amud_b = '(?:שם )?ע״ב'
        if re.search(f'^(דף|{amud_b})', par):
            if re.search(f'^{amud_b}', par):
                if not len(new) // 2 == len(new) / 2:
                    new.append([])
            else:
                daf_re = re.search('^דף (.{1,4}) ע״([אב])', par)
                if daf_re:
                    daf = daf_re.group(1)
                    if daf == 'יוד':
                        daf = daf[0]
                    page = gematria(daf) * 2 + gematria(daf_re.group(2)) - 2
                    if len(new) > page:
                        print('going backward', par)
                    else:
                        new += [[] for _ in range(page-len(new))]
                else:
                    print(111, par)
            new[-1].append([])
        elif re.search(f'^({"|".join(new_word)})', par):
            new[-1].append([])
        new[-1][-1].append(par)
    return new


with open('dor4.txt') as fp:
    data = fp.read()

data = first_data_manipulation(data)
chars = set(data)
legal_chars = 'א-ת \n״\-׳\.\?!:\]\[\)\(,' + 'ַ ֶ ָ ְ ֵ' + '</b>'
unknown = re.findall(f'[^{legal_chars}]', ''.join(chars))
for i, c in enumerate(unknown):
    print(i, c)

lines = data.split('\n')
paragraphs = make_paragraphs(lines)
paragraphs['דיפולט'] = handle_main(paragraphs['דיפולט'])
print(list(paragraphs))
assert len(paragraphs) == 21

def make_ja_node(titles=None, depth=1):
    node = JaggedArrayNode()
    if titles:
        node.add_primary_titles(*titles)
    else:
        node.default = True
        node.key = "default"
        node.toc_zoom = 2
    node.depth = depth
    node.addressTypes = ['Integer']
    node.sectionNames = ['Paragraph']
    if depth != 1:
        node.addressTypes = ['Talmud', 'Integer', 'Integer']
        node.sectionNames = ["Daf", "Comment", "Paragraph"]
        node.toc_zoom = 2
    node.validate()
    return node

title = "Dor Revi'i"
he_title = 'דור רביעי'
main_titles = [('Foreword', 'הקדמה'), ('Preface', 'פתיחה'), ('Appendix', 'נספח'), ('', 'דיפולט'), ('General Preface', 'פתיחה כללית')]
record = SchemaNode()
record.add_primary_titles(title, he_title)
record.append(make_ja_node(main_titles[0]))
preface = SchemaNode()
preface.add_primary_titles(*main_titles[1])
preface.append(make_ja_node())
en_princs = ['Slaughter and Stabbing', 'Slaughter Permits Immediately and Stabbing after Soul Departing',
             'Unfit Slaughter', 'Slaughtering Measure in Beast and Fowl', "Slaughter's Disqualifications",
             'Knife Checking for Slaughter', 'Extended Limb, Dangling Limb and Ben Pekuah',
             'Uncertainty with regard to Slaughter and "Slaughtered, Permitted"', 'Terefah and Carcass',
             '18 Tereifot Stated to Moses at Sinai', 'Perforated Gullet']
preface_titles = [f'Principle {n+1}; {t}' for n, t in enumerate(en_princs)]
for en, he in zip(preface_titles, list(paragraphs)[2:13]):
    preface.append(make_ja_node((en, he)))
gen_preface = SchemaNode()
gen_preface.add_primary_titles(*main_titles[4])
gen_preface.append(make_ja_node(()))
for i in range(5):
    gen_preface.append(make_ja_node((int_to_roman(i+1), list(paragraphs)[-7+i])))
preface.append(gen_preface)
record.append(preface)
record.append(make_ja_node(depth=3))
record.append(make_ja_node(main_titles[2]))
record.validate()
index_dict = {
    'title': title,
    'categories': ["Talmud", "Bavli", "Acharonim on Talmud"],
    "schema": record.serialize(),
    'dependence': "Commentary",
    'base_text_titles': ['Chullin']
}
post_index(index_dict)

text_version = {
    'versionTitle': 'Cluj-Napoca, 1921',
    'versionTitle': 'Cluj-Napoca, 6000',
    'versionSource': 'https://www.nli.org.il/he/books/NNL_ALEPH990018691260205171/NLI',
    'language': 'he',
}

for en_t, he_t in main_titles[:4]:
    if he_t == 'נספח':
        he_t = 'הנספח'
    if en_t:
        en_t = f', {en_t}'
    print(he_t)
    text_version['text'] = paragraphs[he_t]
    post_text(f'{title}{en_t}', text_version, index_count='on')
en_t, he_t = main_titles[4]
print(he_t)
text_version['text'] = paragraphs[he_t]
post_text(f'{title}, {main_titles[1][0]}, {en_t}', text_version, index_count='on')
for i, en_t in enumerate(preface_titles):
    key = list(paragraphs)[i+2]
    print(key)
    text_version['text'] = paragraphs[key]
    post_text(f'{title}, {main_titles[1][0]}, {en_t}', text_version, index_count='on')
for i in range(5):
    key =list(paragraphs)[-7 + i]
    print(key)
    text_version['text'] = paragraphs[key]
    post_text(f'{title}, {main_titles[1][0]}, {main_titles[4][0]}, {int_to_roman(i+1)}', text_version, index_count='on')


