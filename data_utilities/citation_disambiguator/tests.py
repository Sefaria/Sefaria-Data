import pytest
import django
django.setup()
import json
from sefaria.model import *
from .main import disambiguate_one, CitationDisambiguator


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


@pytest.mark.parametrize('input_output', [
    ("Shemirat HaLashon, Book I, The Gate of Torah 4:25", "Shevuot 39a:22", True),
    ("Commentary on Sefer Hamitzvot of Rasag, Positive Commandments 136:4", "Horayot 5a:1", False),
], indirect=True)
def test_citation_disambiguator(input_output):
    input, output = input_output

    ld = CitationDisambiguator()
    good, bad = disambiguate_one(ld, input["main"], input["main"].text('he'), input["quote"], input["quote"].text('he'))
    if output["quote"] is None:
        # output should be bad
        assert good == []
        assert bad == [] or bad[0]['Quoting Ref'] == output["main"].normal()
    else:
        # output is good
        assert good[0]['Quoted Ref'] == output["quote"].normal()
        assert bad == []
