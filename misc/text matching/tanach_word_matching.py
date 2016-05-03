from sefaria.model import *
import sefaria.system.database as database
import codecs
import math

'''
The idea is to find repeating words or phrases in tanach.
'''


def count_repeating(query, results):
    """
    Algorithm outline:

    Create a dictionary.

    If word / phrase is in dictionary, increment.

    Otherwise, add word / phrase to dictionary.

    :param query: A string we want to check how many times it repeats in a large text
    :param results: A dictionary that contains the all phrases and how many times they repeat.
    :return: An updated results dictionary
    """

    if query in results.keys():
        results[query] += 1.0

    else:
        results[query] = 1.0

    return results


def get_all_text():

    """
    :return: All text in tanach as a single string
    """
    books = library.get_indexes_in_category('Tanach')
    text_holder = []

    for book in books:
        text_holder.append(TextChunk(Ref(book), vtitle=u'Tanach with Text Only', lang='he').as_string())

    full_text = ' '.join(text_holder)

    # remove bothersome characters
    full_text = full_text.replace(u'\u05be', u' ')
    full_text = full_text.replace(u'[', '')
    full_text = full_text.replace(u']', '')
    full_text = full_text.replace(u'<br><small>', ' ')
    return full_text


def loop_through_text(phrase_length):
    """
    Loops through a large text getting phrases of defined length and counts how many time each phrase appears
    :param phrase_length: length of phrase
    :return: a list of tuples of phrases and appearances sorted by appearances
    """

    # get text
    tanach = get_all_text()
    tanach = tanach.split()

    results = {}

    for index in xrange(len(tanach)):
        query = ' '.join(tanach[index:index+phrase_length])

        if query in results:
            results[query] += 1

        else:
            results[query] = 1

    return results


def get_most():
    data = codecs.open('data.txt', 'w', 'utf-8')
    for length in range(1, 11):
        matches = loop_through_text(length)
        for result in sorted(matches.items(), key=lambda x:x[1], reverse=True)[0:10]:
            data.write(u"%s: %s\n" % result)
        data.write(u'\n')
    data.close()


y = sorted(loop_through_text(1).values(), reverse=True)
x = range(1, len(y)+1)

total = 0.0
for number in y:
    total += number

for index in xrange(len(y)):
    y[index] = math.log(y[index], 10)
    x[index] = math.log(x[index], 10)

output = open('zilpf.csv', 'w')
zilpf = zip(x, y)
for pair in zilpf:
    output.write('%s,%s\n' % pair)

output.close()
