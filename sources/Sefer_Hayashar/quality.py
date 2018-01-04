#encoding=utf-8
from sefaria.model import *
from sefaria.helper.schema import *
en_chapters = ["INTRODUCTION",
                "CHAPTER I The Mystery of the Creation of the World",

                "CHAPTER II The Pillars Of The Service Of God And Its Motivation",

                "CHAPTER III Concerning Faith and Matters Involved In The Mysteries Of The Creator Blessed Be He",

                "CHAPTER IV Service Briefly Discussed",

                "CHAPTER V Concerning The Pillars Of Worship",

                "CHAPTER VI An Explanation Of The Things Which Help In The Worship Of God May He Be Extolled And The Things Which Hinder",

                "CHAPTER VII Concerning Repentance And All Matters Pertaining To It From The Order Of Prayer And The Matters Of Self Restraint",

                "CHAPTER VIII Matters Concerning The Knowledge Of The Creator Blessed Be He",

                "CHAPTER IX Concerning The Signs Of The Will Of The Creator And How A Man Can Know He Has Found Favor In The Eyes Of His God And If God Has Accepted His Deeds",

                "CHAPTER X Concerning Repentance",

                "CHAPTER XI Concerning The Virtues Of The Righteous",

                "CHAPTER XII Concerning The Mysteries Of The World To Come",

                "CHAPTER XIII Concerning Service to God",

                "CHAPTER XIV Concerning The Reckoning A Man Must Make With Himself",

                "CHAPTER XV Explaining The Time Which Is Most Proper For The Service Of God Blessed Be He",

                "CHAPTER XVI I shall note in this chapter some of the delights of the world to come and as opposed to them I will note the plagues the stumbling blocks and the evil of this world",

                "CHAPTER XVII When A Man Remembers The Day Of Death",

                "CHAPTER XVIII Concerning The Difference Between The Righteous Man And The Wicked One",

                "TRANSLATORS FOREWORD",

                "Addendum I THE ETHICAL WORK SEFER HAYASHAR AND THE PHILOSOPHICAL VIEWS CONTAINED THEREIN",

                "Addendum II THE LOVE AND THE FEAR OF GOD IN THE SEFER HAYASHAR"]

def add_default_node_and_addendums():
    index = library.get_index("Sefer HaYashar")
    root = index.nodes

    node_titles = [node.get_titles("en") for node in root.children]
    if [] in node_titles:
        print "Already has default"
    else:
        default = JaggedArrayNode()
        default.key = "default"
        default.default = True
        default.add_structure(["Chapter", "Paragraph"])

        attach_branch(default, root, 1)

    if "Addendum I" in node_titles:
        print "Already has addendum"
    else:
        node = JaggedArrayNode()
        node.add_structure(["Paragraph"])
        node.add_primary_titles("Addendum I", u"נספח א")
        attach_branch(node, root, -1)

        node = JaggedArrayNode()
        node.add_structure(["Paragraph"])
        node.add_primary_titles("Addendum II", u"נספח ב")
        attach_branch(node, root, -1)

def remove_chapter_nodes():
    index = library.get_index("Sefer HaYashar")
    root = index.nodes
    old_nodes = []

    for node in root.children:
        if getattr(node, "default", False):
            continue
        title = node.get_titles("en")[0]
        if "CHAPTER" in title:
            old_nodes.append((node.get_titles('en')[0], node.get_titles('he')[0]))
            remove_branch(node)
        elif "Addendum" in title:
            old_title = node.get_titles('en')[0]
            if len(old_title.split(" ")) >= 3:
                remove_branch(node)
        elif "Footnotes" in title:
            remove_branch(node)
    return old_nodes


def rewriter(ref):
    ref = Ref(ref)
    if ref.is_range():
        start = ref.starting_ref().normal()
        end = ref.ending_ref().normal()
        if start in segment_map and end in segment_map:
            return Ref(segment_map[start]).to(Ref(segment_map[end])).normal()
        elif start in segment_map:
            return segment_map[start]
        elif end in segment_map:
            return segment_map[end]
        else:
            return ref.normal()
    elif ref.normal() not in segment_map:
        return ref.normal()
    else:
        return segment_map[ref.normal()]


def needs_rewrite(str, *kwargs):
    try:
        needsRewrite = str.startswith("Sefer HaYashar, CHAPTER") or str.startswith("Sefer HaYashar, Addendum I")
        if needsRewrite:
            print "NEEDS REWRITER: {}".format(str)
        return needsRewrite
    except InputError as e:
        print "Problem with {}".format(str)
        print e.message



