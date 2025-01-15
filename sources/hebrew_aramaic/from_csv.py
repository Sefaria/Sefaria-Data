import csv
import re
from lxml import etree
from lxml.html.soupparser import fromstring

def get_data():
    with open('entries.csv') as fp:
        return list(csv.DictReader(fp))

def merge_entries(entry_string):
    row['problem'] = '2 entry tags'
    return f"{re.sub('(?<!^)</?entry[^>]*>', '', entry_string)}</entry>"

def find_tags(entry_string):
    opening_tags = re.findall('<([^/ >]*)[ >]', entry_string)
    closing_tags = re.findall('</([^>]*)>', entry_string)
    return opening_tags, closing_tags

def find_extra_tags(more_tags, less_tags): # only we know that one direction is problematic
    for tag in less_tags:
        more_tags.remove(tag)
    return more_tags

def handle_first_splitted(entry_string):
    opening_tags, closing_tags = find_tags(entry_string)
    row['problem'] = f'missing closing tags: {find_extra_tags(opening_tags, closing_tags)}'
    row['fixed'] = etree.tostring(fromstring(entry_string), encoding="unicode")[6:-7]

def handle_second_splitted(entry_string, prev_id):
    opening_tags, closing_tags = find_tags(entry_string)
    row['problem'] = f'missing opening tags: {find_extra_tags(closing_tags, opening_tags)}'
    return f'<entry id="{prev_id}+">{entry_string}'

def find_all_extra_tags(opening_tags, closing_tags):
    extra_tags = []
    for tag in opening_tags:
        try:
            closing_tags.remove(tag)
        except ValueError:
            extra_tags.append(tag)
    extra_tags += closing_tags
    return extra_tags

def handle_middle_splitted(entry_string):
    opening_tags, closing_tags = find_tags(entry_string)
    row['problem'] = 'no entry tags.'
    extra_tags = find_all_extra_tags(opening_tags, closing_tags)
    if extra_tags:
        row['problem'] += f' other unbalanced tags: {extra_tags}'

def handle_other_errors(entry_string, e):
    opening_tags, closing_tags = find_tags(entry_string)
    extra_tags = find_all_extra_tags(opening_tags, closing_tags)
    if extra_tags:
        row['problem'] = f'unbalanced tags: {extra_tags}'
    else:
        row['problem'] = e

def find_text_in_tags(tag, set_to_add):
    for child in entry.findall(f'.//{tag}'):
        text = child.text.strip() if child.text else ''
        if text:
            set_to_add.add(text)

def check_text(tag, allowed, fieldname):
    text = tag.text.strip() if tag.text else ''
    text = text.replace('"', '״')
    allowed_reg = f'(?:{"|".join(allowed)})'
    allowed_punc_reg = '[ ,]*'
    if text and not re.search(f'^{allowed_punc_reg}{allowed_reg}{allowed_punc_reg}$', text):
        row[fieldname] += text

def check_tag(tag_name, allowed):
    fieldname = f'{tag_name} pos'
    row[fieldname] = ''
    for tag in entry.findall(f'.//{tag_name}'):
        check_text(tag, allowed, fieldname)

def check_pos():
    allowed = ['ז׳',  'ז״ר',  'זו״נ',  'כנ׳',  'מה״ג',  'מה״ח',  'מה״י',  'מה״ק',  'מה״ש',  'נ׳',  'נ״ר',  'פ״י',  'פ״ע',  'פיו״ע',  'פעל',  'שה״מ',  'שם',  'איש',  'שם',  'מקום',  'ת׳',  'תה״פ', 'פעו״י', 'שם איש', 'שם מקום']
    check_tag('pos', allowed)

def check_binyan_name():
    allowed = ['אפ׳',   'אפע׳',   'אַפע׳',   'אתפ׳',   'הפ׳',   'הָפ׳',   'הפע׳',   'הָפע׳',   'הפעי׳',   'הָפעל',   'התפ׳',   'נפ׳',   'נתפ׳',   'פיעל',   'פיעל',   'פיעל',   'פעול',   'פַעל',   'פֻעל']
    check_tag('binyan-name', allowed)



if __name__ == '__main__':

    CHECK_TAGS = False #true neans check tags and not content, false assume tags are ok, check content

    data = get_data()
    poses, binyan_names = set(), set()
    _id = 0
    for r, row in enumerate(data):
        data[r] = row = {'xml': row['xml']}
        entry = row['xml'].strip()
        if CHECK_TAGS:
            if not entry:
                continue
            if entry.count('<entry') > 1:
                entry = merge_entries(entry)
            if not entry.startswith('<entry') and not entry.endswith('</entry>'):
                handle_middle_splitted(entry)
            elif not entry.startswith('<entry'):
                entry = handle_second_splitted(entry, _id)
            elif not entry.endswith('</entry>'):
                handle_first_splitted(entry)
            else:
                try:
                    entry = etree.fromstring(entry)
                except Exception as e:
                    handle_other_errors(entry, e)
            row['fixed'] = row.get('fixed') or ''
            row['problem'] = row.get('problem') or ''

        else:
            entry = etree.fromstring(entry)
            check_pos()
            check_binyan_name()


    fieldnames = data[0].keys()
    report_name = 'tags' if CHECK_TAGS else 'pos and binyan-name'
    with open(f'krupnik {report_name} report.csv', 'w') as fp:
        w = csv.DictWriter(fp, fieldnames=fieldnames)
        w.writeheader()
        for row in data:
            w.writerow(row)

    if CHECK_TAGS:
        print(len([row for row in data if row.get('problem')]))
        print(len([row for row in data if row.get('fixed')]))
    else:
        print(len([row for row in data if row.get('pos pos')]))
        print(len([row for row in data if row.get('binyan-name pos')]))
