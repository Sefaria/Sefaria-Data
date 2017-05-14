# encoding=utf-8

import codecs
import re
from collections import OrderedDict
import unicodecsv as csv
from data_utilities.util import getGematria, numToHeb
from data_utilities.util import ja_to_xml, multiple_replace, traverse_ja, file_to_ja_g, file_to_ja
from sefaria.datatype.jagged_array import JaggedArray
from sefaria.model import *
from sources.functions import post_text, post_index, post_link


def map_semak_days(ja_smk):# https://github.com/Sefaria/Sefaria-Project/wiki/Index-Records-for-Simple-%26-Complex-Texts
    days = {'day1': u'א-לו', 'day2': u'לז -קא ','day3': u'קב - קנא', 'day4': u'קנב-קצו', 'day5': u'קצז - רלח',
            'day6': u'רלט-רעט', 'day7': u'רפ - רצד'}
    days = {'day1': [1, 36], 'day2': [37, 101], 'day3': [102, 151], 'day4': [152, 196], 'day5': [197, 238],
            'day6': [239, 279], 'day7': [280, 294]}

def parse_semak(filename):

    def cleaner(my_text):
        replace_dict = {u'@11(.*?)@12': ur'<b>\1</b>', u'@33(.*?)@34': ur'<b>\1</b>', u'@66(.*?)@67': ur'\1'}#, u'@55[\u05d0-\u05ea]{1,3}' : u'<i-tags = >'}
        new = []
        for line in my_text:
            line = multiple_replace(line, replace_dict, using_regex=True)
            new.append(line)
        return new


    regs = [ur'@22(?P<gim>[\u05d0-\u05ea]{1,3})'] #, u'@(11|23|33)(?P<gim>)']
    with codecs.open(filename, 'r', 'utf-8') as fp:
        lines = fp.readlines()
    starting = None
    # check if we got to the end of the legend and change to started
    # clean all lines of days start with @00
    cleaned = []
    letter_section = []
    alt_day = []
    for line_num, line in enumerate(lines):
        if line == u'\n':
            starting = line_num + 1
            break
    for line_num, line in enumerate(lines[starting:]):
        if re.search(u'@00', line):
            alt_day.append(line_num)
        if not re.search(u'@00', line) and not line.isspace():
            if re.search(u'@22', line):
                line = re.split(u'(@22[\u05d0-\u05ea]{1,3})', line)
                if isinstance(line, basestring):
                    cleaned.append(line)
                else:
                    [cleaned.append(st) for st in line if st]
            else:
                cleaned.append(line)
    alt_day.append(len(lines))
    print alt_day
    try:
        smk_ja = file_to_ja_g(2, cleaned, regs, cleaner, gimatria=True,  grab_all=[False, True, True], group_name='gim').array()
    except AttributeError:
        print 'there are more regs then levels...'

    ja_to_xml(smk_ja, ['letter', 'segments'], 'smk.xml')

    return smk_ja


def parse_Raph(filename):
    def cleaner(my_text):
        replace_dict = {u'@(?:11|77)[\u05d0-\u05ea]{0,3}': u'', u'@(33|22)': u''}#{u'@11(.*?)@12': ur'<b>\1</b>', u'@33(.*?)@34': ur'<b>\1</b>', u'@33(.*?)@34': ur'<b>\1</b>', u'@66(.*?)@67': ur'\1'}
        new = []
        for line in my_text:
            line = multiple_replace(line,replace_dict,using_regex=True)
            new.append(line)
        return new

    regs = [ur'@77(?P<gim>[\u05d0-\u05ea]{0,3})', ur'@11(?P<gim>[\u05d0-\u05ea]{1,3})']  # (?P<gim>[\u05d0-\u05ea]{1,3})
    with codecs.open(filename, 'r', 'utf-8') as fp:
        lines = fp.readlines()
    starting = None
    # check if we got to the end of the legend and change to started
    # clean all lines of days start with @00
    cleaned = []
    letter_section = []
    for line_num, line in enumerate(lines):
        if line == u'\n':
            starting = line_num + 1
            break
    for line_num, line in enumerate(lines[starting:]):
        if not re.search(u'@00', line) and not line.isspace():
            line = re.split(u'(@(?:77|11)[\u05d0-\u05ea]{0,3})', line)
            if isinstance(line, basestring):
                cleaned.append(line)
            else:
                [cleaned.append(st.strip()) for st in line if st]#(st and not re.search(u'@(77)', st))]
            # else:
            #     cleaned.append(line)
    try:
        ja = file_to_ja_g(3, cleaned, regs, cleaner, gimatria=True,  grab_all=[False, False, True], group_name='gim').array()
    except AttributeError:
        print 'there are more regs then levels...'

    ja_to_xml(ja, ['page', 'letter', 'segments'], 'raph.xml')

    return ja


