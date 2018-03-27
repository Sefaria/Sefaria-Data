# encoding=utf-8

import codecs
import re
from collections import OrderedDict
import unicodecsv as csv
from data_utilities.util import getGematria, numToHeb
from data_utilities.util import ja_to_xml, multiple_replace, traverse_ja, file_to_ja_g, file_to_ja
from sefaria.datatype.jagged_array import JaggedArray
from sefaria.model import *
from sources.functions import post_text, post_index, add_term, post_link, add_category, post_text_weak_connection
from sources.EinMishpat.ein_parser import *
from data_utilities.ibid import *
from sefaria.helper.schema import *


def parse_semak(filename):

    def cleaner(my_text):
        replace_dict = {u'@11(.*?)@12': ur'<b>\1</b>', u'@33(.*?)@34': ur'<b>\1</b>', u'@66(.*?)@67': ur'\1',
                        u"@44": u""}

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
        replace_dict = {u'@(?:11|77)[\u05d0-\u05ea]{0,3}': u'', u'@33': u''}#{u'@11(.*?)@12': ur'<b>\1</b>', u'@33(.*?)@34': ur'<b>\1</b>', u'@33(.*?)@34': ur'<b>\1</b>', u'@66(.*?)@67': ur'\1'}
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
        replace_dict = {u'@(?:11|77)[\u05d0-\u05ea]{0,3}': u'', u'@33': u''}#{u'@11(.*?)@12': ur'<b>\1</b>', u'@33(.*?)@34': ur'<b>\1</b>', u'@33(.*?)@34': ur'<b>\1</b>', u'@66(.*?)@67': ur'\1'}
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
          siman.append(obj['raph'])
          continue
        else:
            ja.append(siman)
            while getGematria(obj['siman']) != (getGematria(prev_siman) + i):
                ja.append([])
                i += 1
            i = 1
            siman = []
            siman.append(obj['raph'])
        prev_siman = obj['siman']
    ja.append(siman)
    ja_to_xml(ja, ['siman', 'letter'], 'raph_simanim.xml')
    return ja


def parse_hagahot_by_letter(filename):
    def cleaner(my_text):
        replace_dict = {u'@11\([\u05d0-\u05ea]{0,3}\)': u'', u'@77': u''}
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
    # if eof:
    #     ja.append(letter)
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
    i = 0
    for raph, smk_l in zip(letter_ja, lst_raph):  # zip(raph_11, lst_raph):

        # print re.search(u'@11([\u05d0-\u05ea]{1,3})', raph['data']).group(1), smk_l[0], numToHeb(smk_l[2])
        csv_dict = {u'smk letter': smk_l[0],  u'raph': raph[i], u'siman': numToHeb(smk_l[2]), u'aprx page in scan': smk_pages[numToHeb(smk_l[2])]}
        # u'raph letter': re.search(u'@11([\u05d0-\u05ea]{1,3})', raph['data']).group(1), u'raph line': raph['data']
        # u'smk words': smk_l[1],
        i += 0
        if re.search(u'@77', smk_l[1]):
            page += 1
        # if re.search(u'@11([\u05d0-\u05ea]{1,3})', raph['data']).group(1) != smk_l[0]:
        #     prob += 1
        #     print "*"
        #     csv_dict['problem'] = True
        #     # break
        csv_lst.append(csv_dict)
    print 'prob', prob
    print 'done'
    toCSV(u'testcsvreport', csv_lst, [u'smk letter', u'raph',
                                 u'siman', u'aprx page in scan'])  #, u'problem', u'smk words',u'raph line',
    return csv_lst


def toCSV(filename, list_rows, column_names):
    with open(u'{}.csv'.format(filename), 'w') as csv_file:
        writer = csv.DictWriter(csv_file, column_names)
        writer.writeheader()
        writer.writerows(list_rows)


