import django
django.setup()
from sefaria.model import *
from sefaria.model.schema import AbstractTitledObject


def add_titles():
    term: AbstractTitledObject = NonUniqueTerm.init('yerushalmi')
    term.add_title("Jerusalem", 'en')
    term.save()
    term: AbstractTitledObject = NonUniqueTerm.init('bavli')
    term.add_title("Babylonian", 'en')
    term.save()
    term: AbstractTitledObject = NonUniqueTerm.init('marriage')
    term.add_title("Relationships", 'en')
    term.save()
    term: AbstractTitledObject = NonUniqueTerm.init('chullin')
    term.add_title("Chulin", 'en')
    term.save()
# marriage => Relationships  #Mishneh Torah
# chullin => Chulin

if __name__ == '__main__':
    add_titles()
    index: Index = library.get_index("Jerusalem Talmud Yoma")
    match_templates = index.nodes.get_match_templates()
    for template in match_templates:
        terms: list[NonUniqueTerm] = template.get_terms()
        for term in terms:
            print(term.slug)
        print('---')

    print(term.get_titles())

    term = NonUniqueTerm.init('hilchot')
    print(term.get_titles())