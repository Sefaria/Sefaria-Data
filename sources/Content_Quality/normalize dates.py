import django
django.setup()
from sefaria.model import *
from sefaria.system.database import db
from collections import defaultdict, Counter
from tqdm import tqdm
def is_num(x):
    if isinstance(x, dict):
        x = x.get('value')
    return x is not None and (isinstance(x, int) or x.isdigit())

def year_range_in_string(years_string):
    start, end = years_string.split('-')
    if len(end) < 4:
        end = start[:4 - len(end)] + end
    return [int(start), int(end)]


def parse_years(years_string):
    years = years_string.split('-')
    assert len(years) == 2
    if len(years) == 2:
        start = int(years[0])
        end_str = years[1]

        start_str = str(start)

        if len(end_str) < len(start_str):
            end = int(start_str[:-len(end_str)] + end_str)
        else:
            end = int(end_str)
        return [start, end]

def convert(x, error, o):
    if "," in x:
        x = x.replace(",", "-")
    x = x.replace("ca. ", "").replace("c. ", "")
    x = x.replace("1860s", "1860-1869").replace("1769-1670", "1769-1770")
    if x.endswith(" BCE"):
        x = "-"+x.split()[0]
    if error is not None:
        x = int(x)
        return [x-int(error), x+int(error)]

    if x.find("-") == 0 and x.rfind("-") == 0:
        return [-1 * int(x[1:])]
    elif x.find("-") >= 0:
        assert error is None
        x = parse_years(x)
        assert isinstance(x[0], int) and isinstance(x[1], int)
        assert x[0] <= x[1]
        if x[0] == x[1]:
            return [x[0]]
        return x
    else:
        return [int(x)]


def process(data, b, k, title_func, setter_func):
    temp = getattr(b, k, None) or getattr(b, 'properties', {}).get(k, {}).get('value', None)
    if isinstance(temp, list):
        return False
    elif temp:
        if is_num(temp):
            if isinstance(temp, int):
                data[k]['ints'] += 1
            elif temp.isdigit():
                data[k]['string ints'] += 1
            error = getattr(b, 'errorMargin', None)
            if k == 'compDate' and error:
                setter_func(b, k, [int(temp)-int(error), int(temp)+int(error)])
            else:
                setter_func(b, k, [int(temp)])
        else:
            error = getattr(b, 'errorMargin', None)
            if k != 'compDate':
                error = None
            new = convert(temp, error, b)
            data[k]["others"][title_func(b)] = temp
            setter_func(b, k, new)
        return True

def book_setter(o, k, v):
    setattr(o, k, v)

def topic_setter(o, k, v):
    curr = o.properties[k]
    curr['value'] = v


books = IndexSet()
authors = TopicSet({"subclass": 'author'})
book_data = defaultdict()
error_margins = {}
topic_data = defaultdict()
dropping_error_margin = False

for k in ['pubDate', 'compDate', 'errorMargin']:
    book_data[k] = {"ints": 0, "string ints": 0, "others": {}}
for b in tqdm(books):
    changed = False
    for k in ['pubDate', 'compDate', 'errorMargin']:
        changed = process(book_data, b, k, lambda x: x.title, book_setter) or changed
    if hasattr(b, 'errorMargin'):
        del b.errorMargin
        b.hasErrorMargin = True
        changed = True
    if changed:
        try:
            b.save(override_dependencies=True)
        except:
            print(b)

for k in ['birthYear', 'deathYear']:
    topic_data[k] = {"ints": 0, "string ints": 0, "others": {}}
for b in tqdm(authors):
    props = getattr(b, 'properties', {})
    if 'birthYear' in props:
        curr = b.properties['birthYear']['value']
        b.properties['birthYear']['value'] = int(curr)
    if 'deathYear' in props:
        curr = b.properties['deathYear']['value']
        b.properties['deathYear']['value'] = int(curr)
    b.save(override_dependencies=True)
