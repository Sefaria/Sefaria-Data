
import django
django.setup()
from sefaria.model import *
from sources.functions import *
from bs4 import BeautifulSoup
import pandas as pd
from sources.functions import eng_parshiot, heb_parshiot
from sefaria.tracker import modify_bulk_text
superuser_id = 171118


title = "The Kehot Chumash; A Chasidic Commentary"

def ingest_version(map_text):
    # vs = VersionState(index=library.get_index("Introductions to the Babylonian Talmud"))
    # vs.delete()
    # print("deleted version state")
    index = library.get_index(title)
    cur_version = VersionSet({'title': title})
    if cur_version.count() > 0:
        cur_version.delete()
        print("deleted existing version")
    chapter = index.nodes.create_skeleton()
    version = Version({"versionTitle": "The Torah; Chabad House Publications, Los Angeles, 2015-2023",
                       "versionSource": "https://www.chabadhousepublications.org/books",
                       "title": title,
                       "language": "en",
                       "chapter": chapter,
                       # "digitizedBySefaria": True,
                       "license": "PD",
                       "status": "locked"
                       })


    modify_bulk_text(superuser_id, version, map_text)

num_to_book_map = {
    **{i: 'Genesis' for i in range(1, 13)},
    **{i: 'Exodus' for i in range(13, 24)},
    **{i: 'Leviticus' for i in range(24, 34)},
    **{i: 'Numbers' for i in range(34, 44)},
    **{i: 'Deuteronomy' for i in range(44, 55)},
                   }

def file_name_to_book(file_name):
    num_prefix = file_name[0:2]
    if not num_prefix.isdigit():
        return None
    num = int(num_prefix)
    if num == 0 or num > 54:
        return None
    return num_to_book_map[num]
def insert_style(html_text):
    soup = BeautifulSoup(html_text, 'html.parser')

    for span in soup.find_all(['span', 'p'], class_=['bold-small-text', "Overvview-heading-2-NEW"]):
        b_tag = soup.new_tag('b')
        b_tag.string = span.get_text()
        span.replace_with(b_tag)
    for span in soup.find_all(['span', 'p'], class_=['it-small-text']):
        i_tag = soup.new_tag('i')
        i_tag.string = span.get_text()
        span.replace_with(i_tag)
    for p in soup.find_all('p'):
        p.replaceWithChildren()
    return str(soup)

def extract_notes_dict(html: str) -> dict[int, str]:
    soup = BeautifulSoup(html, "html.parser")
    notes: dict[int, str] = {}

    for p in soup.find_all("p", class_="FNote-Eng"):
        for span in p.find_all("span", class_="FNN-Peshat"):
            m = re.match(r"(\d+)\.?\s*", span.get_text())
            if not m:
                continue
            num = int(m.group(1))
            # Collect all sibling content until the next note span
            parts = []
            for sib in span.next_siblings:
                if sib.name == "span" and "FNN-Peshat" in sib.get("class", []):
                    break
                parts.append(getattr(sib, "get_text", lambda: str(sib))())
            text = " ".join(" ".join(parts).split())
            notes[num] = text

    return notes



def extract_overview_footnotes(html: str,
                      *,
                      start: int = 1,
                      footnote_cls = "FNote-Eng"
                      ) -> dict[int, str]:
    """
    Return {footnote_number: plain-text_footnote} parsed from an HTML string.

    Parameters
    ----------
    html : str
        The raw HTML containing one *or more* <p class="FNote-Eng"> … </p>.
    start : int, optional
        The first foot-note number you expect to see (default 1).
        This acts as a simple guard against “p. 110.”-style false positives.
    footnote_cls : str | tuple[str, ...], optional
        Class name(s) that mark the footnote paragraph(s).

    Notes
    -----
    •  The function looks for the textual hint “`<number>. `” – i.e. *digits*,
       a dot, and at least one space – to locate each marker.
    •  Only markers that appear in strictly ascending order
       (*start*, *start* + 1, …) are accepted; everything else is ignored.
       This prunes out pattern matches inside citations like
       “`Exodus 19:5.`” or “`p. 110.`”.
    """
    soup = BeautifulSoup(html, "html.parser")

    # 1 – Keep only the HTML that contains footnotes
    para_html = " ".join(str(tag) for tag in soup.find_all(class_=footnote_cls))
    if not para_html:                       # fallback: treat whole input as one chunk
        para_html = html

    # 2 – Strip outer <p> tags and normalise &nbsp;
    para_html = re.sub(r"^<p[^>]*>|</p>$", "", para_html).replace("&nbsp;", " ")

    # 3 – Locate every “…<digits>. ” in the paragraph
    marker = re.compile(r"(\d{1,4})\.\s")   # e.g. “3. ”
    matches = list(marker.finditer(para_html))

    footnotes, expect = {}, start
    for i, m in enumerate(matches):
        num = int(m.group(1))
        if num != expect:                   # skip anything out of sequence
            continue

        # slice runs from the end of this marker to the *next* marker with expect+1
        nxt = next((n.start() for n in matches[i + 1:]
                    if int(n.group(1)) == expect + 1),
                   len(para_html))
        raw_snippet = para_html[m.end():nxt].strip()

        # strip residual tags → plain text
        txt = BeautifulSoup(raw_snippet, "html.parser").get_text(" ", strip=True)
        footnotes[num] = txt
        expect += 1

    return footnotes


