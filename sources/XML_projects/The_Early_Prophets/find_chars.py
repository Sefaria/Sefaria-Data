from sources.functions import *
chars = set()
with open("The_Early_Prophets.xml", 'r', errors='surrogateescape') as f:
    for line in f:
        for x in re.findall("&#[A-Za-z\d]+;", line):
            chars.add(x)
print(chars)