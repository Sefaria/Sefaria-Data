# -*- coding: utf-8 -*-
import django

django.setup()

from sefaria.model import *
from sefaria.helper import category
from sources import functions


def create_term_and_category():
    """
    Index() objects for texts have a collective title, which must be a Sefaria Term() object. Therefore, the
    first step for creating indices is creating a Term which can serve as the collective title.

    Additionally, Index() objects must have categories, which is a list containing a path to the category. The
    path is in order of how someone can browse from the Table of Contents, so in this case it goes from
    "Mishnah" to "Modern Commentary on Mishnah" (both pre-existing categories) to our new category, nested beneath
    the pre-existing ones, "My Sample Commentary". The new category must also be a Term() object, which is
    why Term() creation happens first.

    This function creates a new Term(), and a new Category() assuming they do not already exist.
    """
    # Check if the Term already exists
    ts = TermSet({'name': 'My Sample Commentary'})
    if ts.count() == 0:

        # If the Term does not yet exist, create the Term
        t = Term()

        # Add the Term name
        t.name = "My Sample Commentary"

        # Create the primary titles, in English and Hebrew
        t.add_primary_titles("My Sample Commentary", "פירוש דוגמא")

        # Save the Term to the Database.
        t.save()

    # Check if the Category already exists
    cs = CategorySet({'sharedTitle': 'My Sample Commentary'})
    if cs.count() == 0:

        # If it does not yet exist, create the category by passing in a valid path, with the new
        # category at the end.
        category.create_category(["Mishnah", "Modern Commentary on Mishnah", "My Sample Commentary"])


def create_index_record(en_title, he_title):
    """
    Creating the Index record, or the Schema, is a critical first step to creating an Index.
    The Index will be based on this Schema record, and needs to be created first.

    :param en_title: The English title of the Index
    :param he_title: The Hebrew title of the Index
    :return record: The Schema for the Index creation
    """

    # Create a Schema Node
    record = SchemaNode()

    # Concatenate the Hebrew title for the Schema
    he_title = "פירוש דוגמא על " + he_title

    # Concatenate the English title for the Schema
    en_title = f"My Sample Commentary on {en_title}"

    # Add the English title as a primary title with the proper language code "en"
    record.add_title(en_title, 'en', primary=True, )

    # Add the Hebrew title as a primaru title with the proper language code "he"
    record.add_title(he_title, "he", primary=True, )

    # Create the key, by concatenating the title name with the collective title for the
    # overarching commentary
    record.key = f"My Sample Commentary on {en_title}"

    # Create the collective title, the string passed must already be a term
    record.collective_title = "My Sample Commentary"

    return record


def add_text_node(record):
    """
    Helper function which created a JaggedArrayNode() for the text, and appends it
    to our overarching record (SchemaNode()).
    :param record: Our SchemaNode()
    :return: None. Modifies the provided record.
    """

    # Create a JaggedArrayNode for text
    text_node = JaggedArrayNode()

    # Set the key to "default"
    text_node.key = "default"
    text_node.default = record.primary_title()

    # Set the depth of the text based on specifications
    text_node.depth = 3

    # Set the addressTypes and the corresponding sectionNames, the number of items in the list
    # will correspond to the depth of the text. For example, a depth-2 text like the Tanakh
    # would have addressTypes = ["Integer", "Integer"] and sectionNames = ["Perek", "Pasuk"]
    text_node.addressTypes = ['Integer', 'Integer', 'Integer']
    text_node.sectionNames = ['Chapter', 'Mishnah', 'Paragraph']

    # Append the text node to the parent record (SchemaNode).
    record.append(text_node)


def create_index_main():
    """
    This function calls the other helper functions above to create an Index for the Sample Commentary
    on each Mishnah. Each Mishnah commentary will live as a separate Index, under a shared collective title.
    So for example: "My Sample Commentary on Berakhot", "My Sample Commentary on Demai", "My Sample Commentary on Peah"
    are each independent indices.
    The collective title is "My Sample Commentary".
    """

    # Query a list of all Mishnah indices
    mishnayot = library.get_indexes_in_category("Mishnah", full_records=True)

    # For each Mishnah
    for mishnah_index in mishnayot:

        # Retrieve the English title of the Index
        en_title = mishnah_index.get_title("en")

        # Retrieve the Hebrew title of the Index
        he_title = mishnah_index.get_title("he")

        # Create the record (aka the SchemaNode) using create_index_record() passing in
        # the English and Hebrew titles of the record.
        record = create_index_record(en_title, he_title)

        # Add a text node to the record
        add_text_node(record)

        # Validate the SchemaNode record
        record.validate()

        # Create the Index
        # (Everything until this point was creating the SCHEMA for the index. Below, we will
        # actually create the index itself, by appropriately filling out the necessary fields.)
        index = {
            # The primary title of the SchemaNode record
            "title": record.primary_title(),

            # The category path, as created above
            "categories": ["Mishnah", "Modern Commentary on Mishnah", "My Sample Commentary"],

            # A serialization of the SchemaNode record
            "schema": record.serialize(),

            # The following fields allow the commentary we are creating to
            # auto-link as a commentary to the base text. So in our case, the
            # commentary "My Sample Commentary on Mishnah Berakhot" will link
            # "Mishnah Berakhot" as the base_text_titles, as a commentary, dependant, and many_to_one.
            "base_text_titles": [en_title],
            "base_text_mapping": "many_to_one",
            "is_dependant": True,
            "dependence": "Commentary"
        }

        # Use the function post_index to post the Index to the API locally.
        functions.post_index(index)

        print(index)


if __name__ == '__main__':
    create_term_and_category()
    create_index_main()