def get_citations(ja_smk, filenametxt):
    cittxt = codecs.open(u'{}.txt'.format(filenametxt), 'w', encoding='utf-8')
    citations = []
    regs = {u'rambam': re.compile(u'(\u05e8\u05de\u05d1"\u05dd.*?)(?:\.|\u05d5?\u05d8\u05d5\u05e8|\u05d5?\u05e1\u05de"?\u05d2|\n)'),
    u'smg' : re.compile(u'(\u05e1\u05de"?\u05d2.*?)(?:\.|\u05d5?\u05d8\u05d5\u05e8|\u05d5?\u05e8\u05de\u05d1"\u05dd|\n)'),
    u'tur' : re.compile(u'\u05d8\u05d5\u05e8(.*?)(?:\.|:|\n|@)')}
    for i, siman in enumerate(ja_smk):
        for j, line in enumerate(siman):
            if re.search(u'@23', line):
                cittxt.write(u"{} ".format(i+1))
                cittxt.write(u"{} ".format(j + 1))
                cittxt.write(re.search(u'@23(.*)', line).group(1))
                cittxt.write(u'\n')
                cit_dict = {"siman": i+1, "full": re.search(u'@23(.*)', line).group(1)}
                for comm, reg in regs.items():
                    if comm == 'smg':
                        continue
                    if reg.search(line):
                        cit_dict[comm] = reg.search(line).group(1)
                        if comm == u'tur':
                            cit_dict[comm] = u'טור, ' + reg.search(line).group(1).strip()
                        if comm == u'rambam':
                            testing = cit_dict[comm]
                            cit_dict[comm] = sarsehu(cit_dict[comm])
                            if testing != cit_dict[comm]:
                                print cit_dict[comm]
                        text = cit_dict[comm]
                        while True:
                            if not text:
                                break
                            try:
                                cit_dict[comm] = Ref(text)
                                break
                            except InputError:
                                split_ref = re.split(u'\s', text)
                                text = u' '.join(split_ref[:-1])
                citations.append(cit_dict)
    links, smgs = link_smg(filenametxt)
    for (smk_siman, smg) in smgs:
        citations[int(smk_siman)-1][u'smg'] = eval(smg)

    toCSV(filenametxt, citations, ['siman', 'rambam', 'smg', 'tur', 'full'])

    return citations


def fromCSV(fromcsv, newfile, header):

    '''

    :param fromcsv: csv file to read the QAed lines from
    :param newfile: txt file name to write the fixed lines into for the sake of creating a new (fixed) csv file
    :param header: str of header to write into the txt file
    :return: fieldnames, lines. fieldnames = list of the headers from the csv, lines = list of rows from header column
    '''

    f = codecs.open(u'{}.txt'.format(newfile), 'w', encoding='utf-8')
    with open(fromcsv, 'r') as csvfile:
        file_reader = csv.DictReader(csvfile)
        lines = []
        for i, row in enumerate(file_reader):
            if not row:
                continue
            f.write(u'{} {} '.format(row[u'siman'], row[u'siman']))
            f.write(row[header].strip() + u'\n')
            lines.append({u'siman': row['siman'], u'full': row[header].strip()})
        return file_reader.fieldnames, lines


def rewrtie_csv(fromcsv, newcsv, readColumnHeader, toWriteHeaders=None):
    headerNames, lines = fromCSV(fromcsv, u'fixed_{}'.format(readColumnHeader), readColumnHeader)
    if not toWriteHeaders:
        toWriteHeaders = headerNames
    regs = {u'rambam': re.compile(
        u'(\u05e8\u05de\u05d1"\u05dd.*?)(?:\.|\u05d5?\u05d8\u05d5\u05e8|\u05d5?\u05e1\u05de"?\u05d2|\n)'),
            u'smg': re.compile(
                u'(\u05e1\u05de"?\u05d2.*?)(?:\.|\u05d5?\u05d8\u05d5\u05e8|\u05d5?\u05e8\u05de\u05d1"\u05dd|\n)'),
            u'tur': re.compile(u'\u05d8\u05d5\u05e8(.*?)(?:\.|:|\n|@)')}
    # rows = OrderedDict()
    rows = []
    siman_cit_lines = 1
    prv_siman = 1
    for line_dict in lines:
        repdict = {u'טוא"ח': u'טור אורח חיים', u'טא"ח': u'טור אורח חיים',u'טי"ד':u'טור יורה דעה', u'טוי"ד':u'טור יורה דעה',u'טח"מ': u'טור חושן משפט',u'טוח"מ': u'טור חושן משפט'}
        line = multiple_replace(line_dict[u'full'], repdict)
        # line = line_dict[u'full']
        row_dict = {u'siman': line_dict[u'siman'], u'full': line}# +u'.'}
        if line_dict[u'siman'] == prv_siman:
            siman_cit_lines += 1
        else:
            siman_cit_lines = 1
        rambam = re.search(regs[u'rambam'], line)
        if rambam:
            rambam = sarsehu(rambam.group(1).strip())
            rambam = get_a_Ref_from_chopped_txt(rambam, VERBOSE=False)
            row_dict[u'rambam'] = rambam
        tur = re.search(regs[u'tur'], line)
        if tur:
            tur = tur.group(1).strip()
            tur = get_a_Ref_from_chopped_txt(u'טור, {}'.format(tur))
            row_dict[u'tur'] = tur
        rows.append(row_dict)
        # rows[(row_dict[u'siman'], siman_cit_lines)] = row_dict
        prv_siman = line_dict[u'siman']
    links, smgs = link_smg(u'fixed_{}'.format(readColumnHeader)) #link_smg(u'smg_smk_test')

    for i, (smk_siman, seg, smg) in enumerate(smgs):
        if smg:
            rows[i][u'smg'] = eval(smg)
            rows[i][u'smk_segment'] = seg #int(smk_siman)-1
    toCSV(newcsv, rows, toWriteHeaders)

