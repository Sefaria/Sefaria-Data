import django
django.setup()
from sefaria.model import *
import re
import csv

if __name__ == '__main__':

    with open('sheet.csv', newline='') as f:
        titles_from_sheet = [dict(zip(['slug', 'title', 'mark'], row)) for row in csv.reader(f)]

    for title_dict in titles_from_sheet:
        if title_dict['mark'] != 'disambiguated' and title_dict['mark'] != 'ignore':
            topic = Topic().load({'slug': title_dict['slug']})
            if not topic:
                continue
            for i, title in enumerate(topic.titles):
                title_text = title["text"]
                if title_text == title_dict['title'] and re.search(r"\((.+)\)$", title_text):
                    title_text = re.sub(r"\((.+)\)$", r'[\1]', title_text)
                    topic.titles[i]['text'] = title_text
                    topic.save()
                    print(title_text)