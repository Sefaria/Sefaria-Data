# encoding=utf-8

"""
Objectives:
  1) Split files into Ammud structure
  2) Break each Ammud into workable paragraphs
  3) Create a new file with each Ammud marked and the paragraphs seperated by newlines (\n)

  Let's think about testing as well. For the three methods parse_pages, parse_paragraphs, prepare_output, what sort of
  inputs do they accept? Do they return the expected output?
"""

from data_utilities.ParseUtil import ParsedDocument, Description, ParseState

TEXT_OUTPUT, PARSING_STATE = [], ParseState()


def parse_pages(doc_lines: list) -> list:
    return []


def parse_paragraphs(page: str) -> list:
    return []


def prepare_output(segment: str, output_list: list, parsing_state: ParseState) -> None:
    """
    We'll use this method to get the text ready for output to a new file.

    To get the current page, use PARSING_STATE.get_ref('page')
    To get the current paragraph, use PARSING_STATE.get_ref('paragraph')

    Now attach the page number to the @22 with a newline
    Once we've edited the segment, append to TEXT_OUTPUT
    """


descriptors = [
    Description('page', parse_pages),
    Description('paragraph', parse_paragraphs)
]

parsed_doc = ParsedDocument('<add english title>', '<add hebrew title>', descriptors)

parsed_doc.attach_state_tracker(PARSING_STATE)
# open the file and load into a list (bonus points -> use a generator that doesn't load the whole file into memory)
raw_file = []
parsed_doc.parse_document(raw_file)
parsed_doc.filter_ja(prepare_output, TEXT_OUTPUT, PARSING_STATE)
with open('output_filename.txt', 'w') as fp:
    fp.write('\n'.join(TEXT_OUTPUT))

