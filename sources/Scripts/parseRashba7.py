# -*- coding: utf-8 -*-
import codecs
import regex
from data_utilities import util


def parse(file1):
    line_with_siman_number = regex.compile(u'\u05e1\u05d9\u05de\u05df\s([\u05d0-\u05ea]{1,5})')

    rashba_section_seven = []
    second_level_list = []
    first_time = True
    siman_number, count = 0, 1

    with codecs.open(file1, 'r', 'utf-8') as the_file:
        for each_line in the_file:

            each_line = each_line.strip()
            search_object = line_with_siman_number.match(each_line)


            if search_object:
                if not first_time:
                    while siman_number > count:
                        rashba_section_seven.append([])
                        count += 1

                    rashba_section_seven.append(second_level_list)
                    count += 1
                    second_level_list = []

                siman_number = util.getGematria(search_object.group(1))
                first_time = False

            elif not each_line:
                continue

            else:
                each_line = each_line.strip( '+' )
                second_level_list.append(each_line)

        while siman_number > count:
            rashba_section_seven.append(None)
            count += 1

        rashba_section_seven.append(second_level_list)
    return rashba_section_seven


rashba_section_seven = parse('rashba7.txt')

hello = codecs.open('hello.txt', 'w', 'utf-8')
util.jagged_array_to_file(hello,rashba_section_seven,('Siman', 'Text'))
hello.close()