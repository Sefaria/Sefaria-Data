import django

django.setup()
from sefaria.model import *


def get_peninei_halakhah_titles():
    """
    Get all titles of books starting with 'Peninei Halakhah'
    """
    indexes = IndexSet({'title': {'$regex': '^Peninei Halakhah'}})

    titles = []
    for index in indexes:
        title_en = index.title
        title_he = index.get_title('he')
        titles.append({
            'english': title_en,
            'hebrew': title_he
        })

    return titles


if __name__ == '__main__':
    titles = get_peninei_halakhah_titles()

    print(f"\nFound {len(titles)} books starting with 'Peninei Halakhah':\n")
    print("-" * 80)

    for i, book in enumerate(titles, 1):
        print(f"{i}. {book['english']}")
        # print(f"   {book['hebrew']}")
        print()
