# coding=utf-8

"""
Map out stars in Mechaber text to Beer HaGolah

1) Identify locations in Beer HaGolah file where stars appear:
{
    siman_num,
    star_count: number of stars appearing one after the next,
    preceding_index: number of preceding (lettered) beer hagolah comment,  0 if star appears at the beginning of a siman
    preceding_letter: letter of preceding beer hagolah comment,  None if star appears at the beginning of a siman
    following_index: 0 if star appears at the end of a siman
    following_letter: None if star pears at the en of a siman
}

2) Instantiate a StructuredDocument around the Shulchan Arukh files

3) Use the StructuredDocument to find stars based on the identifying data. Check that the correct number of stars exist
at the desired location
"""

import re
import codecs
from data_utilities.util import getGematria

filenames = {
    'part_1': u'/home/jonathan/sefaria/Sefaria-Data/sources/Shulchan_Arukh/txt_files/Even_Haezer/part_1/באר הגולה אבן העזר חלק א.txt',
    'part_2': u'/home/jonathan/sefaria/Sefaria-Data/sources/Shulchan_Arukh/txt_files/Even_Haezer/part_2/שולחן ערוך אבן האזל חלק ב באר הגולה.txt'
}


def identify_star_locations(filename):
    def get_regex():
        partial_regexes = [u'@12([\u05d0-\u05ea]{1,3})', u'@11([\u05d0-\u05ea])', u'@11(\*)']
        names = [u'siman', u'seif', u'star']
        my_full_regexes = [u'(?P<{}>{})'.format(*i) for i in zip(names, partial_regexes)]
        return re.compile(u'|'.join(my_full_regexes))

    with codecs.open(filename, 'r', 'utf-8') as infile:
        lines = infile.readlines()

    siman, seif_index, seif_letter, num_stars = -1, 0, None, 0
    star_locations, current_star = [], {}
    line_regex = get_regex()

    for line in lines:
        line_data = line_regex.search(line)
        if line_data is None:
            continue

        elif line_data.lastgroup == u'star':
            num_stars += 1
            current_star = {
                u'siman_num': siman,
                u'preceding_index': seif_index,
                u'preceding_letter': seif_letter
            }

        else:
            if line_data.lastgroup == u'seif':
                seif_index += 1
                seif_letter = line_data.group(line_data.lastindex+1)

            elif line_data.lastgroup == u'siman':
                siman = getGematria(line_data.group(line_data.lastindex+1))
                seif_index = 0
                seif_letter = None

            else: raise LookupError(u"Expecting seif or siman, got {}".format(line_data.lastgroup))

            if num_stars >= 1:
                current_star[u'star_count'] = num_stars
                current_star[u'following_index'] = seif_index
                current_star[u'following_letter'] = seif_letter
                star_locations.append(current_star)
                num_stars = 0
    else:
        if num_stars >= 1:
            current_star[u'star_count'] = num_stars
            current_star[u'following_index'] = 0
            current_star[u'following_letter'] = None
            star_locations.append(current_star)

    return star_locations
