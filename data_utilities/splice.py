# -*- coding: utf-8 -*-

import regex as re
import bisect
import itertools

from sefaria.model import *
from sefaria.system.exceptions import InputError
from sefaria.search import delete_text, index_text, get_new_and_current_index_names
from sefaria.sheets import get_sheets_for_ref, get_sheet, save_sheet
from sefaria.system.database import db
from dibur_hamatchil_matcher import match_text


class AbstractSplicer(object):

    def __init__(self):
        self._report = False
        self._report_error = False
        self._save = False
        self._save_text_only = False
        self._executed = False
        self._ready = False
        self._mode = None
        self._rebuild_toc = True
        self._refresh_states = True

        self.book_ref = None
        self.index = None
        self.versionSet = None
        self.commentary_titles = None
        self.commentary_versions = None

        self.joiner = u" "

    def is_ready(self):
        return self._ready

    def report(self):
        """
        Report what the splicer will do, but don't make any changes.
        :return:
        """
        if self._executed:
            print "Already executed"
            return
        if not self._ready:
            print "No complete job given to Splicer"
            return
        self._report = True
        self._save = False
        self._run()
        self._report = False

    def bulk_mode(self):
        #self._save_text_only = True  # debug
        self._rebuild_toc = False  # debug/time
        self._refresh_states = False
        return self

    def execute(self):
        """
        Execute the splice.
        :return:
        """
        if self._executed:
            print "Already executed"
            return
        if not self._ready:
            print "No complete job given to Splicer"
            return
        self._save = True
        self._report = True
        self._run()
        if self._refresh_states:
            self.refresh_states()
        if self._rebuild_toc:
            self._update_summaries()
        self._executed = True

    def refresh_states(self):
        # Refresh the version state of main text and commentary
        print u"\n*** Refreshing States"
        VersionState(self.index).refresh()
        for vt in self.commentary_titles:
            VersionState(vt).refresh()

    def _update_summaries(self):
        library.update_index_in_toc(self.index.title)
        for vt in self.commentary_titles:
            library.update_index_in_toc(vt)

    def _run(self):
        pass


