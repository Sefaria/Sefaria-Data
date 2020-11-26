# encoding=utf-8

import re
import json
import django
from urllib import parse
django.setup()
from sefaria.model import *
from sefaria.model import manuscript
from pymongo.errors import DuplicateKeyError
from sources.NLI.munich import get_rows_from_db
from sefaria.system.exceptions import InputError

MANUSCRIPT_DATA = {
    'Kaufmann Manuscript': {
        'title': 'Kaufmann Manuscript',
        'he_title': 'כתב יד קאופמן',
        'source': 'http://kaufmann.mtak.hu/en/study04.htm',
        'description': '',
        'he_description': '',
    },
    'Leningrad Codex': {
        'title': 'Leningrad Codex',
        'he_title': 'כתב יד לנינגרד',
        'source': 'https://www.tanach.us/',
        'description': '',
        'he_description': '',
    },
    'Munich Manuscript': {
        'title': 'Munich Manuscript',
        'he_title': 'כתב יד מינכן',
        'source': 'https://www.digitale-sammlungen.de//',
        'description': '',
        'he_description': '',
    },
    'Vienna Manuscript': {
        'title': 'Vienna Manuscript',
        'he_title': 'כתב יד וינה',
        'source': 'check',
        'description': '',
        'he_description': '',
    },
    'Bomberg Pressing': {
        'title': '1523 Bomberg (Venice) Pressing',
        'he_title': 'דפוס בומברג (ונציה) 1523',
        'source': 'check',
        'description': '',
        'he_description': ''
    },
    'Vilna Pressing': {
        'title': 'Romm Vilna Pressing',
        'he_title': 'דפוס וילנא של האלמנה והאחים ראם',
        'source': 'check',
        'description': '',
        'he_description': '',
    },
}


def is_rangeable(ref_list):
    try:
        first, last = Ref(ref_list[0]), Ref(ref_list[-1])
    except InputError:
        return False
    if first.book == last.book:
        try:
            first.to(last)
            return True
        except AssertionError:
            return False


def find_first_range(ref_list) -> int:
    """
    :return: index where max range can be found from the first ref
    """
    loc = 1
    while is_rangeable(ref_list[0:loc+1]):
        if loc + 1 >= len(ref_list):
            return len(ref_list)
        loc += 1

    return loc


def find_ranges(ref_list):
    start, ranges = 0, []
    while start < len(ref_list):
        end = start + find_first_range(ref_list[start:])
        ranges.append(Ref(ref_list[start]).to(Ref(ref_list[end-1])))
        start = end
    return ranges


def create_manuscript(title, manuscript_data):
    mongo_manuscript = manuscript.Manuscript().load({'title': title})
    if mongo_manuscript is not None:
        print(f'{title} exists, doing nothing')
        return
    mongo_manuscript = manuscript.Manuscript().load_from_dict(manuscript_data)
    mongo_manuscript.save()
    print(f'{title} created successfully')


def create_kaufmann():
    title = 'Kaufmann Manuscript'
    k_man = manuscript.Manuscript().load({'title': title})
    if k_man is not None:
        print('Kaufmann Manuscript exists, doing nothing')
        return

    data = {
        'title': title,
        'he_title': 'כתב יד קאופמן',
        'source': 'http://kaufmann.mtak.hu/en/study04.htm',
        'description': '',
        'he_description': ''
    }
    k_man = manuscript.Manuscript().load_from_dict(data)
    k_man.save()
    print('Kaufmann Manuscript created successfully')


def create_kaufmann_page(page_json):
    data = {
        'manuscript_slug': manuscript.ManuscriptPage.get_slug_for_title('Kaufmann Manuscript'),
        'page_id': re.match(r'^(.*)-large\.jpg', page_json['image_content']).group(1),
        'image_url': page_json['image_url'],
        'thumbnail_url': re.sub(r'large\.jpg$', 'large_thumbnail.jpg', page_json['image_url']),
        'contained_refs': [r.normal() for r in find_ranges(page_json['expanded_refs'])],
        'expanded_refs': page_json['expanded_refs'],
    }
    page = manuscript.ManuscriptPage().load_from_dict(data)
    page.save()


def import_kaufmann():
    with open('kaufman_filemap.json') as fp:
        kaufmann = json.load(fp)

    expanded_only = [k['expanded_refs'] for k in kaufmann]
    problems = [e for e in expanded_only if not is_rangeable(e)]
    print(f'We have {len(problems)} problematic manuscripts')
    # print(problems[0])
    # first_range = find_first_range(problems[0])
    find_ranges(problems[2])
    for i, p in enumerate(problems):
        print(i, p, find_ranges(p), '\n', sep='\n')
    print(find_ranges(expanded_only[0]))
    print(kaufmann[0])
    for i, k in enumerate(kaufmann):
        if i % 20 == 0:
            print(i)
        create_kaufmann_page(k)


def create_leningrad():
    title = 'Leningrad Codex'
    create_manuscript(title, MANUSCRIPT_DATA[title])

    with open('Leningrad_map.json') as fp:
        leningrad = json.load(fp)

    url_prefix = 'https://storage.googleapis.com/sefaria-manuscripts/Leningrad'
    for i, (page, ref_range) in enumerate(leningrad.items()):
        if i % 25 == 0:
            print(f'{i} / {len(leningrad)}')
        data = {
            'manuscript_slug': manuscript.ManuscriptPage.get_slug_for_title(title),
            'page_id': page.replace(".jpg", ""),
            'image_url': f'{url_prefix}/{page}',
            'thumbnail_url': f'{url_prefix}/{page.replace(".jpg", "_thumbnail.jpg")}',
        }
        page_obj = manuscript.ManuscriptPage().load_from_dict(data)
        for tref in ref_range.split('; '):
            page_obj.add_ref(tref)
        page_obj.save()


