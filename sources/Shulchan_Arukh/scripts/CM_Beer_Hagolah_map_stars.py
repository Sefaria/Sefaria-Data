#encoding=utf-8
"""
Create a listing of each Seif in Shulchan Arukh. This can just be a nested list as follows:
[[{'SA': 5, 'BH': 5}, {'SA': 7, 'BH': 4]]
Outer list is Seif, inner is Siman

Each Seif must record number of '*'s in both SA and BH
Running through SA is simple. Go seif by seif and count '*'s
For BH, count '*'s, then determine seif by using the rid and CommentStore.

"""
import re
import codecs
from sources.Shulchan_Arukh.ShulchanArukh import *


def bh_to_sa_mapping(beer_simanim):
    mapping = []
    comment_store = CommentStore()
    for chapter in beer_simanim:
        while chapter.num - len(mapping) > 1:
            print "adding at {}".format(chapter.num)
            mapping.append([])
        mapping.append([comment_store[s.rid]['seif'][0]-1 for s in chapter.get_child()])

    return mapping



def jump_tag(parent_tag, tag_names):
    """
    Converts a tag to a string while skipping over a specific descendant
    :param Tag parent_tag: Tag to convert to string
    :param tag_names: list of names to skip over
    :return: unicode string
    """
    return u''.join([unicode(c) for c in filter(lambda x: None if x.name in tag_names else True, parent_tag.children)])

simanim = []
root = Root('../Choshen_Mishpat.xml')
root.populate_comment_store()
match_locations = set()

base = root.get_base_text()
for siman in base.get_simanim():
    cur = []
    for seif in siman.get_child():
        # count stars, but skip over xrefs and itags
        num_stars = u''.join([jump_tag(p.Tag, {u'xref', u'i'}) for p in seif.get_child()]).count(u'*')
        cur.append({'SA': num_stars, 'BH': 0})

        # check for other stars inside xrefs and itags that might cause issues
        if unicode(seif).count(u'*') != num_stars:
            print "Problem at Shulchan Arukh {}:{}".format(siman.num, seif.num)

    simanim.append(cur)

beer = root.get_commentaries().get_commentary_by_title(u"Be'er HaGolah")
store = CommentStore()
for siman in beer.get_simanim():
    for seif in siman.get_child():
        num_stars = u''.join([jump_tag(p.Tag, {u'xref', u'i'}) for p in seif.get_child()]).count(u'*')
        b_siman, b_seif = store[seif.rid]['siman'], store[seif.rid]['seif'][0]
        simanim[b_siman-1][b_seif-1]['BH'] += num_stars

        # check for other stars inside xrefs and itags that might cause issues
        if unicode(seif).count(u'*') != num_stars:
            print "Problem at Be'er HaGolah {}:{}".format(siman.num, seif.num)

for si_index, siman in enumerate(simanim):
    for se_index, seif in enumerate(siman):
        if (seif['SA'] == seif['BH']) and (seif['SA'] > 0):
            match_locations.add((si_index, se_index))

"""
We now have a mapping of locations where '*'s can be fixed.
This can be done easily enough in SA
Be'er HaGolah is more complex
One solution is to keep the parsed text and use that to get 'rid's to look up in the CommentStore
Another solution is make a simpler map of Be'er HaGolah to SA.
It could look like this:
[[1, 1, 1, 2, 2, 3, 3, 4....]]
where each internal array represents a siman and each number represents which seif this maps to in the base text

When iterating over a file, keep track of Siman, Seif
Each file will need it's own markup system. Ideally, we would stick a Be'er HaGolah tag right next to the *
In the Be'er Hagolah files, we'll need to wrap these with line endings, but maybe that can be done in post-processing

A simple function can encapsulate the re-writing. It would need the file, match locations, starting siman, how to mark
up stars, a 'start-mark' and for Ba'er HaGolah a mapping to base seifim. Also, a regex for simanim and seifim.

There are not more stars hidden in xrefs
"""
def mark_stars(filename, markup, edit_locations, siman_mark, seif_mark, starting_siman=-1, start_mark=None,
               is_beer=False, test_mode=True):
    with codecs.open(filename, 'r', 'utf-8') as infile:
        lines = infile.readlines()
    fixed_lines = []
    if is_beer:
        beer_mapping = bh_to_sa_mapping(beer.get_simanim())
    else:
        beer_mapping = None

    if not start_mark:
        started = True
    else:
        started = False

    current_siman, current_seif = starting_siman, -1

    for line in lines:
        if started:
            if re.search(siman_mark, line):
                current_siman += 1
                current_seif = -1
            elif re.search(seif_mark, line):
                current_seif += 1
            else:
                if is_beer:
                    base_seif = beer_mapping[current_siman][current_seif]
                else:
                    base_seif = current_seif
                if (current_siman, base_seif) in edit_locations:
                    line = line.replace(u'*', markup)

        else:
            if re.search(start_mark, line):
                started = True

        fixed_lines.append(line)

    if test_mode:
        filename = re.sub(ur'\.txt', u'_test.txt', filename)
        assert re.search(u'_test', filename) is not None
    with codecs.open(filename, 'w', 'utf-8') as outfile:
        outfile.writelines(fixed_lines)

beer_1 = {
    'filename': u'../txt_files/Choshen_Mishpat/part_1/שוע חושן משפט חלק א באר הגולה.txt',
    'markup': u'\n@11s\n',
    'edit_locations': match_locations,
    'siman_mark': '@12',
    'seif_mark': '@11',
    'is_beer': True
}
base_1 = {
    'filename': u'../txt_files/Choshen_Mishpat/part_1/שולחן ערוך חושן משפט חלק א מחבר.txt',
    'markup': u'@68s',
    'edit_locations': match_locations,
    'siman_mark': u'@22',
    'seif_mark': u'@11',
    'start_mark': u'!start!'
}
