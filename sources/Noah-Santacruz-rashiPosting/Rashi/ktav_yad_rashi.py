# coding=utf-8

"""
In Menahot 72b - 94a there is a commentary known as ktav yad rashi which is different than Rashi. These two were
combined into 1 source in our text files. First I will split these into separate files, then I will re-upload Rashi on
these pages.
"""

from sources import functions
import codecs


def check_demarcation(search_key):
    """
    Sanity check function: make sure a certain search key can be used to find the beginning of the ktav yad rashi in
    text. Prints out files missing the search key, as well as number of files searched and number of keys found.
    :param search_key: A string indicating where ktav yad rashi begins.
    """

    total, count = 0, 0

    # loop through files
    for page in range(functions.get_page(72, 'b'), functions.get_page(94, 'a')+1):
        file_name = u'מנחות_{}.txt'.format(functions.get_daf(page))
        rashi_file = codecs.open(file_name, 'r', 'utf-8')
        total += 1

        found_key = False
        for line in rashi_file:
            if line.find(search_key) != -1:
                found_key = True
                count += 1
                break

        if not found_key:
            print file_name

        rashi_file.close()

    print '{} files scanned, found key in {} file'.format(total, count)


def split_files(search_key):
    """
    Loops through files, splitting Rashi and ktav yad rashi into 2 different files.
    Recommend running check_demarcation first.
    :param search_key: key to find end of Rashi and beginning of ktav yad rashi
    """

    # loop through files
    for page in range(functions.get_page(72, 'b'), functions.get_page(94, 'a') + 1):
        file_name = u'מנחות_{}.txt'.format(functions.get_daf(page))
        rashi = codecs.open(u'rashi_fixed/{}'.format(file_name), 'w', 'utf-8')
        ktav_yad_rashi = codecs.open(u'ktav_yad_rashi/{}'.format(file_name), 'w', 'utf-8')
        original = codecs.open(file_name, 'r', 'utf-8')

        found = False

        for line in original:

            if line.find(search_key) != -1:
                found = True

            if not found:
                rashi.write(line)
            if found:
                ktav_yad_rashi.write(line)

        original.close()
        rashi.close()
        ktav_yad_rashi.close()
