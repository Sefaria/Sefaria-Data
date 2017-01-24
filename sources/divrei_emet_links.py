# encoding=utf-8

import re
from sefaria.model import *
from sources.functions import post_link
from data_utilities.dibur_hamatchil_matcher import match_ref


class DivreiLinks:

    def __init__(self):
        self.stored_links =[]
        self.divrei_refs = []
        self.base_refs = []

    @staticmethod
    def _dh_extract_method(some_string):
        raw_match = re.search(ur'<b>(.*?)</b>', some_string).group(1)
        raw_match = re.sub(u'[.,]', u'', raw_match)

        mulitple = re.split(ur"\u05d5?(\u05db|\u05d2)\u05d5'", raw_match)
        if len(mulitple) > 1:
            return reduce(lambda x, y: x if len(x) > len(y) else y, mulitple)  # finds the longest match
        else:
            return raw_match

    @staticmethod
    def _base_tokenizer(some_string):
        some_string = re.sub(u'\u05be', u' ', some_string)
        return some_string.split()

    @staticmethod
    def _filter(some_string):
        match = re.search(ur'<b>(.*?)</b>', some_string)
        if match is None:
            return False
        elif len(match.group(1)) <= 2:
            return False
        else:
            return True

    def get_refs(self, node):
        """
        :param SchemaNode node:
        """
        if node.is_leaf():
            nodes = [node]
        else:
            nodes = node.get_leaf_nodes()

        for leaf_node in nodes:
            if leaf_node.sharedTitle is None:
                continue
            else:
                term = Term().load({'name': leaf_node.sharedTitle})
                self.base_refs.append((Ref(term.ref)))
                self.divrei_refs.append(leaf_node.ref())

    def match(self, base_ref, comment_ref, verbose=False):
        assert isinstance(base_ref, Ref)
        assert isinstance(comment_ref, Ref)

        base_version = "Tanach with Text Only"
        mei_version = 'Divrei Emet, Zalkowa 1801'
        word_count = base_ref.text('he', base_version).word_count()

        return match_ref(base_ref.text('he', base_version), comment_ref.text('he', mei_version),
                         self._base_tokenizer, dh_extract_method=self._dh_extract_method, verbose=verbose,
                         rashi_filter=self._filter, char_threshold=0.4, boundaryFlexibility=word_count)

    def match_all(self, verbose=False):
        missed = []
        for base, mei in zip(self.base_refs, self.divrei_refs):
            matching = self.match(base, mei, verbose=verbose)
            if matching.get('matches') is None or matching.get('comment_refs') is None:
                continue
            for base_ref, diverei_ref in zip(matching['matches'], matching['comment_refs']):
                if base_ref is None or diverei_ref is None:
                    missed.append(diverei_ref)
                    continue
                else:
                    self.stored_links.append((base_ref.normal(), diverei_ref.normal()))
        print 'stored {} links, missed {}'.format(len(self.stored_links), len(missed))
        for i in missed:
            print i

    def post_links(self):
        links = [{
            'refs': [l[0], l[1]],
            'type': 'commentary',
            'auto': True,
            'generated_by': 'Divrei Emet linker'
        } for l in self.stored_links]
        post_link(links)

de = library.get_index("Divrei Emet")
linker = DivreiLinks()
tnode = de.nodes.children[-2]
linker.get_refs(tnode)
linker.match_all()
linker.post_links()
