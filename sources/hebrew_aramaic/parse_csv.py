import csv
from lxml import etree
import re
import traceback
import django
from pymongo.errors import DuplicateKeyError

from sefaria.helper.normalization import TableReplaceNormalizer, RegexNormalizer, NormalizerComposer
from sefaria.system.exceptions import InputError

django.setup()
from sefaria.model import *
from sefaria.model.linker.ref_resolver import AmbiguousResolvedRef
from sefaria.model.lexicon import KrupnikEntry
from sefaria.model.schema import DictionaryNode
from sources.functions import post_index, post_text, post_link
from linking_utilities.weighted_levenshtein import WeightedLevenshtein
from linking_utilities.dibur_hamatchil_matcher import match_ref


weighted_levenshtein = WeightedLevenshtein()
set1, set2, set3, set4 = set(), set(), set(), set()
y,n=0,0
hebrew_letters_range = range(1488, 1515)
nikkud_range = [x for x in range(1456, 1469)] + [1473, 1474, 1479]
geresh = [1523,1524]
legit_in_word = [x for x in hebrew_letters_range] + [x for x in nikkud_range] + [x for x in geresh]
other_in_hw = [32, 8230, 33, 63, 1470] #space, elipsis, !, ?, ־
legit_in_hw = legit_in_word + other_in_hw
linker = library.get_linker('he')
refs_report = []
no_refs = []

with open('abbr.csv') as fp:
    abbr = sorted(csv.DictReader(fp), key=lambda i: -len(i['from']))
    abbr = {row['from']: row['to'] for row in abbr}
ref_replacement_table = {**abbr, '׃': ';', ':': ';'}
bereshit_normalizer = RegexNormalizer('בר׳ (?=[^פ ][^ ]* [^ע])', r'בראשית ')
table_normalizer = TableReplaceNormalizer(ref_replacement_table)
yer_masechtot = [i.get_title('he').replace('תלמוד ירושלמי ', '') for i in library.get_indexes_in_corpus('Yerushalmi', full_records=True)]
masechet_reg = f"(?:{'|'.join(yer_masechtot)})"
yer = 'ירושלמי'
yer_lookbehind = f'(?<={yer} {masechet_reg} )'
yerushalmi_normalizer = RegexNormalizer(f'{yer_lookbehind}פ(?:״[א-כ]|[ט-כ]״[א-ט]) ', ' דף ')
perek = '([א-כפ]׳|[ט-כ]״[א-ט])'
page_lookahead = '(?= (?:[א-צ]׳|[ט-צ]״[א-ט]) ע״[א-ד])'
yerushalmi_no_peh = RegexNormalizer(f'{yer_lookbehind}{perek}{page_lookahead}', 'דף')
tags_normalizer = RegexNormalizer('[<>/bi]', '')
normalizer = NormalizerComposer(steps=[bereshit_normalizer, table_normalizer, yerushalmi_normalizer, yerushalmi_no_peh, tags_normalizer])

def is_venice(ref):
    if isinstance(ref, str):
        ref = Ref(ref)
    for node in getattr(ref.index, 'alt_structs', {'Venice': {'nodes': []}})['Venice']['nodes']:
        if ref.normal() in node['refs']:
            return True


def match(ref, text):
    strip = lambda t: re.sub('[^א-ת ]', '', t)
    base_tokenizer = lambda t: strip(t).split()
    dh_extract_method = lambda t: strip(t)
    oref = Ref(ref)
    if not oref.is_empty():
        try:
            base_tc = oref.text('he')
        except InputError:
            pass
        else:
            matches = match_ref(base_tc, [text], base_tokenizer, dh_extract_method=dh_extract_method)
            if matches['matches'][0]:
                return matches['matches'][0].normal()
    return 'NONE'


