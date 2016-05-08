# -*- coding: utf-8 -*-
"""
This module gives a series of tools designed for analyzing texts received from OCR.
"""
import re


def count_by_regex(some_file, regex):
    """
    After OCR, text files are returned with many tags, the meaning of which may not be clear or ambiguous.
    Even if the meaning of each tag is known it can be useful to know how many times each tag appears, as
    errors may have arisen during the scanning and OCR. By using a regular expression to search, entire
    documents can be scanned quickly and efficiently.

    :param some_file: A file to be scanned.
    :param regex: The regex to be used
    :return: A dictionary where the keys are all the strings that match the regex and the values are the
    number of times each one appears.
    """

    # instantiate a dictionary to hold results
    result = {}

    # compile regex
    reg = re.compile(regex)

    # loop through file
    for line in some_file:

        # search for regex
        found = re.findall(reg, line)

        # count instances found
        for item in found:
            if item not in result:
                result[item] = 1
            else:
                result[item] += 1

    # reset file for reuse
    some_file.seek(0)
    return result


class Tag:
    """
    This represents a tag such as those that appear in texts sent by srikot. This class can hold all relevant
    data necessary to analyze tags - i.e. an associated regular expression and file.
    """

    def __init__(self, tag, tag_file, reg=None, name=u''):

        # this is the exact string of the tag
        self.tag = tag

        # this is a file associated with the tag
        self.file = tag_file

        # number of time tag appears in associated file
        self.appearances = self.count_all_tags()

        # a regular expression associated with the tag
        self.reg = reg

        # name of the text tag is associated with. If possible, make this a string that can be recognized by a
        # Ref object
        self.name = name

        if self.reg:

            # a dictionary where the keys are the strings that match self.reg and values are the number of
            # times they each appear.
            self.types = count_by_regex(self.file, self.reg)

    def count_all_tags(self):
        """
        :return: Number of times tag can be found in file
        """
        count = 0

        # go to beginning of file
        self.file.seek(0)

        for line in self.file:
            count += line.count(self.tag)

        self.file.seek(0)

        return count

    def count_tags_by_segment(self, segment_tag):
        """
        Counts the number of times a tag appears in each segment of a text. Assumes segment_tag is on it's own line.
        :param segment_tag: A tag indicating the beginning of a new segment. Can be a regular expression
        :return: An array where the nth value is the number of times the tag appears in the nth segment.
        """
        self.file.seek(0)

        found_first_segment = False
        count, all_counts = 0, []

        for line in self.file:

            if re.search(segment_tag, line):
                if found_first_segment:
                    all_counts.append(count)
                else:
                    found_first_segment = True
                count = 0
            else:
                count += line.count(self.tag)

        # add last segment
        all_counts.append(count)
        self.file.seek(0)
        return all_counts

    def grab_by_section(self, segment_tag=None, capture_group=0):
        """
        Grab all matches of the regular expression and add to an array. This will analyze the file until it hits
        a match for the segment tag. Running this function in a loop till the end of a file will return a 2-D
        array, with each sub-array containing the captures within the matching segment.
        :param segment_tag:  String that indicates end of segment. If not set, function will run to the
        end of the file
        :param capture_group: Capture group to be returned.
        :return: An array of strings which match the regular expression.
        """

        captures = []
        for line in self.file:

            # check for the end of the segment
            if segment_tag:
                if re.search(segment_tag, line):
                    return captures

            matches = re.finditer(self.reg, line)
            for match in matches:
                captures.append(match.group(capture_group))
