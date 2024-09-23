from ebooklib import epub
import ebooklib
from bs4 import BeautifulSoup
from bs4 import Tag, NavigableString
import re
from sources.functions import *
import difflib
allowed_tags = ['i', 'b', 'u', 'small', 'a']
special_node_names = {"Postbiblical Interpretations": [], "Contemporary Reflection": [], "Another View": [], "Parashah Introductions": []}
parshiot = []
for book in ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]:
    parshiot += [Term().load({"name": x["sharedTitle"]}).get_primary_title('en') for x in
                 library.get_index(book).alt_structs["Parasha"]["nodes"]]

for node in special_node_names:
    special_node_names[node] = {key: [] for key in parshiot}

def get_parasha(name):
    url = "http://localhost:8000/api/name/"+name

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return

    try:
        data = response.json()
    except ValueError:
        print("Unable to parse JSON response.")
        return

    return [x for x in data["completion_objects"] if x['type'] == "Topic"][0]
def remove_unwanted_tags(soup_element):
    # List of allowed tags
    allowed_tags = {'i', 'b', 'u', 'small', 'a'}

    # Iterate through all descendants recursively
    for tag in soup_element.find_all(recursive=True):
        if tag.name not in allowed_tags:
            # Decompose removes the tag and its children from the tree
            tag.decompose()
def parse(children):
    elements = list(children)

    # Initialize variables to keep track of the current chapter
    current_chap = None
    parent_chap = None
    parents = []
    for elem in elements:
        # Check for 'chap' elements
        if not isinstance(elem, Tag):
            continue
        classes = str(elem.get('class', []))
        ignore_words = ['new-head', 'page-break-before:always;', 'box1', 'sidebar', 'boxv']
        ignoring = False
        for ignore in ignore_words:
            if elem.name == 'div' and ignore in classes:
                ignoring = True
        if elem.name == "table":
            ignoring = True
        if ignoring:
            continue
        if elem.name == 'div' and ('chap' in classes or 'note' in classes):
            if parent_chap and len(parent_chap) == 1:
                parent_chap.append(elem.contents[0])
            elif parent_chap:
                parents.append(parent_chap)
                parent_chap = elem
            else:
                remove_unwanted_tags(elem)
                parent_chap = elem
        elif parent_chap:
            parent_chap.append(elem)

    parents.append(parent_chap)
    return parents

def element_has_dh(child):
    startswith_bi = lambda x: str(x).startswith("<b><i>") or str(x).startswith("<i><b>")
    return startswith_bi(child)
    # just_tags = [x for x in child.contents if isinstance(x, Tag)]
    # next_is_dh = False
    # if len(just_tags) > 1:
    #     next_is_dh = startswith_bi(child.contents[0]) and startswith_bi(just_tags[1])
    # this_one_has_dh = len(child.contents[0].text) > (len(verse_and_chapter) + 2)
    # return this_one_has_dh or next_is_dh

def extract_text(element):
   if isinstance(element, NavigableString):
       return str(element)
   elif element is not None and hasattr(element, 'get_text'):
       return element.get_text()
   return ''
