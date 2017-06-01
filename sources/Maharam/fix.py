# -*- coding: utf-8 -*-

import re
import os
if __name__ == "__main__":
    files = [file.replace(".txt", "") for file in os.listdir(".") if not file.endswith("2.txt") and file.endswith(".txt")]
    files = ["avodah zarah"]
    running_line = ""
    lines = []
    for line in open("avodah zarah.txt"):
        line = line.replace("\n", "")
        if line.startswith("@11"):
            if len(running_line) > 0:
                lines.append(running_line)
            running_line = line
        else:
            running_line += line


    lines.append(running_line)

    print len(lines)
    new_f = open("avodah zarah2.txt", 'w')
    for line in lines:
        temp_result = line.split('@44ע"ב')
        assert len(temp_result) in [1, 2]
        if len(temp_result) == 1:
            new_f.write(line+"\n")
        else:
            new_f.write(temp_result[0]+"\n")
            new_f.write("@11 "+temp_result[1]+"\n")