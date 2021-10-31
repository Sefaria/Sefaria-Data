import django
django.setup()
from data_utilities.normalization import *

def test_itag_normalizer():
    text = "Yo <sup>3</sup><i class=\"footnote\"> <i> Am </i>. 4:4</i>."
    itn = ITagNormalizer(' ')
    norm_text = itn.normalize(text)
    assert norm_text == "Yo   ."
    text_to_remove = itn.find_text_to_remove(text)
    assert len(text_to_remove) == 2
    (s1, e1), r1 = text_to_remove[0]
    assert (s1, e1) == (3, 15)
    (s2, e2), r2 = text_to_remove[1]
    assert (s2, e2) == (15, len(text)-1)

def test_replace_normalizer():
    text = "Hello, what is up? You is nice"
    rn = ReplaceNormalizer(' is ', ' are ')
    norm_text = rn.normalize(text)
    assert norm_text == text.replace(' is ', ' are ')
    text_to_remove = rn.find_text_to_remove(text)
    assert len(text_to_remove) == 2
    (s1, e1), r1 = text_to_remove[0]
    assert (s1, e1) == (11, 15)
    (s2, e2), r2 = text_to_remove[1]
    assert (s2, e2) == (22, 26)

def test_br_tag_html_composer():
    """
    These two normalizers composed seem to cause issues
    """
    text = """<i>hello</i><br><b>as well as</b> yo"""
    normalized = """ hello   as well as yo"""
    nsc = NormalizerComposer(['br-tag', 'html'])
    assert nsc.normalize(text) == normalized
    text_to_remove = nsc.find_text_to_remove(text)
    assert len(text_to_remove) == 5
    (start1, end1), repl1 = text_to_remove[1]
    assert text[start1:end1] == '</i>'
    (start2, end2), repl2 = text_to_remove[2]
    assert repl2 == ' '
    assert text[start2:end2] == '<br>'
    (start4, end4), repl4 = text_to_remove[4]
    assert repl2 == ' '
    assert text[start4:end4] == '</b> '

def test_normalizer_composer():
    text = """(<i>hello</i> other stuff) [sup] <b>(this is) a test</b>"""
    normalized = """ sup  a test """
    nsc = NormalizerComposer(['html', "parens-plus-contents", 'brackets'])
    assert nsc.normalize(text) == normalized
    text_to_remove = nsc.find_text_to_remove(text)
    assert len(text_to_remove) == 6
    (start0, end0), repl0 = text_to_remove[0]
    assert text[start0:end0] == "(<i>hello</i> other stuff)"
    assert repl0 == ''

def test_html_normalizer_for_empty_prefix():
    text = """It is written<sup>24</sup><i class="footnote"><i>1K</i>. 17:1.</i> <i>Elijah the Tisbite</i>"""
    normalizer = NormalizerComposer(['html'])
    ne = "Elijah the Tisbite"
    norm_text = "It is written 24   1K . 17:1.  Elijah the Tisbite "
    assert normalizer.normalize(text) == norm_text
    ne_start = norm_text.index(ne)
    ne_norm_prefix_inds = (ne_start, ne_start)
    assert norm_text[ne_norm_prefix_inds[0]:ne_norm_prefix_inds[0]+len(ne)] == ne
    mapping = get_mapping_after_normalization(text, normalizer.find_text_to_remove)
    ne_inds = convert_normalized_indices_to_unnormalized_indices([ne_norm_prefix_inds], mapping)[0]
    # actual test
    assert ne_inds[0] == ne_inds[1]
    assert text[ne_inds[0]:ne_inds[0]+len(ne)] == ne

def test_nested_itag():
    text = """<sup>outer</sup><i class="footnote">bull<sup>nested</sup><i class="footnote">The</i>.</i>"""
    normalizer = ITagNormalizer(' ')
    norm_text = normalizer.normalize(text)
    assert norm_text == "  "
    text_to_remove = normalizer.find_text_to_remove(text)
    assert len(text_to_remove) == 2
    (s, e), r = text_to_remove[0]
    assert text[s:e] == "<sup>outer</sup>"
    (s, e), r = text_to_remove[1]
    assert text[s:e] == """<i class="footnote">bull<sup>nested</sup><i class="footnote">The</i>.</i>"""
"""
Definitely a later norm that larger or the same trumps an earlier one
But what about later norm that's smaller
e.g.
<br> => <br/>
<br/> => </>
"""