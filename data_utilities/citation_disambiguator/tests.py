import pytest
import django
django.setup()
import json
from sefaria.model import *
from .main import disambiguate_one, CitationDisambiguator


def get_input_output():
    input_trefs = [
        ("Shemirat HaLashon, Book I, The Gate of Torah 4:25", "Shevuot 39a:22", True),
        ("Commentary on Sefer Hamitzvot of Rasag, Positive Commandments 136:4", "Horayot 5a:1", False),
    ]
    input_output = []
    for main_tref, quote_tref, is_good in input_trefs:
        main_oref = Ref(main_tref)
        quote_oref = Ref(quote_tref)
        input_output += [{
            "in": {
                "main": main_oref,
                "quote": quote_oref.section_ref()
            },
            "out": {
                "main": main_oref,
                "quote": quote_oref if is_good else None
            }
        }]
    return input_output


@pytest.mark.parametrize('test_item', get_input_output())
def test_link_disambiguator(test_item):

    ld = CitationDisambiguator()
    good, bad = disambiguate_one(ld, test_item["in"]["main"], test_item["in"]["main"].text('he'), test_item["in"]["quote"], test_item["in"]["quote"].text('he'))
    if test_item["out"]["quote"] is None:
        # output should be bad
        assert good == []
        assert bad == [] or bad[0]['Quoting Ref'] == test_item["out"]["main"].normal()
    else:
        # output is good
        assert good[0]['Quoted Ref'] == test_item["out"]["quote"].normal()
        assert bad == []
