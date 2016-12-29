# encoding=utf-8

import re
from sources.functions import post_link
from sefaria.model.text import library, Ref
from data_utilities.dibur_hamatchil_matcher import match_ref
from sefaria.model.schema import JaggedArrayNode, SchemaNode, Term


class MeiLinks:  # excuse the pun
    # TODO: Handle segments with no bold marker

    def __init__(self):
        self.stored_links = []
        self.version_map = {'Mei HaShiloach': 'Mei HaShiloach; Publication of Sifrei Izhbitza Radzin, Bnei Brak 2005.'}
        self.mei_refs = []
        self.base_refs = []

    def set_version_by_category(self, book_name):
        book_ref = Ref(book_name)
        if book_ref.is_tanach():
            self.version_map[book_name] = 'Tanach with Text Only'
        elif book_ref.is_bavli():
            self.version_map[book_name] = 'Wikisource Talmud Bavli'
        else:
            raise AttributeError(
                '{} does not match a default category, use set_version_by_book instead'.format(book_name))

    def set_version_by_book(self, book_name, vtitle):
        self.version_map[book_name] = vtitle

    @staticmethod
    def _dh_extract_method(some_string):
        return re.search(ur'<b>(.*?)</b>', some_string).group(1)

    @staticmethod
    def _base_tokenizer(some_string):
        some_string = re.sub(u'\u05be', u' ', some_string)
        return some_string.split()

    def get_refs(self, node):
        assert isinstance(node, SchemaNode)
        if node.is_leaf():
            nodes = [node]
        else:
            nodes = node.get_leaf_nodes()

        for leaf_node in nodes:
            assert isinstance(leaf_node, JaggedArrayNode)

            if leaf_node.sharedTitle is not None:
                term = Term().load({'name': leaf_node.sharedTitle})
                self.base_refs.append(Ref(term.ref))
                self.mei_refs.append(leaf_node.ref())

            else:
                for subref in leaf_node.ref().all_subrefs():
                    assert isinstance(subref, Ref)
                    if not subref.is_section_level():  # Don't bother trying to match depth 1 texts
                        break

                    if subref.is_empty():
                        continue
                    else:
                        base_book = leaf_node.primary_title('en')
                        base_chapter = subref.sections[0]
                        self.base_refs.append(Ref("{} {}".format(base_book, base_chapter)))
                        self.mei_refs.append(subref)

    def match(self, base_ref, comment_ref, verbose=False):
        assert isinstance(base_ref, Ref)
        assert isinstance(comment_ref, Ref)

        if self.version_map.get(base_ref.book) is None:
            self.set_version_by_category(base_ref.book)  # Books that can't be linked by category need to be set manually
        base_version, mei_version = self.version_map[base_ref.book], self.version_map[comment_ref.index.title]

        return match_ref(base_ref.text('he', base_version), comment_ref.text('he', mei_version),
                         self._base_tokenizer, dh_extract_method=self._dh_extract_method, verbose=verbose)

    def match_all(self):
        for base, mei in zip(self.base_refs, self.mei_refs):
            matching = self.match(base, mei)
            for base_ref, mei_ref in zip(matching['matches'], matching['comment_refs']):
                self.stored_links.append((base_ref.normal(), mei_ref.normal()))

    def post_links(self):
        links = [{
            'refs': [l[0], l[1]],
            'type': 'commentary',
            'auto': True,
            'generated_by': 'Mei HaShiloach linker'
        } for l in self.stored_links]
        post_link(links)


mei = library.get_index('Mei HaShiloach')
test_node = mei.nodes.children[0].children[1]
linker = MeiLinks()
linker.get_refs(test_node)
linker.match_all()
for i, j in linker.stored_links:
    print '{} : {}'.format(i, j)
