from sources.NLI.Leningrad import convert_file
from PIL import Image

for i in range(6, 449):
    convert_file(f'{i}_erfurt.pdf', 'erfurt_pdfs', 'erfurt_jpgs')
    im = Image.open(f'erfurt_jpgs/{i}_erfurt.jpg')
    height, length = im.size
    aspect_ratio = length / height
    new_h = 256
    new_l = int(aspect_ratio * length)
    im.thumbnail((new_h, new_l))
    im.save(f'erfurt_jpgs/{i}_erfurt_thumbnail.jpg')
