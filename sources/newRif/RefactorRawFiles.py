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
from data_utilities.ParseUtil import ParsedDocument, Description, ParseState
from sefaria.utils.talmud import section_to_daf
from sefaria.utils.hebrew import encode_hebrew_daf
from rif_utils import tags_map, path, netlen, rif_files

TEXT_OUTPUT, PARSING_STATE = [], ParseState()


def parse_pages(doc_lines: list) -> list:
    doc_lines, masechet = doc_lines
    pages = [''.join(page) for page in ''.join(doc_lines).split('@20')]
    if pages[0] == '': pages.pop(0)
    elif '@00' in pages[0] and len(pages[0])<23:
        pages[0] = pages.pop(0) + pages[0]
    pages = [page.strip() for page in pages]
    for n, page in enumerate(pages):
        pages[n] = [page, True, masechet] if n == 0 or pages[n-1][0][-1] == ':' or pages[n-1][0][-1] == '.' else [page, False, masechet]
    return pages

def parse_paragraphs(page: list) -> list:
    page, prev, masechet = page
    new = page.replace('.', '.A').replace(':', ':A').replace('\n', 'A')
    for note in re.findall(tags_map[masechet]['note_reg'], new): #now return colon and period which are in refs (and for that in notes)
        new = new.replace(note, note.replace('A', ''))
    for suspect in re.findall(r'(?:{}|{}|{})(?:(?!{}).)*[\.:]A'.format(*[tags_map[masechet][tag] for tag in ['gemara_refs', 'notes', 'tanakh_refs', 'end_tag']]), new):
        #mark places when newline come after period/colon suspected as part of ref
        new = new.replace(suspect[:-1], suspect[:-1]+'@$')
    for n, sec in enumerate(new.split('A')): #concut short lines
        if netlen(sec) < 6 and (n > 0 or prev) and sec != '':
            new = new.replace(sec+'A', sec)
    return [sec.strip() for sec in new.split('A') if sec.strip()!='']

def prepare_output(segment: str, output_list: list, parsing_state: ParseState) -> None:
    if parsing_state.get_ref('paragraph') == 0:
        output_list.append('@20' + encode_hebrew_daf(section_to_daf(parsing_state.get_ref('page')+1)))
    output_list.append(segment)

descriptors = [
    Description('page', parse_pages),
    Description('paragraph', parse_paragraphs)
]

for en_masechet, heb_masechet, file in rif_files:
    parsed_doc = ParsedDocument(en_masechet, heb_masechet, descriptors)

    parsed_doc.attach_state_tracker(PARSING_STATE)
    raw_file = (line for line in file.readlines())
    #parsed_doc.parse_document([raw_file, en_masechet])
    #parsed_doc.filter_ja(prepare_output, TEXT_OUTPUT, PARSING_STATE)
    with open(path+'/rif_segmented/rif_{}.txt'.format(en_masechet), 'w') as fp:
        fp.write('\n'.join(TEXT_OUTPUT))
