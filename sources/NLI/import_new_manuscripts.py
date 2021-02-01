# encoding=utf-8

import re
import os
import csv
import json
import django
from PIL import Image, UnidentifiedImageError
from urllib import parse
django.setup()
from sefaria.model import *
from sefaria.model import manuscript
from pymongo.errors import DuplicateKeyError
from sources.NLI.munich import get_rows_from_db
from sefaria.system.exceptions import InputError
from concurrent.futures.process import ProcessPoolExecutor

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


def create_manuscript(manuscript_data):
    title = manuscript_data['title']
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
    create_manuscript(MANUSCRIPT_DATA[title])

    with open('Leningrad_map.json') as fp:
        leningrad = json.load(fp)

    url_prefix = 'https://storage.googleapis.com/sefaria-manuscripts/leningrad-color'
    for i, (page, ref_range) in enumerate(leningrad.items()):
        if i % 25 == 0:
            print(f'{i} / {len(leningrad)}')
        data = {
            'manuscript_slug': manuscript.ManuscriptPage.get_slug_for_title(title),
            'page_id': page.replace(".jpg", ""),
            # 'image_url': f'{url_prefix}/{page}',
            # 'thumbnail_url': f'{url_prefix}/{page.replace(".jpg", "_thumbnail.jpg")}',
        }
        page_obj = manuscript.ManuscriptPage().load(data)
        if not page_obj:
            page_obj = manuscript.ManuscriptPage().load_from_dict(data)
        page_obj.contained_refs = []
        page_obj.set_expanded_refs()
        file_conversion_data = re.search(r'_([0-9]+)([vr])', page)
        if not file_conversion_data:
            print(f'weird filename: {page}')
            continue
        else:
            number, side = file_conversion_data.group(1), file_conversion_data.group(2)
            new_filename = f'BIB_LENCDX_F{number.zfill(3)}{"B" if side == "v" else "A"}.jpg'
            page_obj.image_url = f'{url_prefix}/{new_filename}'
            page_obj.thumbnail_url = f'{url_prefix}/{new_filename}'.replace('.jpg', '_thumbnail.jpg')

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


def create_bomberg():
    manuscript_data = MANUSCRIPT_DATA['Bomberg Pressing']
    manuscript_title = manuscript_data['title']
    create_manuscript(manuscript_data)
    missing_files, tractates_to_check = [], []

    with open('Bomberg_map.csv') as fp:
        map_rows = list(csv.DictReader(fp))

    url_prefix = 'https://storage.googleapis.com/sefaria-manuscripts/bomberg'
    slug = manuscript.ManuscriptPage.get_slug_for_title(manuscript_title)
    ms = manuscript.ManuscriptPageSet({'manuscript_slug': slug})
    ms.delete()

    for row in map_rows:
        try:
            current, first, last = 0, int(row['FirstDaf']), int(row['lastDaf'])
        except ValueError:
            continue
        for section in Ref(row['Tractate']).all_subrefs()[2:]:  # subrefs will add daf 1a and 2b
            page_id = section.normal()
            # print(page_id)
            filename = f'masekhet_{row["Number"].zfill(2)}_{str(first+current).zfill(4)}.jpg'
            if not os.path.exists(os.path.join('./Bomberg/bomberg_original', filename)):
                missing_files.append((page_id, filename))
                current += 1
                continue
            data = {
                'manuscript_slug': slug,
                'page_id': page_id
            }
            page_obj = manuscript.ManuscriptPage().load(data)
            if page_obj is None:
                page_obj = manuscript.ManuscriptPage().load_from_dict(data)
            page_obj.image_url = f'{url_prefix}/{filename}'
            page_obj.thumbnail_url = f'{url_prefix}/{filename.replace(".jpg", "_thumbnail.jpg")}'
            if hasattr(page_obj, 'contained_refs'):
                page_obj.contained_refs = []
                page_obj.set_expanded_refs()
            page_obj.add_ref(page_id)
            page_obj.save()
            current += 1
        if current + first - 1 != last:
            tractates_to_check.append(row['Tractate'])

    print(f'number of weird tractates is {len(tractates_to_check)}')
    for t in tractates_to_check:
        print(t)
    print(f'number of missing files is {len(missing_files)}')
    for m in missing_files[:10]:
        print(m)


