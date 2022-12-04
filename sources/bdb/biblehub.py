from bs4 import BeautifulSoup
import requests
import copy

for i in range(1, 8675):
    print(i)
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    page = requests.get(f'https://biblehub.com/bdb/{i}.htm', headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')
    new = BeautifulSoup('<p></p>', 'html.parser')
    curr_p = new.p
    element = soup.find(class_='vheading', text='Brown-Driver-Briggs')
    if not element:
        print('no bdb', i)
        continue
    element = element.next_sibling
    while element.name != 'iframe':
        print(1,element)
        if element.name == 'p':
            p = soup.new_tag('p')
            curr_p.insert_after(p)
            curr_p = p
            element = element.contents[0]
        curr_p.append(copy.copy(element))
        new_element = element.next_sibling
        if new_element:
            element = new_element
        else:
            element = element.next_element
    with open(f'biblehub/{i}.html', 'w') as fp:
        fp.write(new.prettify())
