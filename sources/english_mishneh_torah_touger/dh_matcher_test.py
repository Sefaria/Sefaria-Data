import pytest
from dh_matcher import *


@pytest.fixture(autouse=True)
def sample_i_from_for_loop():
    return 4


@pytest.fixture()
def footnote(sample_i_from_for_loop):
    comment_body = "ABCDE"
    return f"<sup class=\"footnote-marker\">{sample_i_from_for_loop + 1}</sup><i class=\"footnote\">{comment_body}</i>"


@pytest.fixture()
def sample_matcher_tuples():
    return [(52, 62), (63, 71), (0, 6), (27, 36), (23, 34), (52, 62)]


@pytest.fixture()
def insertion_index(sample_i_from_for_loop, sample_matcher_tuples):
    num_insertions = 20
    end_idx_for_comment = sample_matcher_tuples[sample_i_from_for_loop][-1]
    insertion_idx = (end_idx_for_comment + 1) + num_insertions
    return insertion_idx


@pytest.fixture()
def base_words():
    return ['Hello', 'there', 'my', 'name', 'is', 'Sefaria.<br>I', 'like', '<b>Jewish</b>', 'texts.']


@pytest.fixture()
def html_words_dict():
    return {5: 'Sefaria.<br>I', 7: '<b>Jewish</b>'}


@pytest.fixture()
def dh_serials():
    return []


@pytest.fixture()
def num_insertions():
    return 4


@pytest.fixture()
def unclean_text():
    return "-- can you clean this text?<br>"


@pytest.fixture()
def text():
    return "This is the dibbur hamatchil - and this is the main text<br>"


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
def manual_expected_result(ref, mt_dict, sample_dh, sample_comment, sample_i_from_for_loop):
    return [{
        'ref': ref,
        'text': mt_dict[ref],
        'dh_serial': sample_i_from_for_loop + 1,
        'unplaced_dh': sample_dh,
        'unplaced_comment': sample_comment
    }]


@pytest.fixture()
def successful_insertion_list():
    return []


@pytest.fixture()
def success_expected_result(base_words, ref, dh_serials):
    return [{'ref': ref,
             'text_with_comments': " ".join(base_words),
             'dh_inserted_serials': dh_serials}]


@pytest.fixture()
def expected_base_words_footnote():
    return ['Hello', 'there', 'my', 'name', 'is', 'Sefaria.<br>I', 'like', '<b>Jewish</b>', 'texts.',
            '<sup class="footnote-marker">5</sup><i class="footnote">Sample comment</i>']


def test_insert_footnote_into_base_words(sample_i_from_for_loop, sample_comment, dh_serials, num_insertions, base_words,
                                         sample_matcher_tuples,
                                         expected_base_words_footnote):
    assert expected_base_words_footnote == insert_footnote_into_base_words(sample_i_from_for_loop, sample_comment,
                                                                           dh_serials,
                                                                           num_insertions, base_words,
                                                                           sample_matcher_tuples)


def test_create_footnote(sample_i_from_for_loop, footnote):
    assert footnote == create_footnote(sample_i_from_for_loop, "ABCDE")


def test_get_insertion_index(sample_i_from_for_loop, insertion_index):
    assert insertion_index == get_insertion_index(tuples=[(52, 62), (63, 71), (0, 6), (27, 36), (23, 34), (52, 62)],
                                                  i=sample_i_from_for_loop,
                                                  num_insertions=20)


def test_clean_html_base_words(base_words, html_words_dict):
    # Assert dict is being built
    assert html_words_dict == clean_html_base_words(base_words)
    # Assert base_words is being properly cleaned by the function
    assert base_words == ['Hello', 'there', 'my', 'name', 'is', 'Sefaria.I', 'like', 'Jewish', 'texts.']


def test_get_base_words_with_html(html_words_dict, base_words):
    assert base_words == get_base_words_with_html(html_words_dict, base_words)