def create_vilna():
    manuscript_data = MANUSCRIPT_DATA['Vilna Pressing']
    manuscript_title = manuscript_data['title']
    create_manuscript(manuscript_data)

    url_prefix = 'https://storage.googleapis.com/sefaria-manuscripts/vilna-romm'
    slug = manuscript.ManuscriptPage.get_slug_for_title(manuscript_title)
    ms = manuscript.ManuscriptPageSet({'manuscript_slug': slug})
    ms.delete()

    file_directory = '/home/jonathan/sefaria/Sefaria-Data/sources/NLI/Romm/full_size'
    filenames = [f for f in os.listdir(file_directory) if f.endswith('.jpg')]
    for i, f in enumerate(filenames, 1):
        if i % 100 == 0:
            print(f'{i}/{len(filenames)}')
        tref = f.replace('.jpg', '').replace('_', ' ')
        if not Ref.is_ref(tref):
            print(f'bad filename for {f}')
            continue
        data = {
            'manuscript_slug': slug,
            'page_id': Ref(tref).normal(),
            'image_url': f'{url_prefix}/{f}',
            'thumbnail_url': f'{url_prefix}/{f.replace(".jpg", "_thumbnail.jpg")}',
        }
        page_obj = manuscript.ManuscriptPage().load_from_dict(data)
        page_obj.add_ref(tref)
        page_obj.save()



def bad_remove_bad_first_image(page_set: list, final_page_url=None):
    """
    url on first image is unrelated, second url should be on the first image
    By shifting the urls up by one, we're leaving the final page with no data. If this can be determined, supply it with
    final_page_url
    :param page_set:  ManuscriptPageSet to be corrected
    :param final_page_url: url for the last page, which is presumably incorrect and will get orphaned by running this
    method
    :return:
    """
    page_set.sort(key=lambda x: Ref(x.expanded_refs[0]).sections)
    urls = [{'u': p.image_url, 't': p.thumbnail_url} for p in page_set]
    urls.pop(0)
    final_page = page_set.pop()
    for p, u in zip(page_set, urls):
        p.image_url = u['u']
        p.thumbnail_url = u['t']
        # p.save()
    if final_page_url:
        final_page.image_url = final_page_url
        final_page.thumbnail_url = final_page_url.replace(".jpg", "_thumbnail.jpg")
    else:
        final_page.image_url = 'orphaned'
    # final_page.save()
    return


def remove_bad_first_image(tractate, final_page=None, use_dummy=False, dummy_tref=None):
    """

    :param tractate:
    :param final_page:
    :param use_dummy: Some tractates are off by one,but don't have a first image. For that case, I've set up a dummy
    :param dummy_tref: Should span up till where the second page starts
    image that we can use.
    :return:
    """
    if use_dummy:
        dummy = create_dummy_munich()  # this will not create duplicates
        if dummy_tref:
            dummy.add_ref(dummy_tref)
        else:
            dummy.add_ref(f'{tractate} 2a')
        dummy.save()
    page_set = m95_for_tractate(tractate)
    contained_refs, next_contained_refs = [], []
    for page in page_set:
        for cr in page.contained_refs:
            if Ref(cr).book == tractate:
                page.remove_ref(cr)
                next_contained_refs.append(cr)
        for cr in contained_refs:
            page.add_ref(cr)

        page.save()
        contained_refs = next_contained_refs
        next_contained_refs = []
    if final_page:
        for cr in contained_refs:
            final_page.add_ref(cr)
        final_page.save()


def add_missing_first_page(page_set: list, first_page_url):
    page_set.sort(key=lambda x: Ref(x.expanded_refs[0]).sections)
    urls = [{'u': p.image_url, 't': p.thumbnail_url} for p in page_set]
    urls.insert(0, {'u': first_page_url, 't': first_page_url.replace(".jpg", "_thumbnail.jpg")})
    urls.pop()  # presumably the last url is unrelated
    for p, u in zip(page_set, urls):
        p.image_url = u['u']
        p.thumbnail_url = u['t']
        p.save()


def get_url_for_file(filename, manuscript_dir):
    """
    Useful tool for correcting munich
    """
    return f'https://storage.googleapis.com/sefaria-manuscripts/{manuscript_dir}/{filename}'


