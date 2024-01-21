import django

django.setup()

from sefaria.model import *
import time


# Todo
# 1. Comments
# 2. Generate CSV
# 3. Run across indices


# Bug: Checker counts the number of idx-by-cat to make sure it matches count of distinct idx. On Tanakh, it doesn't match
# When I output the specific indices to check a set intersection, they are all there (and match the distinct idx count),
# Is something going wrong with the checker? Are we missing texts by category?


def write_to_txt(file_name, list, code="w"):
    with open(f'{file_name}.txt', code) as file:
        file.write(str(list[0]) + '. Link ID: ' + str(list[1]._id))


def get_distinct_indices_linked_to_text(ls, index_name):
    counts = {}

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

    # write_to_txt("distinct_idx", counts.keys())

    return len(counts), counts


def get_distinct_category_counts(ls, index_name):
    category_counts = {}

    for link in ls:
        try:
            idx1 = Ref(link.refs[0]).index
            idx2 = Ref(link.refs[1]).index
        except Exception as e:
            write_to_txt("bad_refs_in_links", [e, link], "a")

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

    ## For debugging, remove this later
    # set_cc = []
    # for c in category_counts:
    #     set_cc += set(category_counts[c])
    # write_to_txt("category_distinct_texts", set_cc)

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
    t1 = time.time()
    linkset_to_index = LinkSet({'refs': {"$regex": i.title}})
    num_links_to_index = linkset_to_index.count()
    t2 = time.time()
    print(f"{index_name} has {num_links_to_index} total links, in {(t2-t1)/60} min")

    # Primary version word count
    t1 = time.time()
    v = Version().load({"title": i.title, "isPrimary": True})
    num_words_in_primary_version = v.word_count()
    t2 = time.time()
    print(f"Primary version word count is {num_words_in_primary_version}, in {(t2-t1)/60} min")

    # Links over number of words
    links_over_num_words = num_links_to_index / num_words_in_primary_version
    print(f"Links over num words is {links_over_num_words}")

    # Count of distinct indices linked to this text
    t1 = time.time()
    distinct_texts_linked, idx_counts_dict = get_distinct_indices_linked_to_text(linkset_to_index, index_name)
    t2 = time.time()
    print(f"Count of distinct indices linked to {index_name} is {distinct_texts_linked}, in {(t2-t1)/60} min")

    # Number of top-level categories linked to this text
    t1 = time.time()
    category_count_dict = get_distinct_category_counts(linkset_to_index, index_name)
    num_categories_linked_to_text = len(category_count_dict)
    t2 = time.time()
    print(f"Number of categories linked to {index_name} are {num_categories_linked_to_text}, in {(t2-t1)/60} min")

    categories = ["Tanakh", "Mishnah", "Talmud", "Midrash", "Halakhah", "Kabbalah",
                  "Liturgy", "Jewish Thought", "Tosefta", "Chasidut", "Musar",
                  "Responsa", "Second Temple", "Reference"]

    num_texts_linked_by_category_dict = {}
    num_links_by_category_dict = {}
    checker = 0
    for c in categories:
        num_texts = category_count_dict[c]["distinct_texts_linked_in_category"] if c in category_count_dict else 0
        num_texts_linked_by_category_dict[c] = num_texts
        checker += num_texts

        num_links = category_count_dict[c]["number_of_links"] if c in category_count_dict else 0
        num_links_by_category_dict[c] = num_links

        print(f"{index_name} has {num_texts} distinct texts linked in {c}")
        print(f"{index_name} has {num_links} total links linked in {c}")


    print()
    print(checker)


if __name__ == '__main__':
    
    indices = ["Genesis", "Exodus", "Vayikra", "Bamidbar", "Devarim", "Berakhot"]
    for index in indices:
        total_time_start = time.time()
        callback(index)
        total_time_end = time.time()
        print(f"Total time for {index} is: {(total_time_end-total_time_start)/60.0}")
