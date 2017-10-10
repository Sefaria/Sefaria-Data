# -*- coding: utf-8 -*-

from data_utilities import *
import os
import regex as re
import codecs

"""
p = re.compile(u"@(11|33)" + u"([^@]+)" + u"@(22|44)")

with open('Maaseh Rokeah.txt') as f:
    l = 0
    n = 0
    for line in f:
        l += 1
        for m in p.finditer(line):
            n += 1
            print "#" + str(n)
            print "Line: " + str(l)
            print m.group(2)

exit()
"""

folder = u'./Maaseh Rokeah'


### Delete any old output

for the_file in os.listdir(folder):
    file_path = os.path.join(folder, the_file)
    try:
        if os.path.isfile(file_path):
            os.unlink(file_path)
    except Exception as e:
        print(e)


### Normalize lines - write to new file

split_pattern = re.compile(u"(\s*@(?:11|33)" + u"(?:[^@]+)" + u"@(?:22|44)\s*)")

with codecs.open('Maaseh Rokeah.txt', "r", "utf-8") as f:
    with codecs.open('Maaseh Rokeah - Split.txt', "w", "utf-8") as fout:
        for line in f:
            lines = split_pattern.split(line)
            for l in lines:
                if l:
                    fout.write(l.strip())
                    fout.write("\n")


### Split file into sections

buf = []
buf_has_content = False
file_count = 0
section_name = ""
book_name = ""
book_pattern = re.compile(u"@11" + u"([^@]+)" + u"@22")
halacha_pattern = re.compile(u"@33" + u"([^@]+)" + u"@44")


def write_buf(buf, file_count, book_name, section_name):
    if not len(buf):
        return

    filename = u"{}/{}-{}-{}.txt".format(folder, file_count, book_name, section_name)

    # @55 / @66 - chapter
    # @77 / @88 - halacha
    # @05 Starts dibur hamatchil - may be multiple before @06
    # @06 Ends dibur hamatchil, begins comment body

    with codecs.open(filename, 'w', "utf-8") as fout:

        clean_50s = re.compile(ur"@05([^6]*)@06")
        split_pattern = re.compile(ur"(\s*@(?:55|77)" + u"(?:[^@]+)" + u"@(?:66|88)\s*)")

        for line in buf:
            newline = clean_50s.sub(lambda x: u"\n@05" + x.group(1).replace(u"@05", u"") + u"@06", line)
            lines = split_pattern.split(newline)
            for l in lines:
                if l:
                    fout.write(l.strip())
                    fout.write("\n")



with codecs.open('Maaseh Rokeah - Split.txt','r',"utf-8") as f:
    for line in f:
        mb = book_pattern.search(line)
        mh = halacha_pattern.search(line)

        if mb:
            if buf_has_content:
                file_count += 1
                write_buf(buf, file_count, book_name, section_name)
                buf = []
                buf_has_content = False
            book_name = mb.group(1)
            buf += [line]
            continue

        if mh:
            if buf_has_content:
                file_count += 1
                write_buf(buf, file_count, book_name, section_name)
                buf = []
                buf_has_content = False
            section_name = mh.group(1)
            buf += [line]
            continue

        if line != "\n":
            buf += [line]
            buf_has_content = True

file_count += 1
write_buf(buf, file_count, book_name, section_name)