def generate_segment_mapping(title, mapping, output_file=None, mapped_title=lambda x: "Complex {}".format(x)):
    '''
    :param title: title of Index record
    :param mapping: mapping is a dict where each key is a reference in the original simple Index and each value is a reference in the new complex Index
    such as mapping['Zohar 1:2a'] = 'Zohar, Genesis'
    :param mapped_title: lambda that determines the title of the Index that the map points to.  It will
    usually be lambda x: x or lambda x: "Complex {}".format(x), since it will either be the same Index on both
    sides of the map or it will be a new complex Index temporarily prepended with the word "Complex".
    :param output_file:
    :return segment_map: segment_map is the dict based on mapping

    The function takes each key/value pair in mapping and adds this key/value pair to the segment_map,
    and it also adds every possible key/value pair that are descendants of the key/value pairs in mapping to the segment_map.
    In the above example,
    segment_map['Zohar 1:2a'] = 'Zohar, Genesis'
    segment_map['Zohar 1:2a:1'] = 'Zohar, Genesis 1'
    segment_map['Zohar 1:2a:2'] = 'Zohar, Genesis 2'
    etc.

    :return segment_map:
    '''

    segment_map = {}
    for orig_ref in mapping:
        orig_ref_str = orig_ref
        orig_ref = Ref(orig_ref)
        refs = []

        #now create an array, refs that holds the orig_ref in addition to all of its children
        if orig_ref.is_range():
            depth = orig_ref.range_depth()
            if depth == 1:
                refs = orig_ref.range_list()
            elif depth == 2:
                top_level_refs = orig_ref.split_spanning_ref()
                segment_refs = orig_ref.range_list()
                refs = top_level_refs + segment_refs
            elif depth == 3:
                top_level_refs = orig_ref.split_spanning_ref()
                section_refs = orig_ref.range_list()
                segment_refs = orig_ref.as_ranged_segment_ref().range_list()
                refs = top_level_refs + section_refs + segment_refs
        else:
            refs = orig_ref.all_subrefs()
            if len(refs) > 0 and not refs[0].is_segment_level():
                len_refs = len(refs)
                segment_refs = []
                for i in range(len_refs):
                    segment_refs += refs[i].all_subrefs()
                assert segment_refs[0].is_segment_level()
                refs += segment_refs
            refs += [orig_ref]

        #segment_value is the value of the mapping that the user inputted
        segment_value = mapped_title(mapping[orig_ref_str])

        #now iterate over the refs and create the key/value pairs to put into segment_map
        for each_ref in refs:
            assert each_ref not in segment_map, "Invalid map ranges: Two overlap at reference {}".format(each_ref)
            if each_ref == orig_ref:
                segment_map[each_ref.normal()] = segment_value
            else:
                '''
                get in_terms_of() info to construct a string that represents the complex index's new reference.
                construct the new reference by appending the results of in_terms_of() onto
                segment_value -- where segment_value is the value that the parameter, mapping, returns for the key of orig_ref
                '''
                append_arr = each_ref.in_terms_of(orig_ref)
                assert append_arr, "{} cannot be computed to be in_terms_of() {}".format(each_ref, orig_ref)
                segment_ref = Ref(segment_value)
                core_dict = segment_ref._core_dict()
                core_dict['sections'] += append_arr
                core_dict['toSections'] += append_arr

                segment_map[each_ref.normal()] = Ref(_obj=core_dict).normal()

    #output results so that this map can be used again for other purposes
    if output_file:
        output_file = open(output_file, 'w')
        assert type(output_file) is file
        for key in segment_map:
            output_file.write("KEY: {}, VALUE: {}".format(key, segment_map[key])+"\n")
        output_file.close()
    return segment_map


def add_alt_struct(old_nodes):
    nodes = []
    for count, titles_tuple in enumerate(old_nodes):
        en, he = titles_tuple
        node = ArrayMapNode()
        node.add_primary_titles(en, he)
        node.depth = 0
        node.wholeRef = "Sefer HaYashar {}".format(count+1)
        node.refs = []
        nodes.append(node.serialize())
    index = library.get_index("Sefer HaYashar")
    contents = index.contents(v2=True, raw=True)
    contents['alt_structs'] = {}
    contents['alt_structs']["Chapter"] = {"nodes": nodes}
    index.load_from_dict(contents).save()


def get_mapping():
    mapping = {}
    for i, ch in enumerate(en_chapters):
        ch = "Sefer HaYashar, {}".format(ch)
        if ch.startswith("Sefer HaYashar, CHAPTER "):
            mapping[ch] = "Sefer HaYashar {}".format(i)
        else:
            if "Addendum" in ch:
                new_ch = " ".join(ch.split(" ")[0:4])
            else:
                new_ch = ch
            mapping[ch] = new_ch

    return mapping


if __name__ == "__main__":
    title = "Sefer HaYashar"
    add_default_node_and_addendums()

    #cascade links, sheets, and history from old structure based on chapters to new structure based on default node
    mapping = get_mapping()
    segment_map = generate_segment_mapping(title, mapping, mapped_title=lambda x: x)
    cascade(title, rewriter, needs_rewrite)

    #remove chapter nodes from main structure and create alt struct with the chapters
    old_nodes = remove_chapter_nodes()
    add_alt_struct(old_nodes)

    #still may need to remove data for Footnotes node
    ftnote_links = LinkSet({"refs": {"$regex": "^Sefer HaYashar, Footnotes"}})
    print "Removing {} 'Sefer HaYashar, Footnotes' links".format(ftnote_links.count())
    ftnote_links.delete()

    ftnote_history = HistorySet({"ref": {"$regex": "^Sefer HaYashar, Footnotes"}})
    print "Removing {} 'Sefer HaYashar, Footnotes' history".format(ftnote_history.count())
    ftnote_history.delete()