def get_a_Ref_from_chopped_txt(st, VERBOSE = False):
    '''

    :param st: text that we assume has a readable Ref in it
    :return: Ref
    '''
    if type(st)!= unicode:
        return st
    # st = re.sub()
    ref = u'no ref found'
    while True:
        if not st:
            break
        try:
            if VERBOSE:
                print st
            ref = Ref(st)
            break
        except InputError:
            split_ref = re.split(u'\s', st)
            st = u' '.join(split_ref[:-1])
    return ref


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
        for i, smk_line in enumerate(seg[0]):
            hag_lett = re.findall(ur'@88\((?P<gim>[\u05d0-\u05ea]{1,3})\)', smk_line)
            if hag_lett:
                dict['smk'].extend([(hag_l, i+1) for hag_l in hag_lett])
                # print [getGematria(lett) for lett in hag_lett]
        # print 'RAPH'
        for i, raph_line in enumerate(seg[1]):
            hag_lett = re.findall(ur'@88\((?P<gim>[\u05d0-\u05ea]{1,3})\)', raph_line)
            if hag_lett:
                dict['raph'].extend([(hag_l, i+1) for hag_l in hag_lett])
                # print [getGematria(lett) for lett in hag_lett]
        dict_lst.append(dict)
        dict = {u'siman': [], u'smk': [], u'raph': []}
    return dict_lst


def link_hg(hg_ja, hagahot_dict_lst, ja_raph):

    def link_hg_smk_or_raph(siman, smk_seg, hg, place_smk_hg, base_text):
        link = (
            {
                "refs": [
                    u"{} {}:{}".format(base_text, siman, smk_seg),
                    "Haggahot Chadashot on Sefer Mitzvot Katan {}:{}".format(siman, hg),  # really should be a ref link to the whole raph
                ],
                "type": "commentary",
                'inline_reference': {
                    'data-commentator': 'Haggahot Chadashot on Sefer Mitzvot Katan',
                    'data-order': place_smk_hg
                },
                "auto": True,
                "generated_by": "semak_parser"

            })
        return link

    # linking
    links = []
    smks = []
    raphs = []
    for dict in hagahot_dict_lst:
        smks += dict["smk"]
        raphs += dict["raph"]
    pts = 0
    ptr = 0
    link = None
    for dict in hagahot_dict_lst:
        # link all the haghot in a siman to the correct Semak segment
        pts_0 = 0
        ptr_0 = 0
        sim = getGematria(dict["siman"])
        # print sim
        for j, hgha in enumerate(hg_ja[sim-1]):
            smk_first = True
            if ptr < len(raphs) and smks[pts][0] == raphs[ptr][0]:
                if dict["raph"] and any([re.search(raphs[ptr][0], letter[0]) for letter in dict["raph"]]):
                    smk_first = False
            if smk_first and re.search(u"@11\({}\)".format(smks[pts][0]), hgha):  # pts < len(smks)
                link = link_hg_smk_or_raph(sim, smks[pts][1], j+1, pts_0+1, "Sefer Mitzvot Katan")
                pts += 1
                pts_0 += 1
            elif ptr < len(raphs) and re.search(u"@11\({}\)".format(raphs[ptr][0]), hgha):
                link = link_hg_smk_or_raph(sim, raphs[ptr][1], j+1, ptr_0+1, 'Haggahot Rabbeinu Peretz on Sefer Mitzvot Katan')
                ptr += 1
                ptr_0 += 1
            else:
                print u"error {}: something with the numbering is wrong...".format(dict["siman"])

            if link:
                links.append(link)
    return links


def hagahot_parse(ja_hagahot, hagahot_dict_lst):

    def num_haghot_in_siman(siman_dict):
        return len(siman_dict['smk']) + len(siman_dict['raph'])

    ja_hagahot = JaggedArray(ja_hagahot)
    ja_hagahot = ja_hagahot.flatten_to_array()
    hg_ja = []
    p_hg = 0
    for dict in hagahot_dict_lst:
        if re.search(u"^@[^1]", ja_hagahot[p_hg]):
            p_hg += 1
        p_hg_end = p_hg + num_haghot_in_siman(dict)
        hg_ja.append(ja_hagahot[p_hg:p_hg_end])
        p_hg = p_hg_end
    hg_ja.append(ja_hagahot[p_hg::])

    ja_to_xml(hg_ja, ['siman', 'letter'], 'haghot_by_smk_simanim.xml')
    return hg_ja


