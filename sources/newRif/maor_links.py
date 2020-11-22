import django
django.setup()
import re
import json
import copy
from functools import partial
from sefaria.model import *
from data_utilities.dibur_hamatchil_matcher import match_ref
from rif_utils import maor_tags, hebrewplus, remove_metadata, get_hebrew_masechet, path
from sefaria.system.exceptions import InputError

def find_dh(comm, masechet, rif=True):
    gemara_tag = maor_tags[masechet]['gemara page']
    comm = hebrewplus(comm, '"\'')[:200]
    if (rif and gemara_tag and gemara_tag in comm) or (not rif and (not gemara_tag or gemara_tag not in rif)):
        #when gemara_tag in comm it means this comment is on gemara and nod not rif
        return ''
    if "פי'" in comm:
        comm = comm.split("פי'")[0]
    elif "כו'" in comm:
        comm = "כו'".join(comm.split("כו'")[:-1])
    else:
        comm = ' '.join(comm.split()[:8])
    predhs = ['הא דתנן', 'הא דתניא', 'הא דאיתמר', 'והא ד', 'הרי"ף ז"ל', 'הרי"ף']
    if any(predh in comm for predh in predhs):
        for predh in predhs:
            if predh in comm[:20]:
                comm = comm.split(predh, 1)[1]
    else:
        comm = ' '.join(comm.split()[3:])
    return comm

def mil_dh(string):
    dh = string.split(':')[0]
    dh = hebrewplus(dh, '"\'').strip()
    dh = re.sub(' +', ' ', dh)
    dh = re.split(" וכו'| כו'", dh)[0]
    predhs = ['עוד כתב בספר המאור ז"ל', 'כתב בספר המאור ז"ל', 'כתוב בספר המאור', 'ועוד', 'וכתב עוד', 'ומה שכתב עוד', 'ומ"ש עוד', 'עוד', 'ומה שכתב', 'וכתוב בספר המאור', 'ומה שכתב']
    newdh = dh
    for predh in predhs:
        if dh.startswith(predh):
            newdh = dh.split(predh, 1)[1]
    return newdh

def split_dh(dh):
    return re.split(" וכו'| כו'", dh)

def base_tokenizer(string, masechet):
    if masechet not in ['Chagigah', 'Sotah']:
        string = remove_metadata(string, masechet)
    string = re.sub(r'<sup>.*?<\/i>', '', string)
    string = re.sub('<[^>]*>|\([^)]*\)', '', string)
    return string.split()

def unpack_ref(tref):
    tref = tref.split()[-1]
    tref = tref.split('-')[0]
    a, c = re.split('[ab]:', tref)
    b = re.findall('[ab]', tref)[0]
    return int(a), b, int(c)

def find_gemara(rif, masechet):
    gemara_refs = [link.refs for link in rif.linkset() if link.generated_by == 'rif gemara matcher']
    gemara_refs = [ref for refs in gemara_refs for ref in refs if 'Rif' not in ref and masechet in ref]
    gemara_refs.sort(key = unpack_ref)
    if gemara_refs:
        first = gemara_refs[0].split('-')[0]
        last = re.sub(r'\d*-', '', gemara_refs[-1].split()[-1])
        if last.count(':') == 2: #means two pages in ref
            last = last.split(':', 1)[1]
        return f'{first}-{last}'

