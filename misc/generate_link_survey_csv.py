import django

django.setup()

from sefaria.model import *


def get_distinct_indices_linked_to_text(ls, index_name):
    counts = {}
    counts_by_category = {}
    for link in ls:
        try:
            idx1 = Ref(link.refs[0]).index.title
            idx2 = Ref(link.refs[1]).index.title
        except Exception as e:
            print(f"WARNING: Invalid Ref in links to {index_name}, link: {e}")

        # If it exists, increment - else create with a value of 0
        # Avoid counting the index itself as a link.
        if idx1 != index_name:
            counts[idx1] = counts.get(idx1, 0) + 1
        if idx2 != index_name:
            counts[idx2] = counts.get(idx2, 0) + 1

    return len(counts), counts


def get_distinct_category_counts(ls, index_name):
    category_counts = {}

    for link in ls:
        try:
            idx1 = Ref(link.refs[0]).index
            idx2 = Ref(link.refs[1]).index
        except Exception as e:
            print(f"WARNING: Invalid Ref in links to {index_name}, link: {e}")

        cat1 = idx1.categories[0]
        cat1_index_title = idx1.title
        cat2 = idx2.categories[0]
        cat2_index_title = idx2.title

        if cat1 in category_counts and cat1_index_title != index_name:
            category_counts[cat1].append(cat1_index_title)
        elif cat1 not in category_counts and cat1_index_title != index_name:
            category_counts[cat1] = [cat1_index_title]

        if cat2 in category_counts and cat2_index_title != index_name:
            category_counts[cat2].append(cat2_index_title)
        elif cat2 not in category_counts and cat2_index_title != index_name:
            category_counts[cat2] = [cat2_index_title]

    data = {}
    for category in category_counts:
        data[category] = {"distinct_texts_linked_in_category": len(set(category_counts[category])),
                          "number_of_links": len(category_counts[category])}

    return data


def callback(index_name):
    # Index name
    i = Index().load({"title": index_name})
    print(f"Surveying {i.title}")

    # Top level category
    top_level_category = i.categories[0]
    print(f"{index_name} top level category is {top_level_category}")

    # Number of links to Index
    linkset_to_index = LinkSet({'refs': {"$regex": i.title}})
    num_links_to_index = linkset_to_index.count()
    print(f"{index_name} has {num_links_to_index} total links")

    # Primary version word count
    v = Version().load({"title": i.title, "isPrimary": True})
    num_words_in_primary_version = v.word_count()
    print(f"Primary version word count is {num_words_in_primary_version}")

    # Links over number of words
    links_over_num_words = num_links_to_index / num_words_in_primary_version
    print(f"Links over num words is {links_over_num_words}")

    # Count of distinct indices linked to this text
    distinct_texts_linked, idx_counts_dict = get_distinct_indices_linked_to_text(linkset_to_index, index_name)
    print(f"Count of distinct indices linked to {index_name} is {distinct_texts_linked}")

    # Number of top-level categories linked to this text
    category_count_dict = get_distinct_category_counts(linkset_to_index, index_name)
    num_categories_linked_to_text = len(category_count_dict)
    print(f"Number of categories linked to {index_name} are {num_categories_linked_to_text}")

    categories = ["Tanakh", "Mishnah", "Talmud", "Midrash", "Halakha", "Kabbalah",
                  "Liturgy", "Jewish Thought", "Tosefta", "Chasidut", "Musar",
                  "Responsa", "Second Temple", "Reference"]

    num_texts_linked_by_category_dict = {}
    num_links_by_category_dict = {}
    for c in categories:
        num_texts = category_count_dict[c]["distinct_texts_linked_in_category"] if c in category_count_dict else 0
        num_texts_linked_by_category_dict[c] = num_texts

        num_links = category_count_dict[c]["number_of_links"] if c in category_count_dict else 0
        num_links_by_category_dict[c] = num_links

        print(f"{index_name} has {num_texts} distinct texts linked in {c}")
        print(f"{index_name} has {num_links} total links linked in {c}")



if __name__ == '__main__':
    callback("Genesis")
