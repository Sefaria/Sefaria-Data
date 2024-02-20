import django

django.setup()

from sefaria.model import *

index_titles = [
    "Covenant and Conversation; Genesis; The Book of the Beginnings",
    "Covenant and Conversation; Exodus; The Book of Redemption",
    "Covenant and Conversation; Leviticus; The Book of Holiness",
    "Covenant and Conversation; Numbers; The Wilderness Years",
    "Covenant and Conversation; Deuteronomy; Renewal of the Sinai Covenant",
    "Essays in Ethics; A Weekly Reading of the Jewish Bible",
    "I Believe; A Weekly Reading of the Jewish Bible",
    "Judaism's Life Changing Ideas; A Weekly Reading of the Jewish Bible",
    "Lessons in Leadership; a weekly reading of the Jewish Bible",
    "Studies in Spirituality; A Weekly Reading of the Jewish Bible"
]

for idx_title in index_titles:
    print(idx_title)
    index_object = Index().load({'title': idx_title})
    print(index_object)
    index_object.dependence = "Commentary"
    if "Covenant and Conversation" in idx_title:
        index_object.collective_title = "Covenant and Conversation"
    index_object.save()