class SegmentSplicer(AbstractSplicer):
    """
    Tool for either merging two segments together, or inserting a new segment.

    Sample usage for merge: (self._mode = "join")
        splicer = SegmentSplicer()
        splicer.splice_this_into_next(Ref("Shabbat 7b:11"))
        splicer.report()  # optional, to check what it will do
        splicer.execute()
    A merge can be setup with method splice_this_into_next, splice_next_into_this, splice_prev_into_this, or splice_this_into_prev
    Code wise, this is built from the perspective of merging the second ref into the first, but after numbers get rewritten, it's all equivalent.

    Sample usage for inserting a blank segment: (self._mode = "insert")
        splicer = SegmentSplicer()
        splicer.insert_blank_segment_after(Ref("Shabbat 7b:11"))
        splicer.report()  # optional, to check what it will do
        splicer.execute()

    """
    def __init__(self):
        super(SegmentSplicer, self).__init__()
        self.first_ref = None # In insert mode, this is the ref to insert after
        self.second_ref = None
        self.section_ref = None
        self.first_segment_number = None   # In insert mode, this is the segment to insert after
        self.second_segment_number = None  # In insert mode, this is the segment inserted.
        self.comment_section_lengths = None

        self.last_segment_number = None
        self.last_segment_ref = None
        self._base_links_to_rewrite = []
        self._commentary_links_to_rewrite = []
        self._sheets_to_update = []

    ####  Setup methods ####

    def splice_this_into_next(self, ref):
        assert ref.is_segment_level()
        assert not ref.is_range()
        assert not ref.is_commentary()
        self._mode = "join"
        self.first_ref = ref
        self.second_ref = ref.next_segment_ref()
        assert self.second_ref
        self._setup_refs()
        self._setup_refs_for_join()
        self._ready = True
        return self

    def splice_prev_into_this(self, ref):
        assert ref.is_segment_level()
        assert not ref.is_range()
        assert not ref.is_commentary()
        self._mode = "join"
        self.second_ref = ref
        self.first_ref = ref.prev_segment_ref()
        assert self.first_ref
        self._setup_refs()
        self._setup_refs_for_join()
        self._ready = True
        return self

    # It's a little counter-intuitive, but these are equivalent to their linguistic converse.
    def splice_next_into_this(self, ref):
        return self.splice_this_into_next(ref)

    def splice_this_into_prev(self, ref):
        return self.splice_prev_into_this(ref)

    def insert_blank_segment_after(self, ref):
        assert ref.is_segment_level()
        assert not ref.is_range()
        assert not ref.is_commentary()
        self._mode = "insert"
        self.first_ref = ref
        self._setup_refs()
        self.second_segment_number = self.first_segment_number + 1
        self._ready = True
        return self

    def _setup_refs(self):
        self.first_segment_number = self.first_ref.sections[-1]
        self.section_ref = self.first_ref.section_ref()
        self.book_ref = self.first_ref.context_ref(self.first_ref.index_node.depth)
        self.index = self.book_ref.index
        self.commentary_titles = library.get_commentary_version_titles_on_book(self.index.title)
        self.commentary_versions = library.get_commentary_versions_on_book(self.index.title)
        self.versionSet = VersionSet({"title": self.index.title})
        self.last_segment_number = len(self.section_ref.get_state_ja().subarray_with_ref(self.section_ref))
        self.last_segment_ref = self.section_ref.subref(self.last_segment_number)

    def _setup_refs_for_join(self):
        # Derive other refs and variables from from self.first_ref and self.second_ref
        assert self.section_ref == self.second_ref.section_ref(), "Doesn't work across sections"
        self.second_segment_number = self.second_ref.sections[-1]
        self.comment_section_lengths = self._get_comment_section_lengths(self.first_ref)

    @staticmethod
    def _get_comment_section_lengths(ref):
        # todo: merge into _setup_refs_for_join?
        # How many comments are there for each commenter on the base text?
        ret = {}
        for vtitle in library.get_commentary_version_titles_on_book(ref.index.title):
            commentator_book_ref = Ref(vtitle)
            commentator_segment_ref = commentator_book_ref.subref(ref.sections)
            ret[vtitle] = len(commentator_segment_ref.get_state_ja().subarray_with_ref(commentator_segment_ref))
        return ret

    ### Internal Methods ###
    def _run(self):
        if self._report:
            print u"\n----\n*** Running SegmentSplicer in {} mode.\nFirst Ref: {}".format(self._mode, self.first_ref.normal())

        if self._mode == "join":
            print u"\n*** Merging Base Text and removing segment"
            self._merge_base_text_version_segments()

            print u"\n*** Merging Commentary Text and removing section"
            self._merge_commentary_version_sections()

        elif self._mode == "insert":
            print u"\n*** Inserting segment Base Text"
            self._insert_base_text_version_segments()
            print u"\n*** Inserting Section Commentary Texts"
            self._insert_commentary_version_sections()

        else:
            print u"Error: unknown mode - {}".format(self._mode)
            return
        # For all of the below -
        # It takes longer, but we start at the base text, so as not to miss any ranged refs

        if not self._save_text_only:
            # Rewrite links to base text (including links from own commentary)
            print u"\n*** Rewriting Refs to Base Text"
            print u"\n*** Rewriting Links"
            self._generic_set_rewrite(LinkSet(self.section_ref), ref_attr_name="refs", is_set=True)

            # Note refs
            print u"\n*** Rewriting Note Refs"
            self._generic_set_rewrite(NoteSet({"ref": {"$regex": self.section_ref.regex()}}))

            # Translation requests
            print u"\n*** Rewriting Translation Request Refs"
            self._generic_set_rewrite(TranslationRequestSet({"ref": {"$regex": self.section_ref.regex()}}))

            # History
            # these can be made faster by splitting up the regex
            print u"\n*** Rewriting History Refs"
            self._generic_set_rewrite(HistorySet({"ref": {"$regex": self.section_ref.regex()}}))
            self._generic_set_rewrite(HistorySet({"new.ref": {"$regex": self.section_ref.regex()}}), ref_attr_name="new", sub_ref_attr_name="ref")
            self._generic_set_rewrite(HistorySet({"new.refs": {"$regex": self.section_ref.regex()}}), ref_attr_name="new", sub_ref_attr_name="refs", is_set=True)
            self._generic_set_rewrite(HistorySet({"old.ref": {"$regex": self.section_ref.regex()}}), ref_attr_name="old", sub_ref_attr_name="ref")
            self._generic_set_rewrite(HistorySet({"old.refs": {"$regex": self.section_ref.regex()}}), ref_attr_name="old", sub_ref_attr_name="refs", is_set=True)

            print u"\n*** Rewriting Refs to Commentary"
            for commentary_title in self.commentary_titles:
                commentator_chapter_ref = Ref(commentary_title).subref(self.section_ref.sections)
                # Rewrite links to commentary (including to base text)
                print u"\n*** {}".format(commentator_chapter_ref.normal())
                print u"\n*** Rewriting Links"
                self._generic_set_rewrite(LinkSet(commentator_chapter_ref), ref_attr_name="refs", is_set=True, commentary=True)
                print u"\n*** Rewriting Note Refs"
                self._generic_set_rewrite(NoteSet({"ref": {"$regex": commentator_chapter_ref.regex()}}), commentary=True)
                print u"\n*** Rewriting Translation Request Refs"
                self._generic_set_rewrite(TranslationRequestSet({"ref": {"$regex": commentator_chapter_ref.regex()}}), commentary=True)

                # History?
                # these can be made faster by splitting up the regex
                print u"\n*** Rewriting History Refs"
                self._generic_set_rewrite(HistorySet({"ref": {"$regex": commentator_chapter_ref.regex()}}), commentary=True)
                self._generic_set_rewrite(HistorySet({"new.ref": {"$regex": commentator_chapter_ref.regex()}}), ref_attr_name="new", sub_ref_attr_name="ref", commentary=True)
                self._generic_set_rewrite(HistorySet({"new.refs": {"$regex": commentator_chapter_ref.regex()}}), ref_attr_name="new", sub_ref_attr_name="refs", is_set=True, commentary=True)
                self._generic_set_rewrite(HistorySet({"old.ref": {"$regex": commentator_chapter_ref.regex()}}), ref_attr_name="old", sub_ref_attr_name="ref", commentary=True)
                self._generic_set_rewrite(HistorySet({"old.refs": {"$regex": commentator_chapter_ref.regex()}}), ref_attr_name="old", sub_ref_attr_name="refs", is_set=True, commentary=True)

            # Source sheet refs
            print u"\n*** Rewriting Source Sheet Refs"
            self._find_sheets()
            self._clean_sheets()

            # alt structs?
            print u"\n*** Rewriting Alt Struct Refs"
            self._rewrite_alt_structs()

            print u"\n*** Pushing changes to Elastic Search"
            self._clean_elastisearch()

    def _insert_base_text_version_segments(self):
        # Inserts are self.first_ref
        for v in self.versionSet:
            assert isinstance(v, Version)
            tc = TextChunk(self.section_ref, lang=v.language, vtitle=v.versionTitle)
            if len(tc.text) <= self.first_segment_number:
                continue
            tc.text = tc.text[:self.first_segment_number] + [u""] + tc.text[self.first_segment_number:]
            if self._report:
                print u"Inserting segment after {} ({})".format(self.first_ref.normal(), v.versionTitle)
            if self._save:
                tc.save()

    def _insert_commentary_version_sections(self):
        for v in self.commentary_versions:
            assert isinstance(v, Version)
            commentator_chapter_ref = Ref(v.title).subref(self.section_ref.sections)
            commentator_line_ref = Ref(v.title).subref(self.first_ref.sections)
            tc = TextChunk(commentator_chapter_ref, lang=v.language, vtitle=v.versionTitle)
            if len(tc.text) <= self.first_segment_number:
                continue
            tc.text = tc.text[:self.first_segment_number] + [[]] + tc.text[self.first_segment_number:]
            if self._report:
                print u"Inserting commentary segment after {} ({})".format(commentator_line_ref.normal(), v.versionTitle)
            if self._save:
                tc.save()

    def _merge_base_text_version_segments(self):
        # for each version, merge the text
        for v in self.versionSet:
            assert isinstance(v, Version)
            tc = TextChunk(self.section_ref, lang=v.language, vtitle=v.versionTitle)
            if len(tc.text) < self.second_segment_number:
                continue
            first_line = tc.text[self.first_segment_number - 1]
            second_line = tc.text[self.second_segment_number - 1]
            if first_line or second_line:
                tc.text[self.first_segment_number - 1] = first_line.strip() + self.joiner + second_line.strip()
            tc.text = tc.text[:self.first_segment_number] + tc.text[self.second_segment_number:]
            if self._report:
                print u"{}: {} and {} merging to become {}".format(v.versionTitle, self.first_ref.normal(), self.second_ref.normal(), tc.text[self.first_segment_number - 1])
            if self._save:
                tc.save()

    def _merge_commentary_version_sections(self):
        # Merge comments for all commentary on this text
        for v in self.commentary_versions:
            assert isinstance(v, Version)
            commentator_book_ref = Ref(v.title)
            commentator_section_ref = commentator_book_ref.subref(self.section_ref.sections)
            commentator_segment_ref = commentator_book_ref.subref(self.first_ref.sections)
            tc = TextChunk(commentator_section_ref, lang=v.language, vtitle=v.versionTitle)
            if len(tc.text) < self.second_segment_number:
                continue

            # Pad first section to uniform length, as derived from state, then add the next section on to the end
            comment_section_length = self.comment_section_lengths.get(v.title)
            assert len(tc.text[self.first_segment_number - 1]) <= comment_section_length
            tc.text[self.first_segment_number - 1] = tc.text[self.first_segment_number - 1] + [list() for _ in range(len(tc.text[self.first_segment_number - 1]), comment_section_length)] + tc.text[self.second_segment_number - 1]
            # remove second section
            tc.text = tc.text[:self.first_segment_number] + tc.text[self.second_segment_number:]

            if self._report:
                print u"{} ({}) becoming\n{}".format(commentator_segment_ref.normal(), v.versionTitle, u" | ".join(tc.text[self.first_segment_number - 1]))
            if self._save:
                tc.save()

    def _needs_rewrite(self, old_ref, commentary=False):
        # There is no difference here between join and insert - anything after first_ref needs to be rewritten
        assert isinstance(old_ref, Ref)

        def simple_needs_rewrite(old_simple_ref):
            assert isinstance(old_simple_ref, Ref)

            if (len(old_simple_ref.sections) >= self.first_ref.index_node.depth
                and old_simple_ref.sections[self.first_ref.index_node.depth - 2] == self.section_ref.sections[-1]
                and old_simple_ref.sections[self.first_ref.index_node.depth - 1] > self.first_segment_number
               ):
                return True
            return False

        if old_ref.is_commentary() != commentary:
            return False
        if (not commentary) and (old_ref.index != self.first_ref.index):
            return False
        if commentary and old_ref.index.b_index != self.first_ref.index:
            return False

        if old_ref.is_range():
            return simple_needs_rewrite(old_ref.starting_ref()) or simple_needs_rewrite(old_ref.ending_ref())
        return simple_needs_rewrite(old_ref)

    def _rewrite(self, old_ref, commentary=False):
        assert isinstance(old_ref, Ref)

        def insert_rewrite(old_simple_ref):
            segment_depth = self.first_ref.index_node.depth - 1
            section_depth = self.first_ref.index_node.depth - 2

            if (old_simple_ref.sections[section_depth] == self.first_ref.sections[section_depth]
                    and old_simple_ref.sections[segment_depth] > self.first_segment_number):
                d = old_simple_ref._core_dict()
                d["sections"][segment_depth] += 1
                d["toSections"] = d["sections"]
                return Ref(_obj=d)
            return old_simple_ref

        def join_rewrite(old_simple_ref):
            segment_depth = self.first_ref.index_node.depth - 1
            section_depth = self.first_ref.index_node.depth - 2

            if (commentary
              and old_simple_ref.is_segment_level()
              and old_simple_ref.sections[section_depth] == self.first_ref.sections[section_depth]
              and old_simple_ref.sections[segment_depth] == self.second_segment_number):
                # Position of comment has changed
                d = old_simple_ref._core_dict()
                d["sections"][-2] -= 1
                d["sections"][-1] += self.comment_section_lengths.get(old_simple_ref.index.title)
                d["toSections"] = d["sections"]
                return Ref(_obj=d)
            elif (old_simple_ref.sections[segment_depth] > self.first_segment_number
              and old_simple_ref.sections[section_depth] == self.first_ref.sections[section_depth]):
                if not commentary:
                    return old_simple_ref.prev_segment_ref()
                else:
                    d = old_simple_ref._core_dict()
                    d["sections"][segment_depth] -= 1
                    d["toSections"] = d["sections"]
                    return Ref(_obj=d)
            return old_simple_ref
        try:
            _rewrite_method = insert_rewrite if self._mode == "insert" else join_rewrite
            if old_ref.is_range():
                return _rewrite_method(old_ref.starting_ref()).to(_rewrite_method(old_ref.ending_ref()))
            return _rewrite_method(old_ref)
        except Exception as e:
            print u"Failed to rewrite {}".format(old_ref.normal())
            return old_ref
        
    def _generic_set_rewrite(self, model_set, commentary=False, ref_attr_name="ref", sub_ref_attr_name=None, is_set=False):
        for n in model_set:
            needs_save = False

            try:
                if sub_ref_attr_name:
                    intermediate_obj = getattr(n, ref_attr_name)
                    rawref = intermediate_obj[sub_ref_attr_name]
                else:
                    rawref = getattr(n, ref_attr_name)

                if is_set:
                    refs = [Ref(r) for r in rawref]
                else:
                    refs = [Ref(rawref)]

            except InputError as e:
                if self._report_error:
                    print e
                continue

            for i, ref in enumerate(refs):
                if self._needs_rewrite(ref, commentary=commentary):
                    needs_save = True
                    refs[i] = self._rewrite(ref, commentary=commentary)

            if needs_save:
                if is_set:
                    refs = [r.normal() for r in refs]
                else:
                    refs = refs[0].normal()

                if sub_ref_attr_name:
                    intermediate_obj[sub_ref_attr_name] = refs
                    setattr(n, ref_attr_name, intermediate_obj)
                else:
                    setattr(n, ref_attr_name, refs)

                if self._report:
                    print u"{}.{}{} - converting {} to {}".format(
                        n.__class__.__name__,
                        ref_attr_name,
                        (u"." + sub_ref_attr_name) if sub_ref_attr_name else "",
                        rawref,
                        refs)
                if self._save:
                    n.save()

    def _rewrite_alt_structs(self):
        if not self.index.has_alt_structures():
            return
        needs_save = False
        for name, struct in self.index.get_alt_structures().iteritems():
            for map_node in struct.get_leaf_nodes():
                assert map_node.depth <= 1, "Need to write some code to handle alt structs with depth > 1!"
                wr = Ref(map_node.wholeRef)
                if self._needs_rewrite(wr, wr.is_commentary()):
                    needs_save = True
                    map_node.wholeRef = self._rewrite(wr, wr.is_commentary()).normal()
                for i, r in enumerate(map_node.refs):
                    ref = Ref(r)
                    if self._needs_rewrite(ref, ref.is_commentary()):
                        needs_save = True
                        map_node.refs[i] = self._rewrite(ref, ref.is_commentary()).normal()
        if needs_save:
            if self._report:
                print "Saving {} alt structs".format(self.index.title)
            if self._save:
                self.index.save()

    def _find_sheets(self):
        def _get_sheets_with_ref(oref):
            ref_re = oref.regex()
            sheets = db.sheets.find({"sources.ref": {"$regex": ref_re}}, {"id": 1})
            return [s["id"] for s in sheets]

        self._sheets_to_update += _get_sheets_with_ref(self.section_ref)
        for commentary_title in self.commentary_titles:
            commentator_book_ref = Ref(commentary_title)
            commentator_chapter_ref = commentator_book_ref.subref(self.section_ref.sections)
            self._sheets_to_update += _get_sheets_with_ref(commentator_chapter_ref)

    def _clean_sheets(self):

        def rewrite_source(source):
            needs_save = False
            if "ref" in source:
                try:
                    ref = Ref(source["ref"])
                except InputError as e:
                    print "Error: In _clean_sheets.rewrite_source: failed to instantiate Ref {}".format(source["ref"])
                else:
                    if self._needs_rewrite(ref, ref.is_commentary()):
                        if self._report:
                            print "Sheet refs - rewriting {} to {}".format(ref.normal(), self._rewrite(ref, ref.is_commentary()).normal())
                        needs_save = True
                        source["ref"] = self._rewrite(ref, ref.is_commentary()).normal()
            if "subsources" in source:
                for subsource in source["subsources"]:
                    needs_save = rewrite_source(subsource) or needs_save
            return needs_save

        for sid in self._sheets_to_update:
            needs_save = False
            sheet = db.sheets.find_one({"id": sid})
            if not sheet:
                print "Likely error - can't load sheet {}".format(sid)
            for source in sheet["sources"]:
                if rewrite_source(source):
                    needs_save = True
            if needs_save:
                if self._report:
                    print "Saving modified sheet #{}".format(sheet["id"])
                if self._save:
                    sheet["lastModified"] = sheet["dateModified"]
                    save_sheet(sheet, sheet["owner"])

    def _clean_elastisearch(self):
        """
        Re-index modified chapters in ES
        For joins, delete last segment that hangs off the edge of base text and commentaries
        """

        from sefaria.settings import SEARCH_INDEX_ON_SAVE
        if not SEARCH_INDEX_ON_SAVE:
            return

        index_name = get_new_and_current_index_names()['current']
        for v in self.versionSet:
            if self._report:
                print "ElasticSearch: Reindexing {} / {} / {}".format(self.section_ref.normal(), v.versionTitle, v.language)
            if self._save:
                index_text(index_name, self.section_ref, v.versionTitle, v.language)

            # If this is not a Bavli ref, it's been indexed by segment.  Delete the last dangling segment
            if not self.section_ref.is_bavli() and self._mode == "join":
                if self._report:
                    print "ElasticSearch: Deleting {} / {} / {}".format(self.last_segment_ref.normal(), v.versionTitle, v.language)
                if self._save:
                    delete_text(self.last_segment_ref, v.versionTitle, v.language)

        for commentary_title in self.commentary_titles:
            commentator_book_ref = Ref(commentary_title)
            commentator_chapter_ref = commentator_book_ref.subref(self.section_ref.sections)
            last_commentator_section_ref = commentator_book_ref.subref(self.last_segment_ref.sections)

            for v in VersionSet({"title": commentary_title}):
                for i in range(1, self.last_segment_number):  # no need to do the last one; it's deleted below
                    commentor_section_ref = commentator_chapter_ref.subref(i)
                    if self._report:
                        print "ElasticSearch: Reindexing {} / {} / {}".format(commentor_section_ref.normal(), v.versionTitle, v.language)
                    if self._save:
                        index_text(index_name, commentor_section_ref, v.versionTitle, v.language)

                last_segment = len(last_commentator_section_ref.get_state_ja().subarray_with_ref(last_commentator_section_ref))

                # In join mode, delete dangling records
                if self._mode == "join":
                    if commentator_book_ref.is_bavli() and last_segment > 0:
                        if self._report:
                            print "ElasticSearch: Deleting {} / {} / {}".format(last_commentator_section_ref.normal(), v.versionTitle, v.language)
                        if self._save:
                            delete_text(last_commentator_section_ref, v.versionTitle, v.language)
                    else:
                        for i in range(last_segment):
                            comment_ref = last_commentator_section_ref.subref(i+1)
                            if self._report:
                                print "ElasticSearch: Deleting {} / {} / {}".format(comment_ref.normal(), v.versionTitle, v.language)
                            if self._save:
                                delete_text(comment_ref, v.versionTitle, v.language)

    def __eq__(self, other):
        return self._mode == other._mode and self.first_ref == other.first_ref and self.second_ref == other.second_ref

    def __ne__(self, other):
        return not self.__eq__(other)


