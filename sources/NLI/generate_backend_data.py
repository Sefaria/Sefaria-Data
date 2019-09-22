# encoding=utf-8

import re
import os
import codecs
from database import Database
from bs4 import BeautifulSoup


def generate_qa_document(data_list, outfile='image_qa.html'):
    # todo: add sefaria text for each ref
    soup = BeautifulSoup(u'', 'html5lib')
    style = soup.new_tag('style')
    style.string = '''
    table,
    td {
        border: 1px solid #333;
    }

    thead {
        background-color: #333;
        color: #fff;
    }
    '''
    soup.head.append(style)

    table = soup.new_tag('table')
    soup.body.append(table)
    thead, tbody = soup.new_tag('thead'), soup.new_tag('tbody')
    table.append(thead)
    table.append(tbody)

    head_row = soup.new_tag('tr')
    thead.append(head_row)
    for header in ["Image_Content", "Expanded_Refs", "image_thumbnail", "image_url"]:
        header_obj = soup.new_tag('th')
        header_obj.string = header
        head_row.append(header_obj)

    for data_obj in data_list:
        table_row = soup.new_tag('tr')
        tbody.append(table_row)
        columns = [soup.new_tag('td') for _ in range(4)]

        columns[0].string = data_obj['image_content']

        for ref_num, tref in enumerate(data_obj['expanded_refs'], 1):  # 1 indexed so we know which number item we see
            span = soup.new_tag('span')
            span.string = tref
            columns[1].append(span)
            if ref_num < len(data_obj['expanded_refs']):  # add a <br> between each ref (don't add for last element)
                columns[1].append(soup.new_tag('br'))

        thumbnail = soup.new_tag('img')
        thumbnail['src'] = re.sub(ur'\.jpg', u'_thumbnail.jpg', data_obj['image_url'])
        columns[2].append(thumbnail)

        image_url = soup.new_tag('a')
        image_url['href'] = data_obj['image_url']
        image_url['target'] = "_blank"
        image_url.string = 'full image'
        columns[3].append(image_url)
        for column in columns:
            table_row.append(column)

    with codecs.open(outfile, 'w', 'utf-8') as fp:
        fp.write(unicode(soup))


def expand_refs_from_image_title(image_title):
    # assuming all titles can be split by - and have no skips (;) (appears true for 1723)
    pass


if __name__ == '__main__':
    filenames = sorted([f_name for f_name in os.listdir(u'./kaufman')
                        if not re.search(ur'thumbnail\.jpg$', f_name)])

    db = Database()
    db.cursor.execute('Select * FROM TblImages WHERE Im_Ms=1723 AND Im_Title IS NOT NULL')
    images = [f['Im_Title'] for f in db.cursor.fetchall()]
    filenames = filenames[2:]
    filenames = filenames[:-1]
    print (images[0])
    print len(filenames) - len(images)
    print len(images)

    image_data_list = [{
        'image_content': f_name,
        'expanded_refs': [im_title],
        'image_url': u'https://storage.googleapis.com/kaufman_a_50/{}'.format(f_name)
    } for f_name, im_title in zip(filenames, images)]
    r_image_data_list = image_data_list[::50]
    r_image_data_list.append(image_data_list[-1])
    generate_qa_document(r_image_data_list)
