__author__ = 'stevenkaplan'


if __name__ == "__main__":
    f = open("footnotes")
    n = open("footnotes_new.txt", 'w')
    for line in f:
        if line.find("<italic>Page") >= 0:
            line = line.replace("</p>", "")
        else:
            line = line.replace("<p>", "")
        n.write(line)