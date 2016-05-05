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
    return result


class Tag:
    """
    This represents a tag such as those that appear in texts sent by srikot. This class can hold all relevant
    data necessary to analyze tags - i.e. an associated regular expression and file.
    """

    def __init__(self, tag, tag_file, reg=''):
        self.tag = tag
        self.file = tag_file
        self.reg = reg
        self.appearances = self.count_all_tags()

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
