# coding=utf-8

"""
Map out stars in Mechaber text to Beer HaGolah

1) Identify locations in Beer HaGolah file where stars appear:
{
    siman_num,
    star_count: number of stars appearing one after the next,
    preceding_index: number of preceding (lettered) beer hagolah comment,  -1 if star appears at the beginning of a siman
    preceding_letter: letter of preceding beer hagolah comment,  None if star appears at the beginning of a siman
    following_index: -1 if star appears at the end of a siman
    following_letter: None if star pears at the en of a siman
}

2) Instantiate a StructuredDocument around the Shulchan Arukh files

3) Use the StructuredDocument to find stars based on the identifying data. Check that the correct number of stars exist
at the desired location
"""

import re
import codecs
from data_utilities.util import getGematria, StructuredDocument

filenames = {
    'beer_part_1': u'/home/jonathan/sefaria/Sefaria-Data/sources/Shulchan_Arukh/txt_files/Even_Haezer/part_1/באר הגולה אבן העזר חלק א.txt',
    'beer_part_2': u'/home/jonathan/sefaria/Sefaria-Data/sources/Shulchan_Arukh/txt_files/Even_Haezer/part_2/שולחן ערוך אבן האזל חלק ב באר הגולה.txt',
    'mechaber_part_1': u'/home/jonathan/sefaria/Sefaria-Data/sources/Shulchan_Arukh/txt_files/Even_Haezer/part_1/אבן העזר חלק א מחבר.txt',
    'mechaber_part_2': u'/home/jonathan/sefaria/Sefaria-Data/sources/Shulchan_Arukh/txt_files/Even_Haezer/part_2/שולחן ערוך אבן האזל חלק ב מחבר.txt'
}


def identify_star_locations(filename):
    def get_regex():
        partial_regexes = [u'@12([\u05d0-\u05ea]{1,3})', u'@11([\u05d0-\u05ea])', u'@11(\*)']
        names = [u'siman', u'seif', u'star']
        my_full_regexes = [u'(?P<{}>{})'.format(*i) for i in zip(names, partial_regexes)]
        return re.compile(u'|'.join(my_full_regexes))

    with codecs.open(filename, 'r', 'utf-8') as infile:
        lines = infile.readlines()

    siman, seif_index, seif_letter, num_stars = -1, -1, None, 0
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
                seif_index = -1
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


def fix_stars(siman_text, star_loc):
    siman_char_list = list(siman_text)  # we will use this to make an in-place substitution of the stars
    beer_marks = list(re.finditer(u'@44([\u05d0-\u05ea])', siman_text))

    # we want to limit our search the just the space between the preceding and following beer hagolah markers
    if star_loc['preceding_letter']:
        # check that letters and indices match up between mechaber and beer hagolah
        preceding_letter = beer_marks[star_loc['preceding_index']]
        if preceding_letter.group(1) != star_loc['preceding_letter']:
            star_loc[u'Problem'] = u'Previous letters did not match up ({} at this index in Mechaber)'.format(preceding_letter.group(1))
            raise AssertionError
        start_pos = preceding_letter.end()  # stars must be located after this position
    else:
        start_pos = 0

    if star_loc['following_letter']:
        # same as above, check that letters and indices match up between both files
        following_letter = beer_marks[star_loc['following_index']]
        if following_letter.group(1) != star_loc['following_letter']:
            star_loc[u'Problem'] = u'Following letters did not match up ({} at this index in Mechaber)'.format(following_letter.group(1))
            raise AssertionError
        end_pos = following_letter.start()
    else:
        end_pos = len(siman_text)

    search_space = siman_text[start_pos:end_pos]
    star_matches = list(re.finditer(u'[*|\u2022]', search_space))
    if len(star_matches) != star_loc['star_count']:
        star_loc[u'Problem'] = u'Incorrect number of stars found in Mechaber({})'.format(len(star_matches))
        raise AssertionError

    for match in star_matches:
        star_pos = match.start() + start_pos

        if siman_char_list[star_pos] == u'*':
            siman_char_list[star_pos] = u'@44\u2022'
        elif siman_char_list[star_pos] == u'\u2022':
            continue
        else:
            star_loc[u'Problem'] = u'Replacement index did not contain star'
            raise AssertionError

    return u''.join(siman_char_list)


def correct_stars_in_file(part, test_mode=True):
    file_obj = StructuredDocument(filenames['mechaber_part_{}'.format(part)], u'@22([\u05d0-\u05ea]{1,3})')
    star_locs = identify_star_locations(filenames['beer_part_{}'.format(part)])
    bad_locs = []

    for star_loc in star_locs:
        try:
            file_obj.edit_section(star_loc['siman_num'], fix_stars, star_loc)
        except AssertionError:
            bad_locs.append(star_loc)
    if test_mode:
        file_obj.write_to_file(filenames['mechaber_part_{}'.format(part)].replace(u'.txt', u'_test.txt'))
    else:
        file_obj.write_to_file(filenames['mechaber_part_{}'.format(part)])

    keys = [u'siman_num', u'star_count', u'preceding_letter', u'preceding_index', u'following_letter', u'following_index', u'Problem']
    for b in bad_locs:
        for key in keys:
            print u'{}: {}'.format(key, b[key]),
        print u''

correct_stars_in_file(1)
correct_stars_in_file(2)
