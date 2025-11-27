from sources.functions import post_index


def get_title(titles_dict, lang):
    return [t for t in titles_dict if t['lang'] == 'he'][0]


indexes = ['Minchat Chinukh', 'Sefer_HaChinukh']
for index in indexes:
    server = 'https://www.sefaria.org'
    index = post_index({'title' :index}, method='GET', server=server)
    for node in index['alt_structs']['Parasha']['nodes']:
        for n in node['nodes']:
            title = get_title(n['titles'], 'he')
            new = title['text'].replace('יה;', 'טו;').replace('יו;', 'טז;')
            if new != title['text']:
                print(new)
                title['text'] = new

    # server = 'http://localhost:8000'
    index = post_index(index, server=server)
