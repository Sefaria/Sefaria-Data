#encoding=utf-8
import django
django.setup()
from sefaria.model import *
from sefaria.model.category import TocCategory

#create new terms and categories
if not Term().load({"name": "English Explanation of Mishnah"}):
    t = Term()
    t.name = u"English Explanation of Mishnah"
    t.add_primary_titles(t.name, u"ביאור אנגלי על המשנה")
    t.save()



c = Category().load({"path": ["Modern Works", "Mishnah Yomit"]})
for toc_obj in c.get_toc_object().all_children():
    if isinstance(toc_obj, TocCategory):
        toc_obj.get_category_object().change_key_name("English Explanation of Mishnah")
c.change_key_name("English Explanation of Mishnah")
c.save()


#change index titles and version titles
pre_new_he = u"ביאור אנגלי על "
pre_new_en = "English Explanation of "
indices = library.get_indices_by_collective_title("Mishnah Yomit")
for i, index in enumerate(indices):
    print "CHANGING INDEX TITLE for {}".format(index)
    print index
    index = library.get_index(index)
    mishnah_en = index.base_text_titles[0]
    mishnah_he = library.get_index(mishnah_en).get_title('he')
    new_en = pre_new_en + mishnah_en
    new_he = pre_new_he + mishnah_he
    index.set_title(new_he, "he")
    index.save()
    index.set_title(new_en, "en")
    index.save()
    index.collective_title = "English Explanation of Mishnah"
    new_cat = list(index.categories)
    new_cat[1] = "English Explanation of Mishnah"
    index.categories = new_cat
    index.save()
    print "NOW CHANGING VERSION STATE TITLE"
    index = library.get_index(new_en)
    vs = index.versionSet()
    v = vs[0]
    v.versionTitle = "Mishnah Yomit by Dr. Joshua Kulp"
    v.save()


c = Category().load({"path": ["Modern Works", "Mishnah Yomit"]})
c.delete()
