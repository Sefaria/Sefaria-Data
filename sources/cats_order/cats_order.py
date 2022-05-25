import django
django.setup()
from sefaria.model import *
from sefaria.model.category import TocTree, TocCategory
from sefaria.site.categories import REVERSE_ORDER, CATEGORY_ORDER, TOP_CATEGORIES


def _explicit_order_and_title(node):
    """
    Return sort key as tuple:  (isString, value)
    :param node:
    :return:
    """
    title = node.primary_title("en")

    # First sort by global order list below
    try:
        return (False, CATEGORY_ORDER.index(title))

    # Sort top level Commentary categories just below their base category
    except ValueError:
        if isinstance(node, TocCategory):
            temp_cat_name = title.replace(" Commentaries", "")
            if temp_cat_name in TOP_CATEGORIES:
                return (False, CATEGORY_ORDER.index(temp_cat_name) + 0.5)

        # Sort by an explicit `order` field if present
        # otherwise into an alphabetical list
        res = getattr(node, "order", title)
        return (isinstance(res, str), res)

tt = TocTree(library)
for cat in tt.all_category_nodes():
    if all([hasattr(ca, "base_text_order") for ca in cat.children]):
        continue
    cat.children.sort(key=_explicit_order_and_title)
    cat.children.sort(
        key=lambda node: 'zzz' + node.primary_title("en") if isinstance(node, TocCategory) and node.primary_title("en") in REVERSE_ORDER else 'a')
    print(cat)
    new_ord = 5

    for child in cat.children:
        ord = None
        title = child.primary_title("en")
        try:
            ord = CATEGORY_ORDER.index(title)
        except ValueError:
            if isinstance(child, TocCategory):
                temp_cat_name = title.replace(" Commentaries", "")
                if temp_cat_name in TOP_CATEGORIES:
                    ord = CATEGORY_ORDER.index(temp_cat_name) + 0.5

            if not ord:
                res = getattr(child, "order", title)
                if not isinstance(res, str):
                    ord = res
        if child.primary_title("en") in REVERSE_ORDER:
            ord = -1

        if ord != None:
            if ord == -1:
                new_ord = -5
            try:
                object = child.get_category_object()
                if hasattr(object, 'order') and object.order == new_ord:
                    new_ord += 5
                    continue
                object.order = new_ord
            except AttributeError:
                if cat.get_category_object().path in [['Halakhah'], ['Kabbalah'], ['Second Temple']]:
                    object = library.get_index(child.get_primary_title())
                    if hasattr(object, 'order') and object.order == [new_ord]:
                        new_ord += 5
                        continue
                    object.order = [new_ord]
                else:
                    continue
            print(object, object.order)
            object.save()
            new_ord += 5

