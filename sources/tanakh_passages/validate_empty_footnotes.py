import django
django.setup()
from sefaria.model import *
import re

if __name__ == '__main__':
    all_seg_ref = Index().load({"title": "The Kehot Chumash; A Chasidic Commentary"}).all_segment_refs()
    for ref in all_seg_ref:
        text = ref.text('en').text
        matches = re.findall(r'<i\s+class="footnote"\s*>\s*</i>', text)
        if matches:
            print(f"{ref.normal()}")