def inlinereferencehtml(ja_smk):
    raphs = [0]
    hags = [0]
    def f_raph(matchObj):
        raphs[0] += 1
        return u'<i data-commentator= "Haggahot Rabbeinu Peretz on Sefer Mitzvot Katan" data-order={}></i>'.format(raphs[0])
    def f_hag(matchObj):
        hags[0] += 1
        return u'<i data-commentator= "Haggahot Chadashot on Sefer Mitzvot Katan" data-order={}></i>'.format(hags[0])

    new_ja = []
    for siman in ja_smk:
        raphs[0] = 0
        hags[0] = 0
        new_siman = []
        for seg in siman:
            seg = re.sub(u'@55[\u05d0-\u05ea]{0,3}', f_raph, seg)
            seg = re.sub(u'@88\([\u05d0-\u05ea]{0,3}\)', f_hag, seg)
            seg = re.sub(u'@77', u'', seg)
            new_siman.append(seg)
        new_ja.append(new_siman)
    return new_ja


def post_smk(ja_smk):
    replace_dict = {u"@23(.*)": ur"<small>\1</small>", u"@(?:99|04)(.*?)\n": ur"<small>\1</small>", u"@0(?:1|2|3)(.*)":ur"<b>\1</b>"}
    ja_smk = inlinereferencehtml(ja_smk)
    ja_smk = before_post_cleaner(ja_smk, replace_dict)

    text_version_smk = {
        'versionTitle': 'Sefer Mitzvot Katan, Kopys, 1820',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001771677',
        'language': 'he',
        'text': ja_smk
    }


    text_version_intro = {
        'versionTitle': 'Sefer Mitzvot Katan, Kopys, 1820',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001771677',
        'language': 'he',
        'text': [u"הקדמה"]
    }

    text_version_remazim = {
        'versionTitle': 'Sefer Mitzvot Katan, Kopys, 1820',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001771677',
        'language': 'he',
        'text': [u"א", u"ב"]
    }

    smk_root = SchemaNode()
    smk_root.add_title(u'Sefer Mitzvot Katan', 'en', True)
    smk_root.add_title(u'ספר מצוות קטן', 'he', True)
    smk_root.key = u'Sefer Mitzvot Katan'


    # index record for the introduction
    smk_intro = JaggedArrayNode()
    smk_intro.add_title(u'Introduction', 'en', primary=True, )
    smk_intro.add_title(u'הקדמה', 'he', primary=True, )
    smk_intro.key = u'Introduction'
    smk_intro.depth = 1
    smk_intro.sectionNames = ['Paragraph']
    smk_intro.addressTypes = ['Integer']

    smk_root.append(smk_intro)

    add_term(u"Remazim", u"רמזים")
    smk_remazim = JaggedArrayNode()
    smk_remazim.add_title(u'Remazim', 'en', primary=True, )
    smk_remazim.add_title(u'רמזים', 'he', primary=True, )
    smk_remazim.key = u'Remazim'
    smk_remazim.depth = 1
    smk_remazim.sectionNames = ['Paragraph']
    smk_remazim.addressTypes = ['Integer']
    smk_root.append(smk_remazim)

    smk_schema = JaggedArrayNode()
    smk_schema.key = u"default"
    smk_schema.default = True
    smk_schema.depth = 2
    smk_schema.addressTypes = ['Integer', 'Integer']
    smk_schema.sectionNames = ['Siman', 'Segment']


    smk_root.append(smk_schema)
    smk_root.validate()

    days = [['First Day',u'1-36', u'יום ראשון: מצות התלויות בלב'], ['Second Day',u'37-101', u'יום שני: מצות התלויות בגוף'], ['Third Day',u'102-151', u'יום שלישי: מצות התלויות בלשון'],
            ['Fourth Day',u'152-196', u'יום רביעי: מצות התלויות בידים'], ['Fifth Day',u'197-238', u'יום חמישי: מצות התלויות באכילה'], ['Sixth Day', u'239-279', u'יום ששי: מצות התלויות בממון'],
            ['Seventh Day',u'280-294', u'יום שביעי: מצות של שבת']]
    nodes = []
    for day in days:
        node = ArrayMapNode()
        node.depth = 0
        node.wholeRef = "Sefer Mitzvot Katan {}".format(day[1])
        # node.refs = "Sefer Mitzvot Katan {}".format(day[1])
        node.includeSections = True
        node.add_primary_titles(day[0], day[2])
        nodes.append(node.serialize())

    add_term("Pillars", u"עמודים")

    index_dict = {
        'title': 'Sefer Mitzvot Katan',
        'categories': ['Halakhah'],
        'alt_structs': {"Pillars": {"nodes": nodes}},
        # "author": [u'Isaac ben Joseph of Corbeil'],
        'schema': smk_root.serialize(),  # This line converts the schema into json

    }



    # add_category('Sefer Mitzvot Katan', ['Halakhah'], u'ספר מצוות קטן')
    post_index(index_dict)

    post_text(u'Sefer Mitzvot Katan', text_version_smk)
    # post_text(u'Sefer Mitzvot Katan, Introduction', text_version_intro)