class BlankSegment(object):
    def __init__(self):
        pass

    def __eq__(self, other):
        return self.__class__ == other.__class__

    def __ne__(self, other):
        return self.__class__ != other.__class__

    def get_text(self, current_text_chunk):
        return ""

    def is_blank(self):
        return True


class SegmentMap(object):
    """
    A range of segments within a single section, with optional word-level specification
    Note that we reuse SegmentMap objects.  Keep 'em stateless!

    """
    # Order of args is a bit unintuitive
    def __init__(self, start_ref, end_ref, start_word=None, end_word=None):
        assert start_ref.is_segment_level()
        assert not start_ref.is_range()
        assert end_ref.is_segment_level()
        assert not end_ref.is_range()
        assert start_ref == end_ref or end_ref.follows(start_ref)

        self.start_ref = start_ref
        self.end_ref = end_ref
        self.start_word = start_word
        self.end_word = end_word

        self.joiner = u" "
        self.tokenizer = lambda s: re.split("\s+", s)

        self.first_segment_index = self.start_ref.sections[-1] - 1
        self.last_segment_index = self.end_ref.sections[-1] - 1

        self.num_segments = 1

        self.commentary_mappings = {}

    def __eq__(self, other):
        if (self.__class__ == other.__class__ and
                self.start_ref == other.start_ref and
                self.end_ref == other.end_ref and
                self.start_word == other.start_word and
                self.end_word == other.end_word):
            return True
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "SegmentMap({},{},{},{})".format(self.start_ref.normal(), self.end_ref.normal(), self.start_word, self.end_word)

    def is_blank(self):
        return False

    """
    #used?
    def unbroken_segment_indexes(self):
        usi = [self.first_segment_index] if self.start_word is None else []
        usi += range(self.first_segment_index+1, self.last_segment_index)
        usi += [self.last_segment_index] if self.end_word is None else []
        return usi
    """

    def immediately_follows(self, other):
        if not other.end_word and not self.start_word and self.start_ref.sections[-1] == other.end_ref.sections[-1] + 1:
            return True
        if other.end_word and self.start_word and self.start_word == other.end_word + 1 and self.start_ref == other.end_ref:
            return True
        return False

    def ref_maps(self):
        """
        Returns List of tuples: String -> Offset
            Offset is a list of offsets after the Daf section.
            Each element may be a digit.  Last element may be a digit or a tuple (indicating range).
        For all refs in base text and commentary covered by this segment map
        :return:
        """
        d = [(source_ref.normal(),[0]) for source_ref in self.start_ref.to(self.end_ref).range_list()]
        for commentor in self.commentary_mappings:
            base_ref = Ref("{} on {}".format(commentor, self.start_ref.section_ref().normal()))
            offset_aggregator = 0
            for i, num_in_line in enumerate(self.commentary_mappings[commentor]):
                line_ref = base_ref.subref(self.start_ref.sections[-1] + i)
                for j in range(1, num_in_line + 1):
                    d += [(line_ref.subref(j).normal(), [0, offset_aggregator + j])]
                offset_aggregator += num_in_line
        return d

    def reshape_commentary_version(self, commentator_name, commentator_text_chunk):
        """

        :param commentator_name: Used to identify which commentator we're working with
        :param commentator_text_chunk:
        :return:
        """
        assert self.end_word is None and self.start_word is None
        assert isinstance(commentator_text_chunk, TextChunk)

        old_length_map = self.commentary_mappings[commentator_name]

        full_segment = []

        csections = commentator_text_chunk.text[self.first_segment_index:self.last_segment_index + 1]
        for i, csec in enumerate(csections):
            try:
                new_text = [u""] * old_length_map[i]
                new_text[:len(csec)] = csec
                full_segment += new_text
            except IndexError:
                break
        return [full_segment]

    def build_master_commentary_mapping(self, commentator_name, merged_text_chunk, dh_overrides = None):
        """
        returning map from old commentator refs to new refs
        :param commentator_name: Used to identify which commentator we're working with
        :param merged_text_chunk: The merged version of the commentary text chunk for this super-section
        :return:
        """
        # Assuming this only called on non-split chunks
        # Keep track of number of comments per old segment

        assert self.end_word is None and self.start_word is None
        assert isinstance(merged_text_chunk, TextChunk)

        csections = merged_text_chunk.text[self.first_segment_index:self.last_segment_index + 1]
        old_length_map = [len(section) for section in csections]

        self.commentary_mappings[commentator_name] = old_length_map

    def get_text(self, current_text_chunk):
        new_text_list = []
        try:
            if self.first_segment_index == self.last_segment_index:
                new_text_list += [self._get_partial_text(current_text_chunk, self.first_segment_index, start_word=self.start_word, end_word=self.end_word)
                                 if self.start_word or self.end_word
                                 else current_text_chunk.text[self.first_segment_index]]
            else:
                new_text_list += [self._get_partial_text(current_text_chunk, self.first_segment_index, start_word=self.start_word)
                                 if self.start_word
                                 else current_text_chunk.text[self.first_segment_index]]
                new_text_list += current_text_chunk.text[self.first_segment_index + 1:self.last_segment_index]
                new_text_list += [self._get_partial_text(current_text_chunk, self.last_segment_index, end_word=self.end_word)
                                  if self.end_word
                                  else current_text_chunk.text[self.last_segment_index]]
        except IndexError:
            pass

        return self.joiner.join(new_text_list)

    def _get_partial_text(self, section_text_chunk, segment_index, start_word=None, end_word=None):
        """
        Returns partial segment string, based on starting and ending words specified.
        :param section_text_chunk:
        :param segment_index:
        :param start_word:
        :param end_word:
        :return:
        """
        try:
            return self.joiner.join(self.tokenizer(section_text_chunk.text[segment_index])[start_word and start_word - 1: end_word])
        except IndexError:
            return u""


