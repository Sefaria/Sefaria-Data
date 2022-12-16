import django

django.setup()

import re
from sefaria.model import *


def add_new_term_for_ka():
    """
    This function checks if a term exists for the Kuntres Acharon, and if not, creates a term.
    """

    term_set = TermSet({'name': 'Kuntres Acharon'})
    if term_set.count() > 0:
        print("Kuntres Acharon term already exists")
    else:
        en_title = "Kuntres Acharon"
        he_title = 'קונטרס אחרון'
        term_dict = {
            'name': en_title,
            'scheme': 'toc_categories',
            'titles': [{'lang': 'en', 'text': en_title, 'primary': True},
                       {'lang': 'he', 'text': he_title, 'primary': True}]
        }

        print("Creating a term for Kuntres Acharon")
        term = Term(term_dict)
        term.save()


def get_all_segments(title):
    """
    Loads all segments of the text to a list of dicts, where the keys are the segment ref, and the text.
    :param title: String. Title of the text
    :return: List of refs and text by segment
    """
    all_text = []

    # Defining the callback function to append to the list
    def action(segment_str, tref, he_tref, version):
        # Append each segment of text to the list
        all_text.append({'tref': tref, 'text': segment_str})

    text = Version().load(
        {"title": title,
         "versionTitle": 'Kehot Publication Society'})

    if text:
        text.walk_thru_contents(action)

    return all_text


def create_inline_ref_link(main_text_ref, ka_ref, data_order, data_label, save=True):
    """
    Creates a link with inline-reference metadata between the Kuntres Acharon and the main body
    of the Shulchan Arukh HaRav text.
    :param main_text_ref: String. The segment ref for the corresponding text from the Shulchan Arukh HaRav
    :param ka_ref: String. The segment ref for the corresponding segment of Kuntres Acharon
    :param data_order: String. The numeric value of the link in the sequence of the section
    :param data_label: String. The label for the inline reference, in our case a Hebrew letter corresponding to the value of the data-label
    :param save: Boolean. A boolean for testing purposes, to avoid saving the links to the DB
    """
    link_creation_dict = {
        'refs': [main_text_ref, ka_ref],
        'type': 'commentary',
        # 'auto': True,
        'inline_reference': {
            'data-order': int(data_order),
            'data-commentator': "Kuntres Acharon",
            'data-label': data_label
        }}

    if save:
        try:
            Link(link_creation_dict).save()
            print(f"Created inline-ref link between {main_text_ref} and {ka_ref}")
        except Exception as e:
            print(e)


def create_html_tags(data_order, data_label):
    """
    This function creates the HTML tag to be inserted for the frontend appearance of inline-references.
    :param data_order: String. A number representing the sequential order of the link in the section.
                       ex: In section A: The first link will have a data-order of 1, the second link will have a data-order of 2
                           In section B: The first link will have a data-order of 1, the second link will have a data-order of 2
                           etc.
    :param data_label: String. A Hebrew letter representing the gematria value of data-order for labeling in the text.
    """
    return f" <i data-commentator=\"Kuntres Acharon on Shulchan Arukh HaRav\" data-order=\"{data_order}\" data-label=\"{data_label}\"></i> "


def find_gematria_markers(text):
    """
    Given a segment of Shulchan Arukh HaRav, find the existing Gematria labels.
    :param text: String. Text from the Shulchan Arukh HaRav.
    """
    html_markers = re.findall(r"data-order=\"(.*?)\"></i>", text)
    return html_markers


def get_chelek(tref):
    """
    Given a tref for the main text of Shulchan Arukh HaRav, extract the Chelek (section) name
    :param tref: String. The textual reference.
    :return chelek: String. The chelek (section) of the tref.
    """
    chelek = re.findall(r"Shulchan Arukh HaRav, (.*?)[,\d]", tref)
    if chelek:
        return chelek[0].strip()
    return None


def get_siman(tref, chelek):
    """
    Given a tref and a chelek for the main text of Shulchan Arukh HaRav, extract the siman. In Choshen Mishpat, it will
    be a name, in the rest of the Sefer it is a numeric value.

    Note: Yoreh Deah has one section which is also named, as opposed to numbered ("Shulchan Arukh HaRav, Yoreh Deah, Laws of Interest and Iska")
    This code does not account for that, since there are no Kuntres Acharon links to that section, and therefore it is not needed.

    :param tref: String. The textual reference.
    :param chelek: String. The chelek (section) of the tref.
    :return siman: String. The siman (segment) number of the tref.
    """

    if chelek != "Choshen Mishpat":
        siman_patt = f"Shulchan Arukh HaRav, {chelek} (.*):\d"
        siman_patt = re.compile(siman_patt)
        siman = re.findall(siman_patt, tref)
    else:
        siman = re.findall(r"Shulchan Arukh HaRav, Choshen Mishpat, (.*?)\d", tref)

    if siman:
        return siman[0].strip()
    return None