def identify_chapters(parents, item_id):
    for parent in parents:
        chapter = -1
        if parent.get('class', []) == ['note']:
            for child in parent.children:
                if isinstance(child, NavigableString):
                    continue
                child_classes = str(child.get('class', []))
                if 'head' in child_classes:
                    match = re.search(r'\((\d+):', child.text)

                    # Extract and print the chapter number if found
                    if match:
                        chapter = int(match.group(1))
                elif re.search(r'^(\d+)', child.text) and chapter >= 1:
                    node = child.contents[0]
                    new_text = extract_text(node)
                    match = re.search(r'^(\d+)', new_text)
                    already_pasuk = re.search(r'^(\d+):(\d+)', new_text)
                    if match and already_pasuk is None:
                        new_text = new_text.replace(match.group(0), f"{chapter}:{match.group(0)}", 1)
                    else:
                        chapter = int(already_pasuk.group(1))
                    new_node = Tag(name="b")
                    italics_tag = Tag(name="i")
                    italics_tag.string = new_text
                    new_node.append(italics_tag)
                    node.replace_with(new_node)  # 32-35 becomes 29:32-35
                    range_m = re.search(r"\d+:(\d+[-—–]{1}\d+)\.{0,1}", new_text)
                    if range_m:
                        for char in ["-", "—", '–']:
                            if char in new_text:
                                child.attrs["orig_ref"] = range_m.group(1)
                                pattern = r"(\d+:\d+)[-—–]{1}\d+\."
                                # Replace the matched pattern with the desired format "3:4."
                                adjusted_text = re.sub(pattern, r"\1.", new_text)
                                italics_tag = Tag(name="i")
                                italics_tag.string = adjusted_text
                                new_node.append(italics_tag)
                                new_node.string = adjusted_text


                # elif re.search("<b><i>\D+</i></b>", str(child)):
            found_verse = False
            prepend = []
            diff = 0
            for c in range(len(parent.contents)):
                child = parent.contents[c+diff]
                child_classes = str(child.get('class', []))
                if re.search(r'^(\d+)', child.text) is None:
                    if found_verse and 'head' not in child_classes:
                        br_tag = Tag(name="br")
                        prev_child_num = 1
                        prev_child = parent.contents[c - prev_child_num + diff]
                        while prev_child.text == "":
                            prev_child_num += 1
                            prev_child = parent.contents[c - prev_child_num + diff]
                        is_sentence = False
                        for char in [":", ".", "?", "!"]:
                            is_sentence = is_sentence or prev_child.text.endswith(char) or prev_child.text.endswith(char+")")
                        if (isinstance(prev_child.contents[-1], NavigableString) or prev_child.contents[-1].name != 'br') and is_sentence:
                            prev_child.append(br_tag)
                        else:
                            prev_child.append(NavigableString(" "))
                        for x in list(child.children):
                            prev_child.append(x)
                        child.string = ""
                    else:
                        prepend.append(child)
                else:
                    verse_and_chapter = re.search(r'^(\d+:\d+)', child.text).group(0)
                    # 3 three cases when there's a verse
                    # verse and no dh
                    # <b> verse dh </b>
                    # <b> verse </b> <b> dh </b>
                    # when there's no dh and no range, take the verse out
                    tagless_text = bleach.clean(str(child), strip=True, tags=[])
                    no_range = re.search(r"^\d+:(\d+[-—–]{1}\d+)\.{0,1}", tagless_text) is None
                    # startswith_bi = lambda x: str(x).startswith("<b><i>") or str(x).startswith("<i><b>")
                    # just_tags = [x for x in child.contents if isinstance(x, Tag)]
                    # next_is_dh = False
                    # if len(just_tags) > 1:
                    #     next_is_dh = startswith_bi(child.contents[0]) and startswith_bi(just_tags[1])
                    # this_one_has_dh = len(child.contents[0].text) > (len(verse_and_chapter) + 2)
                    # found_dh = this_one_has_dh or next_is_dh
                    if 'orig_ref' not in child.attrs and no_range: # and found_dh:
                        child.contents[0].string = child.contents[0].text.replace(verse_and_chapter+'. ', '', 1)
                        child.contents[0].string = child.contents[0].text.replace(verse_and_chapter+'.', '', 1)
                        child.contents[0].string = child.contents[0].text.replace(verse_and_chapter, '', 1).strip()
                    elif 'orig_ref' in child.attrs:
                        assert verse_and_chapter in child.contents[0].text
                        child.contents[0].string = child.contents[0].text.replace(verse_and_chapter, child.attrs['orig_ref'].replace(".", ""))
                    else:
                        actual_range = re.search(r"^\d+:(\d+[-—–]{1}\d+)\.{0,1}", tagless_text).group(1)
                        for x in child.contents:
                            if str(x).startswith("<b><i>") or str(x).startswith("<i><b>"):
                                print("POSSIBLE PROBLEM -- "+str(x))
                                x.string = ""
                            elif str(x) in ["-", "—", "–"]:
                                x.replace_with("")
                            else:
                                break
                        node = Tag(name="b")
                        italics_tag = Tag(name="i")
                        italics_tag.string = actual_range+"."
                        node.append(italics_tag)
                        child.insert(0, node)

                    child.attrs["ref"] = verse_and_chapter
                    if len(prepend) > 0:
                        found = None
                        for i, x in enumerate(prepend):
                            if 'head' in str(x.get('class', [])):
                                verse_and_chapter = re.search(r'\((\d+:\d+)', str(x))
                                if verse_and_chapter:
                                    x.attrs["ref"] = verse_and_chapter.group(1)
                                    found = x
                            elif found:
                                found.insert(len(found.contents), x)
                                diff -= 1
                        prepend = []
                    found_verse = True
            if len(prepend) > 0:
                found = None
                for x in prepend:
                    if 'head' in str(x.get('class', [])):
                        verse_and_chapter = re.search(r'\((\d+:\d+)', str(x))
                        if verse_and_chapter:
                            x.attrs["ref"] = verse_and_chapter.group(1)
                            found = x
                    elif found:
                        found.insert(len(found.contents), x)
            for x in parent.find_all("div", {"class": "tab-en1"}):
                if x.text.strip() == "":
                    x.decompose()
            for x in parent.find_all("b"):
                if x.text.strip() == "":
                    x.decompose()
                if x.text.strip() == "Commentary":
                    x.decompose()
            for x in parent.find_all("i"):
                if x.text.strip() == "":
                    x.decompose()
            for x in parent.find_all("b"):
                if x.text.strip() == "":
                    x.decompose()
            # for x in parent.find_all("i"):
            #     if x.text.strip().startswith("—") and x.text.strip().count(" ") in [1, 2]:
            #         x.string = ""
            for c, child in enumerate(parent.contents):
                classes = str(child.get('class', []))
                if 'head' in classes and 'ref' not in child.attrs:
                    child.attrs['ref'] = parent.contents[c+1].attrs['ref']

    return parents

