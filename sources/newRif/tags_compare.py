from collections import Counter, OrderedDict
from tags_fix_and_check import tags_by_criteria

class OrderedCounter(Counter, OrderedDict):
     #Counter that remembers the order elements are first encountered

     def __repr__(self):
         return '%s(%r)' % (self.__class__.__name__, OrderedDict(self))

     def __reduce__(self):
         return self.__class__, (OrderedDict(self),)

def simple_compare(tags_dict, lengths):
    tags_pages = OrderedCounter(sorted([key[1:4] for key in tags_dict]))
    return True if len(tags_pages) == len(lengths) else False

def slice(to_slice, condition):
    array = []
    if isinstance(to_slice, dict):
        sliced = {}
        for item in to_slice:
            if condition(to_slice[item]):
                array.append(sliced)
                sliced = {}
            else:
                sliced[item] = to_slice[item]
        array.append(sliced)
    elif isinstance(to_slice, list):
        sliced = []
        for item in to_slice:
            if condition(item):
                array.append(sliced)
                sliced = []
            else:
                sliced.append(item)
        array.append(sliced)
    else:
        raise ValueError('not list or dict')
    return array

def compare_with_anchors(tags, lengths, up = 2):
    #compare list of lengths to OrderedCounter of daf:tags number using anchors of more tags than up
    #when number of anchors isnt equal returns False
    highs_tags = OrderedCounter({key:tags[key] for key in tags if tags[key] > up})
    highs_lengths = [length for length in lengths if length > up]
    if len(highs_tags) != len(highs_lengths):
        return False
    else:
        condition = lambda x: True if x > up else False
        low_tags, low_lengths = slice(tags, condition), slice(lengths, condition)
        for n in range(len(low_tags)):
            if not simple_compare(low_tags[n], low_lengths[n]):
                list_highs = list(int(key) + 1 for key in highs_tags)
                readable_low_tags = [{int(key)+1: value for key, value in element.items()} for element in low_tags]
                if n == 0:
                    print(f'problem in the bginning before {list_highs[0]}, in rif {readable_low_tags[n]} in mefaresh {low_lengths[n]}')
                elif n == len(low_tags) - 1:
                    print(f'problem in the end after {list_highs[-1]}, in rif {readable_low_tags[n]} in mefaresh {low_lengths[n]}')
                else:
                    print(f'problem after {list_highs[n-1]} and before {list_highs[n]}, in rif {readable_low_tags[n]} in mefaresh {low_lengths[n]}')
        return True

def compare_tags_nums(tags_dict, lengths, unknowns, mefaresh):
    #returns new updated tafs_dict (or None) and OrderedCounter if succes
    tags_pages = OrderedCounter(sorted([key[1:4] for key in tags_dict]))
    unknowns = tags_by_criteria(unknowns, key=lambda x: x[1:4] not in tags_pages, value=lambda x: x['gimatric number']==1)
    with_unk = dict(tags_dict, **unknowns)
    with_unk_pages = OrderedCounter(sorted([key[1:4] for key in with_unk]))
    if simple_compare(tags_dict, lengths):
        print('ok')
        return {}, tags_pages
    elif simple_compare(with_unk, lengths):
        print('ok with unknowns')
        for key in with_unk:
            with_unk[key]['referred text'] = mefaresh
        return with_unk, tags_pages
    else:
        print(len(tags_pages), len(lengths))
        anchor_length = 2
        failed = True
        while failed:
            highs_tags = OrderedCounter({key:tags_pages[key] for key in tags_pages if tags_pages[key]>anchor_length})
            highs_lengths = [length for length in lengths if length > anchor_length]
            if not compare_with_anchors(tags_pages, lengths, up=anchor_length):
                print('not equal anchors', len(highs_tags), len(highs_lengths))
                if compare_with_anchors(with_unk_pages, lengths):
                    print('same anchors number with unknowns', anchor_length, up=anchor_length)
                    failed = False
            else:
                failed = False
            anchor_length += 1
            if anchor_length > 4: break

        length = len(tags_pages)
        if failed and length > 4:
            half_tags = round(length / 2)
            tags_dict1 = {tag:value for tag, value in tags_dict.items() if int(tag[1:4]) < half_tags}
            tags_dict2 = {tag:value for tag, value in tags_dict.items() if int(tag[1:4]) >= half_tags}
            unknowns1 = {tag:value for tag, value in unknowns.items() if int(tag[1:4]) < half_tags}
            unknowns2 = {tag:value for tag, value in unknowns.items() if int(tag[1:4]) >= half_tags}
            lengths1 = lengths[:round(len(lengths)/2)]
            lengths2 = lengths[round(len(lengths)/2):]
            print('1st half')
            compare_tags_nums(tags_dict1, lengths1, unknowns1, 1)
            print('2nd half')
            compare_tags_nums(tags_dict2, lengths2, unknowns2, 1)
    return {}, {}

def compare_tags(tags_dict, lengths, unknowns, mefaresh):
    #assume len of dict and lengths is equal
    tags_pages = OrderedCounter(sorted([key[1:4] for key in tags_dict]))
    with_unk = dict(tags_dict, **unknowns)
    with_unk_pages = OrderedCounter(sorted([key[1:4] for key in with_unk]))
    for page in tags_pages:
        length = lengths.pop(0)
        while tags_pages[page] < length:
            page_tags = tags_by_criteria(tags_dict, key=lambda x: x[1:4]==page)
            last_tag = max([int(key) for key in page_tags])
            optionals = tags_by_criteria(unknowns, key=lambda x: x[0]=='1' and x[1:4]==page and int(x)>last_tag,
            value=lambda x: x['gimatric number']==tags_pages[page]+1)
            if len(optionals) == 1:
                list(optionals.values())[0]['referred text'] = mefaresh
                tags_dict.update(optionals)
                tags_pages = OrderedCounter(sorted([key[1:4] for key in tags_dict]))
            else:
                break
        if tags_pages[page] != length:
            print(f'page {int(page)+1}: {tags_pages[page]} in rif and {length} in mefaresh')
            if length==3 and tags_pages[page]==5 and int(page)+1==37: print(tags_by_criteria(tags_dict, key=lambda x: x[1:4]==page))
    return tags_dict
