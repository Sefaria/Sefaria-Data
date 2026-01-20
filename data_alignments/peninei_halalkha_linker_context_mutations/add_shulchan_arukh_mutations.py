#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to add linker context mutations to Peninei Halakhah books.

When a citation in Peninei Halakhah mentions "Shulchan Arukh" without specifying
which of the 4 parts, this mutation will automatically add the appropriate part
based on the book's subject matter.

Usage:
    python add_shulchan_arukh_mutations.py          # Dry run (debug mode)
    python add_shulchan_arukh_mutations.py --save   # Actually save to database
"""

import sys
import traceback

import django

django.setup()

from sefaria.model import library
from sefaria.model.text import Index

# Configuration
DEBUG_MODE = False

# Map of Peninei Halakhah books to their corresponding Shulchan Arukh section
BOOK_TO_SA_SECTION = {
    "Peninei Halakhah, Berakhot": "orach-chayim",
    "Peninei Halakhah, Days of Awe": "orach-chayim",
    "Peninei Halakhah, Family": "even-haezer",
    "Peninei Halakhah, Family Purity": "yoreh-deah",
    "Peninei Halakhah, Festivals": "orach-chayim",
    "Peninei Halakhah, Kashrut": "yoreh-deah",
    "Peninei Halakhah, Pesach": "orach-chayim",
    "Peninei Halakhah, Prayer": "orach-chayim",
    "Peninei Halakhah, Shabbat": "orach-chayim",
    "Peninei Halakhah, Shemitah and Yovel": "yoreh-deah",
    "Peninei Halakhah, Simchat Habayit U'Virkhato": "even-haezer",
    "Peninei Halakhah, Sukkot": "orach-chayim",
    "Peninei Halakhah, The Nation and the Land": "choshen-mishpat",
    "Peninei Halakhah, Women's Prayer": "orach-chayim",
    "Peninei Halakhah, Zemanim": "orach-chayim"
}

# Slug name mapping for display
SLUG_TO_NAME = {
    "orach-chayim": "Orach Chaim",
    "yoreh-deah": "Yoreh De'ah",
    "even-haezer": "Even HaEzer",
    "choshen-mishpat": "Choshen Mishpat"
}


def create_mutation(sa_section_slug):
    """
    Create a mutation object that adds the specified Shulchan Arukh section
    when only "shulchan-arukh" is mentioned.

    Args:
        sa_section_slug: One of the 4 SA section slugs

    Returns:
        dict: Mutation specification
    """
    return {
        "op": "add",
        "input_terms": ["shulchan-arukh"],
        "output_terms": [sa_section_slug]
    }


def add_mutation_to_book(book_title, sa_section_slug, debug_mode=True):
    """
    Add the mutation to a specific Peninei Halakhah book.

    Args:
        book_title: English title of the book
        sa_section_slug: The SA section slug to add
        debug_mode: If True, only print what would be done without saving

    Returns:
        dict: Result information
    """
    try:
        print(f"\n-- Processing: {book_title} (section slug: {sa_section_slug})")
        # Load the index
        index = library.get_index(book_title)
        print(f"   Loaded index: {index.title}")

        # Get the root node
        root_node = index.nodes
        print(f"   Root node: {root_node.full_title()}")

        # Check if mutations already exist
        existing_mutations = getattr(root_node, 'ref_resolver_context_mutations', None)
        print(f"   Existing mutations: {len(existing_mutations) if existing_mutations else 0}")

        # Create the new mutation
        new_mutation = create_mutation(sa_section_slug)
        print(f"   New mutation: {new_mutation}")

        # Prepare the mutation list
        if existing_mutations:
            # Check if this exact mutation already exists
            for mut in existing_mutations:
                if (mut.get('op') == new_mutation['op'] and
                    mut.get('input_terms') == new_mutation['input_terms'] and
                    mut.get('output_terms') == new_mutation['output_terms']):
                    print("   Mutation already exists; skipping.")
                    return {
                        'status': 'skipped',
                        'reason': 'Mutation already exists',
                        'book': book_title,
                        'section': SLUG_TO_NAME[sa_section_slug]
                    }
            mutations_list = existing_mutations + [new_mutation]
        else:
            mutations_list = [new_mutation]

        # Debug mode: just print what would be done
        if debug_mode:
            print(f"\n{'='*80}")
            print(f"BOOK: {book_title}")
            print(f"{'='*80}")
            print(f"Node: {root_node.full_title()}")
            print(f"Section to add: {SLUG_TO_NAME[sa_section_slug]} (slug: {sa_section_slug})")
            print(f"\nExisting mutations: {len(existing_mutations) if existing_mutations else 0}")
            if existing_mutations:
                for i, mut in enumerate(existing_mutations, 1):
                    print(f"  {i}. {mut}")
            print(f"\nNew mutation to add:")
            print(f"  {new_mutation}")
            print(f"\nTotal mutations after change: {len(mutations_list)}")
            print(f"{'='*80}")

            return {
                'status': 'debug',
                'book': book_title,
                'section': SLUG_TO_NAME[sa_section_slug],
                'node': root_node.full_title(),
                'mutation': new_mutation
            }

        # Actually save the changes
        root_node.ref_resolver_context_mutations = mutations_list

        # Validate the node
        print("   Validating node...")
        root_node.validate()

        # Save the index
        print("   Saving index...")
        index.save()
        print("   Save complete.")

        return {
            'status': 'saved',
            'book': book_title,
            'section': SLUG_TO_NAME[sa_section_slug],
            'node': root_node.full_title(),
            'mutation': new_mutation
        }

    except Exception as e:
        print(f"   ERROR: {e}")
        print(traceback.format_exc())
        return {
            'status': 'error',
            'book': book_title,
            'section': SLUG_TO_NAME.get(sa_section_slug, sa_section_slug),
            'error': str(e)
        }


def main():
    """Main execution function."""
    print("\n" + "="*80)
    print("PENINEI HALAKHAH - SHULCHAN ARUKH MUTATION SCRIPT")
    print("="*80)

    if DEBUG_MODE:
        print("\n🔍 RUNNING IN DEBUG MODE (no changes will be saved)")
        print("   To actually save changes, run with: --save")
    else:
        print("\n💾 RUNNING IN SAVE MODE (changes will be committed to database)")
        print("   WARNING: This will modify the database!")
        response = input("\n   Are you sure you want to continue? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("\n   Aborted by user.")
            sys.exit(0)

    print(f"\n📚 Processing {len(BOOK_TO_SA_SECTION)} Peninei Halakhah books...")

    results = {
        'saved': [],
        'debug': [],
        'skipped': [],
        'error': []
    }

    for book_title, sa_section_slug in BOOK_TO_SA_SECTION.items():
        print("\n" + "-"*80)
        result = add_mutation_to_book(book_title, sa_section_slug, debug_mode=DEBUG_MODE)
        status = result['status']
        results[status].append(result)

    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    if results['debug']:
        print(f"\n✓ Debug mode - reviewed {len(results['debug'])} books")
        print("  No changes were made to the database.")

    if results['saved']:
        print(f"\n✓ Successfully saved mutations for {len(results['saved'])} books:")
        for r in results['saved']:
            print(f"  - {r['book']} → {r['section']}")

    if results['skipped']:
        print(f"\n⊘ Skipped {len(results['skipped'])} books (mutations already exist):")
        for r in results['skipped']:
            print(f"  - {r['book']}")

    if results['error']:
        print(f"\n✗ Errors encountered for {len(results['error'])} books:")
        for r in results['error']:
            print(f"  - {r['book']}: {r['error']}")

    print("\n" + "="*80)
    print("MUTATION DETAILS")
    print("="*80)
    print("\nThese mutations will:")
    print("  1. Match citations containing 'Shulchan Arukh' (slug: shulchan-arukh)")
    print("  2. ADD the appropriate section based on the book's topic")
    print("  3. Only if that specific section doesn't already exist in the citation")
    print("\nExample:")
    print("  Input:  'Shulchan Arukh 25:4'")
    print("  Output: 'Shulchan Arukh, [Section] 25:4'")
    print("\n⚠️  NOTE: The mutation does NOT check if OTHER sections already exist!")
    print("   If 'Shulchan Arukh, Even HaEzer' appears, it will still add the default.")
    print("   This is a known limitation of the current mutation mechanism.")

    print("\n" + "="*80)

    if DEBUG_MODE:
        print("\n💡 To apply these changes, run: python add_shulchan_arukh_mutations.py --save")
    else:
        print("\n✅ Changes have been saved to the database!")

    print()


if __name__ == '__main__':
    main()
