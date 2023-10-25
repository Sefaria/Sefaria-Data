import django
django.setup()
from sefaria.model import *
import unicodecsv as csv
import io

def create_csv_for_refs(trefs, generated_by=None):
    query = {'$and': []}
    for tref in trefs:
        regex_list = Ref(tref).regex(as_list=True)
        ref_clauses = [{"expandedRefs0": {"$regex": r}} for r in regex_list]
        ref_clauses += [{"expandedRefs1": {"$regex": r}} for r in regex_list]
        query['$and'].append({"$or": ref_clauses})
    if generated_by:
        query['$and'].append({'generated_by': generated_by})
    links = LinkSet(query)
    output = io.BytesIO()
    writer = csv.writer(output)
    writer.writerow(['ref1', 'ref2', 'generated_by'])
    for link in links:
        writer.writerow([link.refs[0], link.refs[1], link.generated_by])
    return output.getvalue()

def link_refs(refs, generated_by, type='commentary'):
    assert len(refs) == 2, f'should have 2 refs, not {len(refs)}'
    for ref in refs:
        try:
            Ref(ref)
        except Exception as e:
            print(f'{ref} is not a valid ref, got {e}')
    type = type.lower()
    assert type in ['commentary', 'quotation']
    link = Link({
        'refs': refs,
        'type': type,
        'generated_by': generated_by,
        'auto': True
    })
    link.save()

def link_refs_list(refs_list, generated_by, type='commentary'):
    for refs in refs_list:
        link_refs(refs, generated_by, type)

def make_links_from_csv(fp, generated_by, type='commentary'):
    reader = csv.DictReader(fp)
    fieldnames = reader.fieldnames
    assert len(fieldnames) == 2, f'file has {len(fieldnames)} collumns'
    for row in reader:
        link_refs(row.values(), generated_by, type='commentary')

def update_links_from_csv(fp):
    reader = csv.reader(fp)
    headers = next(reader, [])
    assert headers == ['ref1', 'ref2', 'generated_by', 'new ref1', 'new ref2']
    errors = []
    for row in reader:
        query = {'refs': row[:2], 'generated_by': row[2]}
        link = Link().load(query)
        if not link:
            errors.append(f'cannot find link for query {query}')
            continue
        link.refs = row[3:]
        try:
            link.save()
        except:
            error.append(f'error in saving {row}')
    return errors

def refs_to_csv(title1, title2, refs_list):
    output = io.BytesIO()
    writer = csv.writer(output)
    writer.writerow([title1, title2])
    for refs in refs_list:
        writer.writerow(*refs)
    return output.getvalue()

def default_get_base(node_title):
    return index_title.split(' on ', 1)[1]

def link_to_base_text(index_title, get_base=default_get_base, type='commentary', depth_reduce=1, get_csv=False):
    refs_list = []
    errors = []
    for ref in library.get_index(index_title).all_segment_refs():
        base_tref = get_base(', '.join([a for a in ref.index_node.address() if a != 'default']))
        base_sections = ref.sections[:-depth_reduce]
        try:
            base_node = Ref(base_tref).index_node
        except:
            errors.append(f'{ref} base is {base_tref} which does not exist')
            continue
        try:
            base_ref = Ref(_obj={'index': base_node.index, 'index_node': base_node, 'sections': base_sections, 'toSections': base_sections})
        except:
            errors.append(f'{ref} comes to {base_tref}, but has problem with sections: {base_sections}')
            continue
        refs_list.append((ref.normal(), base_ref.normal()))
    if get_csv:
        return refs_to_csv(index_title, base_node.index.title, refs_list), errors
    else:
        link_refs_list(refs_list, f'{index_title} links tool', type)
    return errors

def link_super_commentar(index_title, get_base=default_get_base, get_base_base=None, depth_reduce=1):
    errors = link_to_base_text(index_title, get_base=get_base, get_csv=get_csv)
    if not get_base_base:
        get_base_base= lambda x: x.split(' on ')[-1]
    erros += link_to_base_text(index_title, get_base=get_base_base, depth_reduce=2, get_csv=False)
    return errors