def add_remazim_node():
    add_term(u"Remazim", u"רמזים")

    smk_remazim = JaggedArrayNode()
    smk_remazim.add_title(u'Remazim', 'en', primary=True, )
    smk_remazim.add_title(u'רמזים', 'he', primary=True, )
    smk_remazim.key = u'Remazim'
    smk_remazim.depth = 1
    smk_remazim.sectionNames = ['Paragraph']
    smk_remazim.addressTypes = ['Integer']

    # library.get_schema_node("Sefer Mitzvot Katan")
    smk_schema = Ref("Sefer Mitzvot Katan").index_node
    attach_branch(smk_remazim, smk_schema, place=1)
    text_version_remazim = {
        'versionTitle': 'Sefer Mitzvot Katan, Kopys, 1820',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001771677',
        'language': 'he',
        'text': [u"א", u"ב"]
    }

    # post_text(u'Sefer Mitzvot Katan, Remazim', text_version_remazim)


def post_raph(ja_raph):
    replace_dict = {u"@22": u"<br>"}
    ja_raph = inlinereferencehtml(ja_raph)
    ja_raph = before_post_cleaner(ja_raph, replace_dict)
    text_version = {
        'versionTitle': 'Sefer Mitzvot Katan, Kopys, 1820',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001771677',
        'language': 'he',
        'text': ja_raph
    }

    schema = JaggedArrayNode()
    schema.add_title('Haggahot Rabbeinu Peretz on Sefer Mitzvot Katan', 'en', True)
    schema.add_title(u'הגהות רבנו פרץ על ספר מצוות קטן', 'he', True)
    schema.key = 'Haggahot Rabbeinu Peretz on Sefer Mitzvot Katan'
    schema.depth = 2
    schema.addressTypes = ['Integer', 'Integer']
    schema.sectionNames = ['Siman', 'Segment']
    schema.validate()
    add_term('Haggahot Rabbeinu Peretz on Sefer Mitzvot Katan', u'הגהות רבנו פרץ על ספר מצוות קטן')
    index_dict = {
        'title': 'Haggahot Rabbeinu Peretz on Sefer Mitzvot Katan',
        'dependence': "Commentary",
        'base_text_titles': ["Sefer Mitzvot Katan"],
        "categories": ["Halakhah", "Commentary"],
        'schema': schema.serialize(),# This line converts the schema into json
        'collective_title': 'Haggahot Rabbeinu Peretz on Sefer Mitzvot Katan',
    }
    post_index(index_dict)

    post_text('Haggahot Rabbeinu Peretz on Sefer Mitzvot Katan', text_version)


def before_post_cleaner(ja, replace_dict):
    new_ja = []
    new_siman = []
    for i, siman in enumerate(ja):
        for seg_number, seg in enumerate(siman):
            seg = multiple_replace(seg, replace_dict, using_regex=True)
            if re.search(u'<small></small>', seg):
                continue
            new_siman.append(seg)
        new_ja.append(new_siman)
        new_siman = []
    return new_ja


