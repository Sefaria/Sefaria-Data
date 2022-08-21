import django
django.setup()
from PIL import Image
from sefaria.utils.talmud import section_to_daf

def make_thumbnail(filename, extension='jpg'):
    with Image.open(f'{filename}.{extension}') as im:
        im.thumbnail((256, 278))
        im.save(f'{filename}_thumbnail.{extension}')

if __name__ == '__main__':
    path = '/home/yishai/Downloads/mss/'
    import requests
    for i in range(103,141):
        page = section_to_daf(i)
        req = requests.get(f'https://manuscripts.sefaria.org/vilna-romm/Shabbat_{page}.jpg')
        with open(f'{path}temp.jpg', 'wb') as fp:
            fp.write(req.content)
        with Image.open(f'{path}temp.jpg') as im:
            im.thumbnail((256, 278))
            im.save(f'{path}Shabbat_{page}_thumbnail.jpg')