def extract_chapters(parents, book_dict):
    for parent in parents:
        chapter = -1
        if parent.get('class', []) == ['note']:
            for child in parent.children:
                if 'ref' in child.attrs:
                    chapter, verse = child.attrs["ref"].split(':')
                    chapter = int(chapter)
                    verse = int(verse)
                    for grandchild in child:
                        if grandchild.name == "div" and 'head' in str(grandchild.get('class', [])):
                            grandchild.append(NavigableString("\n"))
                        if grandchild.name == "div" and 'head' not in str(grandchild.get('class', [])):
                            grandchild.append(NavigableString("\n"))
                    for grandchild in child:
                        if grandchild.text == "Commentary":
                            grandchild.decompose()
                        if isinstance(grandchild, Tag) and grandchild.name == 'b' and grandchild.text.strip() == "":
                            grandchild.decompose()
                    copy_child = BeautifulSoup(str(child), 'html.parser').find(child.name)
                    if verse in book_dict[chapter]:
                        book_dict[chapter][verse].append(NavigableString("\n"))
                        book_dict[chapter][verse].append(copy_child)
                    else:
                        book_dict[chapter][verse] = copy_child

    return book_dict

def extract_book(parents, id):
    #     for p in parshiot:
    #         if p in parents[0].text:
    #             found.append(book)
    global parshiot
    id = int(id.replace("chap", ""))
    if id <= 12:
        return "Genesis"
    elif id <= 23:
        return "Exodus"
    elif id <= 33:
        return 'Leviticus'
    elif id <= 43:
        return "Numbers"
    else:
        return "Deuteronomy"
    # from sefaria.system.database import db
    # #p = parents[0].contents[-1].contents[-1].text.replace("Sh’lach L’cha", "Sh'lach")
    # parents[0].contents[-1].contents[-1].contents[-1].text.replace("Sh’lach L’cha", "Sh'lach")
    # print(p)
    # found = []
    # closest_matches = difflib.get_close_matches(p, parshiot, n=1, cutoff=0.0)
    # if closest_matches:
    #     closest_match = closest_matches[0]
    #     for book in ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]:
    #         book_parshiot = [Term().load({"name": x["sharedTitle"]}).get_primary_title('en') for x in
    #                      library.get_index(book).alt_structs["Parasha"]["nodes"]]
    #         if closest_match in book_parshiot:
    #             return book
    # return None

def extract_special_node_names(parents, chap_num):
    global special_node_names
    global parshiot
    special_node_parents = [x for x in parents if x.attrs['class'] != ['note']]
    for node_name in special_node_names:
        found = -1
        for p, parent in enumerate(special_node_parents):
            check_node_name = node_name
            if node_name == "Postbiblical Interpretations":
                check_node_name = "Post-biblical Interpretations"
            for x in parent.contents[0:2]:
                if check_node_name.lower() in str(x).lower():
                    x.decompose()
                    special_node_names[node_name][parshiot[chap_num - 1]] = parent  # parshiot[chap_num-1]
                    found = p
                    break
            if found != -1:
                break
        if found != -1:
            del special_node_parents[found]


    special_node_names["Parashah Introductions"][parshiot[chap_num - 1]] = special_node_parents[0]
    for intro in special_node_parents[1:]:
        for child in intro:
            if isinstance(child, NavigableString):
                copy_child = str(child)
            else:
                copy_child = BeautifulSoup(str(child), 'html.parser').find(child.name)
            special_node_names["Parashah Introductions"][parshiot[chap_num - 1]].append(copy_child)

    for key in special_node_names:
        special_node_names[key][parshiot[chap_num - 1]] = parse_text(special_node_names[key][parshiot[chap_num - 1]],
                                                                             special_node=True)

