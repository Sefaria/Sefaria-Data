# -*- coding: utf-8 -*-
"""
This module gives a series of tools designed for analyzing texts received from OCR.
"""
import re
import pdb
import util



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


def count_by_regex_jarray(jagged_array, regex, result={}):
    """
    Similar to count_by_regex, runs the same test on a jagged_array that may still need cleaning
    :param jagged_array: Multilevel array, lowest level must be text (str or unicode).
    :param regex: Regular expression to match
    :param result: Dictionary to hold captured strings.
    :return: Dictionary where keys are strings that matched the regex and keys are the number of times
    they appeared.
    """

    for item in jagged_array:
        if type(item) is list:
            result = count_by_regex_jarray(item, regex, result)

        elif type(item) is str or type(item) is unicode:
            captures = regex.finditer(item)
            for capture in captures:
                text = capture.group()
                if text not in result.keys():
                    result[text] = 1
                else:
                    result[text] += 1

        else:
            print 'Jagged array contains unknown type'
            raise TypeError

    return result


class TagTester:
    """
    This represents a tag such as those that appear in texts sent by srikot. This class can hold all relevant
    data necessary to analyze tags - i.e. an associated regular expression and file.
    """

    def __init__(self, tag, tag_file, reg=None, name=u'', fail_func=pdb.set_trace):

        # this is the exact string of the tag
        self.tag = tag

        # this is a file object associated with the tag
        self.file = tag_file
        self.file.seek(0)

        # number of time tag appears in associated file
        self.appearances = self.count_all_tags()

        # a string defining a regular expression associated with the tag
        self.reg = reg

        # name of the text tag is associated with. If possible, make this a string that can be recognized by a
        # Ref object
        self.name = name

        # Flag to determine if file has reached the end
        self.eof = False

        # True if tag always starts a new line.
        self.starts_line = self.does_start_line()

        if not self.reg:
            self.reg = self.tag
        else:
            self.reg = reg

        # a dictionary where the keys are the strings that match self.reg and values are the number of
        # times they each appear.
        self.types = count_by_regex(self.file, self.reg)

        self.fail_func = fail_func

        self.file.seek(0)



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

    def does_start_line(self):
        """
        True if tag always appears at the beginning of a line.
        :return: True or False
        """
        self.file.seek(0)
        for line in self.file:
            if line.find(self.tag) != -1 and line.find(self.tag) != 0:
                self.file.seek(0)
                return False
        else:
            self.file.seek(0)
            return True

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


    def in_order_one_section(self, capture_group=0, callback_tester=None):  
        array_headers = self.grab_each_header(None, capture_group)
        prev_val = -1
        ones_that_passed = []
        for header in array_headers:
            curr_val = util.getGematria(header) if len(header) <= 2 else util.wordToNumber[header]
            if callback_tester is None and prev_val >= curr_val:
                return ("FAILURE", ones_that_passed)
            elif callback_tester is not None and callback_tester(prev_val=prev_val, curr_val=curr_val) == False:
                pdb.set_trace()
                return ("FAILURE", ones_that_passed)
            ones_that_passed.append(curr_val)
            prev_val = curr_val
        return ("SUCCESS", array_headers)


    def in_order_one_section_return_all(self, capture_group=0, callback_tester=None):  
        #Difference between this function and in_order_one_section() is that in_order_one_section()
        #on its first failure, ends the test and returns what has passed the test SO FAR.
        #This function iterates through everything, separating things into failed array and success array
        #and returns both

        array_headers = self.grab_each_header(None, capture_group)
        prev_val = -1
        ones_that_passed = []
        ones_that_failed = []
        for header in array_headers:
            curr_val = util.getGematria(header)
            if callback_tester is None and prev_val >= curr_val:  #default test
                ones_that_failed.append(header)
            elif callback_tester is not None and callback_tester(prev_val=prev_val, curr_val=curr_val) == False:
                ones_that_failed.append(header)
            else:
                ones_that_passed.append(header)
            prev_val = curr_val
        return (ones_that_passed, ones_that_failed)
    

    def in_order_many_sections(self, end_tag, capture_group=0):
        if end_tag == None:
            print 'End tag must have value to distinguish between each section.'
            self.fail_func()
        headers_2d_array = []
        ones_that_passed = []
        while self.eof == False:
            headers_2d_array.append(self.grab_each_header(end_tag, capture_group))
        if headers_2d_array[0] == []:
            headers_2d_array.pop(0)
        for headers_1d_array in headers_2d_array:
            prev_val = -1
            for header in headers_1d_array:
                curr_val = util.getGematria(header)
                if prev_val >= curr_val:
                    return ("FAILURE", ones_that_passed)
                else:
                    ones_that_passed.append(curr_val)
                prev_val = curr_val
        return ("SUCCESS", headers_2d_array)

    def grab_each_header(self, end_tag=None, capture_group=0):
        """
        Grab all matches of the regular expression and add to an array. This will analyze the file until it hits
        a match for the end tag or the end of the file. 
        Each time you call this function, as long as the end of the file hasn't been reached, 
        If there is no end_tag and it simply hits the end of the file, it will return a 1-D array.
        :param segment_tag:  String that indicates end of segment. If not set, function will run to the
        end of the file
        :param capture_group: Capture group to be returned.
        :return: An array of strings which match the regular expression.

        """
        captures = []
        for line in self.file:
            if not isinstance(self.reg, unicode):
                self.reg = self.reg.decode('utf-8')

            if not isinstance(line, unicode):
                line = line.decode('utf-8')

            # check for the end of the segment
            if end_tag:
                if re.search(end_tag, line):
                    return captures

            matches = re.finditer(self.reg, line)
            for match in matches:
                captures.append(match.group(capture_group))
        else:
            self.eof = True
            return captures


    def daf_processor(self):
        headers = self.grab_each_header()
        daf_values = []
        prev_val = 0
        curr_val = 0
        for count, header in enumerate(headers):
            if header.find(u'וע"ב') >= 0:
                pdb.set_trace()
            header = header.replace(u"דף",u"").replace(u'ע"א', u'').replace(self.tag, u"").replace(u"\n", u"").replace("]","").replace("[","")
            if header.find(u'ע"ב') >= 0:
                header = header.replace(u'וע"ב', u'').replace(u'ע"ב', u'').replace(u" ", u"")
                if len(header) > 0:
                    curr_val = util.getGematria(header)
                    daf_values.append(curr_val * 2)
                else:
                    daf_values.append(curr_val * 2)
            else:
                curr_val = util.getGematria(header)
                daf_values.append(curr_val * 2 - 1)
        return daf_values, headers



    def skip_to_next_segment(self, segment_tag):
        """
        Sets self.file to one line after segment_tag is found
        :param segment_tag: string or regular expression used to find segment
        """

        for line in self.file:
            if re.search(segment_tag, line):
                return
        else:
            print 'Reached end of file without finding segment tag'
            self.file.close()
            raise EOFError


def find_double_tags(tag_a, tag_b, infile):
    """
    Find locations where a file has a line that matches two regular expressions
    :param tag_a: First regex to match
    :param tag_b: Second regex to match
    :param infile: File to examine
    :return: A list of numbers which indicate line numbers at which a double tag was found
    """

    reg_a = re.compile(tag_a)
    reg_b = re.compile(tag_b)

    results = []

    for line_num, line in enumerate(infile):

        if reg_a.search(line) and reg_b.search(line):
            results.append(line_num+1)

    return results