def parse_Raph_by_letter(filename):
    '''parsing according to the letters, is the main ja, to post for the raph'''
    def cleaner(my_text):
        replace_dict = {u'@(?:11|77)[\u05d0-\u05ea]{0,3}': u'', u'@(33|22)': u''}#{u'@11(.*?)@12': ur'<b>\1</b>', u'@33(.*?)@34': ur'<b>\1</b>', u'@33(.*?)@34': ur'<b>\1</b>', u'@66(.*?)@67': ur'\1'}
        new = []
        for line in my_text:
            line = multiple_replace(line, replace_dict, using_regex=True)
            new.append(line)
        return new

    regs = [ur'@11(?P<gim>[\u05d0-\u05ea]{1,3})']
    with codecs.open(filename, 'r', 'utf-8') as fp:
        lines = fp.readlines()
    starting = None
    # check if we got to the end of the legend and change to started
    # clean all lines of days start with @00
    cleaned = []
    for line_num, line in enumerate(lines):
        if line == u'\n':
            starting = line_num + 1
            break
    for line_num, line in enumerate(lines[starting:]):
        if not re.search(u'@00', line) and not line.isspace():
            line = re.split(u'(@11[\u05d0-\u05ea]{0,3})', line)
            if isinstance(line, basestring):
                cleaned.append(line)
            else:
                [cleaned.append(st.strip()) for st in line if st]
    new_ja = regs_devide(cleaned, regs)
    try:
        # ja = file_to_ja_g(2, cleaned, regs, cleaner, gimatria=True,  grab_all=[True, True], group_name='gim').array()
        ja = file_to_ja(2, cleaned, regs, cleaner, grab_all=False).array()
    except AttributeError:
        print 'there are more regs then levels...'

    # ja_to_xml(new_ja, ['Alef', 'letter', 'segments'], 'raph_letters.xml')
    ja_to_xml(ja, ['letter', 'segments'], 'raph_letters.xml')

    return ja


def parse_Raph_simanim(alinged_list):
    '''
    note: although there is (not often) a differentiation in the original txt file,
    raph letters can be divided into smaller segments. In this code we combined those segments.
    returning, every raph letter as a line.
    '''
    ja = []
    siman = []
    i = 1
    prev_siman = u'א'
    for obj in alinged_list:
        if obj['siman'] == prev_siman:
          siman.append(obj['raph line'])
          continue
        else:
            ja.append(siman)
            while getGematria(obj['siman']) != (getGematria(prev_siman) + i):
                ja.append([])
                i += 1
            i = 1
            siman = []
            siman.append(obj['raph line'])
        prev_siman = obj['siman']
    ja.append(siman)
    ja_to_xml(ja, ['siman', 'letter'], 'raph_simanim.xml')
    return ja


