# encoding=utf-8

import re
import os
from YD_base import filenames, patterns
from collections import defaultdict, Counter
from parsing_utilities.util import StructuredDocument, getGematria
from sources.Shulchan_Arukh.ShulchanArukh import correct_marks_in_file

u"""
Get all errors in a siman.
several types:
1) mislabled - ח instead of ה 
2) out of place - 1,7,2
3) missing - 1,3,4
4) double tag - 1,2,2,3

We already know how to fix a mislabeled comment. We want to see if it's possible to identify "out of place" comments as
the missing comment in a different sequence.

For this, we should have an error dict:
{
    "type": <out of place or missing>,
    "from_sequence": <which sequence this error came from>,
    "value": <numeric value of tag>,
}
Then we can check all the "out of place" errors against the "missing" errors.
"out_of_place" errors should have a "loc" parameter -> the character position of said tag.
"missing" errors should have a "range" parameter -> the range of characters where said correction must appear.
"out_of_place" error should also have the full matched tag text

Important - we need to ensure that there isn't more that each missing error matches against 1 and only 1 misplaced error
Also, we need to check that each out of place error matches with only 1 missing error.

Error identification:
missing: current - previous == 2; following - current == 1
out of place: following - previous == 1

Error correction:
Construct a regex for the specific tag to be replaced. Catch the numeric part as group 1.
Ensure that there is 1 and only 1 match for said regex.
Use re.sub with a function. The function will then use a code to construct the correct tag. Example:
If @55יג needs to be changed to @44(יג), the function will use the code @44({}) with a .format. 
"""

codes = [
 u'@55{}',
 u'@66({})',
 u'@71({})',
 u'@74({})',
 u'@99[{}]',
 u'@44{}',
 u'&[{}]'
]


def identify_errors(siman, pattern, sequence_code):
    errors = []
    matches = list(re.finditer(pattern, siman))
    previous = 0
    jump_ahead = False
    for i, match in enumerate(matches):
        if jump_ahead:
            jump_ahead = False
            continue
        try:
            current, following = getGematria(match.group(1)), getGematria(matches[i+1].group(1))
        except IndexError:
            break
        if current - previous == 0:  # double tag
            previous = current
            continue

        elif current - previous == 2 and following - current == 1:  # missing tag
            error = {
                u'type': u'missing',
                u'from_sequence': sequence_code,
                u'value': current-1,
            }
            if i == 0:
                error[u'range'] = (0, match.start())
            else:
                error[u'range'] = (matches[i-1].end(), match.start())
            errors.append(error)
            previous = current
            continue

        elif following - previous == 1 and current - previous != 1:  # out of place
            errors.append({
                u'type': u'out_of_place',
                u'from_sequence': sequence_code,
                u'value': current,
                u'tag': match.group(),
                u'loc': match.start()
            })
            previous = following
            jump_ahead = True
        else:
            previous = current
    return errors


def find_correctable(error_list):
    def between(location, acceptable_range):
        return acceptable_range[0] < location < acceptable_range[1]

    missing, out_of_place = defaultdict(list), []
    for error in error_list:
        if error[u'type'] == u'missing':
            missing[error['value']].append(error)
        elif error[u'type'] == u'out_of_place':
            out_of_place.append(error)
        else:
            raise KeyError

    for out_error in out_of_place:
        matches = 0
        for missing_error in missing[out_error['value']]:
            if between(out_error[u'loc'], missing_error[u'range']):
                matches += 1
                out_error[u'correction'] = missing_error[u'from_sequence']
        if matches > 1:  # more than one correction possibility -> we don't know how to correct
            del out_error[u'correction']
    correctable = [out_error for out_error in out_of_place if out_error.has_key(u'correction')]

    # scan through correctable errors and look for possible errors that would resolve to the same place
    correction_counts = Counter([(c[u'value'], c[u'correction']) for c in correctable])
    correctable = [c for c in correctable if correction_counts[(c[u'value'], c[u'correction'])] == 1]
    return correctable


def fix_errors(my_text, fixable_error_list):
    # mark fixable tags so that they will not be confused with regular tags
    my_text = list(my_text)
    for error_dict in fixable_error_list:
        my_text[error_dict['loc']] = u'%'
    my_text = u''.join(my_text)

    for error_dict in fixable_error_list:
        pattern_base = re.sub(ur'[()\[\]]', ur'\\\g<0>', error_dict[u'from_sequence'])
        tag_pattern = pattern_base.format(u'({})'.format(
            re.search(ur'[\u05d0-\u05ea]{1,3}', error_dict[u'tag']).group(0))
        )
        tag_pattern = tag_pattern.replace(u'@', u'%')
        total_matches = len(re.findall(tag_pattern, my_text))
        if total_matches != 1:
            print "Found {} copies - cannot fix".format(total_matches)
            continue
        my_text = re.sub(tag_pattern, lambda x: error_dict[u'correction'].format(x.group(1)), my_text)
    return my_text


for vol in range(1, 5):
    s = StructuredDocument(filenames[vol], u'@22([\u05d0-\u05ea]{1,3})')
    for siman in s.get_chapter_values():
        if siman == 297:
            continue
        print "\n Siman {}".format(siman)
        problems = []
        for pattern, code in zip(patterns, codes):
            problems.extend(identify_errors(s.get_section(siman), pattern, code))
        for p in problems:
            print p
        stuff = find_correctable(problems)
        print "fixable:"
        for i in stuff:
            print i
        s.edit_section(siman, fix_errors, stuff)
    s.write_to_file(filenames[vol])
    for pattern in patterns:
        correct_marks_in_file(filenames[vol], u'@22', pattern)
