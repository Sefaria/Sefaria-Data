#encoding=utf-8

import time
from sources.Shulchan_Arukh.ShulchanArukh import *

filenames = {
    'part_1': u'../../txt_files/Even_Haezer/part_1/באר הגולה אבן העזר חלק א.txt',
    'part_2': u'../../txt_files/Even_Haezer/part_2/שולחן ערוך אבן האזל חלק ב באר הגולה.txt'
}


def add_numbers_to_comments(filename, test_mode=True):
    with codecs.open(filename, 'r', 'utf-8') as infile:
        lines = infile.readlines()
    count = 1

    for line_num, line in enumerate(lines):
        if re.match(u'@12', line):
            count = 1
        elif re.match(u'^@11[\u05d0-\u05ea]($| )', line):
            lines[line_num] = u'{}  ({})\n'.format(line[:4], count)
            count += 1
        else: continue

    if test_mode:
        filename = re.sub(u'\.txt', u'_test.txt', filename)
    with codecs.open(filename, 'w', 'utf-8') as outfile:
        outfile.writelines(lines)


class SimanLocater(object):

    def __init__(self, volume):
        with codecs.open(filenames['part_{}'.format(volume)], 'r', 'utf-8') as infile:
            self.source_lines = infile.readlines()

        self.base_simanim = [{
            'num': s.num,
            'total_refs': len(s.locate_references(u'@44([\u05d0-\u05ea])'))
        } for s in Root('../../Even_HaEzer.xml').get_base_text().get_volume(volume).get_child()]
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

    def locate_merge(self, max_diff=2):
        for siman_index, com_siman in enumerate(self.commentary_simanim):
            if not self.almost_equals(com_siman['total'], self.base_simanim[siman_index]['total_refs'], max_diff):
                combined = self.base_simanim[siman_index]['total_refs']
                num_merged_simanim = 1

                while combined < com_siman['total'] and not self.almost_equals(com_siman['total'], combined, max_diff):
                    combined += self.base_simanim[siman_index+num_merged_simanim]['total_refs']
                    num_merged_simanim += 1

                if self.almost_equals(com_siman['total'], combined, max_diff):
                    print "Suspected merge at lines {}-{}".format(com_siman['start']+1, com_siman['end']+1)
                    return siman_index, num_merged_simanim

                else:
                    print "Major conflict found at lines {}-{}. Should match siman {} (index {}). {} in base while {} in commentary"\
                        .format(com_siman['start']+1, com_siman['end']+1, self.base_simanim[siman_index]['num'],
                                siman_index,self.base_simanim[siman_index]['total_refs'], com_siman['total'])

                    # time.sleep(0.1)  # helps keep error messages from getting jumbled
                    # raise AssertionError
                    print 'Attempting to split'
                    self.resolve_split(siman_index, max_diff)
                    return self.locate_merge(max_diff)

        if len(self.commentary_simanim) == len(self.base_simanim):
            print "No merges found"
            return None
        raise AssertionError("Could not locate merge")

    def resolve_merge(self, merge_index, num_combined_simanim, max_diff=3):
        """
        1) Get number of Seifim in each siman from base
        2) Find locations where a split can be made
        3) For each split location calculate deviation from base text
        4) Get location with lowest deviation
        5) Check that the split is within a reasonable distance from expected
        6) Make the split
        :param merge_index:
        :param num_combined_simanim:
        :param max_diff:
        :return:
        """
        merged_siman = self.commentary_simanim[merge_index]
        this_siman_refs = self.base_simanim[merge_index]['total_refs']
        following_siman_refs = sum([self.base_simanim[merge_index+i]['total_refs'] for i in range(1,num_combined_simanim)])
        # expected_refs = (self.base_simanim[merge_index]['total_refs'], self.base_simanim[merge_index+1]['total_refs'])
        expected_refs = (this_siman_refs, following_siman_refs)
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
        if not best_location['diff'] < max_diff:
            time.sleep(0.1)
            raise AssertionError()

        self.commentary_simanim.insert(merge_index, {
            'start': merged_siman['start'],
            'end': merged_siman['start'] + best_location['line_num'] - 1,
            'total': best_location['count']
        })
        merged_siman['start'] = merged_siman['start'] + best_location['line_num']
        merged_siman['total'] = merged_siman['total'] - best_location['count']

    def resolve_split(self, split_index, max_diff=3):
        """
        Re-combine two simanim that got split due to a poor transition. This could happen if the letters reset in the
        middle of a siman
        :param split_index:
        :param max_diff:
        :return:
        """
        # load number of refs in base
        expected_refs = self.base_simanim[split_index]['total_refs']

        # check that combining this and next commentary simanim match that number
        commentary_refs = (self.commentary_simanim[split_index], self.commentary_simanim[split_index+1])
        combined_refs = sum([c['total'] for c in commentary_refs])
        assert abs(expected_refs - combined_refs) <= max_diff

        # amend current index in commentary_simanim and remove the next index
        self.commentary_simanim[split_index]['total'] = combined_refs
        self.commentary_simanim[split_index]['end'] = self.commentary_simanim[split_index+1]['end']
        self.commentary_simanim.pop(split_index+1)


    def output(self, filename=u'temp_result.txt'):
        full_text = []
        for com_siman, base_siman in zip(self.commentary_simanim, self.base_simanim):
            if not self.almost_equals(com_siman['total'], base_siman['total_refs']):
                print "Divergence in siman {}. {} in base and {} in commentary".format\
                    (base_siman['num'], base_siman['total_refs'], com_siman['total'])

            full_text.append(u'@12{}\n'.format(numToHeb(base_siman['num'])))
            full_text.extend(self.source_lines[com_siman['start']:com_siman['end']+1])
        with codecs.open(filename, 'w', 'utf-8') as outfile:
            outfile.writelines(full_text)
"""
We need to generalize `locate_merge` and `resolve_merge` to accept multiple merged simanim. The general case can be
viewed as breaking up two simanim, where we just break the first siman off (this way we avoid having to find two breaks
at once).

We will keep adding simanim to the merge as long as the number of refs in a commentary siman remains higher than that in the
base text. We will need to ensure that the number of comments in the merged commentary siman matches the sum of comments
in all base simanim.

locate_merge should return the number of simanim included in the merge, and resolve should now accept a parameter to
set the number of simanim included in the merge.

Ideally, repeatedly running merge and resolve should solve this problem, the methods shouldn't need to worry about breaking
up all subsequent merges. Or I could tell resolve to re-run itself on the next index if the number of combined simanim is
higher than 2.  
"""

si = SimanLocater(1)
my_merge = si.locate_merge(3)
while my_merge is not None:
    si.resolve_merge(*my_merge, max_diff=3)
    my_merge = si.locate_merge(3)

si.output()

# for i in [1,2]:
#     add_numbers_to_comments(filenames['part_{}'.format(i)])

