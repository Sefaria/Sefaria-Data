from bs4 import BeautifulSoup
from bs4.element import NavigableString

with open('/Users/joelbemis/Documents/programming/Sefaria-Data/sources/Shinan/test.html', 'r') as infile:
    soup = BeautifulSoup(infile, 'html5lib').body.p
new_soup = BeautifulSoup("<html><head></head><body><p></p></body></html>", "html5lib").body.p

for tag in soup.contents:
    print(tag)

for child in soup.contents:
    if isinstance(child, NavigableString):
        if child == u' ' or child == u'.':
            soup.contents[soup.index(child) - 1].append(child)

print("new_soup")
for tag in soup.contents:
    print(tag)
