from ebooklib import epub
import ebooklib
from bs4 import BeautifulSoup
from bs4 import Tag, NavigableString
import re

def remove_unwanted_tags(soup_element):
    # List of allowed tags
    allowed_tags = {'i', 'b', 'u', 'small', 'img', 'a'}

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

def identify_chapters(parents):
    for parent in parents:
        classes = str(parent.get('class', []))
        chapter = -1
        if 'note' in classes:
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
                    for node in child:
                        if isinstance(node, Tag) and node.name in ['b', 'i']:
                            match = re.search(r'^(\d+)', node.text)
                            already_pasuk = re.search(r'^\d+:\d+', node.text)
                            if match and already_pasuk is None:
                                node.string = node.text.replace(match.group(0), f"{chapter}:{match.group(0)}", 1)
                # elif re.search("<b><i>\D+</i></b>", str(child)):
            found_verse = False
            prepend = []
            for c, child in enumerate(parent.children):
                if re.search(r'^(\d+)', child.text) is None:
                    if found_verse:
                        br_tag = Tag(name='br')
                        prev_child_num = 1
                        prev_child = parent.contents[c - prev_child_num]
                        while prev_child.text == "":
                            prev_child_num += 1
                            prev_child = parent.contents[c - prev_child_num]
                        parent.contents[c - prev_child_num].append(br_tag)
                        for x in list(child.children):
                            parent.contents[c - prev_child_num].append(x)
                        child.string = ""
                    else:
                        prepend.append(child)
                else:
                    if len(prepend) > 0:
                        for i, x in enumerate(prepend):
                            child.insert(i, x)
                        prepend = []
                    found_verse = True



    return parents



# Read the ePUB file
book = epub.read_epub('ISBN_9780881232837.epub')

# Store extracted text
text_content = []
import os
output_dir = 'images'
if not os.path.exists(output_dir):
    os.mkdir(output_dir)
# Iterate over each item in the book
for item in book.get_items():
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
                combined_soup = BeautifulSoup('', 'html.parser')

                # Append each element to the container
                for element in parents:
                    combined_soup.append(element)
                f.write(combined_soup.prettify())
    if item.get_type() == ebooklib.ITEM_IMAGE:
        # Get the image name and content
        image_name = os.path.basename(item.file_name)
        image_data = item.content
        with open(os.path.join(output_dir, image_name), 'wb') as image_file:
            image_file.write(image_data)