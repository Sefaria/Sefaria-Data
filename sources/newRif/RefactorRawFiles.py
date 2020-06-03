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
from rif_utils import note_reg, path

TEXT_OUTPUT, PARSING_STATE = [], ParseState()


def parse_pages(doc_lines: list) -> list:
    return [''.join(page) for page in ''.join(doc_lines).split('@20')]

def parse_paragraphs(page: str) -> list:
    new = page.replace('.', 'A').replace(':', 'B').replace('\n', 'A')
    for note in re.findall(note_reg, new): #now return colon and period which are in refs (and for that in notes)
        new = new.replace(note, note.replace('A', '.').replace('B', ':'))
    new = new.replace('B', 'A')
    return new.split('A')


def prepare_output(segment: str, output_list: list, parsing_state: ParseState) -> None:
    if PARSING_STATE.get_ref('paragraph') == 1:
        TEXT_OUTPUT.append('@20' + encode_hebrew_daf(section_to_daf(PARSING_STATE.get_ref('page')+1)))
    TEXT_OUTPUT.append(segment)


descriptors = [
    Description('page', parse_pages),
    Description('paragraph', parse_paragraphs)
]

parsed_doc = ParsedDocument('Rif Berakhot', 'רי"ף ברכות"', descriptors)

parsed_doc.attach_state_tracker(PARSING_STATE)
with open(path+'/rif/ריף ברכות מוכן.txt', encoding = 'utf-8') as file:
    raw_file = (line for line in file.readlines())
parsed_doc.parse_document(raw_file)
parsed_doc.filter_ja(prepare_output, TEXT_OUTPUT, PARSING_STATE)
with open(path+'/rif_segmented/rif_berakhot.txt', 'w') as fp:
    fp.write('\n'.join(TEXT_OUTPUT))
