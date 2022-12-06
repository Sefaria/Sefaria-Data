import django

django.setup()

import re
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
        try:
            Link(link_creation_dict).save()
            print(f"Created inline-ref link between {main_text_ref} and {ka_ref}")
        except Exception as e:
            print(e)


def create_html_tags(data_order, data_label):
    """
    data-order: the order it appears in
    data-label: the gematria tag we want to use
    """
    return f" <i data-commentator=\"Shulchan Arukh HaRav\" data-order=\"{data_order}\" data-label=\"{data_label}\"></i> "


def find_gematria_markers(text):
    KA_markers = re.findall(r"[^אבגדהוזחטיכלמנסעפצקרשת][<\(]{1,2}[אבגדהוזחטי]{1,2}[>\)]{1,2}[^אבגדהוזחטיכלמנסעפצקרשת]",
                            text)
    # Special regex for KA markers at the beginning of halakha without a space preceding them
    start_markers = re.findall(r"^[<\(]{1,2}[אבגדהוזחטי]{1,2}[>\)]{1,2}[^אבגדהוזחטיכלמנסעפצקרשת]",
                               text)
    KA_markers = KA_markers + start_markers
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


def update_text(tref, text):
    oref = Ref(tref)
    tc = TextChunk(oref, vtitle="Kehot Publication Society", lang='he')
    tc.text = text
    tc.save()


def validate_sequence():
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
    all_text = get_all_segments()

    for text in all_text:
        if not text['is_KA']:
            cur_main_text = text['text']
            cur_main_text_tref = text['tref']
            chelek = get_chelek(cur_main_text_tref)
            siman = get_siman(cur_main_text_tref, chelek)

            markers = find_gematria_markers(cur_main_text)

            # for each marker
            for i in range(len(markers)):
                marker = markers[i]
                is_last_marker_for_siman = False if i < len(markers) - 1 else True
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
                                       save=True)

                # create HTML
                html_tag = create_html_tags(data_order=gematria_marker_value,
                                            data_label=data_label_cleaned)

                # Insert HTML tag
                main_text_with_html = cur_main_text.replace(marker, html_tag)

                if is_last_marker_for_siman:
                    update_text(tref=cur_main_text_tref, text=main_text_with_html)
                else:
                    cur_main_text = main_text_with_html


if __name__ == '__main__':
    match_link_html()
    # validate_sequence()
