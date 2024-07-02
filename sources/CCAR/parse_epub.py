from ebooklib import epub
import ebooklib
from bs4 import BeautifulSoup
from bs4 import Tag, NavigableString
import re
from sources.functions import *
import difflib

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
                    already_pasuk = re.search(r'^\d+:\d+', extract_text(node))
                    new_text = extract_text(node)
                    if match and already_pasuk is None:
                        new_text = new_text.replace(match.group(0), f"{chapter}:{match.group(0)}", 1)
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
                        br_tag = Tag(name='br')
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
                    if verse in book_dict[chapter]:
                        book_dict[chapter][verse].append(Tag(name="br"))
                        book_dict[chapter][verse].append(child)
                    else:
                        book_dict[chapter][verse] = child
                    for grandchild in child:
                        if grandchild.name == "div" and 'head' in str(grandchild.get('class', [])):
                            grandchild.append(Tag(name="br"))
                        if grandchild.name == "div" and 'head' not in str(grandchild.get('class', [])):
                            grandchild.append(Tag(name="br"))
                    for grandchild in child:
                        if grandchild.text == "Commentary":
                            grandchild.decompose()
                        if grandchild.text.strip == "":
                            grandchild.decompose()
    return book_dict

def extract_book(parents):
    #     for p in parshiot:
    #         if p in parents[0].text:
    #             found.append(book)
    print(parents[0].contents[-1].contents[-1].text)
    found = []
    parshiot = []
    for book in ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]:
        parshiot += [Term().load({"name": x["sharedTitle"]}).get_primary_title('en') for x in library.get_index(book).alt_structs["Parasha"]["nodes"]]
    closest_matches = difflib.get_close_matches(parents[0].contents[-1].contents[-1].text, parshiot, n=1, cutoff=0.0)
    if closest_matches:
        closest_match = closest_matches[0]
        for book in ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]:
            parshiot = [Term().load({"name": x["sharedTitle"]}).get_primary_title('en') for x in
                         library.get_index(book).alt_structs["Parasha"]["nodes"]]
            if closest_match in parshiot:
                return book
    return None


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
                parents = parse(soup.find('body').children)
                parents = identify_chapters(parents)
                book_title = extract_book(parents)
                extract_chapters(parents, books[book_title])
                combined_soup = BeautifulSoup('', 'html.parser')

                # Append each element to the container
                for element in parents:
                    combined_soup.append(element)
                f.write(str(combined_soup))
    if item.get_type() == ebooklib.ITEM_IMAGE:
        # Get the image name and content
        image_name = os.path.basename(item.file_name)
        image_data = item.content
        with open(os.path.join(output_dir, image_name), 'wb') as image_file:
            image_file.write(image_data)

for book in ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]:
    book_dict = books[book]
    for chapter in book_dict:
        for verse in book_dict[chapter]:
            book_dict[chapter][verse] = bleach.clean(str(book_dict[chapter][verse]), strip=True, tags=["i", "b", 'br']).replace("<br><br>", "<br>")