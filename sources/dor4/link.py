import django
django.setup()
from sefaria.model import *
import regex as re
from linking_utilities.dibur_hamatchil_matcher import match_text, match_ref
from sefaria.utils.hebrew import gematria
from sources.functions import post_link

TITLE = "Dor_Revi'i"


def remove_first_word(text):
    return ' '.join(text.split()[1:])

def join_regex_in_beginning(regexes):
    return f'^(?:{"|".join(regexes)})'

def get_links_to_base():
    lengthes = set()
    links = []
    book = None
    prev_ref = None
    y = n = 0
    for daf in Ref(TITLE).default_child_ref().all_subrefs():
        daf_string = daf.normal().split()[-1]
        for comment in daf.all_subrefs():
            if not comment.text('he').text:
                continue
            comment_ref_to_link = comment.as_ranged_segment_ref().normal()
            orig_seg = comment.text('he').text[0]
            segment = re.sub('^(?:דף (.{1,4}) )?ע״[אב][,\.]?', '', orig_seg).strip()

            rashi = ['רש״י']
            tosfot = ['תוס׳']
            gmara = ['משנה', 'גמר׳', 'גמרא', 'במשנה', 'גמ׳', 'בגמר׳', 'בגמ׳']
            dibbur = ['באו״ד', 'בא״ד', 'ד״ה', 'בד״ה']
            ibid = ['שם']
            od = ['ע״ש', 'עוד שם']
            new_word = od + rashi + tosfot + gmara + dibbur + ibid
            if not re.search(join_regex_in_beginning(new_word), segment):
                print(111, orig_seg[:20])  # 15 occurrences

            ash = segment
            segment = re.sub(join_regex_in_beginning(od) + ' ', '', segment)

            if segment.startswith('רש״י'):
                book = 'Rashi on Chullin'
                segment = remove_first_word(segment)
            elif segment.startswith('תוס׳'):
                book = 'Tosafot on Chullin'
                segment = remove_first_word(segment)
            elif re.search(join_regex_in_beginning(dibbur), segment):
                if book not in ['Rashi on Chullin', 'Tosafot on Chullin']:
                    print(222, segment, book)  # 0 occurrences
            elif re.search(join_regex_in_beginning(gmara), segment) or comment.normal() in ["Dor Revi'i 84a:9", "Dor Revi'i 84b:1"]:
                segment = re.sub(join_regex_in_beginning(gmara), '', segment)
                book = 'Chullin'
            elif re.search('^שם', segment) or re.search(join_regex_in_beginning(od), ash):
                segment = remove_first_word(segment)
            else:
                book = 'Chullin'

            base_ref = Ref(f'{book} {daf_string}')
            if book != 'Chullin':
                if re.search('^(?:(?:שם )?באו?״ד|בסוף הדבור)', segment):
                    if prev_ref:
                        links += [[comment_ref_to_link, mefaresh_ref], [comment_ref_to_link, gemara_ref]]
                else:
                    if not re.search('^ב?ד״ה', segment):
                        print(333, comment, orig_seg[:50])  # 4 occurrences
                    else:
                        segment = re.sub('^ב?ד״ה', '', segment)

                    def get_start(string, num_of_words):
                        string = re.sub('[^א-ת ]', '', string)
                        return ' '.join(string.split()[:num_of_words])

                    def get_beginnings():
                        dh = get_start(segment, dh_num_words)
                        beginnings = [get_start(c.text('he').text, dh_num_words) for c in comments]
                        return dh, beginnings

                    comments = base_ref.all_segment_refs()

                    for dh_num_words in range(4, 0, -1):
                        dh, beginnings = get_beginnings()
                        matches = match_text(dh.split(), beginnings)['matches']
                        good = [x for x in matches if x!=(-1,-1)]
                        if len(good) == 1:
                            match = [0]
                            break
                        if good:
                            while len(good) > 1 and dh_num_words < 8:
                                dh_num_words += 1
                                dh, beginnings = get_beginnings()
                                matches = match_text(dh.split(), beginnings)['matches']
                                good = [x for x in matches if x != (-1, -1)]
                            break
                    if not good:
                        prev_ref = None
                        print(444, comment_ref_to_link)  # 43 occurrences
                    elif len(good) > 1:
                        prev_ref = None
                        # print(555) # 1 occurrence
                    else:
                        index = matches.index(good[0])
                        mefaresh_ref = comments[index].normal()
                        gemara_ref = ':'.join(mefaresh_ref.split('on ')[1].split(':')[:-1])
                        links += [[comment_ref_to_link, mefaresh_ref], [comment_ref_to_link, gemara_ref]]
                        prev_ref = mefaresh_ref

            else: #link to talmud
                base_text = base_ref.text('he', 'Wikisource Talmud Bavli')
                dh = ' '.join(re.sub('[^א-ת ]', '', segment).split()[:5])
                dh = re.split(',|\.| וכו ', dh)[0]
                base_tokenizer = lambda x: re.sub('[^א-ת ]', '', x).split()
                match = match_ref(base_text, [dh], base_tokenizer)['matches'][0]
                if match:
                    y += 1
                    prev_ref = match.normal()
                    links.append([comment_ref_to_link, prev_ref])
                else:
                    n += 1
                    prev_ref = None
                    # print(comment_ref_to_link)

    print(y, n)

    links = [{
        'type': 'commentary',
        'refs': l,
        'auto': True,
        'generated_by': 'dor revii parser'
    } for l in links]
    return links

