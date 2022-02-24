#<a class="refLink" data-ref="Leviticus 14:1-57" data-ven="The Five Books of Moses, by Everett Fox. New York, Schocken Books, 1995">Leviticus 14:1-57</a>
import django
django.setup()
from sefaria.model import *
for sec_ref in library.get_index("The Five Books of Moses, by Everett Fox").all_section_refs():
    ref = sec_ref.all_segment_refs()[0]
    tc = TextChunk(ref, lang='en', vtitle="The Five Books of Moses, by Everett Fox. New York, Schocken Books, 1995")
    try:
        Ref(tc.text)
        tc.text = f'<a class="refLink" data-ref="{tc.text}" data-ven="The Five Books of Moses, by Everett Fox. New York, Schocken Books, 1995">{tc.text}</a>'
        tc.save()
    except:
        try:
            Ref(tc.text[1:-1])
            assert tc.text.startswith("(") and tc.text.endswith(")")
            tc.text = f'<a class="refLink" data-ref="{tc.text[1:-1]}" data-ven="The Five Books of Moses, by Everett Fox. New York, Schocken Books, 1995">{tc.text[1:-1]}</a>'
            tc.save()
        except:
            print(ref)
