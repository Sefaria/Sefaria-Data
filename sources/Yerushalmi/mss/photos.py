import requests

for ms in [937041, 937421]:
    part = 'I' if ms == 937041 else 'II'
    data = requests.get(f'https://digitalcollections.universiteitleiden.nl/iiif_manifest/item%253A{ms}/manifest').json()
    i = 0
    for canvas in data["sequences"][0]["canvases"]:
        i += 1
        print(f'Downloading image {i} of {len(data["sequences"][0]["canvases"])}')
        label = canvas['label']
        base_url = canvas["images"][0]["@id"]

        for side in (0, -1):
            for size in ('full', ',256'):
                img_url = f"{base_url}/pct:{side*-50},0,50,100/{size}/0/default.jpg"
                print(img_url)
                req = requests.get(img_url)
                name = label.split('-')[-side-1]
                name = re.sub(r'[^I\dab]', '', name)
                if size == ',256':
                    name += '_thumbnail'
                open(f"images/{part}{name}.jpg", "wb").write(req.content)
