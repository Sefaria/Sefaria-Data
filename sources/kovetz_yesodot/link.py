import csv

import django
django.setup()
from sefaria.model import *
from sefaria.system.exceptions import DuplicateRecordError
from linking_utilities.citation_disambiguator.citation_disambiguator import CitationDisambiguator, count_words
import regex

count_words('he', False)
cd = CitationDisambiguator('he', 'Kovetz Yesodot VaChakirot')
links = []
table = []
i=0
counter = {}
X=[]
lang = 'he'
for le in LexiconEntrySet({ 'parent_lexicon' : 'Kovetz Yesodot VaChakirot' }):
    ref = Ref(f'Kovetz Yesodot VaChakirot, {le.headword} 1')
    for key, value in le.content.items():
        for t, text in enumerate(value):
            unique_titles = set(library.get_titles_in_string(text, lang))
            refs_from_string_to_save = []
            for title in unique_titles:
                refs_from_string = library._internal_ref_from_string(title, text, lang, return_locations=True)
                if not refs_from_string:
                    continue
                for linked_oref, indexes in refs_from_string:
                    if linked_oref.is_talmud():
                        main_text = ref.text('he')
                        main_text.text = text[:indexes[1]+1]
                        main_text.vtitle = ''
                        good, bad = cd.disambiguate_one(ref, main_text, linked_oref, snip_only_before=True)
                        result_len = len(good+bad)
                        counter[result_len] = counter.get(result_len, 0) + 1
                        if not result_len:
                            table.append({
                                'headword': le.headword,
                                'snippet': linked_oref.normal(),
                            })
                        for result in good+bad:
                            table.append({
                                'headword': le.headword,
                                'snippet': result['Snippet'],
                                'quoted ref': result['Quoted Ref'],
                                'quoted text': Ref(result['Quoted Ref']).text('he').text,
                                'good': 'good' if result in good else 'bad',
                                'score': result['Score']
                            })
                        if good:
                            linked_oref = Ref(max(good, key= lambda x: x['Quoted Ref'])['Quoted Ref'])
                        else:
                            continue
                    elif linked_oref.index.categories[0] != 'Tanakh' and 'Shulchan Arukh' not in linked_oref.normal() and not linked_oref.normal().startswith('Jerusalem Talmud'):
                        print(55555, ref, linked_oref)

                    link = Link({
                        "refs": [ref.normal().replace('<d>', ''), linked_oref.normal()],
                        "type": "",
                        "auto": True,
                        "generated_by": "kovetz_yesodot_links_from_text",
                        "inline_citation": True
                    })
                    refs_from_string_to_save.append((indexes, linked_oref))

                    try:
                        link.save()
                        i+=1
                    except DuplicateRecordError:
                        pass
                    except IndexError as e:
                        print(111, linked_oref)

            if refs_from_string_to_save:
                new = ''
                start = 0
                for indexes, linked_oref in refs_from_string_to_save:
                    new += text[start:indexes[0]] + f'<a class ="refLink" href="/{linked_oref.url()}" data-ref="{linked_oref.normal()}">{text[indexes[0]:indexes[1]]}</a>'
                    start = indexes[1]
                new += text[indexes[1]:]
                le.content[key][t] = new

    le.save()

print(i)
print(X)
print(counter)

with open('links.csv', 'w') as fp:
    w = csv.DictWriter(fp, fieldnames=['headword', 'snippet', 'quoted ref', 'quoted text', 'good', 'score'])
    w.writeheader()
    for row in table:
        w.writerow(row)
