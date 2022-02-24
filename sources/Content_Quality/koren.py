from sources.functions import *
from bs4 import BeautifulSoup
soup = BeautifulSoup("<root>asdf<sup class='endFootnotes'>-a</sup>asdflkj</root>", 'lxml')
tag = soup.find("sup")
is_tanakh_end_sup = tag.name == "sup" and tag.get('class') == ['endFootnotes'] \
                                and re.search("^-[a-zA-Z0-9]{1,2}", tag.text) is not None

library.get_index('Likutei Tefilot').contents(v2=True, with_content_counts=True)

new_ms = ['Sanhedrin', 'Makkot', 'Shevuot', 'Avodah Zarah', 'Horayot', 'Zevachim', 'Menachot', 'Chullin', 'Bekhorot',
          'Arakhin', 'Temurah', 'Keritot', 'Meilah', 'Tamid', 'Niddah']

with open("current koren.csv", 'r') as f:
    rows = list(csv.reader(f))
    for row in rows[5:]:
        ref, comm = row
        set_to_empty = len(new_ms)
        for new_m in new_ms:
            if new_m in ref:
                set_to_empty -= 1
            if set_to_empty == 0:
                tc = TextChunk(Ref(ref), vtitle="William Davidson Edition - English", lang="en")
                if tc.text == comm:
                    print(ref)
                    tc2 = TextChunk(Ref(ref), vtitle="William Davidson Edition - English - old masechtot only", lang="en")
                    tc2.save()
