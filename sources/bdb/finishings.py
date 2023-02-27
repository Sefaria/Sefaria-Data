import re
import django
django.setup()
from sefaria.model import *

def add_to_path(sense, path, append_empty=False):
    path = path[:]
    if 'num' in sense:
        path.append(sense['num'])
    elif 'form' in sense:
        path.append(sense['form'])
    elif append_empty or path:
        path.append('')
    return path

def iterate_sense(senses, path=[]):
    for sense in senses['senses']:
        if 'definition' in sense:
            yield (sense, add_to_path(sense, path))
        else:
            yield from iterate_sense(sense, add_to_path(sense, path, append_empty=True))

def find_by_path(senses, path, return_all=False):
    if not path:
        return senses if return_all else senses[0]
    if path[0] == '':
        sense = [sense for sense in senses if 'num' not in sense and 'form' not in sense][0]
    else:
        sense = [sense for sense in senses if sense.get('num') == path[0] or sense.get('form') == path[0]][0]
    if 'definition' in sense:
        return sense
    else:
        return find_by_path(sense['senses'], path[1:], return_all=return_all)

def is_last_sense(senses, path):
    sense = find_by_path(senses, path, return_all=True)
    above = find_by_path(senses, path[:-1], return_all=True)[-1]['senses']
    if sense == above:
        return True

def find_super(senses, path):
    #doesn't work for senses tht are the first child without num of form
    path = path[:]
    while path and not path[-1]:
        path.pop(-1)
    for i in range(len(path)):
        if is_last_sense(senses, path):
            path.pop(-1)
        else:
            return path
    return path

def notes():
    regex = '\[?<em>Note[\.:]?</em>\.?(?: [12]\.)?'
    for le in LexiconEntrySet({'parent_lexicon': {'$regex': 'BDB.*?Dic'}}):
        notes = []
        for sense, path in iterate_sense(le.content):
            newnotes = []
            renotes = re.findall(regex, sense['definition'])
            renotes = [n for n in renotes if '.' in n or ':' in n]
            for renote in renotes:
                newnotes.append((re.findall(f'{renote}(?:.(?!{regex}))*', sense['definition'])[0], path, renote))
                sense['definition'] = re.sub(f'{renote}(?:.(?!{regex}))*', '', sense['definition'])
                sense['definition'] = sense['definition'].strip()
            notes += newnotes
        if notes:
            note, path, renote = notes[0]
            father = find_super(le.content['senses'], path)
            if le.headword == 'אֶ֫לֶף²':
                print(1)
                father = ['1.', 'c.']
            elif le.headword == 'חָרָה':
                print(2)
                father = ['Qal', '2.', 'b.']
            elif le.headword == 'עַתָּ֫ה':
                print(3)
                father = ['2.']
            father = find_by_path(le.content['senses'], father, return_all=True)
            for note, path, renote in notes:
                num = '1' if '1' in renote else '2' if '2' in renote else None
                note = {'definition': re.sub(renote, '', note).strip(), 'note': True}
                if num:
                    note['num'] = num
                father.append(note)
            le.save()

def afki():
    for x in range(11014, 720, -1):
        le = LexiconEntry().load({'rid': f'BDB{str(x).zfill(5)}'})
        le.rid = f'BDB{str(x+1).zfill(5)}'
        le.save()
    le.prev_hw = 'אַף כִּי'
    le.save()
    le = LexiconEntry({'headword': 'אַף כִּי',
                       'parent_lexicon': 'BDB Dictionary',
                       'rid': 'BDB00721',
                       'next_hw': 'אפד',
                        'prev_hw': 'אַף³',
                       'quotes': [],
                       'content': {'senses': [{'num': '1.', 'definition': '<em>furthermore</em> †<a data-ref="Ezekiel 23:40" href="/Ezekiel.23.40">Ez 23:40</a> <a data-ref="Habakkuk 2:5" href="/Habakkuk.2.5">Hb 2:5</a> (Ges <em>quin imo, quin etiam</em>).'},
                                              {'num': '2.', 'definition': 'in a qu., <em>indeed</em> (is it) <em>that</em> …? †<a data-ref="Genesis 3:1" href="/Genesis.3.1">Gn 3:1</a> <span dir="rtl">אַף כִּי־אָמַר אֱלֹהִים</span> <em>indeed, that</em> God has said …? i.e. has God <em>really</em> said …? (cf. <span dir="rtl">הַאַף</span> above).'},
                                              {'num': '3.', 'definition': 'with ref. to a preceding sentence (which is often introduced by <span dir="rtl">הֵן</span> or <span dir="rtl">הִנֵּה</span>), <em>yea, that</em> …! i.e. <em>how much more</em> (or <em>less</em>)! †<a data-ref="Proverbs 11:31" href="/Proverbs.11.31">Pr. 11:31</a> lo, the righteous is recompensed in the earth <span dir="rtl">אַֹ֝ף כִּי רָשָׁע וְחוֹטֵא</span> <em>’tis indeed that</em> (= how much more) the wicked and the sinner! <a data-ref="Proverbs 15:11" href="/Proverbs.15.11">15:11</a>; <a data-ref="Proverbs 17:7" href="/Proverbs.17.7">17:7</a>; <a data-ref="Proverbs 19:7" href="/Proverbs.19.7">19:7</a>, <a data-ref="Proverbs 19:10" href="/Proverbs.19.10">10</a> <a data-ref="Job 9:14" href="/Job.9.14">Jb 9:14</a>; <a data-ref="Job 15:16" href="/Job.15.16">15:16</a>; <a data-ref="Job 25:6" href="/Job.25.6">25:6</a> <a data-ref="I Samuel 14:30" href="/I_Samuel.14.30">1 S 14:30</a> <a data-ref="I Kings 8:27" href="/I_Kings.8.27">1 K 8:27</a> (= <a data-ref="II Chronicles 6:18" href="/II_Chronicles.6.18">2 Ch 6:18</a>) lo, the heavens … cannot contain thee <span dir="rtl">אַ֕ף כִּי הַבַּיִת הַזֶּה</span> <em>’tis indeed that</em> this house (cannot do so), i.e. <em>how much less</em> this house! <a data-ref="II Chronicles 32:15" href="/II_Chronicles.32.15">2 Ch 32:15</a>. So <span dir="rtl">וְאַף כִּי</span> †<a data-ref="Deuteronomy 31:27" href="/Deuteronomy.31.27">Dt 31:27</a> <a data-ref="I Samuel 21:6" href="/I_Samuel.21.6">1 S 21:6</a> (perhaps; v. RS<sup>Semi.436</sup> Dr<sup>Sm 293</sup>) <a data-ref="I Samuel 23:3" href="/I_Samuel.23.3">23:3</a> <a data-ref="II Samuel 16:11" href="/II_Samuel.16.11">2 S 16:11</a> <a data-ref="II Kings 5:13" href="/II_Kings.5.13">2 K 5:13</a>. (In <a data-ref="Job 35:14" href="/Job.35.14">Jb 35:14</a> (Hi De) <a data-ref="Nehemiah 9:18" href="/Nehemiah.9.18">Ne 9:18</a> <span dir="rtl">אַף כִּי</span> is simply = <em>yea, when</em> …)'}]}})
    le = LexiconEntry().load({'rid': f'BDB00720'})
    le.next_hw = 'אַף כִּי'
    le.save()

if __name__ == '__main__':
    notes()
    #nefesh and choze are done manually
    afki()
