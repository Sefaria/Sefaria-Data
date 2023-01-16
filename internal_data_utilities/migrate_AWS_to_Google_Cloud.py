import django
django.setup()
import csv
from sefaria.model import *
import requests
from sefaria.s3 import HostedFile
from tempfile import NamedTemporaryFile
import os
urls = set()
from PIL import Image
import time
from sefaria.google_storage_manager import GoogleStorageManager
from io import BytesIO
collections = CollectionSet()
urls = set()
for c in collections:
    for url in [getattr(c, "imageUrl", ""), getattr(c, "coverUrl", ""), getattr(c, "headerUrl", "")]:
        if url not in ["", " ", None] and "googleapis" not in url:
            urls.add(url)

with open("migration.csv", 'w') as f:
    writer = csv.writer(f)
    for url in urls:
        done = False
        while not done:
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    name, extension = os.path.splitext(url.split("/")[-1])
                    with NamedTemporaryFile(suffix=extension) as temp_uploaded_file:
                        temp_uploaded_file.write(response.content)
                        # resized_image_file = BytesIO()
                        # image.save(resized_image_file, optimize=True, quality=70, format="PNG")
                        # resized_image_file.seek(0)
                        bucket_name = GoogleStorageManager.COLLECTIONS_BUCKET
                        file_name = url.split("/")[-1]
                        temp_uploaded_file.seek(0)
                        google_url = GoogleStorageManager.upload_file(temp_uploaded_file, file_name, bucket_name)
                        writer.writerow([url, google_url])
                        print(url)
                        done = True
            except:
                print("Sleeping")
                time.sleep(10)
pass
# hosted_file = HostedFile(filepath=temp_resized_file.name, content_type=uploaded_file.content_type)
#
# if old:
#     HostedFile(url=old).delete()