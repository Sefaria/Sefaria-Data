from sources.functions import *
import ebooklib
from ebooklib import epub

book = epub.read_epub('yalkut.epub')
for item in book.get_items():
    if BeautifulSoup(item.content).find_all('section') != []:
        print(item)