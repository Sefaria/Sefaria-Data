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


yad_ramah = function.parse('yad_ramah.txt')
index = function.create_index()
text = function.create_text(yad_ramah)


hello = codecs.open("hello.txt", 'w', 'utf-8')
util.jagged_array_to_file(hello, yad_ramah,['Page', 'Comment'])
hello.close()