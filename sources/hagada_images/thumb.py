import csv
from PIL import Image

with open('table.csv', newline='') as fp:
    data = list(csv.DictReader(fp))

for row in data:
    file = row['filename']
    with Image.open(f'/home/yishai/Downloads/hag/{file}.jpg') as img:
        img.thumbnail((256, 278))
        img.save(f'/home/yishai/Downloads/hag/{file}_thumbnail.jpg', 'jpeg')
