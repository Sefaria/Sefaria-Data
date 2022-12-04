from google.cloud import storage
import re

def section_to_daf(section):
    """
    Transforms a section number to its corresponding daf string,
    in English or in Hebrew.
    """
    section += 1
    daf = section // 2

    if section > daf * 2:
        daf = "{}b".format(daf)
    else:
        daf = "{}a".format(daf)

    return daf

def daf_to_section(daf):
    """
    Transforms a daf string (e.g., '4b') to its corresponding stored section number.
    """
    amud = daf[-1]
    daf = int(daf[:-1])
    section = daf * 2
    if amud == "a": section -= 1
    return section

def rename(bucket_name, filename, reg, off, pages=True):
    storage_client = storage.Client(project="production-deployment")
    bucket = storage_client.get_bucket(bucket_name)
    file = bucket.blob(filename)
    old_name = file.name
    old_daf = re.search(reg, file.name).group(0)
    if pages:
        new_daf = section_to_daf(int(daf_to_section(old_daf) + off))
    else:
        new_daf = str(int(old_daf) + off).zfill(len(old_daf))
    new_name = re.sub(reg, new_daf, file.name, 1)
    bucket.rename_blob(file, new_name)
    print(f'changed {old_name} to {new_name}')

if __name__ == '__main__':
    bucket_name = 'manuscripts.sefaria.org'
    off = 2
    for n in range(224,2,-1):
        page = section_to_daf(n)
        reg = r'\d{1,3}[ab]'
        filename = f'vilna-romm/Ketubot_{page}.jpg'
        rename(bucket_name, filename, reg, off)
        filename = f'vilna-romm/Ketubot_{page}_thumbnail.jpg'
        rename(bucket_name, filename, reg, off)
    # off = 2
    # for n in range(17, 10, -1):
    #     page = str(n).zfill(4)
    #     reg = '\d{4}'
    #     filename = f'bomberg/masekhet_13_{page}.jpg'
    #     rename(bucket_name, filename, reg, off, pages=False)
    #     filename = f'bomberg/masekhet_13_{page}_thumbnail.jpg'
    #     rename(bucket_name, filename, reg, off, pages=False)