def post_hagahot(ja_hg):
    replace_dict = {u"@11\([\u05d0-\u05ea]{1,3}\)\s?@33": u"",
                    u"@77": u"", u"@44": u"<br>", u"@55": u"<b>", u"@66": u"</b>", u"@00(.+?)\s(.+)": u"",
                    u"@(?:99|01)(.*?)@": ur"<br><small>\1</small><br>"}
    ja_hg = before_post_cleaner(ja_hg, replace_dict)

    text_version = {
        'versionTitle': 'Sefer Mitzvot Katan, Kopys, 1820',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001771677',
        'language': 'he',
        'text': ja_hg
    }
    schema = JaggedArrayNode()
    schema.add_title('Haggahot Chadashot on Sefer Mitzvot Katan', 'en', True)
    schema.add_title(u'הגהות חדשות על ספר מצוות קטן', 'he', True)
    schema.key = 'Haggahot Chadashot on Sefer Mitzvot Katan'
    schema.depth = 2
    schema.addressTypes = ['Integer', 'Integer']
    schema.sectionNames = ['Siman', 'Segment']
    schema.validate()

    add_term('Haggahot Chadashot on Sefer Mitzvot Katan',u'הגהות חדשות על ספר מצוות קטן')
    index_dict = {
        'title': 'Haggahot Chadashot on Sefer Mitzvot Katan',
        'dependence': "Commentary",
        'base_text_titles': ["Sefer Mitzvot Katan", 'Haggahot Rabbeinu Peretz on Sefer Mitzvot Katan'],
        "categories": ["Halakhah", "Commentary"],
        'schema': schema.serialize(),  # This line converts the schema into json
        'collective_title': 'Haggahot Chadashot on Sefer Mitzvot Katan',
    }
    post_index(index_dict)

    post_text('Haggahot Chadashot on Sefer Mitzvot Katan', text_version)


def post_all_smk(ja_smk, ja_raph, ja_hagahot, raph_links, hg_links):
    post_smk(ja_smk)
    post_raph(ja_raph)
    post_link(raph_links)
    post_hagahot(ja_hagahot)
    post_link(hg_links)


def link_raph(ja_smk, ja_raph_simanim):  # look how to get this information where it is coming from.
    # ja_raph_simanim = siman, letter
    links = []
    i = 0
    prev_siman = 1
    for seg in traverse_ja(ja_smk):
        for x in re.findall(u'@55', seg['data']): # if re.search(u'@55', seg['data']):
            siman = seg['indices'][0] + 1

            if siman != prev_siman:
                i = 0
            prev_siman = siman

            segment = seg['indices'][1] + 1
            i += 1
            link = (
                {
                    "refs": [
                        "Sefer Mitzvot Katan {}:{}".format(siman, segment),
                        "Haggahot Rabbeinu Peretz on Sefer Mitzvot Katan {}:{}".format(siman, i),  # really should be a ref link to the whole raph
                    ],
                    "type": "commentary",
                    'inline_reference': {
                        'data-commentator': 'Haggahot Rabbeinu Peretz on Sefer Mitzvot Katan',
                        'data-order': i
                    },
                    "auto": True,
                    "generated_by": "semak_parser"

                })
            # dh_text = dh['data']
            # append to links list
            links.append(link)
    return links


def link_remazim():
    links = []
    remazim = Ref("Sefer Mitzvot Katan, Remazim").all_segment_refs()

    for siman, remez in enumerate(remazim):
        siman += 1
        simanlen = len(Ref(u'Sefer Mitzvot Katan {}'.format(siman)).all_segment_refs())
        link = ({"refs": [
            u'Sefer Mitzvot Katan {}.{}-{}'.format(siman, 1, simanlen),
            remez.normal()
        ],
            "type": "commentary",
            "auto": True,
            "generated_by": "semak_parser"  # _sfm_linker what is this parametor intended to be?
        })
        links.append(link)
    return links


def link_smg(filenametxt):
    '''

    :param ja_smk:
    :param filenametxt: a txt file where the lines may have a smg citation, get_citations creates it. note that get_citations calls this method
    :return: links = links smk-smg, smgis = list of tupules (smk_siman, smg) use smgies for csv of the full @23line in smk
    '''
    # get_citations(ja_smk, filenametxt)
    run1(filenametxt, EM=False)
    links = []
    smgis = []
    i = 0
    with open(u'{}.csv'.format(filenametxt), 'r') as csvfile:
        seg_reader = csv.DictReader(csvfile)
        for row in seg_reader:
            i += 1
            siman = row[u"Perek running counter"]
            seg = row[u"page running counter"]
            smg = row[u'Semag']
            simanlen = len(Ref(u'Sefer Mitzvot Katan {}'.format(siman)).all_segment_refs())
            smgis.append((siman, seg, smg))
            if smg:
                # smgis.append((siman, seg, smg))
                smg = eval(row[u'Semag'])
                for smgi in smg:
                    # and to the next segment but not to all segments of the siman
                    link = ({"refs":[
                                u'Sefer Mitzvot Katan {}.{}-{}'.format(siman, 1, simanlen),
                                u'{}'.format(smgi)
                    ],
                    "type": "Sifrei Mitzvot",
                    "auto":True,
                    "generated_by" : "semak_parser_sfm_linker"  #_sfm_linker what is this parametor intended to be?
                    })
                    links.append(link)

    return links, smgis


