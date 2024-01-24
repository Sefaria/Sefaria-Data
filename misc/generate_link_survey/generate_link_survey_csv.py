import logging

import django

django.setup()

from sefaria.model import *
import time
import csv
import os

logging.basicConfig(filename='logfile.log', level=logging.INFO)



def write_errors_to_csv(file_name, list, index_name, code="w"):
    """
    Function to write bad refs in Links to a CSV for future QA.
    This function is a typical "Write-to-file" function, except it has custom styling
    for the nature of the output.
    :param file_name String: Name of the file to output the data to
    :param list List: A list of the exception in position 0, and the link id in position 1
    :param code String: A code of either "w" (write, overwriting) or "a" (append to existing) determining the write behavior of the function
    """
    with open(file_name, code, newline='') as file:
        # Create a CSV writer
        writer = csv.DictWriter(file, fieldnames=["index", "link_id", "refs", "error_msg"])

        # Write the data to the CSV file
        csv_dict = {"index": index_name, "link_id": list[1], "refs": list[2], "error_msg": list[0]}
        writer.writerow(csv_dict)


def write_to_csv(file_name, dict):
    """
    This function writes the data about each index to a CSV progressively, saving
    after each index to prevent data loss with such a long running function.
    :param file_name String: Name of the CSV file
    :param dict Dictionary: A dictionary where the keys correspond to the column names, and the values the row data for the CSV
    """

    # Check if the file already exists
    file_exists = True
    try:
        with open(file_name, 'r'):
            pass
    except FileNotFoundError:
        file_exists = False

    # Open the CSV file in append mode
    with open(file_name, 'a', newline='') as file:
        # Create a CSV writer
        writer = csv.DictWriter(file, fieldnames=dict.keys())

        # Write header only if the file is newly created
        if not file_exists:
            writer.writeheader()

        # Write the data to the CSV file
        writer.writerow(dict)


def get_distinct_indices_linked_to_text(ls, index_name):
    """
    Creates a count dict of where the key is an index, and the value is the number of times it is
    linked to the given text.
    :param ls LinkSet: The linkset of all links to the current index
    :param index_name String: The name of the current index
    :return len(counts) Int: The total number of distinct indices linked to the current index
    :return counts Dictionary: The counts dictionary. For example {"Berakhot": 10, "Ketubot": 11} would indicate that
                                Berakhot is linked to the current index 10 times, and Ketubot 11 times.
    """
    counts = {}

    for link in ls:

        idx1 = None
        idx2 = None

        try:
            idx1 = Ref(link.refs[0]).index.title
            idx2 = Ref(link.refs[1]).index.title
        except Exception as e:
            write_errors_to_csv("broken_links.csv", [e, link._id, link.refs], index_name, "a")

        # If the index is already in the dict, increment. If not yet present, add with
        # a value of 1. Check to make sure not counting the index itself (i.e. in a link Genesis-Mekhilta,
        # we wouldn't want to count the Genesis side, if that's the index we're checking).
        if idx1 and idx1 != index_name:
            counts[idx1] = counts.get(idx1, 0) + 1
        if idx2 and idx2 != index_name:
            counts[idx2] = counts.get(idx2, 0) + 1

    return len(counts), counts


def get_distinct_category_counts(ls, index_name):
    """
    Returns a dictionary where the keys are the categories, and the value is another dict containing the total
    number of links to the current index within that category (for example, 3,198 Tanakh links) as well as the
    number of distinct indices linked within that category (for example, of the 3,198 total Tanakh links, there are 12 distinct
    books of Tanakh where those links appear).
    :param ls LinkSet: The LinkSet of the current index
    :param index_name: The name of the current index
    :return data Dictionary: Category counts dictionary
    """
    category_counts = {}

    for link in ls:

        idx1 = None
        idx2 = None
        cat1 = None
        cat2 = None

        try:
            idx1 = Ref(link.refs[0]).index
            idx2 = Ref(link.refs[1]).index
        except Exception as e:
            logging.info(e)

        if idx1:
            cat1 = idx1.categories[0]
            cat1_index_title = idx1.title

        if idx2:
            cat2 = idx2.categories[0]
            cat2_index_title = idx2.title

        # Appending the index to the dict by category,
        # checking to ensure that the index being added is the link,
        # not the index itself being linked.
        if cat1 and cat1 in category_counts and cat1_index_title != index_name:
            category_counts[cat1].append(cat1_index_title)
        elif cat1 and cat1 not in category_counts and cat1_index_title != index_name:
            category_counts[cat1] = [cat1_index_title]

        if cat2 and cat2 in category_counts and cat2_index_title != index_name:
            category_counts[cat2].append(cat2_index_title)
        elif cat2 and cat2 not in category_counts and cat2_index_title != index_name:
            category_counts[cat2] = [cat2_index_title]

    # Crunching distinct numbers to return
    data = {}
    for category in category_counts:
        data[category] = {"distinct_texts_linked_in_category": len(set(category_counts[category])),
                          "number_of_links": len(category_counts[category])}
    return data