def replace_inline_notes(html: str, notes_map: dict[int, str]) -> str:
    soup = BeautifulSoup(html, "html.parser")
    pattern = re.compile(r'^\d+$')

    for span in soup.find_all("span", class_=["FNR-Chasidic", "Footnote-Anchor"]):
        txt = span.get_text(strip=True)
        if not pattern.fullmatch(txt):
            continue
        num = int(txt)
        footnote_text = notes_map.get(num, "")

        # Create new <sup> and <i> tags directly
        sup = soup.new_tag("sup", **{"class": "footnote-marker"})
        sup.string = str(num)

        itag = soup.new_tag("i", **{"class": "footnote"})
        itag.string = footnote_text

        # Insert them before the span
        span.insert_before(sup)
        span.insert_before(itag)

        # Remove the original <span>
        span.decompose()

    return str(soup)

def closest_word(input_str, words):
    input_str = input_str.replace("’", "'").replace("’", "'").replace("'", "")
    distances = [Levenshtein.distance(input_str, w) for w in words]
    best = min(distances)
    # Get first minimal match; you can adjust tie-breaking if needed
    return words[distances.index(best)]



if __name__ == "__main__":
    # chumash_base_dict = {}
    # for chumash in ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]:
    #     seg_refs = library.get_index(chumash).all_segment_refs()
    #     for seg_ref in seg_refs:
    #         chumash_base_dict[seg_ref.tref] = ""  # Initialize with empty string
    # # print(chumash_base_dict)
    book_map = {}
    directory = '../kehot_chp_chumash/html'

    for filename in sorted(os.listdir(directory)):
        file_path = os.path.join(directory, filename)
        if not os.path.isfile(file_path):
            continue
        print(file_path)
        current_book = file_name_to_book(filename)
        if current_book is None:
            continue
        # print(current_book)
        current_chapter = 0
        curr_chapter_and_verse_num = None
        curr_segment_num = 0

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            html_content = file.read()
            # print(html_content)
        soup = BeautifulSoup(html_content, 'html.parser')

        # notes = soup.select(".FNote-Eng .FNN-Peshat")
        notes_map = extract_notes_dict(html_content)

        html_content = replace_inline_notes(html_content, notes_map)
        soup = BeautifulSoup(html_content, 'html.parser')


        chasidic_boxes = soup.find_all(class_="chasidic-insights-box")
        chasidic_ps = [p for box in chasidic_boxes for p in box.find_all("p")]

        for elem in chasidic_ps:
            match = re.match(r'^(\d+):(\d+)', elem.text.strip())
            chapter_and_verse_num = match.group(0) if match else None
            if chapter_and_verse_num:
                curr_chapter_and_verse_num = chapter_and_verse_num
                curr_segment_num = 0
            # print(elem.text.strip())
            if 'class="bold-small-text' in str(elem):
                curr_segment_num += 1

            key = f"{title}, {current_book} {curr_chapter_and_verse_num}:{curr_segment_num}"
            # patch
            if key == f"{title}, Numbers None:1":
                key = f"{title}, Numbers 33:1"
            # if key == f"{title}, Genesis 30:43:1":
            #     elem = str(elem).replace("Shir HaShirim Rabbah 2:45", "Shir HaShirim Rabbah 2:16")
            elem = str(elem).replace("Shir HaShirim Rabbah", "SHR")

            book_map[key] = f"{book_map[key]}<br>{elem}" if key in book_map else str(elem)
   # parashot intros
    for filename in sorted(os.listdir(directory)):
        file_path = os.path.join(directory, filename)
        if not os.path.isfile(file_path):
            continue
        print(file_path)

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            html_content = file.read()
            # print(html_content)
        notes_map = extract_overview_footnotes(html_content)
        html_content = replace_inline_notes(html_content, notes_map)
        soup = BeautifulSoup(html_content, 'html.parser')
        parasha_name_element = soup.find(class_="Overview-heading-1-NEW")
        if not parasha_name_element:
            continue
        intro_text_segments = []
        parasha_name = parasha_name_element.get_text(strip=True)
        parasha_name = closest_word(parasha_name, eng_parshiot)
        print(parasha_name)

        intro_title = str(soup.find(class_="Overvview-heading-2-NEW"))
        intro_text_segments.append(intro_title)
        intro_elements = soup.find_all(class_=re.compile(r'^O-body'))
        intro_text_segments += [str(elem) for elem in intro_elements]

        segment_number = 1
        for intro_text in intro_text_segments:
            key = f"{title}, Parashah Overviews, {parasha_name}, {segment_number}"
            book_map[key] = insert_style(intro_text)
            segment_number += 1




    for key, value in book_map.items():
        book_map[key] = insert_style(value)



    pd.DataFrame(list(book_map.items()), columns=["ref", "html"]) \
        .to_html("book_map.html",  # output file
                 index=False,  # no row numbers
                 escape=False)  # keep the inner HTML un-escaped

    ingest_version(book_map)
    print('hi')