def get_rambam_links():
    links = []

    mishne = 'Mishneh Torah'

    halakhot_names = set()
    halakhot_reg_to_check = 'מ(?:\S*(?: |$)){1,2}'
    m = 'מ'
    halakhot = '(?:הלכ׳|הל׳) '
    halakhot_map = {
        'ע״ז': 'Foreign Worship and Customs of the Nations',
        'ט״א': 'Defilement of Foods',
        'טו״א': 'Defilement of Foods',
        'טומאת אוכלין': 'Defilement of Foods',
        'מ״א': 'Forbidden Foods',
        'מא״א': 'Forbidden Foods',
        'מאכלות אסורות': 'Forbidden Foods',
        'מעה״ק': 'Sacrificial Procedure',
        'אה״ט': 'Other Sources of Defilement',
        'אבה״ט': 'Other Sources of Defilement',
        'אבות הטומאה': 'Other Sources of Defilement',
        'חמץ ומצוה':'Leavened and Unleavened Bread',
        'בכורים': 'First Fruits and other Gifts to Priests Outside the Sanctuary',
        'דעות': 'Human Dispositions',
        'רוצח': 'Murderer and the Preservation of Life',
        'תרומות': 'Heave Offerings',
        'טו״מ': 'Defilement by a Corpse',
        'טומאת מת': 'Defilement by a Corpse',
        'מעשר': 'Tithes',
        'פסה״מ': 'Sacrifices Rendered Unfit',
        'שחיטה': 'Ritual Slaughter',
        'ה״ש': 'Ritual Slaughter',
        'הל״ש': 'Ritual Slaughter',
        'מלכים': 'Kings and Wars',
        'עבדים': 'Slaves',
        'שבת': 'Sabbath',
        'מכירה': 'Sales',
        'סנהדרין': 'The Sanhedrin and the Penalties within Their Jurisdiction',
        'פ״א': 'Red Heifer',
        'איסורי מזבח': 'Things Forbidden on the Altar',
        'יו״ט': 'Rest on a Holiday',
        'שבועות': 'Oaths',
        'ביה״ב': 'The Chosen Temple',
        'לולב': 'Shofar, Sukkah and Lulav',
        'ק״פ': 'Paschal Offering',
        'מחוסרי כפרה': 'Offerings for Those with Incomplete Atonement',
        'גזלה ואבדה': 'Robbery and Lost Property',
        'גירושין': 'Divorce'
    }
    halakhot_reg = f'{m}(?:{halakhot})?(?:{"|".join(halakhot_map)})'
    def get_halakhot(string):
        string = re.sub(f'^{m}(?:{halakhot})?', '', string)
        return halakhot_map[string]

    ot_reg = '(?:[א-ל]׳|[ט-ל]״[א-ט]|יו״ד)'
    ot_after_reg = '(?:״[א-ל]|[ט-ל]״[א-ט])'
    def get_ot(string):
        if string == 'יו״ד':
            return 10
        return gematria(string)

    perek = '(?:פרק|פר׳)'
    p = 'פ'
    perek_reg = f'(?:{p}{ot_after_reg}|{perek} {ot_reg})'
    def get_perek(string):
        ot = re.search(f'(?:{p}({ot_after_reg})|{perek} ({ot_reg}))', string).groups()
        ot = [x for x in ot if x][0]
        return get_ot(ot)

    halakha = '(?:הלכה|הלכ׳|הל׳)'
    h = 'ה'
    halakha_reg = f'(?:{h}{ot_after_reg}|{halakha} {ot_reg})'
    resh_reg = 'ריש'
    def get_halakha(string):
        if string == resh_reg:
            return 1
        ot = re.search(f'(?:{h}({ot_after_reg})|{halakha} ({ot_reg}))', string).groups()
        ot = [x for x in ot if x][0]
        ot = get_ot(ot)
        if ot > 30:
            print(666, string) # 1 occurence
            ot -= 30
        return ot


    optional_b = 'ב?'
    ibid = 'שם'

    patterm1 = f'{optional_b}({resh_reg}) ({perek_reg}) ({halakhot_reg})'
    patterm2 = f'{optional_b}({perek_reg}) ({halakha_reg}) ({halakhot_reg})'
    patterm3 = f'{optional_b}({perek_reg}) ({halakhot_reg}) ({halakha_reg})'
    patterm4 = f'({"|".join(halakhot_map)}) ({perek_reg}) ({halakha_reg})'

    def get_explicit_patterm_to_check():
        p1 = f'{optional_b}{resh_reg} {perek_reg} ({halakhot_reg_to_check})'
        p2 = f'{optional_b}{perek_reg} {halakha_reg} ({halakhot_reg_to_check})'
        p3 = f'{optional_b}{perek_reg} ({halakhot_reg_to_check}) {halakha_reg}'
        p4 = f'({halakhot_reg_to_check}) {perek_reg} {halakha_reg}'
        return f'{p1}|{p2}|{p3}|{p4}'

    def add_rambam_refs(string):
        raws = []
        for hal, cha, hil in re.findall(patterm1, string):
            raws.append((hil, cha, hal))
        for cha, hal, hil in re.findall(patterm2, string):
            raws.append((hil, cha, hal))
        for cha, hil, hal in re.findall(patterm3, string):
            raws.append((hil, cha, hal))
        for hil, cha, hal in re.findall(patterm4, string):
            raws.append((f'מ{hil}', cha, hal))
        for hil, cha, hal in raws:
            ref = f'{mishne}, {get_halakhot(hil)} {get_perek(cha)}:{get_halakha(hal)}'
            try:
                oref = Ref(ref)
            except:
                ref = ref.replace('Ritual Slaughter', 'Sabbath')
                try:
                    oref = Ref(ref)
                except:
                    print(777, ref, text)  # 0 occurrences
                    continue
            if oref.is_empty():
                print(888, ref)  # 0 occurrences
            else:
                links.append([ref, segment.normal()])


    # b= set()
    for segment in library.get_index(TITLE).all_segment_refs():
        text = segment.text('he').text
        # matches = re.findall(get_explicit_patterm_to_check(), text)
        # if matches:
        #     l = {m for match in matches for m in match if m}
        #     b |= l
        add_rambam_refs(text)

        # anonymous_patterm = f'(?<!{ibid} )({optional_b}{perek_reg} {halakha_reg})(?! {ibid})'
        # for match in re.finditer('.{,20}(' + anonymous_patterm + ').{,20}', text):
        #     full = match.group(0)
        #     if re.search(f'{patterm1}|{patterm2}|{patterm4}', full) or 'שם ב' +match.group(1) in full:
        #         continue
        #
        #     print(999, re.search(full+'{,50}', text).group())


    print(len(links))
    # print(b)
    links = [{
        'type': 'quotation',
        'refs': l,
        'auto': True,
        'generated_by': 'dor revii parser'
    } for l in links]
    return links

def get_yod_links():
    yod = 'יו״ד'
    for segment in Ref(TITLE).all_segment_refs():
        text = segment.text('he').text
        matches = re.findall('.{,20}' + yod + '.{,20}', text)
        for match in matches:
            print(match)



if __name__ == '__main__':
    links = []
    links += get_links_to_base()
    # links += get_rambam_links()
    # get_yod_links()
    # post_link(links, skip_lang_check=False, VERBOSE=False)
