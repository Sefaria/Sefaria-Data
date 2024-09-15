from ebooklib import epub
import ebooklib
from bs4 import BeautifulSoup
from bs4 import Tag, NavigableString
import re
from sources.functions import *
import difflib
allowed_tags = {'i', 'b', 'u', 'small', 'a'}
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

def extract_text(element):
   if isinstance(element, NavigableString):
       return str(element)
   elif element is not None and hasattr(element, 'get_text'):
       return element.get_text()
   return ''
def identify_chapters(parents):
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
                    match = re.search(r'^(\d+)', extract_text(node))
                    already_pasuk = re.search(r'^(\d+):(\d+)', extract_text(node))
                    new_text = extract_text(node)
                    if match and already_pasuk is None:
                        new_text = new_text.replace(match.group(0), f"{chapter}:{match.group(0)}", 1)
                    else:
                        chapter = int(already_pasuk.group(1))
                    new_node = Tag(name="b")
                    new_node.string = new_text
                    node.replace_with(new_node)
                    if '–' in new_text:
                        child.attrs["orig_ref"] = new_text.replace(".", "")
                        new_node.string = new_text.split('–')[0]+"."


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
                        if isinstance(prev_child.contents[-1], NavigableString) or prev_child.contents[-1].name != 'br':
                            prev_child.append(br_tag)
                        for x in list(child.children):
                            prev_child.append(x)
                        child.string = ""
                    else:
                        prepend.append(child)
                else:
                    verse_and_chapter = re.search(r'^(\d+:\d+)', child.text).group(0)
                    child.contents[0].string = child.contents[0].text.replace(verse_and_chapter+'. ', '', 1)
                    child.contents[0].string = child.contents[0].text.replace(verse_and_chapter+'.', '', 1)
                    child.contents[0].string = child.contents[0].text.replace(verse_and_chapter, '', 1).strip()

                    child.attrs["ref"] = verse_and_chapter
                    if len(prepend) > 0:
                        for i, x in enumerate(prepend):
                            child.insert(i, x)
                            diff -= 1
                        prepend = []
                    found_verse = True

            for x in parent.find_all("div", {"class": "tab-en1"}):
                if x.text.strip() == "":
                    x.decompose()
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

def extract_book(parents):
    #     for p in parshiot:
    #         if p in parents[0].text:
    #             found.append(book)
    global parshiot
    p = parents[0].contents[-1].contents[-1].text.replace("Sh’lach L’cha", "Sh'lach")
    print(p)
    found = []
    closest_matches = difflib.get_close_matches(p, parshiot, n=1, cutoff=0.0)
    if closest_matches:
        closest_match = closest_matches[0]
        for book in ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]:
            book_parshiot = [Term().load({"name": x["sharedTitle"]}).get_primary_title('en') for x in
                         library.get_index(book).alt_structs["Parasha"]["nodes"]]
            if closest_match in book_parshiot:
                return book
    return None

def extract_special_node_names(parents, chap_num):
    global special_node_names
    global parshiot
    special_node_parents = [x for x in parents if x.attrs['class'] != ['note'] and len(x.contents) > 7]
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
            copy_child = BeautifulSoup(str(child), 'html.parser').find(child.name)
            special_node_names["Parashah Introductions"][parshiot[chap_num - 1]].append(copy_child)

    for key in special_node_names:
        special_node_names[key][parshiot[chap_num - 1]] = parse_text(special_node_names[key][parshiot[chap_num - 1]],
                                                                             special_node=True)

def parse_text(node, special_node=False):
    segments = []
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
for item in book_file.get_items():
    if item.get_type() == ebooklib.ITEM_DOCUMENT:
        # Use BeautifulSoup to parse HTML
        soup = BeautifulSoup(item.get_content(), 'html.parser')
        # with open(f"{item.id}.html", 'w', encoding='utf-8') as f:
        #     f.write(soup.prettify())
        if 'chap' in item.id:
            for span in soup.find_all('span'):
                txt = span.get_text()
                span.replace_with(txt)
            for a_tag in soup.find_all('a'):
                txt = a_tag.get_text()
                a_tag.replace_with(txt)
            with open(f"parsed_HTML/{item.id}.html", 'w', encoding='utf-8') as f:
                children_iterator = soup.find('body').children
                parents = parse(children_iterator)
                parents = identify_chapters(parents)
                book_title = extract_book(parents)
                print(book_title)
                parents = [x for x in parents if len(x.contents) > 4]
                extract_chapters(parents, books[book_title])
                extract_special_node_names(parents, int(item.id.replace("chap", "")))
                combined_soup = BeautifulSoup('', 'html.parser')

                # Append each element to the container
                for element in parents:
                    combined_soup.append(element)
                f.write(str(combined_soup))
        elif item.id.startswith("fm") and 10 <= int(item.id.replace("fm", "").replace("a", "")) <= 18:
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            soup.find("div", {"class": "fmtitle"}).decompose()
            for br in soup.find_all('br'):
                br.append("\n")
            fm_text = bleach.clean(str(soup), tags=["i", "b", "u", "small"], strip=True)
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
versionTitle = "CCAR Press / Women of Reform Judaism 2008"
versionSource = "https://www.ccarpress.org/shopping_product_detail.asp?pid=50296"
for node in special_node_names:
    for parasha in special_node_names[node]:
        ref = f"{title}, {node}, {parasha}"
        send_text = {
            "text": special_node_names[node][parasha],
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
                "text": book_dict[chapter][verse],
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