class Entry:

    def __init__(self, entry_string):
        self.xml = etree.fromstring(entry_string)
        self.id = self.xml.get('id')
        self.headword = None
        self.alt_headwords = []

        self.manipulate_xml_pre_parsing()
        self.handle_headwords()

    @staticmethod
    def print_element(element):
        print(etree.tostring(element, encoding="unicode"))

    @staticmethod
    def manipulate_text(text):
        text = text.replace('ױ', 'וי').replace('ֽ', 'ְ').replace('̇', 'ֹ').replace('--&gt;', '').replace('׃', ':')
        double = 'וו|יי'
        nikkud_after_double = 'ְֳִֵֶַָֹּ'
        text = re.sub(f'({double})([{nikkud_after_double}]+)', lambda m: f'{m.group(1)[0]}{m.group(2)}{m.group(1)[1]}', text)
        text = re.sub('[\u034F‬‍‎‏\*]', '', text)
        text = re.sub(' +\.', '.', text)
        return ' '.join(text.split())

    def get_text_of_only_text_element(self, element):
        text = element.text
        if not text:
            print('no string:')
            self.print_element(element)
            return ''
        return self.manipulate_text(text)

    def manipulate_headwords(self):
        for hw_tag in self.xml.findall(".//head-word"):
            text = self.get_text_of_only_text_element(hw_tag)
            text = text.replace('׃', ';')
            parts = re.split('([=;]|(?<!^)\()', text, 1)
            hws = re.split(',(?![^[]*\])', parts[0])
            hws = [hw for hw in hws if hw]
            if len(parts) > 1:
                _, delim, post = parts
                hws[-1] += delim + post
            hw_index = self.xml.index(hw_tag)
            self.xml.remove(hw_tag)
            for i, hw in enumerate(hws):
                new_hw_tag = etree.Element('head-word')
                new_hw_tag.text = hw.strip()
                self.xml.insert(hw_index+i, new_hw_tag)

    def manipulate_xml_pre_parsing(self):
        self.manipulate_headwords()

    def get_parsed_hw(self, hw_tag):
        parsed = {}
        headword = self.get_text_of_only_text_element(hw_tag)
        if '=' in headword:
            headword, *equals = headword.split('=')
            parsed['equals'] = [' '.join(e.replace(',', '').split()) for e in equals]
        if ';' in headword:
            headword, used = headword.split(';')
            parsed['used_in'] = used.strip()
        if re.search('[\.·–]', headword):
            #check nothing after
            splitted = re.split('[\.·–]', headword)
            splitted = [s.strip() for s in splitted if s.strip()]
            if len(splitted) > 1:
                row['biblical'] = 'something after biblical sign'

            parsed['biblical'] = True
            headword = re.sub('[\.·–]', '', headword)
        if '[' in headword:
            headword, emendation = re.findall('^([^[]*)\[([^]]*)', headword)[0]
            parsed['emendation'] = emendation
        if headword.startswith('('): #todo handle גּוֹבְעִין (גוביהן) ; גְּמִילוּת (חֲסָדִים) ; גַּעְגְּעָא (דְמַיָּא) ; (כפר) בְּקִיעִין ; (הֵימְ־) הֵימֶנְךָ, הֵימֶךָ, הֵימֶנּוּ, הֵימֶנָּהּ
            binyan_form = headword.split(')')[1]
            if binyan_form:
                binyan_form_tag = etree.Element('binyan-form')
                binyan_form_tag.text = binyan_form.strip()
                next_tag = hw_tag.getnext()
                next_tag_child = next(next_tag.iterchildren(), None)
                if next_tag.tag == 'binyan' and next_tag_child.tag == 'binyan-name':
                    next_tag.insert(0, binyan_form_tag)
                elif next_tag.tag != 'binyan': #TODO these 2 cases seems to be data problems and not handled
                    row['binyan'] = 'seems to miss binyan tag in the beginning'
                else:
                    row['binyan'] = 'binyan-name is missing in first binyan tag'
            headword = re.findall('\(([^)]*)\)', headword)[0]
            parsed['no_binyan_kal'] = True


        parsed['word'] = ' '.join(headword.split())

        pos_list = []
        next_element = hw_tag.getnext()
        while next_element is not None and next_element.tag == 'pos':
            pos_list.append(self.get_text_of_only_text_element(next_element))
            next_element = next_element.getnext()
        self.first_not_hw_element = next_element
        if pos_list:
            parsed['pos_list'] = pos_list

        return parsed

    def handle_headwords(self):
        for i, hw_tag in enumerate(self.xml.findall('head-word')):
            hw_dict = self.get_parsed_hw(hw_tag)
            if i == 0:
                self.headword = hw_dict
            else:
                self.alt_headwords.append(hw_dict)

    def handle_xrefs(self):
        global y,n
        for xref in self.xml.findall('.//xref'):
            rid = xref.get('rid')
            xref_hw = self.manipulate_text(xref.text).replace('.', '')
            new_xref = None
            if not rid:
                strip = lambda x: re.sub('[^ א-ת]', '', x)
                xref_hw_stripped = strip(xref_hw)
                # addenda_entries = [e for e in entries]# if e.id.startswith('A')]
                matches = [e for e in entries if strip(e.headword['word']) == xref_hw_stripped]
                if len(matches) == 1:
                    rid = matches[0].id
                    xref.set('id', matches[0].id)
                    new_xref = matches[0].id
                else:
                    optional_matches = []
                    for entry in entries:
                        if entry.id == self.id:
                            continue
                        hw = strip(entry.headword['word'])
                        permitted_distance = min(len(hw), len(xref_hw_stripped)) * .4
                        distance = weighted_levenshtein.calculate(hw, xref_hw_stripped, False)
                        if distance < permitted_distance:
                            optional_matches.append((entry, distance))
                    if len(optional_matches) > 0:
                        match = min(optional_matches, key=lambda x: x[1])[0]
                        rid = match.id
                        row['xref'] = f'suggested match for {xref_hw}: xref: {match.id}, hw: {match.headword["word"]}'
                        row['linked headword'] = (etree.tostring(match.xml, encoding="unicode"))
                    else:
                        row['xref'] = 'xref without rid'
            if rid:
                linked_entry = [e for e in entries if e.id == rid]
                if not linked_entry:
                    row['xref'] = f'rid does not exist: {rid}'
                else:
                    if len(xref) != 0:
                        print(f'xref with sub elements')
                    if not xref.text:
                        print('xref without text')
                    linked_entry = linked_entry[0]
                    ref_hw = linked_entry.headword['word']
                    new_xref = xref.text
            if new_xref:
                a_string = f'<a class="refLink" data-ref="{index_title}, {ref_hw}" href="/{index_title},_{ref_hw}" data-scroll-link="true">{new_xref}</a>'
                xref.text = a_string


    def handle_refs(self, text):
        # text = text.replace('׳', "'").replace('״', '"')
        # mishna_titles = [i.get_title("he").replace('משנה ', '') for i in library.get_indexes_in_corpus("Mishnah", full_records=True)]
        # mishna_reg = f'מ׳ ({"|".join(mishna_titles)})'
        # text = re.sub(mishna_reg, r'משנה \1', text)
        # text = re.sub('[^ \'"א-ת]', '', text)
        # text = f'({text})'
        # refs = library.get_refs_in_string(text, 'he')
        text = ' '.join(text.split())
        normalized_text = normalizer.normalize(text)
        mapping, subst_end_indices = normalizer.get_mapping_after_normalization(text)
        try:
            doc = linker.link(normalized_text, with_failures=True)
        except Exception as e:
            print(9999, e, text)
            return
        has_valid_refs = False
        replacings = []
        for rr in doc.resolved_refs:
            ambiguation = ''
            if isinstance(rr, AmbiguousResolvedRef):
                ref_text = rr.resolved_raw_refs[0].raw_entity.span.text
                optional_refs = [r.ref.normal() for r in rr.resolved_raw_refs]
                optional_refs = [r for r in optional_refs if 'Lieberman' not in r]
                if len(optional_refs) == 1:
                    ref = optional_refs[0]
                elif ref_text.startswith('ירושלמי'):
                    ref = ''
                    for r in rr.resolved_raw_refs:
                        if is_venice(r.ref):
                            ref = r.ref.normal()
                            break
                    if not ref:
                        pass
                        # print(7777, ref_text, [r.ref.normal() for r in rr.resolved_raw_refs])
                else:
                    ref = 'Ambiguous'
                    ambiguation = [r.ref.normal() for r in rr.resolved_raw_refs]
            else:
                ref_text = rr.raw_entity.span.text
                ref = rr.ref
                if ref_text.startswith('אסתר רבה'):
                    ref = Ref('Esther Rabbah')
                if ref_text.startswith('רות רבה'):
                    ref = Ref('Ruth Rabbah')
                if ref:
                    ref = ref.normal()

            if '(' in ref_text:
                if ref and 'Tosefta' in ref:
                    ref_text += ')'
                else:
                    ref_text = ref_text.split('(')[0].strip()
                    if not ref:
                        for new in linker.link(ref_text, with_failures=True).resolved_refs:
                            if not isinstance(new, AmbiguousResolvedRef):
                                ref = new.raw_entity.span.text
                            break

            norm_ind_start = normalized_text.find(ref_text)
            norm_range = (norm_ind_start, norm_ind_start + len(ref_text))
            orig_range = normalizer.norm_to_unnorm_indices_with_mapping([norm_range], mapping, subst_end_indices)[0]

            prev_words = text[:orig_range[0] or 1].strip().split(' ')
            if prev_words[-1] == 'תרג׳':
                orig_range = (orig_range[0]-5, orig_range[1])
                ref = None
            elif len(prev_words) > 1 and prev_words[-2] == 'תרג׳':
                orig_range = (len(' '.join(prev_words[:-2])) + 1, orig_range[1])
                ref = None
            orig_text = text[slice(*orig_range)]
            if orig_text.startswith('תרג׳') and not ref:
                tanakh_part = ' '.join(orig_text.split()[-3:])
                tanakh_part = normalizer.normalize(tanakh_part)
                try:
                    tanakhe_ref = Ref(tanakh_part)
                except:
                    pass
                    # print(88888, orig_text, tanakh_part, ref_text)
                else:
                    targ_part = ' '.join(orig_text.split()[:-3])
                    if targ_part == 'תרג׳':
                        if tanakhe_ref.index.categories[-1] == 'Torah':
                            targum_ref = 'Onkelos'
                        elif tanakhe_ref.index.categories[-1] == 'Prophets':
                            targum_ref = 'Targum Jonathan on'
                        elif 'Chronicles' in tanakhe_ref.index.title:
                            targum_ref = 'Targum of'
                        elif tanakhe_ref.index.categories[-1] == 'Writings':
                            targum_ref = 'Aramaic Targum to'
                        else:
                            targum_ref = 'NO'
                    elif targ_part in ['תרג׳ ירוש׳', 'תרג׳ יר׳']:
                        targum_ref = 'Targum Jerusalem,'
                    elif targ_part == 'תרג׳ יב״ע':
                        targum_ref = 'Targum Jonathan on'
                    elif targ_part == 'תרג׳ שני':
                        targum_ref = 'Targum Sheni on'
                    else:
                        targum_ref = 'NOOO'
                    try:
                        oref = Ref(f'{targum_ref} {tanakhe_ref.normal()}')
                        ref = oref.normal()
                    except:
                        ref = None
                        # print(888888, orig_text, f'{targum_ref} {tanakhe_ref.normal()}')

            if ref and ref.startswith('Jerusalem Talmud') and 'Shekalim' not in ref:
                if not is_venice(ref):
                    pass
                    # print(8888, ref_text, ref, normalized_text)


            if ref:
                has_valid_refs = True

            quot = segment_ref = base_text = ''
            if ref and Ref.is_ref(ref) and (not Ref(ref).is_segment_level() or Ref(ref).is_range()):
                remain = text[orig_range[1]:].strip()
                word = '[א-ת,׳״)(]+'
                regex = f'^(?:{word} ?){{,5}}[׃:;]'
                before_quot = re.search(regex, remain)
                if not before_quot:
                    pass
                else:
                    global y,n
                    remain = re.split(regex, remain)[1]
                    quot = re.split('[\.;׃:(\d]|וכו׳', remain)[0]
                    quot = ' '.join(quot.split()[:7])
                    segment_ref = match(ref, quot)
                    if segment_ref == 'NONE':
                        base_text = ''
                        if ref_text.startswith('ירושלמי'):
                            pass
                            # n+=1
                    else:
                        if ref_text.startswith('ירושלמי'):
                            y+=1
                        base_text = Ref(segment_ref).text('he').text
            if segment_ref or (ref and Ref.is_ref(ref) and Ref(ref).is_segment_level()  and not Ref(ref).is_range()):
                tref = segment_ref or ref
                if tref and tref != 'NONE' and not Ref(tref).is_empty():
                    replacings.append((orig_text, f'<a class="refLink" data-ref="{tref}" href="/{Ref(tref).url()}">{orig_text}</a>'))
                    links.append({
                        'refs': [tref, f'{index_title}, {self.headword["word"]} 1'],
                        'type': 'quotation',
                        'auto': True,
                        'generated_by': 'krupnik parser'
                    })


            refs_report.append({'identified text': ref_text,
                                'original text': orig_text,
                                'ref': ref,
                                'ghost ref': True if ref and Ref.is_ref(ref) and Ref(ref).is_empty() else None,
                                'ambiguation': ambiguation,
                                'xml': etree.tostring(self.xml, encoding="unicode"),
                                'quot': quot,
                                'segment ref': segment_ref,
                                'base text': base_text})
        if not has_valid_refs and ':' in text:
            no_refs.append(etree.tostring(self.xml, encoding="unicode"))
            pass
        for rep in replacings:
            text = text.replace(*rep)

        return text

    def handle_rest_naively(self, elements):
        rest = ''
        for element in elements:
            rest += f' {etree.tostring(element, encoding="unicode")}'
        content = rest
        for tag in ['italic', 'binyan-form']:
            t = tag[0]
            content = content.replace(f'<{tag}>', f' <{t}>').replace(f'</{tag}>', f'</{t}> ')
        content = re.sub('</?[^>/]{2,}>', ' ', content)
        content = content.replace('&lt;', '<').replace('&gt;', '>')
        content = ' '.join(content.split())
        content = self.handle_refs(content)
        if content:
            content = self.manipulate_text(content)
        return content

    def handle_sense(self, sense):
        sense_dict = {}
        number = sense.find("number")
        pos = sense.find("pos")
        definition = sense.find("definition")
        notes = sense.find("notes")
        if definition is not None and definition.find('pos') is not None:
            if pos is not None:
                print('pos in sense and another one in its definition')
            pos = definition.find('pos')
            definition.remove(pos)
            index = sense.index(definition) #this is redundant for this xml is not in use anympre, but i'm doing it for a case i'll print it and won't understand
            sense.insert(index, pos)
        if number is not None:
            sense_dict['number'] = int(re.search('\d', number.text).group(0))
        if pos is not None:
            sense_dict['pos'] = pos.text.strip()
        if definition is not None:
            tags = tuple(e.tag for e in definition)
            set1.add(tags)
            if 'bold' in tags or 'italic' in tags:
                row['definition'] = f'definition had bold or italic: {etree.tostring(definition, encoding="unicode")}'
            sense_dict['definition'] = self.handle_rest_naively([definition])
        if notes is not None:
            set3.add(tuple(e.tag for e in notes))
            sense_dict['notes'] = self.handle_rest_naively([notes])
        return sense_dict

    def handle_senses(self, senses):
        return [self.handle_sense(sense) for sense in senses]

    def handle_binyan(self, binyan):
        binyan_arr = []
        for element in binyan:
            if element.tag == 'senses':
                binyan_arr.append({'senses': self.handle_senses(element)})
            else:
                binyan_arr.append({element.tag: ' '.join(element.text.split())})
        return binyan_arr

    def handle_rest_tags(self, elements):
        if elements[0].tag == 'senses':
            self.content = {'senses': self.handle_senses(elements[0])}
        else:
            self.content = {'binyans': [self.handle_binyan(binyan) for binyan in elements]}

    def handle_rest(self):
        next_element = self.first_not_hw_element
        rest = []
        while next_element is not None:
            if next_element.tag == 'pgbrk':
                next_element = next_element.getnext()
                continue
            rest.append(next_element)
            next_element = next_element.getnext()
        if any(all(e.tag == tag for e in rest) for tag in ['senses', 'binyan']):
        # if False:
            self.handle_rest_tags(rest)
        else:
            # set1.add(tuple(e.tag for e in rest))
            global n
            n+=1
            row['tags problem'] = [e.tag for e in rest]
            self.content = self.handle_rest_naively(rest)
            row['xml'] = etree.tostring(self.xml, encoding="unicode")

    def parse(self):
        self.handle_xrefs()
        self.handle_rest()

