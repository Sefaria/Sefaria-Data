# -*- coding: utf-8 -*-

from sefaria.model import *
import codecs


def word_count_by_ref(ref_name, lang=u'he', version=None):
    """
    Get a dictionary of words and the number of times they appear
    :param ref_name:
    :param lang: language to count from
    :param version: name of the version. If not specified, function will get it on it's own.
    :return:
    """

    counts = {}

    # get version title if not supplied
    if not version:
        version = next(v for v in Ref(ref_name).version_list() if v['language'] == lang)

    # convert ref into a list of words
    text = TextChunk(Ref(ref_name), lang, version['versionTitle']).as_string()
    text = text.split()

    for word in text:
        if word in counts.keys():
            counts[word] += 1
        else:
            counts[word] = 1

    return counts


def most_common_words(counts, n=-1):
    """
    Given a dictionary of word counts, return counts in a sorted list.
    :param counts: Dictionary of words and the number of times they appear
    :param n: Number of results. If -1 (default), will return all words.
    :return: List of tuples, tuples contain word and the number of times it appears
    """

    result = sorted(counts.items(), key=lambda x: x[1], reverse=True)

    if n == -1:
        return result
    else:
        return result[:n]


ref_list = [u'Bava Kamma.83b-94a', u'Berakhot.2a-30b', u'Megillah.2a-17a', u'Megillah.25b-32a',
            u'Shabbat.67b-76b']

for thing in ref_list:
    filename = 'Most common words in {}.txt'.format(thing)

    outfile = codecs.open(filename, 'w', 'utf-8')

    c = most_common_words(word_count_by_ref(thing), 150)

    for result in c:
        outfile.write(u'{}: {}\n'.format(*result))

    outfile.close()
