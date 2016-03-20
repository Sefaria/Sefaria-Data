# coding=utf-8
# from sefaria.model import *
import regex as re
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


kol_bo = codecs.open('kol_bo.txt', 'r', encoding='utf-8')
out = codecs.open('output.txt', 'w', encoding='utf-8')
reg = re.compile(ur'@02.*[.]')
for line in kol_bo:
    result = re.search(reg, line)
    if result:
        out.write(result.group()[3:] + '\n')

kol_bo.close()
out.close()