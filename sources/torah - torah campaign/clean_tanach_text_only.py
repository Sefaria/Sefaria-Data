import regex as re

"""
Takes tanakh text as input and removes any text between brackets []
"""

if __name__ == '__main__':
    with open('torah.txt', 'r', encoding='utf8') as inf, \
            open('torah_cleaned.txt', 'w+', encoding='utf8') as outf:
        for line in inf:
            # for letter in line:
            if line.strip():
                cleaned = re.sub(r"\[[\u0590-\u05fe ]+\]", "", line)
                outf.write(cleaned)