def parse_hagahot_by_letter(filename):
    def cleaner(my_text):
        replace_dict = {u'@11\([\u05d0-\u05ea]{0,3}\)': u''}
        new = []
        for line in my_text:
            line = multiple_replace(line, replace_dict, using_regex=True)
            new.append(line)
        return new

    regs = [ur'@11\((?P<gim>[\u05d0-\u05ea]{1,3})\)']
    with codecs.open(filename, 'r', 'utf-8') as fp:
        lines = fp.readlines()
    starting = None
    # check if we got to the end of the legend and change to started
    # clean all lines of days start with @00
    cleaned = []
    for line_num, line in enumerate(lines):
        if line == u'\n':
            starting = line_num + 1
            break
    for line_num, line in enumerate(lines[starting:]):
        if not re.search(u'\$', line) and not line.isspace():
            line = re.split(u'(@11\([\u05d0-\u05ea]{0,3}\))', line)
            if isinstance(line, basestring):
                cleaned.append(line)
            else:
                [cleaned.append(st.strip()) for st in line if st]
    try:
        ja = file_to_ja_g(2, cleaned, regs, cleaner, gimatria=True,  grab_all=[True, True], group_name='gim').array()
    except AttributeError:
        print 'there are more regs then levels...'
    new_ja = regs_devide(cleaned, regs, u'(נשלם מלאכת שבעת הימים)')
    ja_to_xml(new_ja, ['siman', 'letter', 'segments'], 'hagahot_letters.xml')

    return new_ja


def map_semak_page_siman(smk_ja, to_print = True):
    '''
    create a dictionary from key: siman value: page(s) that the siman is on
    :param smk_ja: smk ja parsed according to simanim @22
    :return: dictionary. keys: siman (he letter), value: list of pages the siman spans over. (pages according to scan -
    starts on p. 21)
    '''
    siman_page = OrderedDict()
    page_count = 21
    start_page = False
    lst_seg = {'data': '', 'indices': []}
    for seg in traverse_ja(smk_ja):
        for i, page in enumerate(re.finditer(u'@77', seg['data'])):
            page_count += 1
            try:
                siman_page[numToHeb(seg['indices'][0]+1)].append(page_count)
            except KeyError:
                if not start_page:
                    siman_page[numToHeb(seg['indices'][0] + 1)] = [page_count - 1, page_count]
                    start_page = False
                else:
                    siman_page[numToHeb(seg['indices'][0]+1)] = [page_count]
            if re.search(u'@77 ?$', lst_seg['data']):
                start_page = True
                siman_page[numToHeb(lst_seg['indices'][0] + 1)].remove(page_count)
        if not list(re.finditer(u'@77', seg['data'])):
            try:
                siman_page[numToHeb(seg['indices'][0]+1)]
            except KeyError:
                siman_page[numToHeb(seg['indices'][0] + 1)] = [page_count]
            if re.search(u'@77 ?$', lst_seg['data']):
                start_page = True
                try:
                    siman_page[numToHeb(lst_seg['indices'][0] + 1)].remove(page_count)
                except ValueError:
                    pass
        lst_seg = seg
    if to_print:
        for k in siman_page.keys():
            print k, siman_page[k]
    return siman_page


def link_semak_raph(smk_ja, raph_ja):
    #if segment in smak_ja has a @55[\u05d0-\u05ea]{0,3} extract the letter and match it to the segment in the ja_raph
    #by running on the ja_raph segments
    smk_raph = []
    raph_letter = []
    for seg in traverse_ja(smk_ja):
        if re.search(u'@55[\u05d0-\u05ea]{0,3}', seg['data']):
            for letter in re.findall(u'@55([\u05d0-\u05ea]{0,3})', seg['data']):
                # smk_raph.append([seg['indices'][:], letter])
                smk_raph.append([letter, seg['indices']])
    last = [-1, -1]
    for seg in traverse_ja(raph_ja):
        if seg['indices'][0:2] == last[0:2]:
            continue
        else:
            raph_letter.append(seg)
        last = seg['indices']

    problem_count = 0
    for smk, raph in zip(smk_raph, raph_letter):
        if getGematria(smk[0]) == (raph['indices'][1]+1):
            print getGematria(smk[0]), raph['indices'][1]+1, \
                [item+1 for item in smk[1]], [item +1 for item in raph['indices']]
        else:
            problem_count +=1
            print 'problem:', getGematria(smk[0]), raph['indices'][1]+1,\
                [item+1 for item in smk[1]], [item +1 for item in raph['indices']]
    print problem_count