def create_munich():
    """
    keep logic for url derivation
    convert munich_filemap from a list to dict with <image_file> as key
    html_map = get_rows_from_db()
    get tref, url_list from html_map
    for each url, derive manuscript, image_number & filename
    from filename, load the page data from the json

    :return:
    """
    def get_page_for_manuscript(number, page_url):
        if number == 6:
            parsed = parse.urlparse(page_url)
            query = parse.parse_qs(parsed.query)
            return query['seite'][0]
        else:
            return re.search('image_([0-9]+)$', page_url).group(1)

    with open('munich_filemap.json') as fp:
        munich_data_list = json.load(fp)
    url_prefix = 'https://storage.googleapis.com/sefaria-manuscripts/munich-manuscript'
    munich_filemap = {page['image_file']: page for page in munich_data_list}
    print(next(iter(munich_filemap.keys())))

    manuscript_mapper = {
        6569: 6,
        3409: 95,
        6568: 140,
        6547: 141,
    }
    manuscript_json = MANUSCRIPT_DATA['Munich Manuscript']
    for n in manuscript_mapper.values():
        manuscript_json['title'] = f'Munich Manuscript {n}'
        manuscript_json['he_title'] = f'כתב יד מינכן {n}'
        create_manuscript(f'Munich Manuscript {n}', manuscript_json)

    bizzarre = []
    for item, (tref, url_list) in enumerate(get_rows_from_db().items()):
        if item % 200 == 0:
            print(item)
        for i, url in enumerate(url_list):
            filename = f'munich_images/{tref}.jpg' if i == 0 else f'munich_images/{tref}({"I"*i}).jpg'
            manuscript_hint = re.match(r'^http://daten.digitale-sammlungen.de/([^/]+)/', url).group(1)
            manuscript_number = int(re.search(r'0*([0-9]+)$', manuscript_hint).group(1))
            manuscript_number = manuscript_mapper[manuscript_number]
            slug = manuscript.ManuscriptPage.get_slug_for_title(f'Munich Manuscript {manuscript_number}')
            storage_url = filename.replace("munich_images", url_prefix)
            try:
                page_json = munich_filemap[filename]
            except KeyError as e:
                bizzarre.append(filename)
                continue
                # tractate = re.search(r'munich_images/([^\s]+\s[0-9])', filename)
                # if not tractate:
                #     print('debug statement insufficient')
                # close_keys = [k for k in munich_filemap.keys() if tractate.group(1) in k]
                # print(f'near matches to key {filename}:', *close_keys, sep='\n')
                # manuscript.ManuscriptPageSet({'manuscript_slug': {'$regex': 'munich.*'}}).delete()
                # raise e
            data = {
                'manuscript_slug': slug,
                'page_id': f'Cod. hebr. {manuscript_number} pg. {get_page_for_manuscript(manuscript_number, url)}',
                'image_url': storage_url,
                'thumbnail_url': storage_url.replace('.jpg', '_thumbnail.jpg'),
            }
            page_obj = manuscript.ManuscriptPage().load_from_dict(data)
            page_obj.add_ref(page_json['full_ref'])
            try:
                page_obj.save()
            except DuplicateKeyError as e:
                print(e, 'cleaning up', sep='\n')
                manuscript.ManuscriptPageSet({'manuscript_slug': {'$regex': 'munich.*'}}).delete()
                raise e
    print(f'number of weird cases is: {len(bizzarre)}', *bizzarre, sep='\n')

    # title = 'Munich Manuscript'
    # create_manuscript(title, MANUSCRIPT_DATA[title])
    #
    # munich = [{'foo': 'bar'}]
    # slug = manuscript.ManuscriptPage.get_slug_for_title(title)
    # for i, page in enumerate(munich):
    #     if i % 25 == 0:
    #         print(f'{i} / {len(munich)}')
    #     full_url = page["image_file"].replace("munich_images", url_prefix)
    #     data = {
    #         'manuscript_slug': slug,
    #         'page_id':  page['full_ref'],
    #         'image_url': full_url,
    #         'thumbnail_url': full_url.replace('.jpg', '_thumbnail.jpg')
    #     }
    #     page_obj = manuscript.ManuscriptPage().load_from_dict(data)
    #     page_obj.add_ref(page['full_ref'])
    #     try:
    #         page_obj.save()
    #     except DuplicateKeyError as e:
    #         print(e, 'cleaning up', sep='\n')
    #         manuscript.ManuscriptPageSet({'manuscript_slug': slug}).delete()
    #         raise e


create_munich()
"""
manuscript attrs:
- title:
- he_title
- source
- description
- he description

page attrs:
 - manuscript_slug
 - page_id
 - image_url
 - thumbnail_url
 - contained_refs
 - expanded_refs
"""
# html_map = get_rows_from_db()
# possible_manuscripts, samples = set(), []
# for key, value in html_map.items():
#     for url in value:
#         result = re.match(r'^http://daten.digitale-sammlungen.de/([^/]+)/', url)
#         if result:
#             manuscript_id = result.group(1)
#             if manuscript_id not in possible_manuscripts:
#                 samples.append(url)
#             possible_manuscripts.add(manuscript_id)
#
#         else:
#             print(f'bad url: {url}')
# num = len(possible_manuscripts)
# print(f'number of possible manuscripts: {num}')
# if num <= 10:
#     for n in possible_manuscripts:
#         print(n)
#
# for s in samples:
#     print(s)
