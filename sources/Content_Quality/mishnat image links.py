import django
django.setup()
from sefaria.model import *
from sources.functions import *
img_locs = {}
def replace_img(r, img_loc, whole):
    link = f"<a href='/{img_loc.url()}' data-ref='{img_loc.normal()}' class='refLink'>{whole}</a>"
    tc = TextChunk(r, lang='he', vtitle='Mishnat Eretz Yisrael, Seder Nezikin, Jerusalem, 2013')
    if link not in tc.text:
        print(r)
        tc.text = tc.text.replace(whole, link, 1)
        tc.save(force_save=True)

for sec in library.get_index("Mishnat Eretz Yisrael on Pirkei Avot").all_section_refs():
    for r in sec.all_segment_refs():
        if "<img" in r.text('he').text:
            for m in re.findall("איור מס' (\d+)", r.text('he').text):
                if m not in img_locs:
                    img_locs[m] = r
            for m in re.findall("איור (\d+)", r.text('he').text):
                if m not in img_locs:
                    img_locs[m] = r

for sec in library.get_index("Mishnat Eretz Yisrael on Pirkei Avot").all_section_refs():
    for r in sec.all_segment_refs():
        if "<img" in r.text('he').text:
            continue
        ranges = re.findall('(איורים (\d+)-(\d+))', r.text('he').text)
        regular = re.findall('((איור )(\d+))', r.text('he').text)
        assert (len(regular) == 0 and len(ranges) == 0) or ((len(regular) == 0) ^ (len(ranges) == 0))
        for m in ranges:
            first = m[2]
            second = m[1]
            img_loc_1 = img_locs[first]
            img_loc_2 = img_locs[second]
            img_loc = img_loc_1.to(img_loc_2)
            whole = m[0]
            replace_img(r, img_loc, whole)
        for m in regular:
            img_loc = img_locs[m[2]]
            whole = m[0]
            replace_img(r, img_loc, whole)