class SplitSegmentGroup(object):
    """
    When a old segment is split between new segments, this is used to rewrite the commentaries,
    using Dibbur Hamatchil matching in order to place them
    """
    def __init__(self, segment_maps, section_text):
        """
        :param segment_maps: List of SegmentMaps
        :param section_text: TextChunk - the canonical Hebrew for this base text section
        """
        assert isinstance(section_text, TextChunk)
        assert all([isinstance(a, SegmentMap) for a in segment_maps])

        self.segment_maps = segment_maps
        self.section_text = section_text
        self.num_segments = len(segment_maps)
        self.segment_range = range(self.segment_maps[0].first_segment_index, self.segment_maps[-1].last_segment_index + 1)
        self.segment_breaks = self._get_segment_breaks()
        self.commentary_mappings = {}   # In the shape of the old commentary, a list of offsets in the new commentary to place at.
        self.commentary_determinations = []  # List of {} with keys: section: string, commentator: string, comment: string, dh: string, choice: int, potential_placements: list,

    def __repr__(self):
        return "SplitSegmentGroup({})".format(self.segment_maps)

    def _get_segment_breaks(self):
        """
        Return a dictionary, keyed by source segment number, one for each segment contained in this group.
        Value is a dictionary, with key "offset" - indicating position of resultant segments
            (relative to this SplitSegmentGroup only, i.e. index in self.segment_maps where this segment is found)
        If a segment is broken, value has key "breaks": list of word indexes where segments transition
        :return:
        """
        segment_breaks = {}
        for i in self.segment_range:
            segment_breaks[i] = {}
        for smi, sm in enumerate(self.segment_maps):
            if sm.start_word is not None:
                segment_breaks[sm.first_segment_index]["breaks"] += [sm.start_word - 1]
                for i in range(sm.first_segment_index + 1, sm.last_segment_index + 1):
                    segment_breaks[i]["offset"] = smi
            else:
                for i in range(sm.first_segment_index, sm.last_segment_index + 1):
                    segment_breaks[i]["offset"] = smi
            if sm.end_word is not None and segment_breaks[sm.last_segment_index].get("breaks", None) is None:
                segment_breaks[sm.last_segment_index] = {"breaks": [], "offset": smi}
        return segment_breaks

    def ref_maps(self):
        """
        Returns list of tuples String -> Offset
            Offset is a list of offsets after the Daf section.
            Each element may be a digit.  Last element may be a digit or a tuple (indicating range).
        For all refs in base text and commentary covered by this segment map
        :return:
        """
        d = []
        section_ref = self.segment_maps[0].start_ref.section_ref()
        for seg_num in self.segment_range:
            if "breaks" not in self.segment_breaks[seg_num]:
                d += [(section_ref.subref(seg_num + 1).normal(), [self.segment_breaks[seg_num]["offset"]])]
            else:
                d += [(section_ref.subref(seg_num + 1).normal(), [(self.segment_breaks[seg_num]["offset"], self.segment_breaks[seg_num]["offset"] + len(self.segment_breaks[seg_num]["breaks"]))])]

        for commentor in self.commentary_mappings:
            base_ref = Ref("{} on {}".format(commentor, section_ref.normal()))

            old_to_new = self.commentary_mappings[commentor]

            offset_aggregator = {a: 1 for a in xrange(self.num_segments)}
            for i, section in enumerate(old_to_new):
                for j, offset in enumerate(section):
                    d += [(base_ref.subref(self.segment_range[i] + 1).subref(j+1).normal(), [offset, offset_aggregator[offset]])]
                    offset_aggregator[offset] += 1

        return d

    def build_master_commentary_mapping(self, commentator_name, merged_text_chunk, dh_overrides = None):
        """
        Use the merged Hebrew version of the commentator in order to build a master map
        of how the old commentary maps to the new.
        In the shape of the old commentary, a list of offsets in the new commentary to place at.
        :param commentator_name: Used to identify which commentator we're working with
        :param merged_text_chunk: The merged version of the commentary text chunk for this super-section
        :param dh_overrides: dictionary keyed by tuple (commentator, dh) -> placing
        :return:
        """
        old_to_new = []
        for i in self.segment_range:
            try:
                if self.segment_breaks[i].get("breaks", None) is None:
                    old_to_new += [len(merged_text_chunk.text[i]) * [self.segment_breaks[i]["offset"]]]
                else:
                    words = re.split("\s+", self.section_text.text[i])
                    breaks = self.segment_breaks[i]["breaks"]
                    offset = self.segment_breaks[i]["offset"]
                    subsegs = [(0, breaks[0])] + [(breaks[bi - 1], breaks[bi]) for bi in xrange(1, len(breaks))] + [(breaks[-1], None)]
                    potential_placements = [u" ".join(words[a:b]) for a, b in subsegs]

                    # match_text returns [(start,end)...] - we're  using just the start word to make our judgement
                    word_ranges = match_text(words,
                                             merged_text_chunk.text[i],
                                             dh_extract_method=dh_extract_method,
                                             place_all=True
                                             )["matches"]
                    placements = [bisect.bisect_right(breaks, w[0]) for w in word_ranges]

                    # Check if there are any manual overrides for these comments
                    if dh_overrides:
                        for j, comment in enumerate(merged_text_chunk.text[i]):
                            dh = dh_extract_method(comment)
                            if (commentator_name, dh) in dh_overrides:
                                placements[j] = int(dh_overrides[(commentator_name, dh)]) - 1

                    old_to_new += [[p + offset for p in placements]]

                    self.commentary_determinations += [{
                        "section": self.section_text._oref.normal(),
                        "commentator": commentator_name,
                        "comment": comment,
                        "dh": dh_extract_method(comment),
                        "choice": placements[j] + 1,
                        "potential_placements": potential_placements,
                    } for j, comment in enumerate(merged_text_chunk.text[i])]
            except IndexError:
                # Commentary ends before end of section
                break
        self.commentary_mappings[commentator_name] = old_to_new

    def reshape_commentary_version(self, commentator_name, commentator_text_chunk):
        """
        Use the master mapping of a commentator to reshape this text
        :param commentator_name: Used to identify which commentator we're working with
        :param commentator_text_chunk:
        :return:
        """
        old_to_new = self.commentary_mappings[commentator_name]
        new_sections = [[] for _ in xrange(self.num_segments)]

        # Iterate over map, move new segments into place as indicated
        for i, section in enumerate(old_to_new):
            for j, offset in enumerate(section):
                try:
                    new_sections[offset] += [commentator_text_chunk.text[self.segment_range[i]][j]]
                except IndexError:
                    new_sections[offset] += [u""]

        return new_sections