def regs_devide(lines, regs, eof=None):
    reg = regs[0]
    ja = []
    letter = []
    siman = []
    for line in lines:
        comb_letter = ' '.join(letter)
        if re.search(reg, line) or (eof and re.search(eof, line)):
            siman.append(comb_letter)
            letter = []
            if re.search(reg, line):
                gim = getGematria(re.search(reg, line).group(1))
            if gim == 1 or (eof and re.search(eof, line)):
                ja.append(siman)
                if siman == ['']:
                    ja.pop()
                siman = []
        letter.append(line)
    return ja


def raph_alignment_report(ja_smk, letter_ja):
    csv_lst = []
    lst_raph = []
    smk_siman = 0
    smk_pages = map_semak_page_siman(ja_smk, to_print=False)
    for seg in traverse_ja(ja_smk):
        for raph_l_in_smk in re.finditer(u'@55([\u05d0-\u05ea]{1,3})', seg['data']):
            lst_raph.append((raph_l_in_smk.group(1),
                             seg['data'][raph_l_in_smk.span()[0] - 20: raph_l_in_smk.span()[1] + 20],
                             (seg['indices'][0] + 1)))
    raph_11 = []
    for raph in traverse_ja(letter_ja):
        raph_11.append(raph)  # re.search(u'@11([\u05d0-\u05ea]{1,3})', raph['data']).group(1))
    page = 21
    prob = 0
    for raph, smk_l in zip(raph_11, lst_raph):

        print re.search(u'@11([\u05d0-\u05ea]{1,3})', raph['data']).group(1), smk_l[0], numToHeb(smk_l[2])
        csv_dict = {u'smk letter': smk_l[0], u'raph letter': re.search(u'@11([\u05d0-\u05ea]{1,3})', raph['data']).group(1),
                    u'smk words': smk_l[1], u'raph line': raph['data'], u'siman': numToHeb(smk_l[2]), u'aprx page in scan': smk_pages[numToHeb(smk_l[2])]}
        if re.search(u'@77', smk_l[1]):
            page += 1
        if re.search(u'@11([\u05d0-\u05ea]{1,3})', raph['data']).group(1) != smk_l[0]:
            prob += 1
            print "*"
            csv_dict['problem'] = True
            # break
        csv_lst.append(csv_dict)
    print 'prob', prob
    print 'done'
    toCSV(u'testcsvreport', csv_lst, [u'smk letter', u'raph letter', u'smk words',
                                u'raph line', u'siman', u'aprx page in scan', u'problem'])
    return csv_lst


def toCSV(filename, list_rows, column_names):
    with open(u'{}.csv'.format(filename), 'w') as csv_file:
        writer = csv.DictWriter(csv_file, column_names)
        writer.writeheader()
        writer.writerows(list_rows)


def hagahot_alignment(ja_smk, ja_raph, ja_hagahot):
    ja_smk = JaggedArray(ja_smk)
    ja_raph = JaggedArray(ja_raph)
    ja_hagahot = JaggedArray(ja_hagahot)
    # for i, seg_smk, j, seg_raph in zip(enumerate(ja_smk.array()), enumerate(ja_raph.array())):
    dict_lst = []
    dict = {u'siman':[], u'smk':[], u'raph':[]}
    for i, seg in enumerate(zip(ja_smk.array(), ja_raph.array())):
        # print numToHeb(i+1)
        dict['siman'] = numToHeb(i+1)
        for smk_line in seg[0]:
            hag_lett = re.findall(ur'@88\((?P<gim>[\u05d0-\u05ea]{1,3})\)', smk_line)
            if hag_lett:
                dict['smk'].append(hag_lett)
                # print [getGematria(lett) for lett in hag_lett]
        print 'RAPH'
        for raph_line in seg[1]:
            hag_lett = re.findall(ur'@88\((?P<gim>[\u05d0-\u05ea]{1,3})\)', raph_line)
            if hag_lett:
                dict['raph'].append(hag_lett)
                # print [getGematria(lett) for lett in hag_lett]
        dict_lst.append(dict)
        dict = {u'siman': [], u'smk': [], u'raph': []}
    return dict_lst


