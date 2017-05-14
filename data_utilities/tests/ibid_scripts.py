# encoding=utf-8


import unicodecsv, random
from collections import defaultdict
from sefaria.model import *
from data_utilities.ibid import *
import regex as re


def count_regex_in_all_db(pattern=u'(?:\(|\([^)]*? )שם(?:\)| [^(]*?\))', lang='he', text='all', example_num = 7):
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
    ind_done = 0
    if text == 'all':
        indecies = library.all_index_records()
        inds_len = len(indecies)
    else:
        indecies = [library.get_index(text)]
    for iindex, index in enumerate(indecies):
        print "{}/{}".format(iindex, len(indecies))
        # if index == Index().load({'title': 'Divrei Negidim'}):
        #     continue
        if text == 'all':
            ind_done += 1
            print ind_done*1.0/inds_len
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
        cat_sham_dict[ci] = random.sample(population, min(len(population), example_num))

    cat_sham_items = sorted(cat_sham_dict.items(), key=lambda x: x[0][1], reverse=True)
    cat_sham_dict = OrderedDict()
    for k, v in cat_sham_items:
        cat_sham_dict[k] = v


    print "number of unique shams {}".format(len(sham_items))

    print 'total number of shams {}'.format(sum(dict(found).values()))

    return cat_sham_dict
    # return cat_items


def make_csv(sham_items, example_num, filename='sham_examples.csv'):
    f = open(filename, 'wb')
    keys = ['Category', 'Quantity'] + ['Sham {}'.format(i+1) for i in range(example_num)]
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
        for i in range(len(sham_examples), example_num):
            row_dict['Sham {}'.format(i+1)] = u''

        row_dict['Category'] = cat
        row_dict['Quantity'] = count

        csv.writerow(row_dict)
    f.close()

def index_ibid_finder():
    index = library.get_index("Ramban on Genesis")
    inst = IndexIbidFinder(index)
    inst.index_find_and_replace()

def segment_ibid_finder():
    index = library.get_index("Sefer HaChinukh")
    inst = IndexIbidFinder(index)
    r = Ref("Ramban on Genesis 1:18:1")
    st = r.text("he").text
    inst.segment_find_and_replace(st)


if __name__ == "__main__":
    inst = CitationFinder()
    example_num = 20
    #sham_items = count_regex_in_all_db(inst.get_ultimate_title_regex(u'בראשית', 'he'), text = 'all', example_num=example_num) #, text = 'Ramban on Genesis')
    # sham_items = count_regex_in_all_db(example_num=example_num)
    #make_csv(sham_items, example_num, filename='new_sham_example.csv')

    #
    # import cProfile
    # import pstats
    #
    # cProfile.run("inst = CitationFinder(); count_regex_in_all_db(inst.get_ultimate_title_regex(u'שם', 'he'), text = 'Ramban on Genesis',example_num=7)", "stats")
    # p = pstats.Stats("stats")
    # p.strip_dirs().sort_stats("cumulative").print_stats()

    #index_ibid_finder()
    segment_ibid_finder()