# -*- coding: utf-8 -*-
__author__ = 'stevenkaplan'

if __name__ == "__main__":
    files = [open("yevamot_old.txt"), open("kiddushin_old.txt")]
    new_files = [open("yevamot.txt", 'w'), open("kiddushin.txt", 'w')]
    for i, file in enumerate(files):
        big_line = ""
        for line in file:
            if line.startswith('@11ע"ב'):
                assert len(big_line) > 0
                big_line += 'ע"ב'
            elif line.startswith("@00"):
                new_files[i].write(line)
            elif line.startswith("@11"):
                if len(big_line) > 0:
                    big_line = big_line.replace("\n", "") + "\n"
                    arr = []
                    while big_line.find("@11") != big_line.rfind("@11"):
                        end_pos = big_line.rfind("@11")
                        arr.append(big_line[end_pos:])
                        big_line = big_line[0:end_pos]
                    if len(arr) > 0:
                        arr = reversed(arr)
                    else:
                        arr.append(big_line)
                    for each_line in arr:

                        new_files[i].write(each_line)
                big_line = line
            else:
                big_line += line

        file.close()
        new_files[i].close()