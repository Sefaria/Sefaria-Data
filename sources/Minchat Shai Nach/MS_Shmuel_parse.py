# -*- coding: utf-8 -*-
import sys
import os
# for a script located two directories below this file
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
from sources.functions import *
from sefaria.model import *
#here we can toggle if we're posting the index and text and the links
posting_index = True
posting_text = True
posting_links = True
en_books = ['I Samuel','II Samuel']
he_books = [u"שמואל א",u"שמואל ב"]
def get_parsed_text():
    with open('מנחת שי שמואל.txt') as myfile:
        lines = myfile.readlines()
    current_perek = 1
    current_pasuk = 1
    sefer_count = -1
    line_count = -1
    for ascii_line in lines:
        line_count+=1
        line = ascii_line.decode('utf-8')
        if u"@11א" in line:
            if sefer_count>=0:
                if posting_index:
                    print "posting "+en_books[sefer_count]+" index"
                    post_index_ms(sefer_count)
                if posting_text:
                    print "posting "+en_books[sefer_count]+" text"
                    post_text_ms(sefer_array,sefer_count)
                if posting_links:
                    print"posting "+en_books[sefer_count]+" links"
                    post_links_ms(sefer_array,sefer_count)
            sefer_count+=1
            current_perek = 1
            current_pasuk = 1
            sefer_array = make_perek_array(en_books[sefer_count])
        elif u"@11" in line:
            current_perek = getGematria(line)
            current_pasuk=0
        elif u"@22" in line:
            current_pasuk = getGematria(line)
        else:
            try:
                sefer_array[current_perek-1][current_pasuk-1].append(line)
            except Exception as e:
                print e.message
                print u"ERROR! "+str(current_perek)+" "+str(current_pasuk)+" "+he_books[sefer_count]+" "+en_books[sefer_count]
                print line
                print "line is "+str(line_count)
                print len(sefer_array)

    #post last text:
    if posting_index:
        print "posting "+en_books[sefer_count]+" index"
        post_index_ms(sefer_count)
    if posting_text:
        print "posting "+en_books[sefer_count]+" text"
        post_text_ms(sefer_array,sefer_count)
    if posting_links:
        print"posting "+en_books[sefer_count]+" links"
        post_links_ms(sefer_array,sefer_count)


def post_index_ms(sefer_count):
    # create index record
    ms_schema = JaggedArrayNode()
    ms_schema.add_title('Minchat Shai on '+en_books[sefer_count], 'en', primary=True)
    ms_schema.add_title(u"מנחת שי"+u" על "+he_books[sefer_count], 'he', primary=True)
    ms_schema.key = 'Minchat Shai on '+en_books[sefer_count]
    ms_schema.depth = 3
    ms_schema.addressTypes = ["Integer", "Integer", "Integer"]
    ms_schema.sectionNames = ["Chapter", "Verse", "Comment"]
    ms_schema.toc_zoom = 2
    ms_schema.validate()

    index = {
        "title": 'Minchat Shai on '+en_books[sefer_count],
        "categories":['Tanakh','Commentary','Minchat Shai'],
        "schema": ms_schema.serialize(),
        "base_text_titles": [en_books[sefer_count]],
        "dependence": "Commentary"
    }
    post_index(index,weak_network=True)
def post_text_ms(text_array, sefer_count):
    version = {
        'versionTitle': 'Minchat Shai',
        'versionSource': 'http://www.sefaria.org/',
        'language': 'he',
        'text': text_array
    }

    post_text('Minchat Shai on '+en_books[sefer_count], version,weak_network=True)
def post_links_ms(sefer_array, sefer_count):
    book = en_books[sefer_count]
    for perek_index,perek in enumerate(sefer_array):
        for pasuk_index, pasuk in enumerate(perek):
            for comment_index, comment in enumerate(pasuk):
                link = (
                        {
                        "refs": [
                                 'Minchat Shai on {}, {}:{}:{}'.format(book, perek_index+1, pasuk_index+1, comment_index+1),
                                 '{} {}:{}'.format(book,perek_index+1, pasuk_index+1),
                                 ],
                        "type": "commentary",
                        "auto": True,
                        "generated_by": "sterling_minchat_shai_"+book+"_parser"
                        })
                print link.get('refs')
                post_link(link, weak_network=True)
def make_perek_array(book):
    tc = TextChunk(Ref(book), "he")
    return_array = []
    for x in range(len(tc.text)):
        return_array.append([])
    for index, perek in enumerate(return_array):
        tc = TextChunk(Ref(book+" "+str(index+1)), "he")
        for x in range(len(tc.text)):
            return_array[index].append([])
    return return_array

def main():
    pass
if __name__ == "__main__":
    get_parsed_text()
    main()
"""
    if len(sefer_array[0][0])>1:
    for peindex, perek in enumerate(sefer_array):
    for paindex, pasuk in enumerate(perek):
    for cindex, comment in enumerate(pasuk):
    print str(peindex)+" "+str(paindex)+" "+comment
"""
