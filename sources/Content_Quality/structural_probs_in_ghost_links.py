from sources.functions import *
with open("broken_links", 'r') as f:
    for line in f:
        refs = eval(line.split("]")[0]+"]")
        empty_ref = ""
        if len(Ref(refs[0]).text('he').text) == 0:
            empty_ref = refs[0]
        elif len(Ref(refs[1]).text('he').text) == 0:
            empty_ref = refs[1]
        assert len(empty_ref) > 0
        i = Ref(empty_ref).index
        if " on " in i.title:
            if i.categories[0] == "Tanakh" and getattr(i, "base_text_titles", None) and len(i.base_text_titles) == 1:
                base_text_title = i.base_text_titles[0]
                base_ref = empty_ref.replace(i.title, base_text_title)
                if base_ref.find(":") != base_ref.rfind(":"):
                    base_ref = ":".join(base_ref.split(":")[:-1])
                if len(Ref(base_ref).text('he').text) == 0:
                    print(empty_ref)