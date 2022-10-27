import pytest
from dh_matcher import *


@pytest.fixture(autouse=True)
def i():
    return 4


@pytest.fixture()
def footnote(i):
    comment_body = "ABCDE"
    return f"<sup class=\"footnote-marker\">{i + 1}</sup><i class=\"footnote\">{comment_body}</i>"


def test_create_footnote(i, footnote):
    assert footnote == create_footnote(i, "ABCDE")


@pytest.fixture()
def tuples():
    return [(52, 62), (63, 71), (0, 6), (27, 36), (23, 34), (52, 62)]


@pytest.fixture()
def insertion_index(i, tuples):
    num_insertions = 20
    end_idx_for_comment = tuples[i][-1]
    insertion_idx = (end_idx_for_comment + 1) + num_insertions
    return insertion_idx


def test_get_insertion_index(i, insertion_index):
    assert insertion_index == get_insertion_index(tuples=[(52, 62), (63, 71), (0, 6), (27, 36), (23, 34), (52, 62)],
                                                  i=i,
                                                  num_insertions=20)


@pytest.fixture()
def base_words():
    return ['Hello', 'there', 'my', 'name', 'is', 'Sefaria.<br>I', 'like', '<b>Jewish</b>', 'texts.']


@pytest.fixture()
def html_words_dict():
    return {5: 'Sefaria.<br>I', 7: '<b>Jewish</b>'}


def test_clean_html_base_words(base_words, html_words_dict):
    # Assert dict is being built
    assert html_words_dict == clean_html_base_words(base_words)
    # Assert base_words is being properly cleaned by the function
    assert base_words == ['Hello', 'there', 'my', 'name', 'is', 'Sefaria.I', 'like', 'Jewish', 'texts.']


def test_get_base_words_with_html(html_words_dict, base_words):
    assert base_words == get_base_words_with_html(html_words_dict, base_words)


@pytest.fixture()
def dh_serials():
    return []


@pytest.fixture()
def num_insertions():
    return 4


# Todo - Fix the num insertions issue here
def test_update_indices_upon_successful_match(dh_serials, num_insertions, i):
    incremented_num_insertions = update_indices_upon_successful_match(dh_serials, num_insertions, i)
    assert (i + 1) in dh_serials
    assert incremented_num_insertions == num_insertions + 1


@pytest.fixture()
def unclean_text():
    return "-- can you clean this text?<br>"


def test_comment_clean(unclean_text):
    assert "can you clean this text?" == comment_clean(unclean_text)


@pytest.fixture()
def text():
    return "This is the dibbur hamatchil - and this is the main text<br>"


def test_extract_dibbur_hamatchil(text):
    assert "This is the dibbur hamatchil" == extract_dibbur_hamatchil(text)


def test_extract_comment_body(text):
    assert "and this is the main text" == extract_comment_body(text)


@pytest.fixture()
def manual_list():
    return []


@pytest.fixture()
def mt_dict():
    return {'Blessings 1.1': 'The first halacha on blessings',
            'Blessings 1.2': 'The second halacha on blessings',
            'Fringes 3.12': 'Another sample halacha, but this one on Tzitzit'}


@pytest.fixture()
def ref():
    return "Blessings 1.2"


@pytest.fixture()
def sample_dh():
    return "Sample DH"


@pytest.fixture()
def sample_comment():
    return "Sample comment"


@pytest.fixture()
def manual_expected_result(ref, mt_dict, sample_dh, sample_comment, i):
    return [{
        'ref': ref,
        'text': mt_dict[ref],
        'dh_serial': i + 1,
        'unplaced_dh': sample_dh,
        'unplaced_comment': sample_comment
    }]


def test_append_to_manual_list(manual_list, ref, mt_dict, i, sample_dh, sample_comment, manual_expected_result):
    assert manual_expected_result == append_to_manual_list(manual_list, ref, mt_dict, i, sample_dh, sample_comment)


@pytest.fixture()
def successful_insertion_list():
    return []


@pytest.fixture()
def success_expected_result(base_words, ref, dh_serials):
    return [{'ref': ref,
             'text_with_comments': " ".join(base_words),
             'dh_inserted_serials': dh_serials}]


# Todo - failing because can't compare a function to an array, but makes no sense since the manual case is working
def test_append_successes_to_list(base_words, successful_insertion_list, ref, dh_serials, i, footnote):
    assert success_expected_result == append_successes_to_list(base_words, successful_insertion_list, ref, dh_serials)


@pytest.fixture()
def expected_base_words_footnote():
    return ['Hello', 'there', 'my', 'name', 'is', 'Sefaria.<br>I', 'like', '<b>Jewish</b>', 'texts.',
            '<sup class="footnote-marker">5</sup><i class="footnote">Sample comment</i>']


def test_insert_footnote_into_base_words(i, sample_comment, dh_serials, num_insertions, base_words, tuples,
                                         expected_base_words_footnote):
    assert expected_base_words_footnote == insert_footnote_into_base_words(i, sample_comment, dh_serials,
                                                                           num_insertions, base_words, tuples)

# Skipping
# attempt_to_match(base_words, comment_list):
# setup_mt_dict()
# generate_report_and_csvs()
# todo - write a function for the main run?
