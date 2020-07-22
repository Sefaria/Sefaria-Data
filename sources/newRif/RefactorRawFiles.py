# encoding=utf-8

"""
Objectives:
  1) Split files into Ammud structure
  2) Break each Ammud into workable paragraphs
  3) Create a new file with each Ammud marked and the paragraphs seperated by newlines (\n)

  Let's think about testing as well. For the three methods parse_pages, parse_paragraphs, prepare_output, what sort of
  inputs do they accept? Do they return the expected output?
"""
import re
from functools import partial
from data_utilities.ParseUtil import ParsedDocument, Description, ParseState
from sefaria.utils.talmud import section_to_daf
from sefaria.utils.hebrew import encode_hebrew_daf
from rif_utils import tags_map, path, netlen, rif_files

def paragraph_parser(page: str, new_sec: bool, masechet: str) -> list:
    new = page.replace('.', '.A').replace(':', ':A').replace('\n', 'A').replace('\u05c3', ':A') #replacing with A instead of spliting for next lines are simpler with string
    for note in re.findall(tags_map[masechet]['note_reg'], new): #now return colon and period which are in refs (and for that in notes)
        new = new.replace(note, note.replace('A', ''))
    suspected_note = r'(?:{}|{}|{})(?:(?!{}).)*[\.:]A'.format(*[tags_map[masechet][tag] for tag in ['gemara_refs', 'notes', 'tanakh_refs', 'end_tag']])
    for suspect in re.findall(suspected_note, new):
        #mark places when newline come after period/colon suspected as part of ref
        new = new.replace(suspect[:-1], suspect[:-1]+'@$')
        print(masechet, suspect)
    for n, sec in enumerate(new.split('A')): #concut short lines
        if netlen(sec) < 6 and (n > 0 or new_sec) and sec != '':
            new = new.replace(sec+'A', sec)
    if '@99' in new: #@99 is chapter end tag, with the hadran we want to be in his own line
        new = re.sub(r'([^A])@99', r'\1A@99', new)
        new = re.sub(r'(@99[^\n]*?)(@|<)', r'\1A\2', new)
    return [sec.strip() for sec in new.split('A') if sec.strip()!='']

def parse_pages(doc_lines: list) -> list:
    pages = ''.join(doc_lines).split('@20')
    if pages[0] == '': pages.pop(0)
    elif '@00' in pages[0] and len(pages[0]) < 18: #18 for ''@00 chapter one ' or so
        new_opening_line = pages[0] + pages[1]
        pages.pop(0)
        pages[0] = new_opening_line
    pages = [page.strip() for page in pages if page.strip()!='']
    newpages = []
    for n, page in enumerate(pages):
        newpages.append({'page': page.strip(), 'is_start_in_new_sec': True if n == 0 else last_is_punc})
        last_is_punc = True if page[-1] == '.' or page[-1] == ':' else False
    return newpages

def parse_paragraphs(page: dict) -> list:
    page, is_start_in_new_sec = page['page'], page['is_start_in_new_sec']
    return masechet_paragraph_parser(page, is_start_in_new_sec)

def prepare_output(segment: str, output_list: list, parsing_state: ParseState) -> None:
    if parsing_state.get_ref('paragraph') == 0:
        output_list.append('@20' + encode_hebrew_daf(section_to_daf(parsing_state.get_ref('page')+1)))
    output_list.append(segment)

descriptors = [
    Description('page', parse_pages),
    Description('paragraph', parse_paragraphs)
]

for en_masechet, heb_masechet, file in rif_files:
    masechet_paragraph_parser = partial(paragraph_parser, masechet = en_masechet)
    text_output, parsing_state = [], ParseState()
    parsed_doc = ParsedDocument(en_masechet, heb_masechet, descriptors)
    parsed_doc.attach_state_tracker(parsing_state)
    raw_file = (line for line in file.split('\n'))
    parsed_doc.parse_document(raw_file)
    parsed_doc.filter_ja(prepare_output, text_output, parsing_state)
    with open(path+'/rif_segmented/rif_{}.txt'.format(en_masechet), 'w') as fp:
        fp.write('\n'.join(text_output))