index_title = 'A Dictionary of the Talmud'
version_title = 'A dictionary of the Talmud, London, 1927'
lexicon_name = 'Krupnik Dictionary'
server = 'http://localhost:8000'

hw_mappings = []
last_hw = ''
def handle_headwords():
    headwords = [entry.headword['word'] for entry in entries]
    first_letter = ''
    super_nums = {2: '²', 3: '³', 4: '⁴'}
    for i, hw in enumerate(headwords):
        same_hws_before = headwords[:i].count(hw)
        if same_hws_before:
            hw += super_nums[same_hws_before+1]
            entries[i].headword['word'] = hw
        global last_hw
        last_hw = hw
        if hw[0] != first_letter and hw not in ['כפר', 'בַּקִיקָא', 'פַעל', 'נְוַל²', 'לְפָנִים', 'מִפְּנֵי שֶ־', 'פְּנִים']:
            hw_mappings.append([hw[0], f'{index_title}, {hw}'])
        first_letter = hw[0]

def make_lexicon():
    if Lexicon().load({'name': lexicon_name}):
        return
    lexicon = Lexicon({
        'name': lexicon_name,
        'language': 'heb.talmudic',
        'version_lang': 'he',
        'to_language': 'he',
        'index_title': index_title,
        'version_title': version_title,
        'should_autocomplete': True,
        'text_categories': [],
    })
    lexicon.save()

