# encoding=utf-8

"""
Outline:

Run through a tag, attempting to create two "chains". This can be done based on order. For example, an `A` followed by a
`B` can be connected. A subsequent `A` will belong to a different chain.

Identifying which commentator each chain goes can only be determined by external data. One possibility will be matching
to the expected number of comments in the respective commentary. Another will be by manual markup.

A problem can arise when the same value pops up twice, I.E, a `D` followed by another `D`. It will not be known to which
`D` we should connect the following `E`. This will be solved with external data - manually marking the problematic chain
and then connect to the correct chain (whose identity will be resolved by number of comments or manual markup).

Data needed for the resolution:
* Text with markers to resolve
* regex pattern
    - sub-patterns that will be useful for a manual resolution
    - we want 3 patterns -> text a, text b and unknown
    - the unknown pattern should also match the pattern for text a & text b
      e.g. @78 -> text a; @79 -> text b; @7\d -> unknown
* Number of comments in each commentary

The regex patterns can be set for a series of sections. The text needs to be added at each call to the resolution
method. Number of comments will also need to be supplied. That should probably be an independent method. Ultimately,
I'll create a class.

Regexes will be set on the object level. The object will also get filename for base text. Class will then derive number
of comments per commentary from Shulchan Arukh xml. Class should also break up the base text into a StructuredDocument
for easy editing.

We can break into chains in one method, then figure out which chain is which in another.

To derive identity:
1) Can I identify chains by number of comments in section? Check if both commentaries have the same number of comments
2) For each chain -> check that there is a match to 1 and only 1 commentary regex

I should create a Commentary class.
This class will have the commentary title, all the data necessary to parse a file, filepath and the unique regex for
this commentaries tag.

Run over the chains in reverse. Easiest to detect the last chains. I can have three lists of chains: one for each
commentary and an unknown.

"""

import re
import codecs
from data_utilities.util import StructuredDocument, getGematria


class Commentary:

    def __init__(self, name, tag_pattern):
        self.name = name
        self.tag_pattern = tag_pattern
        self.comments_per_section = {}

    def load_comments_per_section(self, filename, section_regex, comment_regex):
        document = StructuredDocument(filename, section_regex)
        chapter_values = document.get_chapter_values()

        for chapter_value in chapter_values:
            section_text = document.get_section(chapter_value)
            self.comments_per_section[chapter_value] = len(re.findall(comment_regex, section_text))


