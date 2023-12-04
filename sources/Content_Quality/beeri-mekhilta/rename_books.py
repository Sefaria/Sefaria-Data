import django

django.setup()

from sefaria.model import *
import time



def rename_old():
    index_query = {"title": "Mekhilta DeRabbi Yishmael"}
    index = Index().load(index_query)
    print(f"Retrieved {index.title}")
    index.set_title("Mekhilta d'Rabbi Yishmael Old")
    index.save()
    print(f"Saved and renamed {index.title}")


def rename_new():
    index_query = {"title": "Mekhilta DeRabbi Yishmael Beeri"}
    index = Index().load(index_query)
    print(f"Retrieved {index.title}")
    index.set_title("Mekhilta DeRabbi Yishmael")
    index.save()
    print(f"Saved and renamed {index.title}")


if __name__ == '__main__':
    rename_old()
    time.sleep(10)
    rename_new()