def delete_lexicon_entries():
    LexiconEntrySet({'parent_lexicon': lexicon_name}).delete()

def make_lexicon_entries():
    entries_len = len(entries)
    for i, entry in enumerate(entries):
        le = KrupnikEntry({
            'parent_lexicon': lexicon_name,
            'rid': f'KRU{str(i).zfill(5)}',
            'headword': entry.headword['word'],
            'content': entry.content
        })
        headword_attrs = ['biblical', 'no_binyan_kal', 'emendation', 'used_in', 'equals', 'pos_list']
        for attr in headword_attrs:
            if entry.headword.get(attr):
                setattr(le, attr, entry.headword[attr])
        if entry.alt_headwords:
            le.alt_headwords = entry.alt_headwords
        if i != 0:
            le.prev_hw = entries[i-1].headword['word']
        if i != entries_len - 1:
            le.next_hw = entries[i+1].headword['word']
        try:
            le.save()
        except DuplicateKeyError:
            pass

def make_node(name, hname):
    node = JaggedArrayNode()
    node.add_primary_titles(name, hname)
    node.addressTypes = ['Integer']
    node.sectionNames = ['Paragraph']
    node.depth = 1
    node.validate()
    return node

def make_index():
    record = SchemaNode()
    record.add_primary_titles(index_title, 'מילון שימושי לתלמוד')
    record.append(DictionaryNode({'lexiconName': lexicon_name,
                           'firstWord': hw_mappings[0][1].split(',')[1].strip(),
                           'lastWord': last_hw,
                           'headwordMap': hw_mappings,
                           'default': True,
                           }))
    for titles in (('Preface', 'הקדמה'), ('Abbreviations', 'לוח ראשי תיבות'), ('Bibliography', 'ביבליוגרפיה')):
        record.append(make_node(*titles))
    index_dict = {'lexiconName': lexicon_name,
        "title": index_title,
        "categories": ['Reference', 'Dictionary'],
        "schema": record.serialize()}
    post_index(index_dict, server=server)

