import os
import sys
import argparse

# # Add the parent directory to the path to import Sefaria functions
# script_dir = os.path.dirname(os.path.abspath(__file__))
# parent_dir = os.path.dirname(script_dir)
# sys.path.insert(0, parent_dir)

import django

django.setup()
from sefaria.model import *
from sources.functions import *

# Import parashot lists from functions
from sources.functions import eng_parshiot, heb_parshiot

# Configuration
CONFIG = {
    "title_en": "The Kehot Chumash; A Chasidic Commentary",
    "title_he": u"פירוש חסידי על התורה",
    # "collective_title": "Kehot Chumash",
    "categories": ["Tanakh", "Modern Commentary on Tanakh"],
    "torah_books": [
        ("Genesis", u"בראשית"),
        ("Exodus", u"שמות"),
        ("Leviticus", u"ויקרא"),
        ("Numbers", u"במדבר"),
        ("Deuteronomy", u"דברים")
    ],
    "sections": [
        ("Introduction", u"הקדמה", "shared_term"),
        ("Prologue", u"פתח דבר", "primary_titles"),
        ("Parashah Overviews", u"הקדמות לפרשה", "primary_titles")
    ]
}


def create_collective_title_term(server=None):
    """
    Create the collective title term if it doesn't exist
    """
    term_name = CONFIG["collective_title"]

    # Check if term already exists
    try:
        existing_term = Term().load({"name": term_name})
        if existing_term:
            print(f"Term '{term_name}' already exists.")
            return True
    except:
        pass

    # Create the term
    term_obj = {
        "name": term_name,
        "scheme": "commentary_works",
        "titles": [
            {
                "lang": "en",
                "text": term_name,
                "primary": True
            },
            {
                "lang": "he",
                "text": u"חומש קהות",
                "primary": True
            }
        ]
    }

    try:
        if server:
            post_term(term_obj, server=server)
        else:
            post_term(term_obj)
        print(f"Created term: {term_name}")
        return True
    except Exception as e:
        print(f"Error creating term '{term_name}': {e}")
        return False


def create_kehot_chumash_index():
    """
    Create the comprehensive index for The Kehot Chumash; A Chasidic Commentary
    """

    # Create the root schema node
    root = SchemaNode()
    root.add_primary_titles(CONFIG["title_en"], CONFIG["title_he"])
    root.key = CONFIG["title_en"]

    # Add special sections (Introduction, Prologue, and Parashah Overviews)
    for section_en, section_he, title_type in CONFIG["sections"]:
        if section_en == "Parashah Overviews":
            # Create SchemaNode for Parashah Overviews with all parashot as children
            section_node = SchemaNode()
            section_node.key = section_en

            if title_type == "shared_term":
                section_node.add_shared_term(section_en)
            else:
                section_node.add_primary_titles(section_en, section_he)

            # Add all 54 Torah parashot as children
            for parsha_en, parsha_he in zip(eng_parshiot, heb_parshiot):
                parsha_node = JaggedArrayNode()
                parsha_node.key = parsha_en

                # Try to use shared term if it exists, otherwise use primary titles
                try:
                    parsha_node.add_shared_term(parsha_en)
                except:
                    parsha_node.add_primary_titles(parsha_en, parsha_he)

                parsha_node.add_structure(["Paragraph"])
                section_node.append(parsha_node)

        else:
            # Regular JaggedArrayNode for Introduction and Prologue
            section_node = JaggedArrayNode()
            section_node.key = section_en

            if title_type == "shared_term":
                section_node.add_shared_term(section_en)
            else:
                section_node.add_primary_titles(section_en, section_he)

            section_node.add_structure(["Paragraph"])

        root.append(section_node)

    # Add default nodes for each book of the Torah
    for book_en, book_he in CONFIG["torah_books"]:
        book_node = JaggedArrayNode()
        book_node.add_primary_titles(book_en, book_he)
        book_node.key = book_en
        book_node.add_structure(["Chapter", "Verse", "Paragraph"])
        book_node.toc_zoom = 2  # Appropriate zoom level for Torah commentaries
        root.append(book_node)

    # Validate the schema
    root.validate()

    # Create the index dictionary
    index = {
        "title": CONFIG["title_en"],
        "schema": root.serialize(),
        "categories": CONFIG["categories"],
        "dependence": "Commentary",
        "base_text_titles": [book[0] for book in CONFIG["torah_books"]],
        # "collective_title": CONFIG["collective_title"]
    }

    return index


def validate_index_structure(index):
    """
    Validate the index structure before posting
    """
    required_fields = ["title", "schema", "categories", "dependence", "base_text_titles"]

    for field in required_fields:
        if field not in index:
            raise ValueError(f"Missing required field: {field}")

    # Validate categories
    if not isinstance(index["categories"], list) or len(index["categories"]) == 0:
        raise ValueError("Categories must be a non-empty list")

    # Validate base_text_titles
    expected_books = [book[0] for book in CONFIG["torah_books"]]
    if index["base_text_titles"] != expected_books:
        raise ValueError(f"Base text titles mismatch. Expected: {expected_books}")

    print("Index structure validation passed.")
    return True


def display_index_info(index):
    """
    Display detailed information about the created index
    """
    print("\n" + "=" * 60)
    print("INDEX INFORMATION")
    print("=" * 60)
    print(f"Title (EN): {index['title']}")
    print(f"Title (HE): {CONFIG['title_he']}")
    print(f"Categories: {' > '.join(index['categories'])}")
    print(f"Dependence: {index['dependence']}")
    print(f"Collective Title: {index.get('collective_title', 'None')}")
    print(f"Base Text Titles: {', '.join(index['base_text_titles'])}")

    print("\nSCHEMA STRUCTURE:")
    print("├── Introduction (הקדמה)")
    print("├── Prologue (פתח דבר)")
    print("├── Parashah Overviews (הקדמות לפרשה)")
    print("│   ├── [54 Torah Parashot]")
    for i, (book_en, book_he) in enumerate(CONFIG["torah_books"]):
        connector = "└──" if i == len(CONFIG["torah_books"]) - 1 else "├──"
        print(f"{connector} {book_en} ({book_he}) [Chapter:Verse:Paragraph]")

    print("=" * 60)


def main():
    """
    Main function with command line argument support
    """
    parser = argparse.ArgumentParser(description="Create Kehot Chumash index for Sefaria")
    parser.add_argument("--post", action="store_true", help="Actually post the index to server")
    parser.add_argument("--server", default="http://localhost:8000", help="Server URL")
    parser.add_argument("--create-term", action="store_true", help="Create collective title term")

    args = parser.parse_args()

    print("Creating index for 'The Kehot Chumash; A Chasidic Commentary'...")
    print(f"Server: {args.server}")

    try:
        # Create collective title term if requested
        # if args.create_term:
        #     print("\nCreating collective title term...")
        #     create_collective_title_term(args.server if args.post else None)

        # Create the index
        print("\nGenerating index structure...")
        index = create_kehot_chumash_index()

        # Validate the index
        print("\nValidating index structure...")
        validate_index_structure(index)

        # Display index information
        display_index_info(index)

        # Post to server if requested
        if args.post:
            print(f"\nPosting index to server: {args.server}")
            response = post_index(index, server=args.server)
            if response:
                print("Index posted successfully!")
            else:
                print("Error posting index.")
        else:
            print("\nIndex created successfully (not posted to server).")
            print("Use --post flag to actually post the index to Sefaria.")

        return index

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()