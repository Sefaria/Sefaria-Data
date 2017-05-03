# encoding=utf-8

from data_utilities.util import numToHeb
from sources.Shulchan_Arukh.ShulchanArukh import *

"""
Todo:
Look for @11(letter) that does not follow a reasonable pattern
A reasonable pattern here is 1,2,3...22,1,2,3
Report on lines that go "off"
This can be done by subtracting both indices. If the result % 22 is not 1 and the second index is not 1, then an issue
can be reported.

Load Simanim From Shulchan Arukh
For each Siman, count how many references appear
Attempt to locate that number of references in commentary file
Ensure that after that number of references, the following reference is 1.
"""
filenames = {
    'part_1': u'../txt_files/Choshen_Mishpat/part_1/שוע חושן משפט חלק א באר הגולה.txt',
    'part_2': u'../txt_files/Choshen_Mishpat/part_2/שולחן ערוך חושן משפט חלק ב באר הגולה.txt',
    'part_3': u'../txt_files/Choshen_Mishpat/part_3/באר הגולה חושן משפט חלק ג.txt'
}
def reasonble_order(index_a, index_b):
    """
    Look for @11(letter) that does not follow a reasonable pattern
    A reasonable pattern here is 1,2,3...22,1,2,3
    Report on lines that go "off"
    This can be done by subtracting both indices. If the result % 22 is not 1 and the second index is not 1, then an issue
    can be reported.
    :param index_a: First index to appear
    :param index_b: Second index to appear (if not 1, should be higher than index_a)
    :return: boolean
    """
    if (index_b - index_a) % 22 != 1:
        if index_b != 1:
            return False
    return True


def find_errors_in_file(filename):
    with codecs.open(filename, 'r', 'utf-8') as infile:
        lines = infile.readlines()
    seif_values = (None, None)
    seif_reg = re.compile(u'^@11([\u05d0-\u05ea])')

    for line_num, line in enumerate(lines):
        match = seif_reg.match(line)
        if match:
            seif_values = (seif_values[1], match.group(1))
            if None not in seif_values and not reasonble_order(*[he_ord(i) for i in seif_values]):
                print u'Issue found on line {}: {} followed by {}'.format(line_num+1, *seif_values)


"""
Find Simanim:
Instantiate an array to hold text
Load Each Siman (base text)
Count references in base text
Begin walking through file, recording how many new_seif patterns were found. Each line should be saved to an array
2 things should occur when a Siman is complete:
    1) The number of new_seif patterns should match the number of references in Siman
    2) The next Seif should be labeled א
If both these conditions are met, append the siman title, then add the rest of the text.
If only the first condition is met, terminate. Also, if a jump back to 1 occurs without the correct number of references
being found, terminate.
On termination - add the rest of the lines in the file to the array, then write the result to a
file. This partial result will help with locating the errors in the original file.
If there are no more Simanim, and there are still lines, terminate.

It seems termination is too extreme. I probably only want to terminate if I've run out of Simanim, or the number of
expected refs far exceeds the number of found refs. In this case, I'll only want to log a mismatch.

Two cases can be defined as an end of siman:
1) A clear transition
2) Finding the expected refs and the following seif is marked as 1

The case of an "unclear" transition presents itself: Where a Siman ends exactly at ת. This is a problem if a mismatch
occurs between expected and found refs.

An arguably better solution would be to locate where transitions appear in advance. I can now attempt to match simanim
based on the order they appear.

An "unclear" transition can located by the fact that simanim separated by these will get merged together. A large
discrepancy between on a group of references that is (give or take 1) equivalent to two Simanim should suffice to break
of the simanim. I will break on the א marker that causes the lowest difference between the expected refs.
"""

