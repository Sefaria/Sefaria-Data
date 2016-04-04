"""
url for original files:
https://drive.google.com/drive/u/1/folders/0BwEntTcxGmMANFdVSGdJRS1hYzQ

Stripped out all footnotes. Footnote markers are in rectangular brackets.

Parsha names are all in caps - use str.upper to find them.

Book names are not clearly marked. A previous line can be indicated as a book name by the chapter number
resetting to 1.

Chapter numbers are listed as <digit><space>. Verse numbers are connected to words.

On every line called, call str.replace as follows:
% --when it follows a letter means that there should be a dot under that letter
@ --stands for "s" with a dot underneath.

A first run should strip out all footnote markers. Later on, a script should be run to map footnotes to
Book, chapter, verse.

"""


