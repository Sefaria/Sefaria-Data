import re
import django
django.setup()
from sefaria.model import *
if __name__ == "__main__":
    with open("lishkat hasofer.txt", 'r') as f:
        for line in f:
            perek = re.search("@9(.*?) ", line)
            verse = re.search("@1(.*?)@2", line)
            dh = re.search("@3(.*?)@4", line)
            comment = re.findall("@4.*?", line)[0]
            if perek:
                current_perek = perek.group(1)
                assert current_perek > prev_perek
                prev_perek = current_perek
            if verse:
                current_verse = verse.group(1)
                assert current_verse > prev_verse
                prev_verse = current_verse
            if dh:
                dh = dh.group(1)

