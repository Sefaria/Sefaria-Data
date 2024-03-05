import csv
import re
import django
django.setup()
from sefaria.model import *
from sefaria.utils.talmud import daf_to_section, section_to_daf
from parsing_utilities.text_align import CompareBreaks
from sources.functions import post_text


class Aligner:

    def __init__(self, page_ref):
        self.ref = Ref(page_ref)
        self.old_text = self.ref.text('he', 'Tikkunei Zohar').text
        self.old_tokens = []
        self.old_new_segmentation = []
        self.new_text = self.ref.text('he', 'Constantinople, 1740').text

    def _tokenize_old_with_mapping_to_original(self):
        paren_reg = '(\([^)]{,25}\))'
        for segment in self.old_text:
            parts = [x.strip() for x in re.split(paren_reg, segment) if x.strip()]
            parts_len = len(parts)
            for i, part in enumerate(parts):
                if re.search(paren_reg, part):
                    first_index = i
                    self.old_tokens.append({
                        'original': part,
                        'normalized': ''
                    })
                else:
                    first_index = len(self.old_tokens)
                    self.old_tokens += [{
                        'original': word,
                        'normalized': re.sub('[^ א-ת]', '', word)
                    } for word in part.split()]
                if i == 0:
                    self.old_tokens[first_index]['order'] = 'first'
                elif i == parts_len - 1:
                    self.old_tokens[-1]['order'] = 'last'

    def break_old_text(self, old_with_breaks):
        new_words = [word for segment in old_with_breaks for word in segment.split()]
        break_reg = '(β\d+β)'
        dont_add = False
        for token in self.old_tokens:
            if token['normalized']:
                word_was_added = False
                while not word_was_added:
                    word = new_words.pop(0)
                    parts = [x.strip() for x in re.split(break_reg, word) if x.strip()]
                    for part in parts:
                        if re.search(break_reg, part):
                            if dont_add:
                                dont_add = False
                            else:
                                self.old_new_segmentation.append([])
                        else:
                            self.old_new_segmentation[-1].append(token['original'])
                            word_was_added = True
            else:
                if token.get('order', '') == 'first':
                    self.old_new_segmentation.append([])
                    dont_add = True
                self.old_new_segmentation[-1].append(token['original'])
        self.old_new_segmentation = [' '.join(words) for words in self.old_new_segmentation]

    def get_aligned_text(self):
        self._tokenize_old_with_mapping_to_original()
        old_text = [' '.join(token['normalized'] for token in self.old_tokens)]
        new_text = [re.sub('[^ א-ת]', '', segment) for segment in self.new_text]
        comparer = CompareBreaks(old_text, new_text)
        old_with_breaks = comparer.insert_break_marks()
        self.break_old_text(old_with_breaks)
        return self.old_new_segmentation

if __name__ == '__main__':
    start = '17a'
    end = '62b'
    title = 'Tikkunei Zohar'
    new_text = [[] for _ in range(daf_to_section(start)-1)]
    for i in range(daf_to_section(start), daf_to_section(end)+1):
        daf = section_to_daf(i)
        tref = f'{title} {daf}'
        aligner = Aligner(tref)
        aligned = aligner.get_aligned_text()
        new_text.append(aligned)
    text_dict = {
        'language': 'he',
        'versionTitle': 'aligned',
        'versionSource': '',
        'text': new_text
    }
    server = 'http://localhost:8000'
    # server = 'https://new-shmuel.cauldron.sefaria.org'
    post_text(title, text_dict, server=server, index_count='on')

    with open('align_old.csv', 'w') as fp:
        w = csv.DictWriter(fp, fieldnames=['ref', 'old', 'new'])
        w.writeheader()
        for i in range(daf_to_section(start), daf_to_section(end)+1):
            daf = section_to_daf(i)
            tref = f'{title} {daf}'
            for seg in Ref(tref).all_segment_refs():
                w.writerow({'ref': seg.normal(),
                            'old': seg.text('he', 'aligned').text,
                            'new': re.sub('<[^>]*>|[A-Za-z]', ' ', seg.text('he', 'Constantinople, 1740').text)})

