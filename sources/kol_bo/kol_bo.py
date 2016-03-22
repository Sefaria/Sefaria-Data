# coding=utf-8
from sefaria.helper.text import replace_using_regex as repreg
import codecs


def count_instances(queries, input_file):
    """
    Counts the number of times a certain two intances appear in the
    :param queries: All strings to be counted
    :param input_file: The file to be examined
    :return: A list of tuples containing (query, count)
    """

    # if query is not a list, place in a list
    if type(queries) != list:
        queries = [queries]

    # initialize counts to 0
    counts = [0] * len(queries)

    # loop through file
    for line in input_file:

        # loop through queries
        for index, query in enumerate(queries):
            counts[index] += line.count(query)

    # reset file
    input_file.seek(0)

    return zip(queries, counts)


def tag_chapters():
    """
    This function will create a new copy of the kol bo, this time with the chapters
    clearly marked.
    """

    # open kol_bo
    kol_bo = codecs.open('kol_bo.txt', 'r', encoding='utf-8')
    kol_bo_chapters = codecs.open('kol_bo_chapters.txt', 'w', encoding='utf-8')
    for line in kol_bo:
        # parse out tags. As the repreg function only replaces when a regex is found,
        # only one of the following two lines will actually edit the text.
        line = repreg('@01@02.*[.]', line, u'@01@02', u'<chapter>')
        line = repreg('@02.*[.]', line, u'@02', u'<chapter>')
        kol_bo_chapters.write(line)

    kol_bo.close()
    kol_bo_chapters.close()