for masechet in maor_tags:
    print(masechet)
    links = []
    gemara_tag = maor_tags[masechet]['gemara page']
    if masechet == 'intro':
        continue
    elif masechet in library.get_indexes_in_category(["Talmud", "Bavli", "Seder Nashim"])+library.get_indexes_in_category(["Talmud", "Bavli", "Seder Nezikin"]):
        title = f'HaMaor HaGadol on {masechet}'
    else:
        title = f'HaMaor HaKatan on {masechet}'
    library.get_index(title).versionState().refresh()
    pages = [ref for ref in Ref(title).all_subrefs() if ref.text('he').text]
    for page in pages:
        maor = page.text('he')
        if masechet not in ['Chagigah', 'Sotah']:
            rif = Ref(f'Rif {page.tref.split(" on ")[1]}')
            trif = rif.text('he')
            if trif.text:
                rif_matches = match_ref(trif, maor, partial(base_tokenizer, masechet=masechet), dh_extract_method=partial(find_dh, masechet=masechet), dh_split=split_dh)["matches"]
            else: #an empty page. we want links to gemara
                rif_matches = [None for _ in maor.text]
            if len(rif_matches) != len(maor.text):
                print(f'{len(maor.text)} paragraphs in text but {len(rif_matches)} in matches')
        else:
            rif_matches = [None]

        for n, match in enumerate(rif_matches):
            if masechet in ['Chagigah', 'Sotah']:
                maor_tref = f"{page}"
            else:
                maor_tref = f"{page}:{n+1}"

            if match:
                links.append({"refs": [maor_tref, match.tref],
                "type": "Commentary",
                "auto": True,
                "generated_by": 'maor rif project'})
                gemara_ref = find_gemara(Ref(match.tref), masechet)
            elif gemara_tag and gemara_tag in Ref(maor_tref).text('he').text:
                gemara_ref = re.findall(r'{}\[(.*?)\]'.format(gemara_tag), Ref(maor_tref).text('he').text)[0]
                gemara_ref = f'{get_hebrew_masechet(masechet)} {gemara_ref}'
                try:
                    Ref(gemara_ref)
                    prev = gemara_ref
                except InputError:
                    if 'ע"ב' in prev:
                        gemara_ref = prev.replace('ע"א', 'ע"ב')
                    else:
                        gemara_ref = prev
                    try:
                        Ref(gemara_ref)
                        prev = gemara_ref
                    except InputError:
                        print(gemara_ref)
                        gemara_ref=''
            elif masechet not in ['Chagigah', 'Sotah']:
                gemara_ref = find_gemara(rif, masechet)
            else:
                gemara_ref = ''

            if gemara_ref:
                gemara_match = match_ref(Ref(gemara_ref).text('he'), Ref(maor_tref).text('he'), partial(base_tokenizer, masechet=masechet), dh_extract_method=partial(find_dh, masechet=masechet), dh_split=split_dh)["matches"][0]
                if gemara_ref=='סוטה דף לא:': print(gemara_match)
                if gemara_match:
                    links.append({"refs": [maor_tref, gemara_match.tref],
                    "type": "Commentary",
                    "auto": True,
                    "generated_by": 'maor rif project'})

    if masechet not in ['Chagigah', 'Sotah']:
        m_title = f'Milchemet Hashem on {masechet}'
        library.get_index(m_title).versionState().refresh()
        mil_pages = [ref for ref in Ref(m_title).all_subrefs() if ref.text('he').text]
        for page in mil_pages:
            p = page.tref.split()[-1]
            if len(page.text('he').text) >= len(Ref(f'{title} {p}').text('he').text):
                for n, _ in enumerate(page.text('he').text):
                    if page == 'Milchemet Hashem on Bava Kamma 33a':
                        if n == 1:
                            continue
                        else:
                            mil_ref = f'{page}:{n}'
                    else:
                        mil_ref = f'{page}:{n+1}'
                    maor_ref = f'{title} {p}:{n+1}'
                    if Ref(maor_ref).is_empty():
                        continue
                    links.append({"refs": [mil_ref, maor_ref],
                    "type": "Commentary",
                    "auto": True,
                    "generated_by": 'maor rif project'})
                    for link in links:
                        if link['refs'][0] == maor_ref:
                            l = copy.deepcopy(link)
                            l['refs'][0] = mil_ref
                            links.append(l)

            else:
                t_maor = Ref(f'{title} {p}').text('he')
                t_mil = page.text('he')
                maor_matches = match_ref(t_maor, t_mil, partial(base_tokenizer, masechet=masechet), dh_extract_method=mil_dh)["matches"]
                for n, match in enumerate(maor_matches):
                    if match:
                        mil_ref = f'{page}:{n+1}'
                        maor_ref = match.tref
                        links.append({"refs": [mil_ref, maor_ref],
                        "type": "Commentary",
                        "auto": True,
                        "generated_by": 'maor rif project'})
                        for link in links:
                            if link['refs'][0] == maor_ref:
                                l = copy.deepcopy(link)
                                l['refs'][0] = mil_ref
                                links.append(l)

    with open(f'{path}/commentaries/json/maor_links_{masechet}.json', 'w') as fp:
        json.dump(links, fp)
