# -*- coding: utf-8 -*-

import argparse
import sys
import json
import csv
import re
import os, errno
import os.path
import requests

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from sefaria.model import *
from sefaria.utils.hebrew import is_hebrew


tag_map = {"bold": "b",
           "italic": "i",
           "underline": "u",
           'language-reference': 'language_reference',
           'language-key': 'language_code'
           }


class JastrowParser(object):
    data_dir = os.path.dirname(__file__) + '/../data/01-Merged XML'
    filename = 'Jastrow-full.xml'
    
    def __init__(self):
        self.dictionary_xml = ET.parse('{}/{}'.format(self.data_dir, self.filename))
        self.namespace = {'Jastrow': 'https://drive.google.com/drive/u/0/folders/0B3wxbTyZwMZPdWpTYzVDeE1TTjA',
                          'lang': 'http://www.w3.org/XML/1998/namespace'}  # TODO: possibly change namespace
        # self.entries_xml = self.dictionary_xml.getroot().findall(".//*[@type='entry']", self.namespace)
        self.chapters = self.dictionary_xml.find('body').findall('chapter')
        self.entries = []

    def parse_contents(self):
        print "BEGIN PARSING"
        Lexicon().delete_by_query({'name': 'Jastrow Dictionary'})
        LexiconEntry().delete_by_query({'parent_lexicon': 'Jastrow Dictionary'})
        self._make_lexicon_obj()
        for chapter in self.chapters:
            for entry in chapter.findall('entry'):
                # if entry.get('id') == 'A00080':
                #     break
                le = self._make_dictionary_entry(entry)
                self.entries.append(le)
                JastrowDictionaryEntry(le).save()
            break

    def _make_lexicon_obj(self):
        jastrow = Lexicon({'name': 'Jastrow Dictionary',
                           'language': 'heb.talmudic',
                           'to_language': 'eng',
                           'text_categories': [
                               "Tanakh, Targum, Onkelos",
                               "Talmud"
                           ]
                           })
        jastrow.save()

    def get_text(self, items):
        text = u''
        for item in items:
            tag = item.tag
            if tag == 'xref':
                text += u'<a class="xref" href="#{}">{}</a>'.format(item.attrib["rid"], item.text)
                self._current_entry['refs'].append(item.attrib["rid"])
            else:
                if tag in tag_map:
                    tag = tag_map[item.tag]
                if item.text:
                    text += u'<{}>{}</{}>'.format(tag, item.text.strip(), tag)
                else:
                    continue
                if item.tail:
                    text += item.tail.strip()
                else:
                    continue
        return text

    def find_refs(self, text):
        begin = -1
        end = -1
        for i, letter in enumerate(text):
            if begin == -1 and is_hebrew(letter):
                begin = i
            if begin != -1 and not is_hebrew(letter):
                end = i
                print text[begin:end]
                begin = -1
                end = -1

        return True

    def get_senses(self, child):
        senses = []
        for sense in list(child):
            cur_sense = {}
            for subsense in list(sense):                          
                try:
                    cur_sense[subsense.tag] = subsense.text.strip() + self.get_text(list(subsense))
                except AttributeError:
                    continue
                # print subsense.tag, cur_sense[subsense.tag]
                # self.find_refs(cur_sense[subsense.tag])

            senses.append(cur_sense)
        return senses

    def _make_dictionary_entry(self, entry):
        # get all div with type "Entry" and the n attr
        # get w lemma= + morph=
        # get strong's def and lexical notes from notes "exegesis" and "explanation"
        # get <list> items
        # parse each list item via its index into senses and definitions.
        self._current_entry = {}
        self._current_entry['parent_lexicon'] = 'Jastrow Dictionary'
        self._current_entry['rid'] = entry.get('id')
        self._current_entry['headword'] = []
        self._current_entry['refs'] = []
        self._current_entry['content'] = []

        for child in list(entry):
            tag = child.tag
            if tag in tag_map:
                tag = tag_map[child.tag]
            try:
                if child.tag == 'head-word':
                    self._current_entry['headword'].append(child.text.strip())
                elif child.tag == 'hw-number':
                    self._current_entry['headword'][-1] += child.text.strip()
                elif child.tag == 'senses':
                    self._current_entry['content'].extend(self.get_senses(child))

                # elif list(child) == []:
                #     self._current_entry[child.tag] = child.text.strip()
                else:
                    try:
                        self._current_entry[tag] = child.text.strip()
                    except AttributeError:
                        continue
                    if len(list(child)) > 0:
                        if tag == 'binyan':
                            binyan = {}
                            for item in list(child):
                                if item.tag == 'senses':
                                    binyan['senses'] = self.get_senses(item)
                                else:
                                    if item.text:
                                        binyan[item.tag] = item.text.strip()
                                    else:
                                        continue
                            self._current_entry['content'].append(binyan)
                        else:
                            if tag != 'language_reference':
                                continue
                            self._current_entry[tag] += self.get_text(list(child))

            except AttributeError:
                continue
        return self._current_entry



""" The main function, runs when called from the CLI"""
if __name__ == '__main__':
    print "INIT LEXICON"

    if True:
        print "parse lexicon"
        strongparser = JastrowParser()
        strongparser.parse_contents()