def sarsehu(line):
    line = re.sub(u"[:;,.]", u'', line)  # maybe re.sub '
    if re.search(u'''(מ|ד)(הלכו'|הלכות|ה"ל|הל'?')''', line):
        line = re.sub(u'''רמב"ם (.*?) (?:מ|ד)(?:הלכו(?:'|ת)?|ה"ל|הל'?)(.*)''', u'רמב"ם הלכות \g<2> \g<1>', line)
        line = re.sub(u'\s+', u' ', line)
    return line


def link_rambam(filename):


    # according to the new method Ref is catching the rambam refs, now we need to read from the CSV,
    # write code to make itrations on the csv after it gets qa correction, and then create the linking from it.
    yad_list = library.get_indexes_in_category(u"Mishneh Torah")
    schema_yad_dict = {}
    for title in yad_list:
        schema_yad_dict[title] = library.get_schema_node(title)

    ## changes addressTypes of all Mishneh Torah indexs to ['Perek' , 'Halkhah']
    # for node in schema_yad_dict.values():
    #     if len(node.sectionNames) != 2:
    #         continue
    #     change_node_structure(node, node.sectionNames, address_types=['Perek','Halakhah'])

    CF = CitationFinder()
    # regex = CF.get_ultimate_title_regex(yad_list, schema_yad_dict, 'he')
    # rambam_tracker = BookIbidTracker()
    all_refs = []
    with codecs.open(filename, 'r', 'utf-8') as fp:
        lines = fp.readlines()
        bad_cnt = 0
        for i, line in enumerate(lines):
            split = re.split(u'ו?ה?(רמב"?ם|סמ"?ג|טור)', line)
            refs = CF.get_potential_refs(u'({})'.format(line), title_rambam=[u'רמב"ם']) #), dropParenthesis=True)
            # split_it = iter(split)
            # for part in split_it:
                # if re.search(ur'''(מיי'|רמב"?ם)''', part):
                #     rambam_cit = split_it.next()
                #     doubles = re.search(u'(?P<first>\u05d4\u05dc\u05db\u05d5\u05ea.*?\u05e4.*?)(?P<second>\u05d5[\u05d0-\u05ea]{1}.*|\n)', rambam_cit)
                #     if doubles:
                #         if re.search(doubles.group(''))
                #     else:
                #         index_name = u'רמב"ם {}'.format(rambam_cit)
                #     # rambam_tracker.resolve()
                #     refs = [rambam_cit]
            print i+1

            for ref in refs:
                if isinstance(ref[0], Ref):
                    # continue
                    print ref
                    all_refs +=ref
                else:
                    print ref[0].group()
                    bad_cnt +=1

    print bad_cnt
    # all_refs += refs
    return all_refs


def link_rambam_smg_tur(csvlinkfile):
    links = []
    links_rambam = []
    links_tur = []
    links_smg = []
    with open(u'{}'.format(csvlinkfile), 'r') as csvfile:
        seg_reader = csv.DictReader(csvfile)
        for row in seg_reader:
            siman = row[u'siman']
            simanlen = len(Ref(u'Sefer Mitzvot Katan {}'.format(siman)).all_segment_refs())
            # Rambam Mishneh Torah
            if row[u'rambam']:
                # rambam = eval(row[u'rambam'])
                if re.search(u'\d+', row[u'rambam']):
                    link = ({"refs": [
                        u'Sefer Mitzvot Katan {}.{}-{}'.format(siman, 1, simanlen),
                        u'{}'.format(row[u'rambam'])
                    ],
                        "type": "Sifrei Mitzvot",
                        "auto": True,
                        "generated_by": "semak_rambam_viasmk_sfm_linker"  # viasmk
                    })
                    try:
                        link = is_ref_empty(link)
                        links_rambam.append(link)
                    except NameError as detail:
                        print u"ref is empty for siman {} of smk:".format(siman), detail
                else:
                    print u'rambam {} no_number'.format(row[u'rambam'])
            if row[u'tur']:
                # tur = eval(row[u'tur'])
                if re.search(u'\d+', row[u'tur']):
                    link = ({"refs": [
                        u'Sefer Mitzvot Katan {}.{}-{}'.format(siman, 1, simanlen),
                        u'{}'.format(row[u'tur'])
                    ],
                        "type": "Sifrei Mitzvot",
                        "auto": True,
                        "generated_by": "semak_tur_viasmk_sfm_linker"  # viasmk
                    })
                    try:
                        is_ref_empty(link)
                        links_tur.append(link)
                    except NameError as detail:
                        print u"ref is empty for siman {} of smk:".format(siman), detail
                else:
                    print u'tur {} no_number'.format(row[u'tur'])

            if row[u'smg']:
                smg = eval(row[u'smg'])
                for smgi in smg:
                    # and to the next segment but not to all segments of the siman
                    smgi_len = len(Ref(smgi).all_segment_refs())
                    link = ({"refs":[
                                u'Sefer Mitzvot Katan {}.{}-{}'.format(siman, 1, simanlen),
                                u'{}.1-{}'.format(smgi, smgi_len)
                    ],
                    "type": "Sifrei Mitzvot",
                    "auto":True,
                    "generated_by" : "semak_smg_viasmk_sfm_linker"  #_sfm_linker what is this parametor intended to be?
                    })
                    try:
                        is_ref_empty(link)
                        links_smg.append(link)
                    except NameError as detail:
                        print u"ref is empty for siman {} of smk:".format(siman), detail
            links = links_rambam + links_tur + links_smg
        return links, links_smg



