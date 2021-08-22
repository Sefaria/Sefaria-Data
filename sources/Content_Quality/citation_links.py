import django
django.setup()
from sefaria.model import *
import sys

cat = sys.argv[1]       # "Bavli"
kind = sys.argv[2]      # "category" or "collective"
uid = int(sys.argv[3])  # user id
titles = library.get_indexes_in_category(cat) if kind == "category" else library.get_indices_by_collective_title(cat)
for title in titles:
	indx = library.get_index(title)
	from sefaria.helper.link import rebuild_links_from_text as rebuild
	rebuild(title, uid)