def parse_text(node, special_node=False):
    segments = []
    for x in node.find_all("div", {"class": "hanga"}):
        x.name = "span"
        x.attrs["class"] = "poetry indentAll"
    for x in node.find_all("span", {"class": ["grey"]}):
        x.append(NavigableString(" "))
    if isinstance(node, Tag):
        if special_node:
            for x in node.contents:
                if isinstance(x, Tag):
                    x.append("\n")
        else:
            for div in node.find_all('div'):
                div.append("\n")
                div.insert(0, "\n")
        for br in node.find_all('br'):
            br.append("\n")
        special_node_string = str(node).replace("&lt;", "<").replace("&gt;", ">")
        if special_node:
            bleached_string = bleach.clean(special_node_string, strip=True, tags=allowed_tags+['span'], attributes=["class"])
        else:
            bleached_string = bleach.clean(special_node_string, strip=True, tags=allowed_tags)
        bleached_string = bleached_string.replace("\n \n", "\n\n").replace("<i></i>", "").replace("<b></b>", "")
        while "\n\n" in bleached_string:
            bleached_string = bleached_string.replace("\n\n", "\n")
        if special_node:
            bleached_string = re.sub(r"([A-Z]{1})\.([A-Z]{1})", r"\1. \2", bleached_string)
        segments = [x for x in bleached_string.split("\n") if x.strip() != ""]
        for i, segment in enumerate(segments):
            if segment.startswith("."):
                segments[i] = segments[i].replace(".", "",1).strip()
    return segments

def post_process(text):
    for i, line in enumerate(text):
        bold_tag = re.search("^<b>.*?</b>", line)
        if bold_tag:
            if "<i>" not in bold_tag.group(0):
                text[i] = line.replace("<b>", "<b><i>", 1).replace("</b>", "</i></b>", 1)
    return text

def remove_a_tags(htmls):
    # Parse the HTML using BeautifulSoup
    new = []
    for html in htmls:
        soup = BeautifulSoup(html, 'html.parser')

        # Find all <a> tags and unwrap them
        for a_tag in soup.find_all('a'):
            a_tag.unwrap()

        # Convert the BeautifulSoup object back to a string
        new.append(str(soup))
    return new
# Read the ePUB file
book_file = epub.read_epub('ISBN_9780881232837.epub')

# Store extracted text
text_content = []
books = {}
for book in ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]:
    books[book] = defaultdict(dict)
    chapters = library.get_index(book).schema['lengths'][0]
    for i in range(chapters):
        books[book][i+1] = {}
import os
output_dir = 'images'
if not os.path.exists(output_dir):
    os.mkdir(output_dir)
fms = {"Foreword": "בראש מילין", "Preface": "פתח דבר", "Acknowledgements": "תודות", "Introduction": "הקדמה",
       "Women and Interpretation of the Torah": "נשים ופרשנות התורה", "Women in Ancient Israel; An Overview": "נשים בישראל בעת העתיקה; סקירה",
       "Women and Postbiblical Commentary": """נשים ופרשנות חז"ל""", "Women and Contemporary Revelation": "נשים וגילויים בני זמננו",
       "The Poetry of Torah and the Torah of Poetry": "שירת התורה ותורת השירה"}
