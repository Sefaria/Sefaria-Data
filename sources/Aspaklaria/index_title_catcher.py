#encoding=utf-8

import django
django.setup()

from tqdm import *
from sefaria.model import *
from sefaria.system import exceptions
from bs4 import BeautifulSoup, element
from sources.functions import *
import string
import unicodecsv as csv
import json
import pickle
from data_utilities.util import getGematria, numToHeb
import codecs
from data_utilities.ibid import *
from aspaklaria_connect import client
from parse_aspaklaria import *

class Source(object):
    cnt = 0
    cnt_sham = 0
    cnt_resolved = 0
    cnt_not_found = 0
    global parser
    indexSet_dict = dict()
    found_term_dict = dict()

    def __init__(self, text, author):
        self.text = text
        self.author = author
        self.index = None
        self.indexs = []
        self.cat = None
        self.raw_ref = None
        self.ref = None

def get_index_via_titles(self, opt_index, words=u""):
    """
    use words to find the correct index (there is also more data to learn from...)
    :param words: words that may be titles
    :return:
    """
    str_of_words = u" ".join(words)
    library.get_titles_in_string(str_of_words)


    wrong_ref = True

    new_ref = None
    include_dependant = True
    look_here = self.extract_cat(include_dependant=include_dependant)
    if look_here:
        look_here.extend(self.indexs)
    if look_here:
        if wrong_ref:
            current_title = opt_index.title
            alt_ref_titles = map(lambda x: x['text'], opt_index.schema['titles'])
            look_here_titles = self.get_look_here_titles(look_here)
            nodes = []
            # if any(type(book) != Index for book in look_here):
            #     print self.raw_ref
            #     look_here = [book for book in look_here if isinstance(book, Index)]
            for a in look_here:
                if isinstance(a, Index) and a.is_complex():
                    nodes += a.nodes.children
            look_here_titles_nodes = [(node.key, node.index) for node in nodes]
            reduced_indexes = []
            if look_here_titles:
                try:
                    reduced_indexes = [index_t[0] for index_t in look_here_titles if (
                                (index_t[-1] in alt_ref_titles) or any(
                            [t for t in alt_ref_titles if t in index_t[-1]]))]
                except:
                    reduced_indexes = []
            reduced_indexes_nodes = [index_t for index_t in look_here_titles_nodes if
                                     (index_t[0] in alt_ref_titles)]
            reduced_indexes.extend(reduced_indexes_nodes)
            if len(reduced_indexes) == 1 or (reduced_indexes and all(
                    [x == reduced_indexes[-1] for x in reduced_indexes])):  # replace with `set()`?
                reduced_indexes = set(reduced_indexes)
                self.index = list(reduced_indexes)[0]
                try:
                    if isinstance(self.index, tuple):
                        index_node_name = self.index[1].title + u', ' + self.index[0]
                    else:
                        index_node_name = self.index
                    new_ref = Ref(u'{}'.format(index_node_name, re.sub(opt_index.title)))
                    self.ref = new_ref
                except exceptions.InputError as e:
                    new_ref = None  # so not to have new_ref that failed scrowing with stuff
                    print u"inputError for this string {}, extracted from this rawref {}".format(
                        u'{}'.format(self.index,
                                        re.sub(opt_index.title).strip()),
                        self.raw_ref)
            elif not reduced_indexes:  # len(reduced_indexes) == 0
                # couldn't find the title in the books maybe it is in there nodes
                if isinstance(look_here[0], Index):
                    if any(type(book) != Index for book in look_here):
                        print self.raw_ref
                        look_here = [book for book in look_here if isinstance(book, Index)]
                    look_here_nodes = reduce(lambda a, b: a + b,
                                             [ind.alt_titles_dict('he').keys() + ind.all_titles('he') for
                                              ind in
                                              look_here])  # todo: note: this was ind.alt_titles_dict('he').items() a few lines down the code called node_name = node[0]
                    look_here_nodes = filter(
                        lambda x: any(re.search(t, x[0]) or re.search(t, x) for t in alt_ref_titles),
                        look_here_nodes)
                    if len(look_here_nodes) >= 1:
                        node = look_here_nodes[0]  # todo: why take the first one??
                        node_name = node  # [0]
                        if node_name:
                            return node_name
                    #
                    #     depth = re.search(u'.*?(\d+):?(\d+)?.*?', self.ref.normal()).groups()
                    #     for d in depth:
                    #         if not d:
                    #             print "break"
                    #             break
                    #         try:
                    #             new_ref = Ref(u'{} {}'.format(node_name, numToHeb(d)))
                    #             break
                    #         except exceptions.InputError as e:
                    #             print u"inputError for this string {}, extracted from this rawref {}".format(
                    #                 u'{} {}'.format(node_name, numToHeb(d)), self.raw_ref.rawText)
                    #             if u"ילקוט שמעוני" in node_name:
                    #                 try:
                    #                     new_ref = Ref(u'{}, {}'.format(ind.title, d))
                    #                 except exceptions.InputError:
                    #                     print u"inputError for this string {}, extracted from this rawref {}".format(
                    #                         u'{} {}'.format(node_name, numToHeb(d)), self.raw_ref.rawText)
                    #         except IndexError as e:
                    #             print u'IndexError {} not sure why...'.format(e)
                    #     self.ref = new_ref
                    # if len(look_here_nodes) > 1:  # todo: what if there are more than 2 look_here_nodes?
                    #     print u'look at these i took the first: {}'.format(look_here_nodes[0])
            else:
                depenent_indexes = []
                main_indexes = []
                for ind_title in list(reduced_indexes):
                    if isinstance(ind_title, unicode):
                        ind = library.get_index(ind_title)
                    elif isinstance(ind_title, Index):
                        ind = ind_title
                    else:
                        ind = None
                    if ind and not ind.is_dependant_text():
                        main_indexes.append(ind_title)
                    elif ind and ind.is_dependant_text():
                        depenent_indexes.append(ind_title)
                if main_indexes:
                    self.index = main_indexes[0]
                elif depenent_indexes:
                    self.index = depenent_indexes[0]
                else:
                    self.ref = None

                if self.index:
                    try:
                        if isinstance(self.index, tuple):
                            index_node_name = self.index[1].title + u', ' + self.index[0]
                        else:
                            index_node_name = self.index
                        new_ref = Ref(u'{}'.format(index_node_name, re.sub(opt_index.title).strip()))
                        self.ref = new_ref
                    except exceptions.InputError as e:
                        new_ref = None  # so not to have new_ref that failed scrowing with stuff),

    else:  # couldn't find a indexs for this author
        parser.missing_authors.add(self.author)
    # if look_here and (self.index or wrong_ref):
    #     # than try to get the true title from the cat from look_here
    #     look_here_shared_title_word = u'({})'.format(
    #         u'|'.join(list(set.intersection(*[set(x.title.split()) for x in look_here]))))
    #     alt_ref_titles = map(lambda x: x['text'], self.ref.index.schema['titles'])
    #     found_index = [ind for ind in look_here for tanakh_book in alt_ref_titles if
    #                    tanakh_book in re.sub(look_here_shared_title_word, u'', ind.title).strip()]
    #     if found_index:
    #         if len(set(found_index)) > 1:  # assert len(found_index) == 0
    #             print "more than one index option"  # todo: problem with אלשיך דברים and with books I, II
    #             print found_index[0].title, found_index[-1].title
    #         self.index = found_index[0]
    #         try:
    #             new_ref = Ref(u'{} {}'.format(self.index.title, re.sub(self.ref.index.title, u'', self.ref.normal()).strip()))
    #             print u"deleting wrong: {} found new Index: {} new ref: {}".format(self.ref, self.index, new_ref)
    #             self.ref = new_ref
    #         except exceptions.InputError as e:
    #             print u"inputError for this string {}, extracted from this rawref {}".format(u'{} {}'.format(self.index.title, re.sub(self.ref.index.title, u'', self.ref.normal()).strip()), self.raw_ref)
    # tanakh is wrong but can't find the index ex: רש"ר הירש
    if self.index and not self.ref:
        ind = self.index
        # todo: look into the original catching see why it is not catching kalla. also see how to copy the intresting parts to here
        self.raw_ref.book = ind.title
        split_raw_text = re.sub(u'[\(\)]', u'', self.raw_ref.rawText).split()
        self.raw_ref.section_level = split_raw_text

        pass
    return self.ref