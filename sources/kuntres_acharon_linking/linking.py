import django

django.setup()

import re
import csv
from sefaria.model import *
from sefaria.utils.hebrew import gematria


def get_all_segments():
    all_text = []

    # Defining the callback function to append to the list
    def action(segment_str, tref, he_tref, version):
        # Append each segment of text to the list
        is_ka = True if "Kuntres Acharon" in tref else False
        all_text.append({'tref': tref, 'text': segment_str, 'is_KA': is_ka})

    sar = Version().load(
        {"title": 'Shulchan Arukh HaRav',
         "versionTitle": 'Kehot Publication Society'})

    if sar:
        sar.walk_thru_contents(action)

    return all_text


# Find the letters
# Create the Link
# Insert the HTML to replace, create a CSV
# Re-ingest text with new CSV

def create_inline_ref_link(main_text_ref, ka_ref, data_order, save=True):
    link_creation_dict = {
        'refs': [main_text_ref, ka_ref],
        'type': 'commentary',
        'inline_reference': {
            'data-commentator': ka_ref,
            'data-order': data_order
        }}
    if save:
        Link(link_creation_dict).save()
    # Todo - indent this line once testing done
    print(f"Created inline-ref link between {main_text_ref} and {ka_ref}")


def create_html_tags(ka_ref, data_order, data_label):
    """
    data-order: the order it appears in
    data-label: the gematria tag we want to use
    """
    return f"<i data-commentator=\"{ka_ref}\" data-order=\"{data_order}\" data-label=\"{data_label}\"></i>"


def find_gematria_markers(text):
    KA_markers = re.findall(r"[^אבגדהוזחטיכלמנסעפצקרשת][<\(]{1,2}[אבגדהוזחטי]{1,2}[>\)]{1,2}[^אבגדהוזחטיכלמנסעפצקרשת]",
                            text)
    return KA_markers


def get_chelek(tref):
    chelek = re.findall(r"Shulchan Arukh HaRav, (.*?)[,\d]", tref)
    if chelek:
        return chelek[0].strip()
    return None


def get_siman(tref, chelek):
    # Note: Not catching "Shulchan Arukh HaRav, Yoreh Deah, Laws of Interest and Iska" since the
    # siman is also a string, versus a number. Doesn't matter for us because there is no KA on that siman
    # but important to note.
    if chelek != "Choshen Mishpat":
        siman_patt = f"Shulchan Arukh HaRav, {chelek} (.*):\d"
        siman_patt = re.compile(siman_patt)
        siman = re.findall(siman_patt, tref)
    else:
        siman = re.findall(r"Shulchan Arukh HaRav, Choshen Mishpat, (.*?)\d", tref)

    if siman:
        return siman[0].strip()
    return None

def clean_marker(marker):
    cleaned_marker = re.findall(r"[אבגדהוזחטיכלמנסעפצקרשת]{1,2}", marker)
    if cleaned_marker:
        return cleaned_marker[0]
    return None

def generate_csv(dict_list, headers):
    with open('SAR_text_with_KA_inline_refs.csv', 'w+') as file:
        c = csv.DictWriter(file, fieldnames=headers)
        c.writeheader()
        c.writerows(dict_list)
    print(f"File writing of Shulchan Arukh HaRav with Kuntres Acharon as inline-refs complete")


def match_link_html():
    all_text = get_all_segments()
    html_csv_dict = []
    for text in all_text:
        if text['is_KA'] == False:
            cur_main_text = text['text']
            cur_main_text_tref = text['tref']
            chelek = get_chelek(cur_main_text_tref)
            siman = get_siman(cur_main_text_tref, chelek)

            markers = find_gematria_markers(cur_main_text)

            # for each marker
            for marker in markers:
                # print(f"{marker}: {gematria(marker)}")
                gematria_marker_value = gematria(marker)
                data_label_cleaned = clean_marker(marker)

                if chelek != "Choshen Mishpat":
                    ka_ref = f"Shulchan Arukh HaRav, Kuntres Acharon, {chelek} {siman}:{gematria_marker_value}"
                else:
                    ka_ref = f"Shulchan Arukh HaRav, Kuntres Acharon, Choshen Mishpat, {siman} {gematria_marker_value}"

                # create a link
                # If cur ref is SAR OC 8:x, the KA ref will be SAR KA OC 8:marker_in_gematria
                create_inline_ref_link(main_text_ref=cur_main_text_tref,
                                       ka_ref=ka_ref,
                                       data_order=gematria_marker_value,
                                       save=False)  # Todo toggle this switch when ready

                # create HTML
                html_tag = create_html_tags(ka_ref=ka_ref,
                                             data_order=gematria_marker_value,
                                             data_label=data_label_cleaned)

                # Insert HTML tag
                main_text_with_html = cur_main_text.replace(marker, html_tag)
                html_csv_dict.append({'ref': cur_main_text_tref,
                                      'text': main_text_with_html})

    # Save to new CSV
    generate_csv(html_csv_dict, headers=['ref', 'text'])


if __name__ == '__main__':
    match_link_html()
