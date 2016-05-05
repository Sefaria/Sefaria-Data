__author__ = 'stevenkaplan'

import pdb

f = open("Choshen Mishpat/tur choshen mishpat.txt")
new_f = open("Choshen Mishpat/tur choshen mishpat2.txt",'w')
new_comment = ""
for line in f:
    if line.find('22') >= 0:
        if len(new_comment) > 0:
            new_f.write(new_comment+"\n")
            new_comment = ""
        new_comment += line.replace("\n","")
    else:
        new_comment += line.replace("\n", "")
f.close()
new_f.close()