def smk_schema():
    record_root = SchemaNode()
    # record_root.add_title('Semak', 'en', True)
    # record_root.add_title(u'ספר מצוות קטן', 'he', True)
    # record_root.key = 'Semak'
    # intro_node = JaggedArrayNode()
    # intro_node.depth = 1
    # intro_node.add_primary_titles(u'Introduction', u'הקדמה')
    # intro_node.add_structure(['Paragraph'])
    # record_root.validate()

    return record_root


def post_smk(ja_smk):
    text_version = {
        'versionTitle': 'Sefer Mitzvot Katan, Kopys, 1820',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001771677',
        'language': 'he',
        'text': ja_smk
    }

    schema = JaggedArrayNode()
    schema.add_title('Sefer Mitzvot Katan', 'en', True)
    schema.add_title(u'ספר מצות קטן', 'he', True)
    schema.key = 'Sefer Mitzvot Katan'
    schema.depth = 2
    schema.addressTypes = ['Integer', 'Integer']
    schema.sectionNames = ['Siman', 'Segment']
    schema.validate()

    index_dict = {
        'title': 'Sefer Mitzvot Katan',
        'categories': ['Halakhah'],
        'schema': schema.serialize()  # This line converts the schema into json
    }
    post_index(index_dict)

    post_text('Sefer Mitzvot Katan', text_version)


def post_raph(ja_raph):
    text_version = {
        'versionTitle': 'Sefer Mitzvot Katan, Kopys, 1820',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001771677',
        'language': 'he',
        'text': ja_raph
    }

    schema = JaggedArrayNode()
    schema.add_title('Hagahot Rabbenu Peretz', 'en', True)
    schema.add_title(u'הגהות רבנו פרץ', 'he', True)
    schema.key = 'Hagahot Rabbenu Peretz'
    schema.depth = 2
    schema.addressTypes = ['Integer', 'Integer']
    schema.sectionNames = ['Siman', 'Segment']
    schema.validate()

    index_dict = {
        'title': 'Hagahot Rabbenu Peretz',
        'dependence': "Commentary",
        'base_text_titles': ["Sefer Mitzvot Katan"],
        "categories": ["Halakhah", "Commentary"],
        'schema': schema.serialize() # This line converts the schema into json
    }
    post_index(index_dict)

    post_text('Hagahot Rabbenu Peretz', text_version)


def link_raph(ja_smk, ja_raph_simanim):  # look how to get this information where it is coming from.
    # ja_raph_simanim = siman, letter
    links = []
    i = 0
    for seg in traverse_ja(ja_smk):
        for x in re.findall(u'@55', seg['data']): # if re.search(u'@55', seg['data']):
            siman = seg['indices'][0] + 1
            segment = seg['indices'][1] + 1
            i += 1
            link = (
                {
                    "refs": [
                        "Sefer Mitzvot Katan {}:{}".format(siman, segment),
                        "Hagahot Rabbenu Peretz {}:{}".format(i, 1),  # really should be a ref link to the whole raph
                    ],
                    "type": "commentary",
                    "auto": True,
                    "generated_by": "semak_parser"
                })
            # dh_text = dh['data']
            # append to links list
            links.append(link)
    return links


if __name__ == "__main__":
    ja_smk = parse_semak('Semak.txt')
    # # # siman_page = map_semak_page_siman(ja_smk, to_print=False)
    letter_ja = parse_Raph_by_letter(u'Raph_on_Semak.txt')
    raph_smk_alignment = raph_alignment_report(ja_smk, letter_ja)
    # # # ja_hagahot = parse_hagahot_by_letter(u'Semak_hagahot_chadashot.txt')
    ja_raph = parse_Raph_simanim(raph_smk_alignment)
    # # hgh_align = hagahot_alignment(ja_smk, ja_raph, ja_hagahot)
    # # post_smk(ja_smk)
    # # # post_raph(ja_raph)
    # # # link_raph(ja_raph)  # try to find where this is coming from
    # raph = parse_Raph_by_letter('Raph_on_Semak.txt')
    # post_raph(raph)
    # raph_links = link_raph(ja_smk, raph)
    # post_link(raph_links)
