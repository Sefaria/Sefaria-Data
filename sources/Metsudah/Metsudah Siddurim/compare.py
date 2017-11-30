import codecs
def get_ords_line(line):
    ords = []
    spaces = 0
    for i in range(len(line) / 2):
        start = i*2 - spaces
        end = i*2 + 2 - spaces
        if line[start] == " ":
            ords.append(u" ")
            spaces += 1
        else:
            char_to_add = line[start:end].decode('utf-8')
            ords.append(char_to_add)
    return ords

dgs = open("dgs.txt").read()
norm = open("norm.txt").read()
dgs_char_per_line = codecs.open("dgs_char_per_line.txt", 'w', encoding='utf-8')
norm_char_per_line = codecs.open("norm_char_per_line.txt", 'w', encoding='utf-8')
for char in get_ords_line(norm):
    norm_char_per_line.write(char+u"\n")
for char in get_ords_line(dgs):
    dgs_char_per_line.write(char+u"\n")

first_word_norm = norm.split(" ")[0]
first_word_dgs = dgs.split(" ")[0]
print len(first_word_norm)
print len(first_word_dgs)
for i, char in enumerate(first_word_norm):
    norm_char = ord(char)
    if len(first_word_dgs) > i:
        dgs_char = ord(first_word_dgs[i])
        print "{} vs {}".format(norm_char, dgs_char)
    else:
        print "{}".format(norm_char)

print "***************************"
# for string in [dgs, norm]:
#     for i in range(len(string) / 2):
#         print string[i*2:2+(i*2)]