def make_version():
    text_version = {
            'versionTitle': version_title,
            'versionSource': 'https://www.nli.org.il/he/books/NNL_ALEPH990026160720205171/NLI',
            'language': 'he',
            'text': ['א']}
    post_text(f'{index_title}, Preface', text_version, server=server, index_count='on')

def post_links():
    post_link(links, skip_lang_check=False, VERBOSE=False)

def make_objects():
    make_lexicon()
    delete_lexicon_entries()
    make_lexicon_entries()
    make_index()
    make_version()
    post_links()

if __name__ == '__main__':
    with open('entries.csv') as fp:
        data = list(csv.DictReader(fp))
    entries = []
    links = []
    for row in data:
        try:
            entry = Entry(row['xml'])
            entries.append(entry)
        except Exception as e:
            print(1,e, row['xml'])
    handle_headwords()
    for row, entry in zip(data, entries):
        try:
            entry.parse()
        except Exception as e:
            print(2,e, row['xml'])
            print(traceback.format_exc())
    print(y,n,set1,set2,set3)

    report_name = 'definition'
    additional_fields = [report_name]
    fieldnames = ['xml'] + additional_fields
    with open(f'krupnik {report_name} report.csv', 'w') as fp:
        w = csv.DictWriter(fp, fieldnames=fieldnames)
        w.writeheader()
        for row in data:
            row = {k: row.get(k, '') for k in fieldnames}
            w.writerow(row)

    make_objects()

    with open('krupnik refs report.csv', 'w') as fp:
        fieldnames = list(refs_report[0].keys())
        if 'segment ref' not in fieldnames:
            fieldnames += ['quot', 'segment ref', 'base text']
        w = csv.DictWriter(fp, fieldnames=fieldnames)
        w.writeheader()
        for row in refs_report:
            if 'segment ref' not in row:
                row['segment ref'] = row['quot'] = row['base text'] = ''
            w.writerow(row)
    with open('krupnik no refs entries.csv', 'w') as fp:
        w = csv.DictWriter(fp, fieldnames=['xml'])
        w.writeheader()
        for row in no_refs:
            w.writerow({'xml': row})



if 'row' not in globals():
    row = {}