# Todo - Fix the num insertions issue here
def test_update_indices_upon_successful_match(dh_serials, num_insertions, sample_i_from_for_loop):
    incremented_num_insertions = update_indices_upon_successful_match(dh_serials, num_insertions,
                                                                      sample_i_from_for_loop)
    assert (sample_i_from_for_loop + 1) in dh_serials
    assert incremented_num_insertions == num_insertions + 1


def test_comment_clean(unclean_text):
    assert "can you clean this text?" == comment_clean(unclean_text)


def test_extract_dibbur_hamatchil(text):
    assert "This is the dibbur hamatchil" == extract_dibbur_hamatchil(text)


def test_extract_comment_body(text):
    assert "and this is the main text" == extract_comment_body(text)


# Todo - failing because can't compare a function to an array, but makes no sense since the manual case is working
def test_append_successes_to_list(base_words, successful_insertion_list, ref, dh_serials, sample_i_from_for_loop,
                                  footnote):
    assert success_expected_result == append_successes_to_list(base_words, successful_insertion_list, ref, dh_serials)


def test_append_to_manual_list(manual_list, ref, mt_dict, sample_i_from_for_loop, sample_dh, sample_comment,
                               manual_expected_result):
    assert manual_expected_result == append_to_manual_list(manual_list, ref, mt_dict, sample_i_from_for_loop, sample_dh,
                                                           sample_comment)

# Todo
# Write an individual test for Berachot 1.3, copy all the data just for that case.
# Test the main run on just the berachot data, copy it into here

@pytest.fixture()
def commentary_dict_test():
    return {"Blessings 1.3": ["Just as we recite blessings for benefit which we derive from the world - as explained above,<br>", "we should also recite blessings for each mitzvah before we fulfill it. - The laws governing the blessings recited over the performance of mitzvot are discussed in Chapter 11.<br>", "Similarly, the Sages instituted many blessings as expressions of praise and thanks to God and as a means of petition - See Chapter 10.<br>", "so that we will always remember the Creator, even though we have not received any benefit or performed a mitzvah. - By reciting blessings over the special events which occur to us, we become conscious of God's control of all aspects of our daily existence. We learn to appreciate Him, not only as the Creator who brought the world into being, but as the One who directs the functioning of our lives and the world around us.<br>"]}

@pytest.fixture()
def mt_dict():
    return {'Blessings 1.3': 'Just as we recite blessings for benefit which we derive from the world, we should also recite blessings for each mitzvah before we fulfill it. <br> Similarly, the Sages instituted many blessings as expressions of praise and thanks to God and as a means of petition, so that we will always remember the Creator, even though we have not received any benefit or performed a mitzvah.'}


@pytest.fixture()
def expected_results_blessings_1_3():
    return [{'ref': 'Blessings 1.3',
             'text_with_comments': 'Just as we recite blessings for benefit which we derive from the world, <sup class="footnote-marker">1</sup><i class="footnote">as explained above,</i> we should also recite blessings for each mitzvah before we fulfill it. <sup class="footnote-marker">2</sup><i class="footnote">The laws governing the blessings recited over the performance of mitzvot are discussed in Chapter 11.</i> <br> Similarly, the Sages instituted many blessings as expressions of praise and thanks to God and as a means of petition<sup class="footnote-marker">3</sup><i class="footnote">See Chapter 10.</i>, so that we will always remember the Creator, even though we have not received any benefit or performed a mitzvah.<sup class="footnote-marker">4</sup><i class="footnote">By reciting blessings over the special events which occur to us, we become conscious of God\'s control of all aspects of our daily existence. We learn to appreciate Him, not only as the Creator who brought the world into being, but as the One who directs the functioning of our lives and the world around us.</i>',
             'dh_inserted_serials': [1, 2, 3, 4]}]


def test_main_function(commentary_dict_test, mt_dict, expected_results_blessings_1_3):
    assert expected_results_blessings_1_3 == run_commentary_insertion(commentary_dict_test, mt_dict)
