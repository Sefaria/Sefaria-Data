import django
django.setup()
from sefaria.model import *

if __name__ == "__main__":
    with open("kohelet.tsv", 'w') as f:
        for line_n, line in enumerate(f):