def get_word_count(i):
    vs = VersionSet({"title": i.title})

    # If no version exists
    if len(vs) < 1:
        return 0

    # Dictionaries have depth issues for wordcount on Ref, so they
    # are handled independently here as a version.
    if i.categories == ['Reference', 'Dictionary']:
        return vs[0].word_count()

    has_is_primary = False
    for v in vs:
        if hasattr(v, 'isPrimary'):
            has_is_primary = True
            if v.isPrimary:
                wc = Ref(v.title).word_count(lang=v.language)

    # No isPrimary on any of the versions
    if not has_is_primary:
        first_v = vs[0]
        wc = Ref(first_v.title).word_count(lang=first_v.language)

    return wc


def calculate_stats(node):
    """
    The main engine of this code, this is the callback function passed into traverse_tree()
    For every node which is an index in the ToC Tree, it calculates each of the desired statistics
    as explained in the line-by-line comments.
    As it proceeds through an index, it concatenates the results into a dictionary, which is written
    to a csv. Instructional print messages are printed to the console.
    :param node: A node in the Sefaria ToC tree.
    """
    # Skip category nodes
    if type(node) == category.TocCategory or type(node) == category.TocCollectionNode:
        return

    total_time_start = time.time()
    result_data = {}

    i = node.get_index_object()
    index_name = i.title

    # Index name
    result_data["Index Title"] = index_name
    print(f"Surveying {index_name}")

    # Top level category
    top_level_category = i.categories[0]
    result_data["Top Level Index Category"] = top_level_category
    print(f"{index_name} top level category is {top_level_category}")

    # Number of links to Index
    linkset_to_index = LinkSet(Ref(i.title))
    num_links_to_index = linkset_to_index.count()
    result_data["Total Number of Links to Index"] = num_links_to_index
    print(f"{index_name} has {num_links_to_index} total links")

    # Primary version (or if no primary, first version) word count
    num_words_in_primary_version = get_word_count(i)


    result_data["Word Count of Primary Version"] = num_words_in_primary_version
    print(f"Primary version word count is {num_words_in_primary_version}")

    # Links over number of words
    links_over_num_words = num_links_to_index / num_words_in_primary_version if num_words_in_primary_version != 0 else -1
    result_data["Number of Links / Number of Words"] = links_over_num_words
    print(f"Links over num words is {links_over_num_words}")

    # Count of distinct indices linked to this text
    distinct_texts_linked, idx_counts_dict = get_distinct_indices_linked_to_text(linkset_to_index, index_name)
    result_data["Number of distinct texts linked to this text"] = distinct_texts_linked
    print(f"Count of distinct indices linked to {index_name} is {distinct_texts_linked}")

    # Number of top-level categories linked to this text
    category_count_dict = get_distinct_category_counts(linkset_to_index, index_name)
    num_categories_linked_to_text = len(category_count_dict)
    result_data["Number of top-level Categories linked"] = num_categories_linked_to_text
    print(f"Number of categories linked to {index_name} are {num_categories_linked_to_text}")

    categories = ["Tanakh", "Mishnah", "Talmud", "Midrash", "Halakhah", "Kabbalah", "Liturgy",
                  "Jewish Thought", "Tosefta", "Chasidut", "Musar", "Responsa", "Second Temple", "Reference"]

    num_texts_linked_by_category_dict = {}
    num_links_by_category_dict = {}
    checker = 0
    for c in categories:
        num_texts = category_count_dict[c]["distinct_texts_linked_in_category"] if c in category_count_dict else 0
        num_texts_linked_by_category_dict[c] = num_texts
        checker += num_texts

        num_links = category_count_dict[c]["number_of_links"] if c in category_count_dict else 0
        num_links_by_category_dict[c] = num_links

        text_key = f"Number of distinct texts linked from {c}"
        links_key = f"Total number of links from {c}"
        result_data[text_key] = num_texts
        result_data[links_key] = num_links

        print(f"{index_name} has {num_texts} distinct texts linked in {c}")
        print(f"{index_name} has {num_links} total links linked in {c}")

    write_to_csv("links_stats.csv", result_data)
    total_time_end = time.time()
    print(f"Total time for {index_name} is: {(total_time_end - total_time_start) / 60.0}")
    print("----------------------------------\n\n")


if __name__ == '__main__':
    date = time.localtime()
    csv_file_path = "links_stats.csv"
    if os.path.exists(csv_file_path):
        # Delete the file
        os.remove(csv_file_path)
        print(f"The file '{csv_file_path}' has been deleted.")
    else:
        print(f"The file '{csv_file_path}' does not exist.")
    root = library.get_toc_tree().get_root()
    root.traverse_tree(calculate_stats)