class TagResolver:

    def __init__(self, filename, section_pattern, unknown_pattern):
        self.unknown_pattern = unknown_pattern
        self.filename = filename
        self.document = StructuredDocument(filename, section_pattern)
        self.resolution_mapping = {}
        self.commentary_a = None
        self.commentary_b = None

    def _resolve_chains(self, chain_list, section):
        """
        :param chain_list:
        :param section
        :return:
        """
        resolution = {
            self.commentary_a.name: [],
            self.commentary_b.name: [],
            u'tbd': []
        }

        def a_to_a(x):
            resolution[self.commentary_a.name].extend(x[0])
            resolution[self.commentary_b.name].extend(x[1])

        def a_to_b(x):
            resolution[self.commentary_a.name].extend(x[1])
            resolution[self.commentary_b.name].extend(x[0])

        def bad_bad_bad(x):
            raise AssertionError(u"Chain marked positively for two commentaries at section {}".format(section))

        resolution_map = {
            ((False, False), (False, False)): lambda x: resolution[u'tbd'].append(x),
            ((False, False), (True, False)): a_to_b,
            ((False, False), (False, True)): a_to_a,
            ((False, True), (False, False)): a_to_b,
            ((False, True), (True, False)): a_to_b,
            ((False, True), (False, True)): bad_bad_bad,
            ((True, False), (False, False)): a_to_a,
            ((True, False), (True, False)): bad_bad_bad,
            ((True, False), (False, True)): a_to_a
        }

        # the last chains have the ability to match to number of comments. Solve those first, then work backwards
        chain_list = list(reversed(chain_list))

        comments_per_section = (self.commentary_a.comments_per_section[section], self.commentary_b.comments_per_section[section])
        if comments_per_section[0] != comments_per_section[1]:
            last_chains = chain_list[0]
            num_tags = [getGematria(i.group(1)) for i in last_chains]

            if num_tags == comments_per_section:
                resolution[self.commentary_a.name].extend(last_chains[0])
                resolution[self.commentary_b.name].extend(last_chains[1])
                chain_list = chain_list[1:]
            elif (num_tags[1], num_tags[0]) == comments_per_section:
                resolution[self.commentary_b.name].extend(last_chains[0])
                resolution[self.commentary_a.name].extend(last_chains[1])
                chain_list = chain_list[1:]
            else:
                print u"Comment number mismatch in section {}".format(section)

        for chain_pair in chain_list:
            # test against each commentary's unique regex
            # check each chain for any appearance of unique tags
            com_a_test = (any(re.search(self.commentary_a.tag_pattern, i.group()) for i in c) for c in chain_pair)
            com_b_test = (any(re.search(self.commentary_b.tag_pattern, i.group()) for i in c) for c in chain_pair)

            # ensure that we don't have cases where both chains have been positively marked for both commentaries
            if all(com_a_test) or all(com_b_test):
                raise AssertionError(u"Chain marked positively for two commentaries at section {}".format(section))
            resolution_map[(com_a_test, com_b_test)](chain_pair)

        self.resolution_mapping[section] = resolution

    @staticmethod
    def build_chains(text, pattern, group=1):
        def digitify(x):
            return getGematria(x)

        chains = []
        current_chain = ([], [])

        all_tags = re.finditer(pattern, text)
        for tag in all_tags:

            # both chains are empty
            if all([len(i) == 0 for i in current_chain]):
                current_chain[0].append(tag)

            # one chain is empty -> no need to worry about broken chains
            elif len(current_chain[1]) == 0:
                if digitify(tag.group(group)) - 1 == digitify(current_chain[0][-1].group(group)):
                    current_chain[0].append(tag)
                else:
                    current_chain[1].append(tag)

            else:
                # both chains are full. Start by testing that the ends of both chains aren't equal (broken chain)
                if digitify(current_chain[0][-1].group(group)) == digitify(current_chain[1][-1].group(group)):
                    chains.append(current_chain)
                    current_chain = ([], [])
                    current_chain[0].append(tag)

                elif digitify(tag.group(group)) - digitify(current_chain[0][-1].group(group)) == 1:
                    current_chain[0].append(tag)
                elif digitify(tag.group(group)) - digitify(current_chain[1][-1].group(group)) == 1:
                    current_chain[1].append(tag)
                else:
                    raise AssertionError("Tag does not match either chain")
        chains.append(current_chain)
        return chains

    def resolve_sections(self, commentary_a, commentary_b, group=1):
        self.resolution_mapping.clear()
        self.commentary_a = commentary_a
        self.commentary_b = commentary_b
        sections = self.document.get_chapter_values()
        for section in sections:
            chain_list = self.build_chains(self.document.get_section(section), self.unknown_pattern, group)
            self._resolve_chains(chain_list, section)

    @staticmethod
    def fix_tag(text, match_obj_list, repl):
        char_list = list(text)
        for match_obj in match_obj_list:
            char_list[match_obj.start()+1] = repl
            char_list[match_obj.start()+2] = repl
        fixed = u''.join(char_list)
        assert len(fixed) == len(text)
        return fixed

    def fix_all_tags(self, test_mode=True):
        if not self.resolution_mapping:
            raise AssertionError("Please run TagResolver.resolve_sections")
        for section in self.document.get_chapter_values():
            resolution = self.resolution_mapping[section]
            if resolution['tbd']:
                print u"unresolved chains at section {}".format(section)
                continue
            self.document.edit_section(section, self.fix_tag,
                                       resolution[self.commentary_a.name], self.commentary_a.tag_pattern)
            self.document.edit_section(section, self.fix_tag,
                                       resolution[self.commentary_b.name], self.commentary_b.tag_pattern)
            if test_mode:
                filename = re.sub(ur'\.txt$', u'_test.txt', self.filename)
            else:
                filename = self.filename
            self.document.write_to_file(filename)






