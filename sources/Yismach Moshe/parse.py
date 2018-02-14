# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
import re


if __name__ == "__main__":
    f = open("yismach moshe.txt")
    how_many_01 = 0
    sections = set()
    tags = set()
    for line in f:
        tags_in_line = re.findall("@\d+", line)
        for each_tag in tags_in_line:
            tags.add(each_tag)
        if "@01פתיחה" in line:
            line = line[line.find("@01פתיחה"):line.find("@02")]
            this_one = line.split(" ")[-1].split("/")[0]
            sections.add(this_one)

    for x in sections:
        print x
    print len(sections)
    print tags