class SimanLocater(object):

    def __init__(self, volume):
        with codecs.open(filenames['part_{}'.format(volume)], 'r', 'utf-8') as infile:
            self.source_lines = infile.readlines()

        self.base_simanim = [{
            'num': s.num,
            'total_refs': len(s.locate_references(u'@68'))
        } for s in Root('../Choshen_Mishpat.xml').get_base_text().get_volume(volume).get_child()]
        self.base_simanim = filter(lambda x: None if x['total_refs']==0 else x, self.base_simanim)
        self.commentary_simanim = self.find_transitions()

    def find_transitions(self):
        """
        Locate Potential Siman transitions in source file.
        :return: List of dictionaries, with fields start and end, which store the line numbers (0 indexed) of the beginning
        and end of each siman, and total, which records total number of simanim found
        """
        def transition(index_a, index_b):
            if None in (index_a, index_b):
                return False
            return (index_b - index_a) % 22 != 1 and index_b == 1

        simanim = []
        seif_values = (None, None)
        siman_start, count = 0, 0
        new_seif_ref = re.compile(u'^@11([\u05d0-\u05ea])')

        for line_num, line in enumerate(self.source_lines):
            match = new_seif_ref.match(line)
            if match:
                seif_values = (seif_values[1], he_ord(match.group(1)))
                if transition(*seif_values):
                    simanim.append({
                        'start': siman_start,
                        'end': line_num-1,
                        'total': count
                    })
                    siman_start = line_num
                    count = 1
                else:
                    count += 1
        else:
            simanim.append({
                'start': siman_start,
                'end': line_num,
                'total': count
            })

        return simanim

    @staticmethod
    def almost_equals(a, b, pad=2):
        return abs(b-a) <= pad

    def locate_merge(self):
        if len(self.commentary_simanim) == len(self.base_simanim):
            print "No merges found"
            return None

        for siman_index, com_siman in enumerate(self.commentary_simanim):
            if not self.almost_equals(com_siman['total'], self.base_simanim[siman_index]['total_refs']):
                combined = self.base_simanim[siman_index]['total_refs'] + self.base_simanim[siman_index+1]['total_refs']
                if self.almost_equals(com_siman['total'], combined):
                    print "Suspected merge at lines {}-{}".format(com_siman['start']+1, com_siman['end']+1)
                    return siman_index
                else:
                    print "Major conflict found at lines {}-{}. Should match siman {}"\
                        .format(com_siman['start']+1, com_siman['end']+1, self.base_simanim[siman_index]['num'])
                    raise AssertionError
        raise AssertionError("Could not locate merge")

    def resolve_merge(self, merge_index, max_diff=3):
        """
        1) Get number of Seifim in each siman from base
        2) Find locations where a split can be made
        3) For each split location calculate deviation from base text
        4) Get location with lowest deviation
        5) Check that the split is within a reasonable distance from expected
        6) Make the split
        :param merge_index:
        :return:
        """
        merged_siman = self.commentary_simanim[merge_index]
        expected_refs = (self.base_simanim[merge_index]['total_refs'], self.base_simanim[merge_index+1]['total_refs'])
        split_locations, count = [], 0
        for line_num, line in enumerate(self.source_lines[merged_siman['start']:merged_siman['end']+1]):
            match = re.match(u'^@11([\u05d0-\u05ea])', line)
            if match:
                if match.group(1) == u'א':
                    split_locations.append({'line_num': line_num, 'count': count})
                count += 1

        for location in split_locations:
            diff_a = abs(expected_refs[0] - location['count'])
            diff_b = abs(expected_refs[1] - (count - location['count']))
            location['diff'] = diff_a + diff_b
        best_location = min(split_locations, key=lambda x: x['diff'])
        assert best_location['diff'] < max_diff

        self.commentary_simanim.insert(merge_index, {
            'start': merged_siman['start'],
            'end': merged_siman['start'] + best_location['line_num'] - 1,
            'total': best_location['count']
        })
        merged_siman['start'] = merged_siman['start'] + best_location['line_num']
        merged_siman['total'] = merged_siman['total'] - best_location['count']

    def output(self, filename=u'temp_result.txt'):
        full_text = []
        for com_siman, base_siman in zip(self.commentary_simanim, self.base_simanim):
            if not self.almost_equals(com_siman['total'], base_siman['total_refs']):
                print "Divergence in siman {}".format(base_siman['num'])

            full_text.append(u'@12{}\n'.format(numToHeb(base_siman['num'])))
            full_text.extend(self.source_lines[com_siman['start']:com_siman['end']+1])
        with codecs.open(filename, 'w', 'utf-8') as outfile:
            outfile.writelines(full_text)




def mark_simanim(volume_number):

    def transition(index_a, index_b):
        return (index_b - index_a) % 22 != 1 and index_b == 1

    def terminate():
        full_text.append(u'@12{}\n'.format(numToHeb(current_siman.num)))
        full_text.extend(current_siman_text)
        full_text.extend(lines[line_num:])
        with codecs.open('temp_result.txt', 'w', 'utf-8') as outfile:
            outfile.writelines(full_text)

    def get_next_siman(siman_list):
        siman, total_refs = None, 0
        while total_refs == 0:
            siman = siman_list.next()
            total_refs = len(siman.locate_references(u'@68'))
        return siman, total_refs


    with codecs.open(filenames['part_{}'.format(volume_number)], 'r', 'utf-8') as infile:
        lines = infile.readlines()

    volume = Root('../Choshen_Mishpat.xml').get_base_text().get_volume(1)
    simanim = iter(volume.get_child())
    current_siman, expected_refs = get_next_siman(simanim)

    full_text, current_siman_text = [],[]
    count = 0
    seif_markers = (None, None)

    for line_num, line in enumerate(lines):
        match = re.search(u'^@11([\u05d0-\u05ea])', line)
        if match:
            count += 1
            seif_markers = (seif_markers[1], he_ord(match.group(1)))

            if count - expected_refs == 1:
                if match.group(1) == u'א':
                    full_text.append(u'@12{}\n'.format(numToHeb(current_siman.num)))
                    full_text.extend(current_siman_text)
                    current_siman_text = []
                    count = 1
                    try:
                        current_siman, expected_refs = get_next_siman(simanim)
                    except StopIteration:
                        print "Ran out of Simanim"
                        terminate()
                        return
                else:
                    print "Siman {}: Completed refs before transition occurred".format(current_siman.num)
                    terminate()
                    return
            elif None not in seif_markers and transition(*seif_markers):
                print "Siman {}: Transition occurred before completing refs".format(current_siman.num)
                terminate()
                return
        current_siman_text.append(line)
    full_text.append(u'@12{}\n'.format(numToHeb(current_siman.num)))
    full_text.extend(current_siman_text)
    with codecs.open('temp_result.txt', 'w', 'utf-8') as outfile:
        outfile.writelines(full_text)

s = SimanLocater(1)
merge_index = s.locate_merge()
while merge_index is not None:
    s.resolve_merge(merge_index)
    merge_index = s.locate_merge()
s.output(filename=filenames['part_1'])

