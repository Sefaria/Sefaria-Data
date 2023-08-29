import django
django.setup()
from sefaria.model import *
import re
from sefaria.utils.hebrew import *

def get_dh(x):
    first_sentence = en.split(".")[0]
    caps = False
    bold = False
    italics = False
    quotes = False
    m = re.search("([A-Z])+.*?", first_sentence)  # all caps is a signal of DH
    if m:
        caps = True
        first_sentence = m.group(1)

    if "<b>" in first_sentence:
        bold = True
    if "<i>" in first_sentence:
        italics = True
    first_sentence = first_sentence.split("</b>")[0].split("</i>")[0]  # inside italics or bold is a sign of DH
    for quote in ['\u2019', '\u201D', '"']:
        if quote in first_sentence:
            quotes = True
            first_sentence = first_sentence.split(quote)[0]
            break
    first_sentence = first_sentence.replace("\u201C", "").replace("\u2018", "")

    if not quotes and not bold and not italics and not caps:  # look for hebrew
        if has_hebrew(first_sentence):
            hebrew = ""
            for word in first_sentence.split():
                if is_all_hebrew(word):
                    hebrew += word + " "
            first_sentence = hebrew

    return " ".join(first_sentence.split()[:8])

            

tanakh_commentaries = [b for b in library.get_indexes_in_corpus("Tanakh", include_dependant=True) if getattr(b, 'dependence', False)]
for book in tanakh_commentaries:
    for r in library.get_index(book).all_segment_refs():
        en = r.text('en').text
        en = get_dh(en)

        when you cant find DH you could use precomputed 3 word phrase or 3 topics
        could hardcode these topics for elastic search or filter in sidebar
        synonyms in elastic search - "https://www.google.com/search?q=elastic+search+use+synonyms&rlz=1C5CHFA_enUS968US972&oq=elastic+search+use+synonyms&gs_lcrp=EgZjaHJvbWUyBggAEEUYOTIICAEQABgWGB4yCggCEAAYhgMYigUyCggDEAAYhgMYigUyCggEEAAYhgMYigUyCggFEAAYhgMYigXSAQgzMTczajBqMagCALACAA&sourceid=chrome&ie=UTF-8"
# idea.  take first sentence of all commentaries they should be bold italics or capitalized,
# if not, look for phrases that are in quotes or italics