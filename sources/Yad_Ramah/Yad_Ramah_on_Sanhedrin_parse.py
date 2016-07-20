"""
parse the text
create links
create index
clean the parse
create text
post
"""
import codecs
import regex
from sefaria.model import *
from data_utilities import util
from sources.Yad_Ramah import function
from sources import functions


sanhedrin_ja = TextChunk(Ref('Sanhedrin'), 'he').text
yad_ramah = function.parse('yad_ramah.txt')
yad_ramah = util.clean_jagged_array(yad_ramah, ['(@22)', '(@100)'])
index = function.create_index()
text = function.create_text(yad_ramah)
links = function.create_links(sanhedrin_ja, yad_ramah)
functions.post_index(index)
functions.post_text('Yad Ramah on Sanhedrin', text)
functions.post_link(links)



# hello = codecs.open("hello.txt", 'w', 'utf-8')
# util.jagged_array_to_file(hello, yad_ramah,['Page', 'Comment'])
# hello.close()