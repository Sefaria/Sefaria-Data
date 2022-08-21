import django
django.setup()
from sefaria.model import *

def change_refs(ms_page, refs):
    ms_page.contained_refs = refs
    ms_page.set_expanded_refs()
    ms_page._validate()
    ms_page.save()

def new_munich_msp(num, refs):
    msp = ManuscriptPage()
    msp.manuscript_slug = 'munich-manuscript-95-(1342-ce)'
    msp.page_id = f'Cod. hebr. 95 pg. {num}'
    msp.image_url = f'https://manuscripts.sefaria.org/munich-manuscript/munich-manuscript-95Cod.hebr.95pg.{str(num).zfill(4)}.jpg'
    msp.thumbnail_url = f'https://manuscripts.sefaria.org/munich-manuscript/munich-manuscript-95Cod.hebr.95pg.{str(num).zfill(4)}_thumbnail.jpg'
    msp.contained_refs = [refs]
    msp.set_expanded_refs()
    msp.validate()
    msp.save()

if __name__ == '__main__':
    for num, ref in [(168, 'Sukkah 3b-7b'), (176, 'Sukkah 32b:3-35a:11')]:
        new_munich_msp(num, ref)
    for num, ref in [(169, 'Sukkah 7b:1-11b:6'), (177, 'Sukkah 35b-38b')]:
        page = ManuscriptPage().load({'image_url': f'https://manuscripts.sefaria.org/munich-manuscript/munich-manuscript-95Cod.hebr.95pg.0{num}.jpg'})
        change_refs(page, [ref])
    # for num in range(122):
    #     num = 1129 - num
    #     page = ManuscriptPage().load({'image_url': f'https://manuscripts.sefaria.org/munich-manuscript/munich-manuscript-95Cod.hebr.95pg.{num}.jpg'})
    #     refs = ManuscriptPage().load(
    #         {'image_url': f'https://manuscripts.sefaria.org/munich-manuscript/munich-manuscript-95Cod.hebr.95pg.{num-1}.jpg'}).contained_refs
    #     if Ref(refs[0]).all_segment_refs()[-1] == Ref(refs[0]).last_segment_ref():
    #         end = Ref(page.contained_refs[0]).all_segment_refs()[0]
    #         if ' 1:1' not in end.normal():
    #             ref = f'{end.book} 1:1-{end.normal().split()[-1]}'
    #             try:
    #                 ref = Ref(ref).normal()
    #             except:
    #                 print('sonething wrong with ref', ref)
    #             refs.append(ref)
    #     print(f'cahnging page num {num} refs, from {page.contained_refs} to {refs}')
    #     change_refs(page, refs)
    # for num in [1133, 1132]:
    #     page = ManuscriptPage().load({'image_url': f'https://manuscripts.sefaria.org/munich-manuscript/munich-manuscript-95Cod.hebr.95pg.{num}.jpg'})
    #     refs = ManuscriptPage().load(
    #         {'image_url': f'https://manuscripts.sefaria.org/munich-manuscript/munich-manuscript-95Cod.hebr.95pg.{num-1}.jpg'}).contained_refs
    #     print(f'cahnging page num {num} refs, from {page.contained_refs} to {refs}')
    #     change_refs(page, refs)
    # for num in [1007, 1131]:
    #     page = ManuscriptPage().load(
    #         {'image_url': f'https://manuscripts.sefaria.org/munich-manuscript/munich-manuscript-95Cod.hebr.95pg.{num}.jpg'})
    #     change_refs(page, [])
    # for num, refs in ((1130, 'Mishnah Oktzin 3:9-12'), (1134, 'Pirkei Avot 5:20-6:11')):
    #     new_munich_msp(num, refs)
