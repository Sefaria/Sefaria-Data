import re
import django
django.setup()
from sources.EinMishpat.ein_parser import parse_em
import csv
from rif_utils import path, tags_map

def fix_file(string):
    replacing = [('פ"ק', 'פ"א'),
        ('טו?ח"מ', 'טור ח"מ'),
        ('טו?או?"ח', 'טור א"ח"'),
        ('טו?י"ד', 'טור י"ד'),
        ('טו?א"ה', 'טור א"ה'),
        ("מאכלו'", 'מאכלות'),
        ('יסודי תורה', 'יסודי התורה'),
        ('א"ת', 'א"ח'),
        ('א"ח"', 'א"ח'),
        ('א"כ', 'א"ח'),
        ('א"ח', 'טור א"ח'),
        ('טור טור', 'טור')]
    for a, b in replacing:
        string = re.sub(a, b, string)
    string = re.sub("עיי'? פ", "מיי' פ", string)
    string = re.sub(r'\([^\)]{1,5}\) \[([^\]]{1,5})\]', r'\1', string)
    return [line for line in string.split('\n') if line]
if __name__=='__main__':
    wrongs, goods = [], []
    for masechet in [tags_map]:
        try:
            with open(f'{path}/commentaries/EM_{masechet}.txt',encoding='utf-8') as fp:
                data = fp.read()
        except FileNotFoundError:
            continue
        data = fix_file(data)
        try:
            rfs = parse_em(f'EM{masechet}', 1, 'emerrors.txt', em_list=data)
        except:
            wrongs.append(masechet)
            continue
        goods.append(f'{masechet} {len(data)} lines {len(rfs)} returned {len([rf for rf in rfs if rf["Rambam"]])} rambams {len([rf for rf in rfs if rf["Semag"]])} smags {len([rf for rf in rfs if rf["Tur Shulchan Arukh"]])} turs')
        if masechet == 'Rosh Hashanah':
            with open(f'{path}/embb.csv', 'w', encoding='utf-8', newline='') as fp:
                awriter = csv.DictWriter(fp, fieldnames=['txt file line', 'Perek running counter', 'page running counter', 'Perek aprx', 'Page aprx', 'Rambam', 'Semag', 'Tur Shulchan Arukh', 'original', 'problem'])
                awriter.writeheader()
                for item in rfs: awriter.writerow(item)

    print('wrongs with', wrongs)
    for g in goods:print(g)
