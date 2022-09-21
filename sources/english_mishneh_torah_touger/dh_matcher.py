import django

django.setup()

import csv
import re
import bleach
from sefaria.helper.normalization import RegexNormalizer
from data_utilities.dibur_hamatchil_matcher import match_text
from commentary_data import commentary_dict

from sefaria.model import *
from mt_utilities import sefaria_book_names, chabad_book_names, create_book_name_map, export_data_to_csv, ALLOWED_ATTRS, \
    ALLOWED_TAGS

name_map = create_book_name_map(chabad_book_names, sefaria_book_names)


# TODO - Fix regexes... slightly off now that we bleach.cleaned


def extract_dibbur_hamatchil(txt):
    dhm = re.findall(r"^(.*?) -", txt, re.DOTALL)
    if len(dhm) < 1:
        return ""
    return dhm[0]


def extract_comment_body(txt, count):
    cb = re.findall(r"^.*? [-—](.*)$", txt, re.DOTALL)
    if len(cb) < 1:
        count += 1
        return txt
    return cb[0]


def insert_successes(base_words, successful_insertion_list, ref, dh_serials):
    text_with_comments = " ".join(base_words)
    successful_insertion_list.append(
        {
            'ref': ref,
            'text_with_comments': text_with_comments,
            'dh_inserted_serials': dh_serials
        }
    )


def comment_clean(text):
    comment_body = text.strip("-")
    if comment_body[-4:] == "<br>":
        comment_body = comment_body[:-4]
    comment_body = comment_body.strip()
    return comment_body


def join_manual_with_footnote_text():
    success_text_map = {}
    for halakha in successful_insertion_list:
        ref = halakha['ref']
        txt = halakha['text_with_comments']
        success_text_map[ref] = txt

    placed_html_manual_list = []
    for comment in manual_list:
        ref = comment['ref']
        m_text = ""
        if ref in success_text_map:
            m_text = success_text_map[ref]
        else:
            m_text = comment['text']  # keep original

        placed_html_manual_list.append({
            'ref': ref,
            'text': m_text,
            'dh_serial': comment['dh_serial'],
            'unplaced_dh': comment['unplaced_dh'],
            'unplaced_comment': comment['unplaced_comment']
        })
    return placed_html_manual_list


def generate_report(count, manual_list, success_count, successful_insertion_list, placed_html_manual_list):
    print(f"{count} can't extract comment body")
    print(f"{len(manual_list)} on manual list, can't find dhm")
    print(f"{success_count} individual comments successfully placed in {len(successful_insertion_list)} refs")
    print(f"{len(placed_html_manual_list)} on NEW manual list")


successful_insertion_list = []
manual_list = []
mt_dict = {}

count = 0
success_count = 0
with open('mishneh_torah_data_cleaned.csv', newline='') as csvfile:
    r = csv.reader(csvfile, delimiter=',')
    for row in r:
        ref = row[0]
        mt_dict[ref] = row[1]

for ref in commentary_dict:
    html_words_dict = {}
    comment_list = commentary_dict[ref]
    base_words = mt_dict[ref].split(" ")

    for i in range(len(base_words)):
        cur_word = base_words[i]
        is_html_word = re.findall(r"<.*?>", cur_word)
        # Save orig word and index for later
        if is_html_word:
            html_words_dict[i] = cur_word

        # Temp replace base word with something cleaned
        base_words[i] = re.sub(r"<.*?>", "", cur_word)

    results = match_text(base_words,
                         comment_list,
                         dh_extract_method=extract_dibbur_hamatchil,
                         lang='en')

    # One re-try with adjusted param / Normalization?
    if (-1, -1) in results["matches"]:
        results = match_text(base_words,
                             comment_list,
                             dh_extract_method=extract_dibbur_hamatchil,
                             lang='en',
                             daf_skips=3,
                             rashi_skips=2,
                             overall=3)


    # Report outstanding errors
    if (-1, -1) in results['matches']:
        count += 1
        tuples = results['matches']
        num_insertions = 0
        dh_serials = []

        # Replace back original HTML
        for index in html_words_dict:
            base_words[index] = html_words_dict[index]

        for i in range(len(tuples)):
            dh = extract_dibbur_hamatchil(comment_list[i])
            comment_body = extract_comment_body(comment_list[i], count)
            comment_body = comment_clean(comment_body)

            if tuples[i] == (-1, -1):  # error and not last
                manual_list.append({
                    'ref': ref,
                    'text': mt_dict[ref],
                    'dh_serial': i + 1,
                    'unplaced_dh': dh,
                    'unplaced_comment': comment_body
                })
                if i == len(tuples) - 1:  # also is last
                    insert_successes(base_words, successful_insertion_list, ref, dh_serials)

            else:  # Found
                end_idx_for_comment = tuples[i][-1]
                insertion_idx = (end_idx_for_comment + 1) + num_insertions

                footnote = f"<sup class=\"footnote-marker\">{i + 1}</sup><i class=\"footnote\">{comment_body}</i>"
                base_words.insert(insertion_idx, footnote)
                num_insertions += 1
                success_count += 1
                dh_serials.append(i + 1)

                # Last time through, append
                if i == len(tuples) - 1:
                    insert_successes(base_words, successful_insertion_list, ref, dh_serials)

    # On full success cases
    else:
        tuples = results['matches']
        num_insertions = 0
        dh_serials = []

        # Replace back original HTML
        for index in html_words_dict:
            base_words[index] = html_words_dict[index]

        for i in range(len(tuples)):
            dh = extract_dibbur_hamatchil(comment_list[i])
            comment_body = extract_comment_body(comment_list[i], count)
            comment_body = comment_clean(comment_body)

            end_idx_for_comment = tuples[i][-1]
            insertion_idx = (end_idx_for_comment + 1) + num_insertions
            footnote = f"<sup class=\"footnote-marker\">{i + 1}</sup><i class=\"footnote\">{comment_body}</i>"
            base_words.insert(insertion_idx, footnote)
            success_count += 1
            dh_serials.append(i + 1)

            # Last time through, append
            if i == len(tuples) - 1:
                insert_successes(base_words, successful_insertion_list, ref, dh_serials)

# for halakha in successful_insertion_list:
#     if halakha['ref'] == 'Blessings 1.1':
#         print(halakha['text_with_comments'])


# If place markers exist, replace the text in manual
placed_html_manual_list = join_manual_with_footnote_text()

generate_report(count, manual_list, success_count, successful_insertion_list, placed_html_manual_list)

export_data_to_csv(placed_html_manual_list, 'qa_reports/manual_commentaries',
                   ['ref', 'text', 'dh_serial', 'unplaced_dh', 'unplaced_comment'])
export_data_to_csv(successful_insertion_list, 'qa_reports/inserted_commentaries',
                   ['ref', 'text_with_comments', 'dh_inserted_serials'])