fm_text_dict = {}
# Iterate over each item in the book
prev_book_title = ""
for item in book_file.get_items():
    if item.get_type() == ebooklib.ITEM_DOCUMENT:
        # Use BeautifulSoup to parse HTML
        soup = BeautifulSoup(item.get_content(), 'html.parser')
        # with open(f"{item.id}.html", 'w', encoding='utf-8') as f:
        #     f.write(soup.prettify())
        if 'chap' in item.id:
            for span in soup.find_all('span'):
                if 'class' not in span.attrs or span.attrs['class'] != ['grey']:
                    span.unwrap()
            for a_tag in soup.find_all('a'):
                a_tag.unwrap()
            with open(f"parsed_HTML/{item.id}.html", 'w', encoding='utf-8') as f:
                children_iterator = list(soup.find('body').children)
                parents = parse(children_iterator)
                parents = identify_chapters(parents, item.id)
                book_title = extract_book(parents, item.id)
                parents = [x for x in parents if len(str(x)) > 100]
                any_bad_ones = [x for x in parents if len(str(x)) < 200]
                extract_chapters(parents, books[book_title])
                extract_special_node_names(parents, int(item.id.replace("chap", "")))
                combined_soup = BeautifulSoup('', 'html.parser')

                # Append each element to the container
                for element in parents:
                    combined_soup.append(element)
                f.write(str(combined_soup))
        elif item.id.startswith("fm") and 10 <= int(item.id.replace("fm", "").replace("a", "")) <= 18:
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            for a_tag in soup.find_all('a'):
                a_tag.unwrap()
            soup.find("div", {"class": "fmtitle"}).decompose()
            fm_text = bleach.clean(str(soup), tags=allowed_tags+['br'], strip=True)
            fm_text = [x for x in fm_text.splitlines() if x.strip() != ""]
            which_fm = int(item.id.replace("fm", "").replace("a", ""))-10
            which_fm = list(fms.keys())[which_fm]
            fm_text_dict[which_fm] = fm_text
    if item.get_type() == ebooklib.ITEM_IMAGE:
        # Get the image name and content
        image_name = os.path.basename(item.file_name)
        image_data = item.content
        with open(os.path.join(output_dir, image_name), 'wb') as image_file:
            image_file.write(image_data)


title = "The Torah; A Women's Commentary"
versionTitle = "CCAR Press / Women of Reform Judaism, 2008"
versionSource = "https://www.ccarpress.org/shopping_product_detail.asp?pid=50296"
versionNotes = "Editors: Tamara Cohn Eskenazi and Andrea L. Weiss"
for node in special_node_names:
    for parasha in special_node_names[node]:
        ref = f"{title}, {node}, {parasha}"
        send_text = {
            "text": remove_a_tags(special_node_names[node][parasha]),
            "versionTitle": versionTitle,
            "versionSource": versionSource,
            "versionNotes": versionNotes,
            "language": "en",
            "actualLanguage": "en",
            "languageFamilyName": "english",
            "isSource": False,
            "isPrimary": False,
            "direction": "ltr",
        }
        post_text(ref, send_text)
LinkSet({"generated_by": "ccar_to_torah"}).delete()
links = []
for book in ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]:
    book_dict = books[book]
    for chapter in book_dict:
        for verse in book_dict[chapter]:
            book_dict[chapter][verse] = parse_text(book_dict[chapter][verse])
            ref = f"{title}, {book} {chapter}:{verse}"
            for s, segment in enumerate(book_dict[chapter][verse]):
                links.append({"generated_by": "ccar_to_torah", "type": "commentary", "auto": True,
                              "refs": [f"{ref}:{s+1}", f"{book} {chapter}:{verse}"]})
            send_text = {
                "text": post_process(book_dict[chapter][verse]),
                "versionTitle": versionTitle,
                "versionSource": versionSource,
                "language": "en",
                "actualLanguage": "en",
                "languageFamilyName": "english",
                "isSource": False,
                "isPrimary": False,
                "direction": "ltr",
            }
            post_text(ref, send_text)

for fm in fm_text_dict:
    ref = f"{title}, {fm}"
    send_text = {
        "text": fm_text_dict[fm],
        "versionTitle": versionTitle,
        "versionSource": versionSource,
        "language": "en",
        "actualLanguage": "en",
        "languageFamilyName": "english",
        "isSource": False,
        "isPrimary": False,
        "direction": "ltr",
    }
    post_text(ref, send_text)
for l in links:
    try:
        Link(l).save()
    except:
        pass

for v in VersionSet({"title": "The Torah; A Women's Commentary"}):
    v.versionNotes = versionNotes
    v.purchaseInformationImage = "https://www.ccarpress.org/product_image.asp?id=4427&szType=4"
    v.purchaseInformationURL = "https://www.ccarpress.org/shopping_product_detail.asp?pid=50296"
    v.save()

from sefaria.helper.link import rebuild_links_from_text as rebuild
rebuild("The Torah; A Women's Commentary", 1)