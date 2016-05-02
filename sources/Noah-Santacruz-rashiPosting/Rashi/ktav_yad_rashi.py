# coding=utf-8

"""
In Menahot 72b - 94a there is a commentary known as ktav yad rashi which is different than Rashi. These two were
combined into 1 source in our text files. First I will split these into separate files, then I will re-upload Rashi on
these pages.
"""

import os
import sys
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print p
sys.path.insert(0, p)
from local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
import functions
from sefaria.model import *
from sefaria import tracker as tracker
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


def get_deepest_ref(ref):
    """
    :return: deepest level ref possible
    """

    if ref.is_segment_level():
        return ref
    else:
        return get_deepest_ref(ref.subref(1))


def find_TextChunk_in_file(ref, text_file):
    """
    Try to find where Ref originated from by looking for it in a file

    :param ref: Ref to examine
    :param text_file: file in which to search
    :return: True if found, False otherwise
    """

    # file may be used repeatedly, start from beginning
    text_file.seek(0)

    # get text from ref
    text = ref.text(lang='he').as_string()

    # make sure there actually is text
    if text == u'':
        print "{}: No text found".format(ref.uid())
        return False

    # loop through file
    for line in text_file:
        if line.replace(u'\n', u'') == text:
            return True

    return False


def separate_ktav_yad_rashi():
    """

    :return: An dict named 'results' which contains lists of refs as described below.
    """

    # set up a range of refs
    ref_range = Ref("Rashi on Menachot.72b-94a")

    ref = get_deepest_ref(Ref("Rashi on Menachot.72b"))

    results = {
        'rashi': [],
        'ktav yad rashi': [],
        'found in both': [],
        'found in none': [],
    }

    while ref_range.contains(ref):
        # open the files
        file_name = u'מנחות_{}.txt'.format(functions.get_daf(ref.sections[0]-2))
        rashi = codecs.open(u'rashi_fixed/{}'.format(file_name), 'r', 'utf-8')
        ktav_yad_rashi = codecs.open(u'ktav_yad_rashi/{}'.format(file_name), 'r', 'utf-8')

        # look for ref in files
        in_rashi = find_TextChunk_in_file(ref, rashi)
        in_ktav_yad = find_TextChunk_in_file(ref, ktav_yad_rashi)

        if in_rashi and in_ktav_yad:
            results['found in both'].append(ref)

        elif not in_rashi and not in_ktav_yad:
            results['found in none'].append(ref)

        elif in_rashi and not in_ktav_yad:
            results['rashi'].append(ref)

        elif not in_rashi and in_ktav_yad:
            results['ktav yad rashi'].append(ref)

        # get next ref
        ref = ref.next_segment_ref()

        rashi.close()
        ktav_yad_rashi.close()

    return results


def structure_refs(ref_list):
    """
    I need to verify that no regular rashis appear after a ktav yad rashi. To help do this, this function will
    structure a ref list so that the daf and line number appear as keys in a dictionary.
    :param ref_list: a list of refs
    :return: A dictionary where the keys are lines (section ref) and the values are an ordered list
    """

    structured = {}

    # add keys to structured
    for ref in ref_list:
        key = ref.section_ref().normal()
        if not structured.has_key(key):
            structured[key] = []

        # add ref number to list
        structured[key].append(ref.sections[-1])

    # sort all arrays
    for key in structured.keys():
        structured[key].sort()

    return structured


def check_trailing(ref_struct):
    """
    Check to ensure no rashi refs follow a ktav rashi ref
    :param ref_struct: object returned from separate_ktav_yad_rashi()
    :return: locations where rashi trails a ktav yad rashi
    """
    rashi = structure_refs(ref_struct['rashi'])
    ktav = structure_refs(ref_struct['ktav yad rashi'])

    bad = []

    for ref in ktav.keys():
        if not rashi.has_key(ref):
            continue
        else:
            if rashi[ref][-1] >= ktav[ref][0]:
                bad.append(ref)
    print 'number of issues: {}'.format(len(bad))
    return bad


def fix_rashi():

    # create version record for ktav yad
    verison = {
        'chapter': [],
        'versionTitle': 'Wikisource Ktav Yad Rashi',
        'versionSource': 'Wikisource',
        'language': 'he',
        'title': 'Ktav Yad Rashi on Menachot'
    }
    Version(verison).save()

    data = separate_ktav_yad_rashi()
    rashi = structure_refs(data['rashi'])
    ktav_yad = structure_refs(data['ktav yad rashi'])

    all_refs = Ref('Rashi on Menachot 72b-94a')
    ref = Ref('Rashi on Menachot 72b').first_available_section_ref()

    while all_refs.contains(ref):

        # keep track of status
        print ref.uid()

        all_text = TextChunk(ref, 'he', u'Wikisource Rashi')

        # if there is no ktav yad on ref - do nothing
        if not (ref.uid() in ktav_yad.keys()):
            ref = ref.next_section_ref()
            continue

        # add ktav texts to an array
        ktav_text = []
        for chunk in ktav_yad[ref.uid()]:
            ktav_text.append(all_text.text[chunk-1])

        # add rashi texts to an array
        rashi_text = []
        if ref.uid() in rashi.keys():
            for chunk in rashi[ref.uid()]:
                rashi_text.append(all_text.text[chunk-1])

        # create a ref for the ktav yad
        ktav_ref = Ref(ref.uid().replace('Rashi', 'Ktav Yad Rashi'))
        tracker.modify_text(USERID, ktav_ref, u'Wikisource Ktav Yad Rashi', 'he', ktav_text)

        # Save rashi text
        tracker.modify_text(USERID, ref, u'Wikisource Rashi', 'he', rashi_text)

        ref = ref.next_section_ref()

    vs = VersionState("Rashi on Menachot")
    vs.refresh()
    vs = VersionState("Ktav Yad Rashi on Menachot")
    vs.refresh()

fix_rashi()
