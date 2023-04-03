import django
django.setup()

import pytest
from sefaria.model import *
from linking_utilities.citation_disambiguator.modify_tanakh_links import convert_section_citation_to_segment_citation, get_text_and_version_from_ref


@pytest.mark.parametrize(['input_text', 'section_tref', 'segment_ref_dict', 'output_text'], [
    ['שלום (בראשית א) מה קורה?', 'Genesis 1', {0: Ref('Genesis 1:1')}, 'שלום (בראשית א׳:א׳) מה קורה?'],
    ['שלום (בראשית א) מה קורה? וגם (בראשית א)', 'Genesis 1', {0: Ref('Genesis 1:1'), 1: Ref('Genesis 1:13')}, 'שלום (בראשית א׳:א׳) מה קורה? וגם (בראשית א׳:י״ג)']
])
def test_convert_section_citation(input_text, section_tref, segment_ref_dict, output_text):
    temp_output_text = convert_section_citation_to_segment_citation(input_text, section_tref, segment_ref_dict)
    assert temp_output_text == output_text


@pytest.mark.parametrize(['tref', 'vtitle'], [
    ['Job 17:1', None]
])
def test_get_text_and_version_from_ref(tref, vtitle):
    text, version = get_text_and_version_from_ref(tref, vtitle)
    assert text == Ref(tref).text('he', vtitle=vtitle).text