def m95_for_tractate(tractate):
    def sort_pages(mp):
        for r in mp.contained_refs:
            oref = Ref(r)
            if oref.book == tractate:
                return oref.sections
        return 999

    mp_array = manuscript.ManuscriptPageSet({
        'expanded_refs': {'$regex': Ref(tractate).regex(anchored=True)},
        'manuscript_slug': 'munich-manuscript-95'
    }).array()
    mp_array.sort(key=sort_pages)
    return mp_array


def create_dummy_munich():
    mp = manuscript.ManuscriptPage().load({'manuscript_slug': "munich-manuscript-95", "page_id": "dummy_manuscript"})
    if mp is not None:
        return mp
    mp = manuscript.ManuscriptPage()
    mp.manuscript_slug = "munich-manuscript-95"
    mp.page_id = "dummy_manuscript"
    mp.image_url = "foo"
    mp.thumbnail_url = 'foo'
    mp.save()
    return mp


def create_thumbnail(filepath: str, thumb_size: int, output_dir=None):
    """
    :param filepath: full filepath
    :param thumb_size:
    :param output_dir: full path to output directory
    :return:
    """
    print(filepath)
    outpath = filepath.replace('.jpg', '_thumbnail.jpg')
    if output_dir:
        filename = re.search(r'[^/]+.jpg$', outpath).group(0)
        outpath = os.path.join(output_dir, filename)
    if os.path.exists(outpath):
        return True
    try:
        im = Image.open(filepath)
    except UnidentifiedImageError:
        return False
    height, length = im.size
    aspect_ratio = length / height
    new_h = thumb_size
    new_l = int(aspect_ratio * length)
    try:
        im.thumbnail((new_h, new_l))
    except OSError:
        return False
    im.save(outpath)
    return True


def check_missing(title_regex):
    manu_meta = manuscript.Manuscript().load({'title': {'$regex': title_regex}})
    talmud = library.get_indexes_in_category('Bavli')
    talmud.sort(key=lambda x: Ref(x).index.order)
    missing = []
    total = 0
    for tractate in talmud:
        print(tractate)
        segs = Ref(tractate).all_segment_refs()
        total += len(segs)
        for seg in segs:
            tref = seg.normal()
            mp = manuscript.ManuscriptPage().load({'manuscript_slug': manu_meta.slug, 'expanded_refs': tref})
            if not mp:
                missing.append(tref)

    as_ranges = find_ranges(missing)
    print(f'{len(as_ranges)} ranges of missing refs')
    print(f'{len(missing)} total missing segments')
    print(f'{total} segments analyzed')
    print(*as_ranges, sep='\n')


if __name__ == '__main__':
    bomberg_man = manuscript.Manuscript().load({'title': {'$regex': r'[bB]omb'}})

    sections = [f for f in Ref("Nedarim").all_subrefs() if not f.is_empty()]
    input_directory = '/home/jonathan/sefaria/Sefaria-Data/sources/NLI/Bomberg/temp'
    thumbnail_directory = '/home/jonathan/sefaria/Sefaria-Data/sources/NLI/Bomberg/temp_thumb'
    files = os.listdir(input_directory)
    files.sort(key=lambda x: int(re.search(r'([0-9]+).jpg$', x).group(1)))
    if len(sections) != len(files):
        raise AssertionError(f'{len(files)} files but ${len(sections)} sections')

    for filename, section in zip(files, sections):
        create_thumbnail(f'{input_directory}/{filename}', 256, thumbnail_directory)
        normal_sec = section.normal()

        data = {
            'manuscript_slug': bomberg_man.slug,
            'page_id': normal_sec,
            'image_url': get_url_for_file(filename, 'bomberg'),
            'thumbnail_url': get_url_for_file(filename.replace('.jpg', '_thumbnail.jpg'), 'bomberg'),
            'contained_refs': [normal_sec]
        }
        mpage = manuscript.ManuscriptPage().load_from_dict(data)
        mpage.set_expanded_refs()
        mpage.save()


"""
The following image is actually the last image in Berkahot:
https://storage.googleapis.com/sefaria-manuscripts/munich-manuscript/Eruvin 72b-75a.jpg

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
