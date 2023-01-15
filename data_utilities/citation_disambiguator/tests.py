import pytest
import django
django.setup()
from sefaria.model import *
from .main import CitationDisambiguator
from .modify_tanakh_links import convert_section_citation_to_segment_citation


@pytest.fixture(scope="module")
def citation_disambiguator():
    return CitationDisambiguator("he")


@pytest.fixture(scope="module")
def input_output(request):
    main_tref, quote_tref, is_good, vtitle = request.param
    main_oref = Ref(main_tref)
    quote_oref = Ref(quote_tref)
    return (
        {
            "main": main_oref,
            "quote": quote_oref.section_ref()
        },
        {
            "main": main_oref,
            "quote": quote_oref if is_good else None
        },
        vtitle
    )


@pytest.mark.parametrize(['input_string', 'output_tokens'], [
    ('שלום', ['שלום']),
    ('יי', ['\u05d9\u05d4\u05d5\u05d4']),
])
def test_tokenizer(citation_disambiguator, input_string, output_tokens):
    test_tokens = citation_disambiguator.tokenize_words(input_string)
    assert test_tokens == output_tokens


@pytest.mark.parametrize('input_output', [
    ("Shemirat HaLashon, Book I, The Gate of Torah 4:25", "Shevuot 39a:22", True, None),
    ("Commentary on Sefer Hamitzvot of Rasag, Positive Commandments 136:4", "Horayot 5a:1", False, None),
    ("Zohar, Vayishlach 26:254", "Zephaniah 3:9", True, "Torat Emet"),
    ("Zohar, Idra Rabba 27:194", "Song of Songs 5:15", True, "Torat Emet"),
    ("Zohar, Pinchas 10:50", "Amos 2:6", True, "Torat Emet"),
    ("Zohar, Mishpatim 28:568", "Deuteronomy 14:3", True, "Torat Emet"),
    ("Zohar, Vayechi 59:579", "Isaiah 63", False, "Torat Emet"),
], indirect=True)
def test_citation_disambiguator(input_output, citation_disambiguator):
    input, output, vtitle = input_output

    main_tc = input["main"].text('he', vtitle=vtitle)
    good, bad = citation_disambiguator.disambiguate_one(input["main"], main_tc, input["quote"])
    if output["quote"] is None:
        # output should be bad
        assert good == []
        assert bad == [] or bad[0]['Quoting Ref'] == output["main"].normal()
    else:
        # output is good
        assert good[0]['Quoted Ref'] == output["quote"].normal()
        assert bad == []


@pytest.mark.parametrize(['input_text', 'section_tref', 'segment_ref_dict', 'output_text'], [
   ['שלום (בראשית א) מה קורה?', 'Genesis 1', {0: Ref('Genesis 1:1')}, 'שלום (בראשית א׳:א׳) מה קורה?'],
   ['שלום (בראשית א) מה קורה? וגם (בראשית א)', 'Genesis 1', {0: Ref('Genesis 1:1'), 1: Ref('Genesis 1:13')}, 'שלום (בראשית א׳:א׳) מה קורה? וגם (בראשית א׳:י״ג)']
])
def test_convert_section_citation(input_text, section_tref, segment_ref_dict, output_text):
    temp_output_text = convert_section_citation_to_segment_citation(input_text, section_tref, segment_ref_dict)
    assert temp_output_text == output_text


