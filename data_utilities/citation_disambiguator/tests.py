import pytest
import django
django.setup()
from sefaria.model import *
from .main import CitationDisambiguator


@pytest.fixture(scope="module")
def citation_disambiguator():
    return CitationDisambiguator("he")


@pytest.fixture(scope="module")
def input_output(request):
    main_tref, quote_tref, is_good = request.param
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
        }
    )


@pytest.mark.parametrize(['input_string', 'output_tokens'], [
    ('שלום', ['שלום']),
    ('יי', ['\u05d9\u05d4\u05d5\u05d4']),
])
def test_tokenizer(citation_disambiguator, input_string, output_tokens):
    test_tokens = citation_disambiguator.tokenize_words(input_string)
    assert test_tokens == output_tokens


@pytest.mark.parametrize('input_output', [
    ("Shemirat HaLashon, Book I, The Gate of Torah 4:25", "Shevuot 39a:22", True),
    ("Commentary on Sefer Hamitzvot of Rasag, Positive Commandments 136:4", "Horayot 5a:1", False),
], indirect=True)
def test_citation_disambiguator(input_output, citation_disambiguator):
    input, output = input_output

    good, bad = citation_disambiguator.disambiguate_one(input["main"], input["main"].text('he'), input["quote"])
    if output["quote"] is None:
        # output should be bad
        assert good == []
        assert bad == [] or bad[0]['Quoting Ref'] == output["main"].normal()
    else:
        # output is good
        assert good[0]['Quoted Ref'] == output["quote"].normal()
        assert bad == []
