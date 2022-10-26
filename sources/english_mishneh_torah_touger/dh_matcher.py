import django

django.setup()

import csv
import re
from data_utilities.dibur_hamatchil_matcher import match_text
from commentary_data import commentary_dict

from sefaria.model import *
from mt_utilities import sefaria_book_names, chabad_book_names, create_book_name_map, export_data_to_csv, ALLOWED_ATTRS, \
    ALLOWED_TAGS

name_map = create_book_name_map(chabad_book_names, sefaria_book_names)


def extract_dibbur_hamatchil(txt):
    dhm = re.findall(r"^(.*?) -", txt, re.DOTALL)
    if len(dhm) < 1:
        return ""
    return dhm[0]


def comment_clean(text):
    comment_body = text.strip("-")
    if comment_body[-4:] == "<br>":
        comment_body = comment_body[:-4]
    comment_body = comment_body.strip()
    return comment_body


def extract_comment_body(txt):
    cb = re.findall(r"^.*? [-—](.*)$", txt, re.DOTALL)
    if len(cb) < 1:
        return comment_clean(txt)
    return comment_clean(cb[0])


def append_successes_to_list(base_words, successful_insertion_list, ref, dh_serials):
    text_with_comments = " ".join(base_words)
    successful_insertion_list.append(
        {
            'ref': ref,
            'text_with_comments': text_with_comments,
            'dh_inserted_serials': dh_serials
        }
    )


def join_manual_with_footnote_text(successful_insertion_list, manual_list):
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


def generate_report(manual_list, successful_insertion_list, placed_html_manual_list):
    print(f"{len(manual_list)} on manual list, can't find dhm")
    print(f"Comments successfully placed in {len(successful_insertion_list)} refs")
    print(f"{len(placed_html_manual_list)} on NEW manual list")


# TODO - add comments & tests to new functions from refactor
def clean_html_base_words(base_words):
    html_words_dict = {}
    for i in range(len(base_words)):
        cur_word = base_words[i]
        is_html_word = re.findall(r"<.*?>", cur_word)
        # Save orig word and index for later
        if is_html_word:
            html_words_dict[i] = cur_word

        # Temp replace base word with something cleaned
        base_words[i] = re.sub(r"<.*?>", "", cur_word)
    return html_words_dict


def create_footnote(i, comment_body):
    return f"<sup class=\"footnote-marker\">{i + 1}</sup><i class=\"footnote\">{comment_body}</i>"


def get_insertion_index(tuples, i, num_insertions):
    end_idx_for_comment = tuples[i][-1]
    insertion_idx = (end_idx_for_comment + 1) + num_insertions
    return insertion_idx


def update_indices_upon_successful_match(dh_serials, num_insertions, i):
    num_insertions += 1
    dh_serials.append(i + 1)


def insert_footnote_into_base_words(i, comment_body, dh_serials, num_insertions, base_words, tuples):
    footnote = create_footnote(i, comment_body)
    insertion_idx = get_insertion_index(tuples, i, num_insertions)
    base_words.insert(insertion_idx, footnote)
    update_indices_upon_successful_match(dh_serials, num_insertions, i)


def get_base_words_with_html(html_words_dict, base_words):
    for index in html_words_dict:
        base_words[index] = html_words_dict[index]
    return base_words


def setup_mt_dict():
    mt_dict = {}
    with open('mishneh_torah_data_cleaned.csv', newline='') as csvfile:
        r = csv.reader(csvfile, delimiter=',')
        br_patt = r"\.<br>"
        for row in r:
            ref = row[0]
            text = row[1]
            if "<br>" in text:
                mt_dict[ref] = re.sub(br_patt, ". <br> ", text)
            else:
                mt_dict[ref] = text
    return mt_dict


def attempt_to_match(base_words, comment_list):
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
    return results['matches']


def append_to_manual_list(manual_list, ref, mt_dict, i, dh, comment_body):
    manual_list.append({
        'ref': ref,
        'text': mt_dict[ref],
        'dh_serial': i + 1,
        'unplaced_dh': dh,
        'unplaced_comment': comment_body
    })


def generate_stats_and_csvs(successful_insertion_list, manual_list):
    # If place markers exist, replace the text in manual
    placed_html_manual_list = join_manual_with_footnote_text(successful_insertion_list, manual_list)
    generate_report(manual_list, successful_insertion_list, placed_html_manual_list)
    export_data_to_csv(placed_html_manual_list, 'qa_reports/manual_commentaries_2',
                       ['ref', 'text', 'dh_serial', 'unplaced_dh', 'unplaced_comment'])
    export_data_to_csv(successful_insertion_list, 'qa_reports/inserted_commentaries_2',
                       ['ref', 'text_with_comments', 'dh_inserted_serials'])


# TODO - hunch, offset happening with the HTML index, split on space and .<
# Todo - Pre-process text by adding a space before each <br>
def run_commentary_insertion():
    successful_insertion_list = []
    manual_list = []

    mt_dict = setup_mt_dict()

    for ref in commentary_dict:

        num_insertions = 0
        dh_serials = []

        # Retrieve the list of comments for this ref
        comment_list = commentary_dict[ref]

        # Divide raw comment text into a list of words, and clean each word for HTML
        base_words = mt_dict[ref].split(" ")
        html_words_dict = clean_html_base_words(base_words)

        # Two attempts with adjusted parameters to use the dibbur_hamatchil_matcher to find
        # the correct dibbur hamatchil, return the tuples of the results
        result_tuples = attempt_to_match(base_words, comment_list)

        # Put the HTML back into the words of the comment
        base_words = get_base_words_with_html(html_words_dict, base_words)

        for i in range(len(result_tuples)):
            dh = extract_dibbur_hamatchil(comment_list[i])
            comment_body = extract_comment_body(comment_list[i])

            if result_tuples[i] == (-1, -1):  # If it's an error
                append_to_manual_list(manual_list, ref, mt_dict, i, dh, comment_body)

            else:  # If it's a match
                insert_footnote_into_base_words(i, comment_body, dh_serials, num_insertions, base_words, result_tuples)

            # Last time through, append successes
            if i == len(result_tuples) - 1:
                append_successes_to_list(base_words, successful_insertion_list, ref, dh_serials)

    generate_stats_and_csvs(successful_insertion_list, manual_list)


if __name__ == '__main__':
    run_commentary_insertion()