def update_text(tref, text):
    """
    Given a tref, and a segment of text that has been updated with the appropriate HTML metadata,
    update the text for the ref.
    :param tref: String. The tref for a given section.
    :param text: String. The new text corresponding to that section.
    """
    oref = Ref(tref)
    tc = TextChunk(oref, vtitle="Kehot Publication Society", lang='he')
    tc.text = text
    tc.save()


def refresh_delete_KA_links():
    """
    Used for testing purposes when links were being created, and then needed to be deleted when adjusting.
    This function deletes any existing Kuntres Acharon refs in the DB.
    """
    links = LinkSet({'refs': {'$regex': 'Shulchan Arukh HaRav'}})
    for link in links:
        if 'Kuntres Acharon' in link.refs[0]:
            link.delete()
            print("link deleted")


def validate_sequence():
    """
    This function is for testing purposes, it validates that all of the found links are in sequential order
    with their data-order, and we are not missing any sections from Kuntres Acharon.

    NOTE: We are expecting errors for Yoreh Deah 1, 2, and 18. These references are to other sources,
    and QA has asked us to ignore.
    """
    all_text = get_all_segments()
    markers = []
    for text in all_text:
        if text['is_KA'] == False:
            cur_main_text = text['text']
            cur_main_text_tref = text['tref']
            found_markers = re.findall(r"data-order=\"(.*?)\"></i>", cur_main_text)
            if found_markers:
                for m in found_markers:
                    markers.append({'marker': int(m), 'tref': cur_main_text_tref})

    prev_marker = markers[0]
    prev_chelek = get_chelek(prev_marker['tref'])
    prev_siman = get_siman(prev_marker['tref'], prev_chelek)
    for i in range(1, len(markers)):
        cur_marker = markers[i]
        chelek = get_chelek(cur_marker['tref'])
        siman = get_siman(cur_marker['tref'], chelek)

        if prev_siman == siman and cur_marker['marker'] - prev_marker['marker'] > 1:
            print(
                f"ERROR: Marker difference greater than one between {prev_marker['tref']} (value of {prev_marker['marker']}) and {cur_marker['tref']} (value of {cur_marker['marker']})")

        prev_marker = cur_marker
        prev_chelek = chelek
        prev_siman = siman


def match_link_html():
    """
    The main function of the script. This function executes the three steps needed to achieve the task:
    1. MATCH - Matching the appropriate segments of Kuntres Acharon to the main text of Shulchan Arukh HaRav
    2. LINK - Creating links between the matching segments
    3. HTML - Creating the appropriate HTML tags for the inline-references, and inserting them into the text appropriately.
    """

    sar_text = get_all_segments("Shulchan Arukh HaRav")

    for text in sar_text:
        cur_main_text = text['text']
        cur_main_text_tref = text['tref']
        chelek = get_chelek(cur_main_text_tref)
        siman = get_siman(cur_main_text_tref, chelek)

        markers = find_gematria_markers(cur_main_text)
        found_labels = re.findall(r"data-label=\"(.*?)\"\s", cur_main_text)

        # for each marker
        for i in range(len(markers)):
            marker = markers[i]
            label = found_labels[i]
            is_last_marker_for_siman = False if i < len(markers) - 1 else True

            if chelek != "Choshen Mishpat":
                ka_ref = f"Kuntres Acharon on Shulchan Arukh HaRav, {chelek} {siman}:{marker}"
            else:
                ka_ref = f"Kuntres Acharon on Shulchan Arukh HaRav, Choshen Mishpat, {siman} {marker}"

            # MATCHING and LINKING
            # If cur ref is SAR OC 8:x, the KA ref will be SAR KA OC 8:marker_in_gematria
            create_inline_ref_link(main_text_ref=cur_main_text_tref,
                                   ka_ref=ka_ref,
                                   data_order=marker,
                                   data_label=label,
                                   save=True)

            # HTML
            # Update text for HTML tag to new index (data-commentator needs to be the collective title)
            main_text_with_html = cur_main_text.replace("data-commentator=\"Shulchan Arukh HaRav\"",
                                                        "data-commentator=\"Kuntres Acharon\"")

            # Update the text in the database only once all of the tags in the siman have been accounted for
            if is_last_marker_for_siman:
                update_text(tref=cur_main_text_tref, text=main_text_with_html)
            else:
                cur_main_text = main_text_with_html


if __name__ == '__main__':
    add_new_term_for_ka()
    match_link_html()
    # validate_sequence()
