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


tag_map = {"bold": "b",
           "italic": "i",
           "underline": "u",
           'language-reference': 'language_reference',
           'language-key': 'language_code'
           }


class JastrowParser(object):
    data_dir = '/Users/kevinwolf/Documents/Sefaria/data.Sefaria/dictionaries/Jastrow/data/01-Merged XML'
    filename = 'Jastrow-full.xml'
    # heb_stems = ["qal","niphal","piel","pual","hiphil","hophal","hithpael","polel","polal","hithpolel","poel","poal","palel","pulal","qal passive","pilpel","polpal","hithpalpel","nithpael","pealal","pilel","hothpaal","tiphil","hishtaphel","nithpalel","nithpoel","hithpoel"]
    # arc_stems = ["P'al","peal","peil","hithpeel","pael","ithpaal","hithpaal","aphel","haphel","saphel","shaphel","hophal","ithpeel","hishtaphel","ishtaphel","hithaphel","polel","","ithpoel","hithpolel","hithpalpel","hephal","tiphel","poel","palpel","ithpalpel","ithpolel","ittaphal"]

    def __init__(self):
        # self.heb_stem_regex = re.compile(ur'^\(('+"|".join(self.heb_stems)+')\)', re.IGNORECASE)
        # self.arc_stem_regex = re.compile(ur'^\(('+"|".join(self.arc_stems)+')\)', re.IGNORECASE)
        self.dictionary_xml = ET.parse('%s/%s' % (self.data_dir, self.filename))
        self.namespace = {'Jastrow': 'https://drive.google.com/drive/u/0/folders/0B3wxbTyZwMZPdWpTYzVDeE1TTjA', 'lang':'http://www.w3.org/XML/1998/namespace'} #TODO: possibly change namespace
        # self.entries_xml = self.dictionary_xml.getroot().findall(".//*[@type='entry']", self.namespace)
        self.chapters = self.dictionary_xml.find('body').findall('chapter')
        self.entries = []

    def parse_contents(self):
        print "BEGIN PARSING"
        self._make_lexicon_obj()
        for chapter in self.chapters:
            for entry in chapter.findall('entry'):
                le = self._make_dictionary_entry(entry)
                self.entries.append(le)
                JastrowDictionaryEntry(le).save()

    def _make_lexicon_obj(self):
        jastrow = Lexicon({'name': 'Jastrow Dictionary', 'language': 'heb.talmudic', 'to_language': 'eng'})
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

    def get_senses(self, child):
        senses = []
        for sense in list(child):
            cur_sense = {}
            for subsense in list(sense):
                # empty = True
                # for item in subsense.iter():
                #     if empty:
                #         if item.text:
                #             text = item.text.strip()
                #         empty = False
                #     else:
                #         tag = item.tag
                #         if tag == 'xref':
                #             text += u'<a class="xref" href="#{}">{}</a>'.format(item.attrib["rid"], item.text)
                #             self._current_entry['refs'].append(item.attrib["rid"])
                #         else:
                #             if tag in tag_map:
                #                 tag = tag_map[item.tag]
                #             text += u'<{}>{}</{}>{}'.format(tag, item.text.strip(), tag, item.tail.strip())                           
                try:
                    cur_sense[subsense.tag] = subsense.text.strip() + self.get_text(list(subsense))
                except AttributeError:
                    continue
                print subsense.tag, text
            
            senses.append(cur_sense)
        return senses

    def _make_dictionary_entry(self, entry):
        #get all div with type "Entry" and the n attr
        #get w lemma= + morph=
        #get strong's def and lexical notes from notes "exegesis" and "explanation"
        #get <list> items
        #parse each list item via its index into senses and definitions.
        self._current_entry = {}
        self._current_entry['parent_lexicon'] = 'Jastrow Dictionary'
        self._current_entry['rid'] = entry.get('id')
        self._current_entry['headword'] = []
        self._current_entry['refs'] = []
        self._current_entry['content'] = []
        try:
            for child in list(entry):
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
                        self._current_entry[child.tag] = child.text.strip()
                    except AttributeError:
                        continue
                    if len(list(child)) > 0:
                        if child.tag == 'binyan':
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
                            if child.tag != 'language-reference':
                                continue
                            self._current_entry[child.tag] += self.get_text(list(child))
        except AttributeError:
            print "poop"
        #         
        #     self._current_entry['headword'].append(child.text)
        #     # TODO: could be more to text word
        # self._current_entry['headword'] = headword_xml.get('lemma')
        # self._current_entry['pronunciation'] = headword_xml.get('POS')
        # self._current_entry['transliteration'] = headword_xml.get('xlit')
        # self._current_entry['language_code'] = headword_xml.get('{http://www.w3.org/XML/1998/namespace}lang')
        # defs = [x.text for x in entry.findall('strong:list/strong:item', self.namespace)]
        # odefs = [self._parse_item_depth(x) for x in defs]
        # self._current_entry['content'] = {}
        # self._current_entry['content']['morphology'] = headword_xml.get('morph')
        # self._current_entry['content']['senses'] = []
        # self._make_senses_dict(odefs, self._current_entry['content']['senses'])
        return self._current_entry


    def _make_senses_dict(self, definitions, senses, depth=1):
        while True:
            try:
                defobj = definitions[0]
                text = defobj['value'].strip()
                def_depth = defobj['depth']

                if def_depth == depth:
                    senses.append(self._detect_stem_information_in_definition(text))
                    #senses.append({'definition': text})
                    definitions.pop(0)
                elif def_depth > depth:
                    current_senses = senses[-1]['senses'] = []
                    self._make_senses_dict(definitions, current_senses, def_depth)
                else:
                    return
            except IndexError:
                break

    def _parse_item_depth(self, def_item):
        depth_re = re.compile(ur"^([^)]+?)\)", re.UNICODE)
        match = depth_re.search(def_item)
        depth = len(match.group())-1 if match else 1
        return {'depth': depth, 'value': depth_re.sub('', def_item,1).strip()}

    def _detect_stem_information_in_definition(self, def_item):
        heb_stem = self.heb_stem_regex.search(def_item)
        if heb_stem:
            return self._assemble_sense_def(heb_stem.group(1), self.heb_stem_regex.sub('',def_item))
        arc_stem = self.arc_stem_regex.search(def_item)
        if arc_stem:
            return self._assemble_sense_def(arc_stem.group(1), self.arc_stem_regex.sub('',def_item))
        return {'definition': def_item}

            #{'definition': text}

    def _assemble_sense_def(self, stem, defn):
        res = {'grammar': {'verbal_stem': stem}}
        if len(defn):
            res['definition'] = defn
        return res







""" The main function, runs when called from the CLI"""
if __name__ == '__main__':
    print "INIT LEXICON"
    #os.chdir(os.path.dirname(sys.argv[0]))
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--lexicon", help="Parse lexicon",
                    action="store_true")
    parser.add_argument("-w", "--wordform", help="Parse word forms",
                    action="store_true")
    args = parser.parse_args()


    if True:
        print "parse lexicon"
        strongparser = JastrowParser()
        strongparser.parse_contents()
    if args.wordform:
        print 'parsing word forms from wlc'
        wordformparser = WLCStrongParser()
        wordformparser.parse_forms_in_books()