class SectionSplicer(AbstractSplicer):
    """
    splicer = SectionSplicer()
    splicer.set_section(Ref("Shabbat 2b"))
    splicer.set_base_version(title, lang)
    splicer.set_segment_map(Ref("Shabbat 2b:1"), Ref("Shabbat 2b:4"))
    splicer.set_segment_map(Ref("Shabbat 2b:5"), Ref("Shabbat 2b:8"), end_word = 4)
    splicer.set_segment_map(Ref("Shabbat 2b:8"), Ref("Shabbat 2b:12"), start_word = 5)
    splicer.report()  # optional, to check what it will do
    splicer.execute()

    There is only one mode.  self._mode is not used.

    """
    def __init__(self):
        super(SectionSplicer, self).__init__()
        self.section_ref = None
        self.book_ref = None
        self.last_segment_ref = None
        self.base_version_title = None
        self.base_version_language = None
        self.base_text_chunk = None
        self.base_length = None
        self.new_en_text = []
        self.new_he_text = []
        self.version_list = []
        self.segment_maps = []           # List of SegmentMap objects, with word specificity, based on primary version
        self.adjusted_segment_maps = []  # List of SegmentMap objects, with segment specificity, for other versions
        self.commentary_split_mappers = []
        self.dh_overrides = []

    def __repr__(self):
        return "SectionSplicer({})".format(self.section_ref.normal())

    def set_section(self, ref):
        assert ref.is_section_level()
        assert not ref.is_range()
        assert not ref.is_commentary()

        self.section_ref = ref
        self.book_ref = ref.index_node.ref()
        self.last_segment_ref = ref.subref(len(ref.text("he").text))  # ref.subref(ref.get_state_ja().sub_array_length([i - 1 for i in ref.sections]))
        self.index = ref.index
        # self.commentary_titles = library.get_commentary_version_titles_on_book(self.index.title)
        self.commentary_titles = library.get_dependant_indices(self.index.title, structure_match=True)
        # self.commentary_versions = library.get_commentary_versions_on_book(self.index.title)
        self.commentary_versions = [v for i in library.get_dependant_indices(self.index.title, structure_match=True, full_records=True) for v in i.versionSet()]
        self.version_list = ref.version_list()
        for v in self.version_list:
            v["text_chunk"] = TextChunk(ref, v["language"], v["versionTitle"])
        return self

    def set_dh_overrides(self, dh_overrides):
        """
        :param dh_overrides: dictionary keyed by tuple (commentator, dh) -> placing
        :return:
        """
        assert isinstance(dh_overrides, dict)
        self.dh_overrides = dh_overrides

    def set_new_texts(self, text_dict_list):
        self.new_en_text = [a["english"] for a in text_dict_list]
        self.new_he_text = [a["hebrew"] for a in text_dict_list]

    def set_base_version(self, base_version_title, base_version_language):
        self.base_version_title = base_version_title
        self.base_version_language = base_version_language
        for v in self.version_list:
            if v["versionTitle"] == self.base_version_title and v["language"] == self.base_version_language:
                v["is_base_version"] = True
                self.base_length = len(v["text_chunk"].text)
                self.base_text_chunk = v["text_chunk"]
            else:
                v["is_base_version"] = False
        if any([len(v["text_chunk"].text) > self.base_length for v in self.version_list]):
            print "Warning: segments beyond base segments in {}".format(self.section_ref.normal())

    def set_segment_map(self, start_ref, end_ref, start_word=None, end_word=None):
        assert self.section_ref, "Please call set_section() before calling set_segment_map()"
        assert self.base_version_title or (not start_word and not end_word), "Word level mappings require a base version."
        assert start_ref.section_ref() == self.section_ref
        assert end_ref.section_ref() == self.section_ref
        assert len(self.segment_maps) or start_ref == self.section_ref.subref(1), "{} - First segment map must begin at start of section.".format(start_ref.normal())

        sm = SegmentMap(start_ref, end_ref, start_word=start_word, end_word=end_word)
        if len(self.segment_maps):
            assert sm.immediately_follows(self.segment_maps[-1]), "{} doesn't follow {}".format(sm.start_ref.normal(), self.segment_maps[-1].end_ref.normal())
        self.segment_maps += [sm]

        if end_ref == self.last_segment_ref and not end_word:
            self._process_segment_maps()
            # If we want to review the complete collection of segments before processing, here's the place.
            self._ready = True

    def get_commentary_determinations(self):
        r = []
        for sm in self.commentary_split_mappers:
            if isinstance(sm, SplitSegmentGroup):
                r += sm.commentary_determinations
        return r

    def ref_maps(self):
        """
        Returns a list of tuples: Ref -> Ref
        Maps Refs in old segmentation to a list of refs in new segmentation that have content from the old ref.
        Both base text and commentary

        Relies on ref_maps() of underlying mappers, which return lists of tuples String -> Offsets
            Offsets is a list of offsets after the Daf section.
            Each element may be a digit.  Last element may be a digit or a tuple (indicating range).
        For all refs in base text and commentary covered by this segment map
        :return:
        """
        result = []
        current_segment = 1
        for mapper in self.commentary_split_mappers:
            for ref, offsets in mapper.ref_maps():
                target_ref = Ref(ref).top_section_ref()
                # first element is daf segment

                if isinstance(offsets[0], tuple):
                    target_ref = target_ref.subref(current_segment + offsets[0][0]).to(target_ref.subref(current_segment + offsets[0][1]))
                else:
                    target_ref = target_ref.subref(current_segment + offsets[0])
                    if len(offsets) == 2:
                        target_ref = target_ref.subref(offsets[1])

                result += [(ref, target_ref.normal())]

            current_segment += mapper.num_segments
        return result

    def get_empty_refs(self):
        """
        :return: a list of empty references in the new merged non-primary texts
        """
        return filter(None, [self.section_ref.subref(i + 1).normal() if sm.is_blank() else None for i, sm in enumerate(self.adjusted_segment_maps)])

    def _process_segment_maps(self):
        # Note that we're reusing SegmentMap objects here.  Keep 'em stateless!
        if not self.base_version_title:
            self.adjusted_segment_maps = self.segment_maps

        last_ref = None
        for detailed_sm in self.segment_maps:
            # If this is a segment bounded SegmentMap, just reuse it
            if not detailed_sm.start_word and not detailed_sm.end_word:
                self.adjusted_segment_maps += [detailed_sm]
                continue

            # Otherwise, determine adjusted ref.
            # If this has a beginning word, it was already covered.  advance past this segment
            elif detailed_sm.start_word is not None:
                # If end ref is later than start ref, just advance start ref
                    # If this has an end word, we want to extend to cover whole segment.
                    # Otherwise, it's already covering the whole segment.
                    # In both cases we end up with the same data.
                if detailed_sm.start_ref != detailed_sm.end_ref:
                    self.adjusted_segment_maps += [SegmentMap(detailed_sm.start_ref.next_segment_ref(), detailed_sm.end_ref)]
                # otherwise, insert a blank
                else:
                    self.adjusted_segment_maps += [BlankSegment()]
                continue

            # Start word is None, but end word is not
            # Trim the word boundaries
            elif detailed_sm.end_word is not None:
                self.adjusted_segment_maps += [SegmentMap(detailed_sm.start_ref, detailed_sm.end_ref)]
                continue

        self._build_commentary_mappers()
        self._build_commentary_mappings()

    def _build_commentary_mappers(self):
        """
        # Generate a list of SplitSegmentGroups and SegmentMaps that cover the whole section
        :return:
        """
        # Commentary on an amud is depth 2
        # Each array is either split or not
        # If not split - mapping is clear
        # If is split - needs determination

        self.commentary_split_mappers = []
        temp = []
        in_split = False

        for sm in self.segment_maps:
            if sm.end_word is not None:
                temp += [sm]
                in_split = True
            elif in_split:
                temp += [sm]
                if sm.end_word is None:
                    in_split = False
                    self.commentary_split_mappers += [SplitSegmentGroup(temp, self.base_text_chunk)]
                    temp = []
            else:
                assert sm.start_word is None
                self.commentary_split_mappers += [sm]

    def _build_commentary_mappings(self):
        for commentator in self.commentary_titles:
            commentator = commentator.split(" on ")[0]
            cssec_ref = Ref("{} on {}".format(commentator, self.section_ref))
            commentator_merged_tc = TextChunk(cssec_ref, "he")

            for mapper in self.commentary_split_mappers:
                mapper.build_master_commentary_mapping(commentator, commentator_merged_tc, self.dh_overrides)

    def _reshape_all_commentary_versions(self):
        for v in self.commentary_versions:
            assert isinstance(v, Version)
            reshaped_commentary = []
            commentator = v.title.split(" on ")[0]
            cssec_ref = Ref("{} on {}".format(commentator, self.section_ref))
            tc = TextChunk(cssec_ref, v.language, v.versionTitle)
            for mapper in self.commentary_split_mappers:
                reshaped_commentary += mapper.reshape_commentary_version(commentator, tc)
            if self._report:
                print u"Reshaping Commentary: {} - {}".format(cssec_ref.normal(), v.versionTitle)
            if self._save:
                tc.text = reshaped_commentary
                tc.save()

    def _reshape_base_text_version_segments(self):
        # for each version, merge the text
        for v in self.version_list:
            seg_maps = self.segment_maps if v["is_base_version"] else self.adjusted_segment_maps
            old_length = len(v["text_chunk"].text)
            v["text_chunk"].text = [seg_map.get_text(v["text_chunk"]) for seg_map in seg_maps]
            if self._report:
                print u"{} {}: Was {} segments.  Now {}.".format(v["versionTitle"], self.section_ref.normal(), old_length, len(v["text_chunk"].text))
            if self._save:
                v["text_chunk"].save()

    def _run(self):
        if self._report:
            print u"\n----\n*** Running SectionSplicer on {}\n".format(self.section_ref.normal())

        print u"\n*** Merging Base Text"
        self._reshape_base_text_version_segments()

        print u"\n*** Merging Commentary 1 Texts"
        self._reshape_all_commentary_versions()


