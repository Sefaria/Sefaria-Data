import django
django.setup()
from sefaria.model import *
vtitle = "Be'er HaGolah, with footnotes and annotations by Rabbi Yehoshua D. Hartman, Machon Yerushalyim, 2002"
refs = """Be'er HaGolah, Introduction to Be'er HaGolah 2
Be'er HaGolah, Well 1 2:4
Be'er HaGolah, Well 2 2:5
Be'er HaGolah, Well 2 4:12
Be'er HaGolah, Well 2 4:13
Be'er HaGolah, Well 2 4:15""".splitlines()
for ref in reversed(refs):
    ref = Ref(ref)
    section = ref.section_ref()
    segment = ref.sections[-1]
    tc = TextChunk(section, vtitle=vtitle, lang='he')
    section_text = tc.text
    curr = section_text[segment-1]
    prev = section_text[segment-2]
    attached = prev + " " + curr
    section_text[segment-2] = attached
    del section_text[segment-1]
    tc.text = section_text
    tc.save(force_save=True)