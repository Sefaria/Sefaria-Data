# coding=utf-8
from sefaria.model import *
from sefaria.helper.nli import manuscript_data

NoteSet({"generated_by": "NLI_manuscript_linker"}).delete()

indxs = library.get_indexes_in_category("Tosefta") + library.get_indexes_in_category("Mishnah")
for title in indxs:
    if "Tosefta Keilim" in title:
        continue
    i = library.get_index(title)
    assert isinstance(i, Index)
    top_ref = Ref(i.title)
    section_refs = top_ref.all_subrefs()
    for section_ref in section_refs:
        print " - " + section_ref.normal()
        for manu in manuscript_data(section_ref):
            print " . " + section_ref.subref(manu["mi_code"]).normal()
            Note({
                "owner": 28,
                "public": True,
                "text": manu["desc_he"] + '<br/><a href="' + manu["app_url"] + '"><img src="' + manu["img_url"] + '"></a>',
                "type": "image",
                "ref": section_ref.subref(manu["mi_code"]).normal(),
                "title": manu["name_he"],
                "generated_by": "NLI_manuscript_linker"
            }).save()

indxs = library.get_indexes_in_category("Bavli")
for title in indxs:
    i = library.get_index(title)
    assert isinstance(i, Index)
    top_ref = Ref(i.title)
    section_refs = top_ref.all_subrefs()
    for section_ref in section_refs:
        print " - " + section_ref.normal()
        for manu in manuscript_data(section_ref):
            print " . "
            Note({
                "owner": 28,
                "public": True,
                "text": manu["desc_he"] + '<br/><a href="' + manu["app_url"] + '"><img src="' + manu["img_url"] + '"></a>',
                "type": "image",
                "ref": section_ref.subref(1).normal(),
                "title": manu["name_he"],
                "generated_by": "NLI_manuscript_linker"
            }).save()