class BlankSectionSplicer(SectionSplicer):
    def __init__(self):
        super(SectionSplicer, self).__init__()
        self._ready = True
        self.new_en_text = []
        self.new_he_text = []
        pass

    def __repr__(self):
        return "BlankSectionSplicer({})".format(self.section_ref.normal())

    def set_section(self, ref):
        assert ref.is_section_level()
        assert not ref.is_range()
        assert not ref.is_commentary()

        self.section_ref = ref
        self.book_ref = ref.index_node.ref()
        self.index = ref.index
        return self

    def get_empty_refs(self):
        return []

    def ref_maps(self):
        return []

    def get_commentary_determinations(self):
        return []

    def _run(self):
        return


class BookSplicer(object):
    """
    This currently has a lot of bespoke code for its particular project
    """

    def __init__(self, book_ref, section_splicers):
        """
        Initializes a book splicer from a list of section splicers
        :param section_splicers: List
        """
        self.book_ref = book_ref

        assert all([isinstance(a, SectionSplicer) for a in section_splicers])
        self.section_splicers = section_splicers

        self.segment_map_list = []
        for s in self.section_splicers:
            self.segment_map_list += s.ref_maps()
        self.segment_map = dict(self.segment_map_list)

        self.he_version = None
        self.en_version = None

    def set_text_versions(self, he_version, en_version):
        self.he_version = he_version
        self.en_version = en_version

    def test(self):
        for sp in self.section_splicers:
            sp.report()

    def get_empty_refs(self):
        return [r for sec in self.section_splicers for r in sec.get_empty_refs()]

    def execute(self):
        assert self.he_version and self.en_version

        for sp in self.section_splicers:
            sp.bulk_mode()
            sp.execute()
            self.en_version.chapter += [sp.new_en_text]
            self.he_version.chapter += [sp.new_he_text]

        self.en_version.save()
        self.he_version.save()

        self.section_splicers[-1].refresh_states()

        from sefaria.helper.link import rebuild_links_for_title
        #  This is long-running - postponing to after-deploy step
        #  rebuild_links_from_text(self.book_ref.normal(), 28)

        for c in self.section_splicers[-1].commentary_titles:
            rebuild_links_for_title(c, 28)

    def get_commentary_determinations(self):
        r = []
        for s in self.section_splicers:
            r += s.get_commentary_determinations()
        return r


def dh_extract_method(s):
    dh = re.split(u"(\s+[-\u2013]\s+|\.\s+)", s)[0] # Try " - ", or failing that ". "
    return re.sub(ur"\s+\u05d5?\u05db\u05d5['\u05f3]", u"", dh)  # space, vav?, kaf, vav, single quote or geresh
