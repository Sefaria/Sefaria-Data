from google.cloud import storage
import re
from sefaria.utils.talmud import section_to_daf, daf_to_section

#those functions are for changing file names in our manuscript google cloud
#beware that changing name to existing name will squash it without recovery option
#for that reason the reanme line is noted out. you can run this script without it for seeing everything (include printing) works and then note it in

BUCKET_NAME = 'manuscripts.sefaria.org'
STORAGE_CLIENT = storage.Client(project="production-deployment")
# if you get DefaultCredentialsError, try "gcloud auth application-default login" in terminal


def rename(filename, reg, off, pages=True):
    bucket = STORAGE_CLIENT.get_bucket(BUCKET_NAME)
    file = bucket.blob(filename)
    old_name = file.name
    old_daf = re.search(reg, file.name).group(0)
    if pages:
        new_daf = section_to_daf(int(daf_to_section(old_daf) + off))
    else:
        new_daf = str(int(old_daf) + off).zfill(len(old_daf))
    new_name = re.sub(reg, new_daf, file.name, 1)
    # bucket.rename_blob(file, new_name)  # note in this line for changing names
    print(f'changed {old_name} to {new_name}')

def change_vilna_pages_in_maechet(masechet, off, start, end):
    dappim = range(start, end+1) if off < 0 else range(end, start-1, -1)
    for daf in dappim:
        page = section_to_daf(daf)
        reg = r'\d{1,3}[ab]'
        filename = f'vilna-romm/{masechet}_{page}.jpg'
        rename(filename, reg, off)
        filename = f'vilna-romm/{masechet}_{page}_thumbnail.jpg'
        rename(filename, reg, off)


if __name__ == '__main__':
    # example
    # change_vilna_pages_in_maechet('Tamid', 47, 3, 66)
