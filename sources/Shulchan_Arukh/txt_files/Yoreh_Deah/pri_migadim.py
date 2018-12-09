# encoding=utf-8

import re
import os
import codecs
from data_utilities.util import ja_to_xml
from data_utilities.util import getGematria, PlaceHolder, convert_dict_to_array

with codecs.open(u'./part_1/שולחן ערוך יורה דעה חלק א משבצות זהב.txt', 'r', 'utf-8') as fp:
    my_lines = fp.readlines()

siman, seif = None, 0
holder = PlaceHolder()
for line in my_lines:
    if holder(re.search(u'@22([\u05d0-\u05ea]{1,2})', line)):
        siman, seif = getGematria(holder.group(1)), 0
    elif holder(re.search(u'@44\(([\u05d0-\u05ea]{1,2})\)', line)):
        new_seif = getGematria(holder.group(1))
        if new_seif - seif != 1:
            print "Siman {}: Jump from seif {} to {}".format(siman, seif, new_seif)
        seif = new_seif

del seif

mishbetzot = list()
chapter, seif = None, None
chap_num, seif_num = -1, -1

holder = PlaceHolder()
for line in my_lines:
    if holder(re.search(u'@22([\u05d0-\u05ea]{1,2})', line)):
        if chapter is not None:
            if seif is not None:
                chapter[seif_num - 1] = seif
            mishbetzot.append(convert_dict_to_array(chapter, default_value=list))
        chapter, chap_num = dict(), getGematria(holder.group(1))
        seif, seif_num = None, -1

    elif holder(re.search(u'@44\(([\u05d0-\u05ea]{1,2})\)', line)):
        if seif is not None:
            chapter[seif_num - 1] = seif
        seif, seif_num = list(), getGematria(holder.group(1))

    else:
        assert re.match(u'^@11', line) is not None
        fixed_line = re.sub(u'@11([^@]+)@33', u'<b>\g<1></b>', line)
        fixed_line = re.sub(u'@66[\[(]#[\])]', u'', fixed_line)
        fixed_line = re.sub(u'@\d{2}', u'', fixed_line)
        fixed_line = re.sub(u' {2,}', u' ', fixed_line)
        fixed_line = re.sub(u'^ +| +$', u'', fixed_line)
        seif.append(fixed_line)
chapter[seif_num - 1] = seif
mishbetzot.append(convert_dict_to_array(chapter, default_value=list))

with codecs.open(u'./part_2/משבצות זהב  יורה דעה חלק ב.txt', 'r', 'utf-8') as fp:
    my_lines = fp.readlines()

siman, seif = None, 0
holder = PlaceHolder()
for line in my_lines:
    if holder(re.search(u'@22([\u05d0-\u05ea]{1,3})', line)):
        siman, seif = getGematria(holder.group(1)), 0

    elif holder(re.search(u'@11\(([\u05d0-\u05ea]{1,2})\)', line)):
        new_seif = getGematria(holder.group(1))
        if new_seif - seif != 1:
            print "Siman {}: Jump from seif {} to {}".format(siman, seif, new_seif)
        seif = new_seif
del chapter, chap_num, seif_num, seif

chapter, seif = None, None
chap_num, seif_num = -1, -1

for line in my_lines:
    if holder(re.search(u'@22([\u05d0-\u05ea]{1,3})', line)):
        if chapter is not None:
            if seif is not None:
                chapter[seif_num - 1] = seif
            mishbetzot.append(convert_dict_to_array(chapter, default_value=list))
        chapter, chap_num = dict(), getGematria(holder.group(1))
        seif, seif_num = None, -1

    elif holder(re.search(u'@11\(([\u05d0-\u05ea]{1,2})\)', line)):
        if seif is not None:
            chapter[seif_num - 1] = seif
        seif, seif_num = list(), getGematria(holder.group(1))

    if re.match(u'^@11', line):
        fixed_line = re.sub(u'@11\(([\u05d0-\u05ea]{1,2})\)', u'@11', line)
        fixed_line = re.sub(u'@11\s?([^@]+)@33', u'<b>\g<1></b>', fixed_line)
        fixed_line = re.sub(u'\(#\)', u'', fixed_line)
        fixed_line = re.sub(u'@\d{2}', u'', fixed_line)
        fixed_line = re.sub(u' {2,}', u' ', fixed_line)
        fixed_line = re.sub(u'^ +| +$', u'', fixed_line)
        seif.append(fixed_line)
chapter[seif_num - 1] = seif
mishbetzot.append(convert_dict_to_array(chapter, default_value=list))

with codecs.open(u'./part_3/‏‏פרי מגדים משבצות זהב שולחן ערוך יורה דעה חלק ג.txt', 'r', 'utf-8') as fp:
    my_lines = fp.readlines()

for line in my_lines:
    if holder(re.search(u'@22([\u05d0-\u05ea]{3})', line)):
        chapter, chap_num = list(), getGematria(holder.group(1))

    elif re.match(u'^@11', line):
        fixed_line = re.sub(u'^@11[^@]+@33\s*', u'', line)
        fixed_line = re.sub(u'^[^\s]+', u'<b>\g<0></b>', fixed_line)
        fixed_line = re.sub(u' {2,}', u' ', fixed_line)
        fixed_line = re.sub(u'^ +| +$', u'', fixed_line)
        chapter.append([fixed_line])
mishbetzot.append(chapter)

ja_to_xml(mishbetzot, ['Siman', 'Seif', 'Paragraph'])
