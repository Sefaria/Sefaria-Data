import django
django.setup()

from bs4 import BeautifulSoup
import requests



# import statistics
import csv
from sefaria.model import *
from sefaria.helper.schema import insert_last_child
from sefaria.tracker import modify_bulk_text




if __name__ == '__main__':
    print("hello")
    # HTML From File
    with open("kuzari.html", "r") as f:
        doc = BeautifulSoup(f, "html.parser")

    tags =  doc.find_all('a', attrs={'name': lambda x: x and '_ftn' in x and 'ref' not in x})
    ps = []
    clean = []

    #tags.sort(key = lambda x:x.attrs["name"])
    for tag in tags:
        ps.append(tag.parent)

    for paragraph in ps:
        par_text = paragraph.get_text()
        start_from = par_text.find(']')
        clean.append(paragraph.get_text()[start_from+1:])


    index = 0
    for node in doc.find_all('a', attrs={'name': lambda x: x and '_ftnref' in x }):
        replacement1 = "<sup class='footnote-marker'>" + str(index+1) + "</sup>"
        replacement2 = "<i class='footnote'>" + clean[index] + "</i>"
        r = replacement1+replacement2
        node.replace_with(r)
        index+=1

a = str(doc)
print(doc.get_text())
with open('kuzari_formatted_footnotes.txt', 'w') as f:
    f.write(doc.get_text())


