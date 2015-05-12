__author__ = 'eliav'
import os

if __name__ == '__main__':
    fuzz_partial = 50
    for i in range(50,85):
        segment = 15
        ratio = 50
        fuzz_partial +=2
        for j in range(50,86):
            segment = 15
            ratio +=2
            for k in range(15,40):
                segment +=1
                os.system("connect-mishnah.py {} {} {}".format(fuzz_partial, ratio ,segment))
                #print "connect-mishnah.py {} {} {}".format(fuzz_partial, ratio ,segment)


