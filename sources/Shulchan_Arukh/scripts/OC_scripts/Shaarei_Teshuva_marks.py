# encoding=utf-8

"""
Problem: Shaarei Teshuva uses the Be'er Hetev marks, but does not use all of them and has some of it's own.
Solution: Create unique marks for the Shaarei Teshuva

Step 1: Identify all locations where Be'er Hetev marks go out of order. Manually check if any of these are unique to
Shaarei Teshuva. If so - change the mark to the new Shaarei Teshuva mark. Keep a record of the locations where these
were added.

Step 2: Compare Be'er Hetev marks to the existing text on Sefaria. Any discrepancy should be checked against Shaarei
Teshuva. As before, any changes should be tracked.

Step 3: Parse Shaarei Teshuva and determine which Be'er Hetev markers need to have a Shaarei Teshuva marker added next
to them. Special care needs to be taken in places where a unique Shaarei Teshuva marker has already been added.
Three lists can be made for each siman:
    1) Available Be'er Hetev marks at which a Shaarei Teshuva mark can be added
    2) Shaarei Teshuva markers that are already there
    3) Shaarei Teshuva comments that need a marker
For each comment that needs a marker, I first check if the marker has already been set. If not, I can then look at the
available locations and set the appropriate marker. If no available locations exist, log the location and handle manually.
Once a location has been used to match, remove from the list of available matches.

Any ambiguity should be logged and handled manually. Ambiguity would be more than one comment in Shaarei Teshuva and
more than one mark. I don't think that can happen. For testing purposes, print locations with double marks in Shaarei
Teshuva to the console so that they can be manually reviewed.

It would be wise to first scan Shaarei Teshuva to make sure the marks follow some semblance of order. They don't, but
strange jumps may indicate a Siman jump that was missed. This would include out-of-order and duplicate comments.

Shaarei Teshuva marked with @62

I'll define a StructuredDocument class, which will have a file broken into it's subsequent chapters with no editing.
This can be used to call up individual chapters. StructuredDocument will have a "get_chapter method", and an
"edit_chapter" method. It will be instantiated with a filepath and a regex. This seems to be a decent class, look to see
if it has potential for re-use.
"""

import re
import codecs
from sefaria.model import *
from sources.functions import getGematria

class StructuredDocument:
    """
    class for extracting specific parts (i.e. chapters) of a text file. Pieces that exist outside the structure (an intro
    for example) will be included, but they will not be as easily accessible as the chapters.
    """

    def __init__(self, filepath, regex):
        with codecs.open(filepath, 'r', 'utf-8') as infile:
            lines = infile.readlines()

        sections, section_mapping = [], {}
        current_section, section_num, section_index = [], None, 0

        for line in lines:
            match = re.search(regex, line)
            if match:
                if len(current_section) > 0:
                    sections.append(u''.join(current_section))
                    if section_num:
                        section_mapping[section_num] = section_index
                    section_index += 1
                    current_section = []
                section_num = getGematria(match.group(1))

            current_section.append(line)
        else:
            sections.append(u''.join(current_section))
            section_mapping[section_num] = section_index

        self._sections = sections
        self._section_mapping = section_mapping

    def get_section(self, section_number):
        section_index = self._section_mapping[section_number]
        return self._sections[section_index]

    def _set_section(self, section_number, new_section):
        section_index = self._section_mapping[section_number]
        self._sections[section_index] = new_section

    def edit_section(self, section_number, callback, *args, **kwargs):
        old_section = self.get_section(section_number)
        new_section = callback(old_section, *args, **kwargs)
        self._set_section(section_number, new_section)

    def get_whole_text(self):
        return u''.join(self._sections)

    def write_to_file(self, filename):
        with codecs.open(filename, 'w', 'utf-8') as outfile:
            outfile.write(self.get_whole_text())