def link_smk_remazim_to_smg_remazim(smg_smk_links):
    links = []
    for old_l in smg_smk_links:
        siman_smk = re.search(u'Sefer Mitzvot Katan (\d{1,3})', old_l['refs'][0]).group(1)
        ref_smg = re.search(u'Sefer Mitzvot Gadol,(.*?)\s(\d{1,3})', old_l['refs'][1])
        part_smg = ref_smg.group(1)
        siman_smg = ref_smg.group(2)
        link = ({"refs":[
                                u'Sefer Mitzvot Katan, Remazim.{}'.format(siman_smk),
                                u'Sefer Mitzvot Gadol,{}, Remazim.{}'.format(part_smg, siman_smg)
                    ],
                    "type": "Sifrei Mitzvot",
                    "auto":True,
                    "generated_by": "semak_parser_remazim_sfm_linker"  #_sfm_linker what is this parametor intended to be?
                    })
        links.append(link)
    return links


def is_ref_empty(link):
    refs = link["refs"]
    for i, ref in enumerate(refs):
        if Ref(ref).is_empty():
            if re.search(u':', ref):
                ref = re.search(u'(.*?):', ref).group(1)
                if not Ref(ref).is_empty():
                    link["refs"][i] = ref
                    print 'fixed{}'.format(link["refs"])
                    return link
            raise NameError(u'Empty Ref {}'.format(ref))
    return link

if __name__ == "__main__":
    ja_smk = parse_semak('Semak.txt')
    # # siman_page = map_semak_page_siman(ja_smk, to_print=True)
    # letter_ja = parse_Raph_by_letter(u'Raph_on_Semak.txt')
    # raph_smk_alignment = raph_alignment_report(ja_smk, letter_ja)
    # ja_raph = parse_Raph_simanim(raph_smk_alignment)
    # # # post_raph(ja_raph)
    # # # link_raph(ja_raph)  # try to find where this is coming from
    # raph = parse_Raph_by_letter('Raph_on_Semak.txt')
    # raph_links = link_raph(ja_smk, ja_raph)
    # ja_hagahot = parse_hagahot_by_letter(u'Semak_hagahot_chadashot.txt')
    # hgh_align = hagahot_alignment(ja_smk, ja_raph, ja_hagahot)
    # ja_hagahot = hagahot_parse(ja_hagahot, hgh_align)
    # hg_links = link_hg(ja_hagahot, hgh_align, ja_raph)
    #
    # # post_all_smk(ja_smk, ja_raph, ja_hagahot, raph_links, hg_links)
    # smg_links = link_smg(ja_smk, u'smg_smk_test')
    # post_link(smg_links, VERBOSE=True)
    # post_link(link_remazim(), VERBOSE=True)
    # remazim_sm_g_k = link_smk_remazim_to_smg_remazim(smg_links)
    # post_link(remazim_sm_g_k, VERBOSE=True)
    # link_rambam("testrambamibid.txt")
    # get_citations(ja_smk, "exctract")
    # fromCSV(u'exctract.csv', u'newfile', u'full')
    old = 22
    new = 23
    # rewrtie_csv(u'fixed{}.csv'.format(old), u'fixed{}'.format(new), u'full', toWriteHeaders=[u'siman', u'smk_segment', u'rambam', u'smg', u'tur', u'full'])
    smkDerivenLinks, links_smg = link_rambam_smg_tur(u'fixed{}.csv'.format(new))
    post_link(smkDerivenLinks, VERBOSE=True)
    remazim_sm_g_k = link_smk_remazim_to_smg_remazim(links_smg)
    post_link(remazim_sm_g_k, VERBOSE=True)