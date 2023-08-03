import sys
import regex as re

if __name__ == '__main__':
    num = int(sys.argv[1])
    i = 0
    buffer = ""
    with open('torah_cleaned.txt', 'r', encoding='utf8') as inf, \
        open('torah_output_letter_'+sys.argv[1]+'.txt', 'w+', encoding='utf8') as outf:
        while i < num:
            char = inf.read(1)
            buffer += char
            if len(buffer) > 50:
                buffer = buffer[1:]
            if re.match(r"[\u0590-\u05fe]", char):
                i += 1

        outf.write("Letter " + sys.argv[1] + ": " + char)
        outf.write("\n\n")
        outf.write("Previous letters in file:\n" + buffer[:-1])
        outf.write("\n\n")
        next_letters = inf.read(50)
        outf.write("Next letters:\n" + next_letters)
        outf.write("\n\n")
        outf.write("Context: \n" + buffer+next_letters)

