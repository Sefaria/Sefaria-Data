import django

django.setup()

from sefaria.model import *
import time


def rename_old():
    index_query = {"title": "Mekhilta DeRabbi Yishmael"}
    index = Index().load(index_query)
    print(f"Retrieved {index.title}")
    index.set_title("Mekhilta DeRabbi Yishmael Old", lang="en")
    index.set_title("מכילתא דרבי ישמעאל ישן", lang="he")
    index.save()
    print(f"Saved and renamed {index.title}")


def rename_new():
    index_query = {"title": "Mekhilta DeRabbi Yishmael Beeri"}
    index = Index().load(index_query)
    print(f"Retrieved {index.title}")
    index.set_title("Mekhilta DeRabbi Yishmael", lang="en")
    index.set_title("מכילתא דרבי ישמעאל", lang="he")
    index.save()
    print(f"Saved and renamed {index.title}")


if __name__ == '__main__':
    rename_old()
