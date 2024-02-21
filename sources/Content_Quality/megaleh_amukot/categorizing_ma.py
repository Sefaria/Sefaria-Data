import django

django.setup()

from sefaria.model import *


ma = Index().load({'title': 'Megaleh Amukot on Torah'})
ma.dependence = "Commentary"
ma.base_text_titles = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]
ma.base_text_mapping = "many_to_one"
ma.save()