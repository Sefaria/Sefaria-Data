# encoding=utf-8

import re, unicodecsv, random
from collections import defaultdict
from sefaria.model import *
from data_utilities.ibid import *

def count_regex_in_all_db(pattern=u'(?:\(|\([^)]* )שם(?:\)| [^(]*\))', lang='he', text='all'):
    '''
    This method is for counting testing perepesis,
    :param lang:
    :param text:
    :return:
    '''



    found = []
    category_dict = defaultdict(int)
    shams_dict = defaultdict(list)

    vtitle = None
    if text == 'all':
        indecies = library.all_index_records()
    else:
        indecies = [library.get_index(text)]
    for index in indecies:
        # if index == Index().load({'title': 'Divrei Negidim'}):
        #     continue
        try:
            unit_list_temp = index.nodes.traverse_to_list(lambda n, _: TextChunk(n.ref(), lang,
                                                                                 vtitle=vtitle).ja().flatten_to_array() if not n.children else [])
            st = ' '.join(unit_list_temp)
            shams = re.finditer(pattern, st)
            cat_key = u'/'.join(index.categories[:-1])
            num_shams = 0
            if shams:
                for s in shams:
                    num_shams += 1
                    curr_sham = s.group()
                    if len(re.split(ur'\s+', curr_sham)) > 6:
                        continue
                    shams_dict[cat_key] += [s.group()]

                # print '{} : {}'.format(index, len(shams))
            found.append((index, num_shams))

            category_dict[cat_key] += num_shams

        except:  # sefaria.system.exceptions.NoVersionFoundError:
            # print 'empty {}'.format(index)
            continue
    max_shams = max(dict(found).values())
    for (k, v) in found:
        if v == max_shams:
            max_index = k
    print 'max: {} with {}'.format(max_index, max_shams)

    cat_items = sorted(category_dict.items(), key=lambda x: x[1])


    for k,v in reversed(cat_items):
        if v == 0:
            continue
        print k,v

    sham_items = sorted(shams_dict.items(), key=lambda x: x[1])

    for k, v in reversed(sham_items):
        if v == 0:
            continue
        print k, v


    cat_sham_dict = defaultdict(list)
    for ci in cat_items:
        population = shams_dict[ci[0]]
        cat_sham_dict[ci] = random.sample(population, min(len(population), 7))

    cat_sham_items = sorted(cat_sham_dict.items(), key=lambda x: x[0][1], reverse=True)
    cat_sham_dict = OrderedDict()
    for k, v in cat_sham_items:
        cat_sham_dict[k] = v


    print "number of unique shams {}".format(len(sham_items))

    print 'total number of shams {}'.format(sum(dict(found).values()))

    return cat_sham_dict
    # return cat_items

def make_csv(sham_items):
    f = open('sham_examples.csv', 'wb')
    keys = ['Category', 'Quantity'] + ['Sham {}'.format(i+1) for i in range(7)]
    csv = unicodecsv.DictWriter(f, keys)
    # csv = unicodecsv.DictWriter(f, ['Category', 'Quantity'])#, 'Example Shams'])
    csv.writeheader()
    for (cat, count), sham_examples in sham_items.items():
    # for cat, count in sham_items:
        # csv.writerow({'Category': cat, 'Quantity': count})# , 'Example Shams': sham_examples})
        row_dict = {
            'Sham {}'.format(i+1): temp_sham
            for i, temp_sham in enumerate(sham_examples)
        }
        for i in range(len(sham_examples),7):
            row_dict['Sham {}'.format(i+1)] = u''

        row_dict['Category'] = cat
        row_dict['Quantity'] = count

        csv.writerow(row_dict)
    f.close()


if __name__ == "__main__":
    inst = CitationFinder()
    #inst.get_ultimate_title_regex(u'שם', 'he'), text='Midrash Tanchuma'
    sham_items = count_regex_in_all_db() #, text = 'Ramban on Genesis')
    make_csv(sham_items)