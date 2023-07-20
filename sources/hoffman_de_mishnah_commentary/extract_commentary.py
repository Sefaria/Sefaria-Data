# -*- coding: utf-8 -*-
import django

django.setup()

from sefaria.model import *
import re



text = {}


def action(segment_str, tref, he_tref, version):
    global text
    text[tref] = segment_str


def retrieve_version_text():
    version_query = {"versionTitle": "Mischnajot mit deutscher Übersetzung und Erklärung. Berlin 1887-1933 [de]"}
    hoffman_version = VersionSet(version_query)
    for v in hoffman_version:
        v.walk_thru_contents(action)


def create_link(mishnah_tref, commentary_tref):
    return {
        'refs': [commentary_tref, mishnah_tref],
        'type': 'commentary',
        'auto': True,
        'generated_by': 'Hoffman linker'
    }


def create_text_data_dict():
    retrieve_version_text()
    data_dict = {}
    links = []

    for mishnah_tref in text:
        commentary_ref_counter = 1
        mishnah_text = text[mishnah_tref]

        # Skipping for now, image issues
        if mishnah_tref == "Mishnah Chagigah 3:4" or mishnah_tref == "Mishnah Eruvin 5:4":
            continue

        res = re.findall(r"(.*?)<sup class=\"footnote-marker\">(\d.*?)<\/sup><i class=\"footnote\">(.*?)</i>",
                         mishnah_text)

        if res:
            for each_comment in res:
                bolded_main_text = f"{each_comment[0]}"

                if bolded_main_text and bolded_main_text[-1] == ")":
                    dh = re.findall(r"[:;.,?!()«»]([a-zA-ZäöüÄÖÜßáéíóúàèìòùâêîôûÂÊÎÔÛ\u0590-\u05FF<>\/= \"«]*[:;.,?!()«» ]*?[a-zA-ZäöüÄÖÜßáéíóúàèìòùâêîôûÂÊÎÔÛ\u0590-\u05FF<>\/= \"«.:]*\))$", bolded_main_text)
                elif bolded_main_text and bolded_main_text[-1] == "?":
                    dh = re.findall(r"[:;.,?!()«»]([a-zA-ZäöüÄÖÜßáéíóúàèìòùâêîôûÂÊÎÔÛ\u0590-\u05FF<>\/= \"«]*\?)$", bolded_main_text)
                elif bolded_main_text:
                    bolded_main_text = f"{bolded_main_text}." ## Period added for DH anchor in regex
                    dh = re.findall(r"[:;.,?!()«»]([a-zA-ZäöüÄÖÜßáéíóúàèìòùâêîôûÂÊÎÔÛ\u0590-\u05FF<>\/= \"«]*\.)$", bolded_main_text)

                # Case where first phrase etc
                if dh == []:
                    dh = [bolded_main_text]


                # Process DH
                dh = dh[0].strip()
                dh = dh.strip("«» ")

                footnote_text = each_comment[2]

                commentary_tref = f"German Commentary on {mishnah_tref}:{commentary_ref_counter}"  # Use the footnote to create specific segment ref
                data_dict[commentary_tref] = f"<b>{dh}</b> {footnote_text}"
                commentary_ref_counter += 1

                if dh == [] or dh == [""]:
                    print(f"{mishnah_tref}")
                    print(f"Main text: {bolded_main_text}")
                    print(f"Parsed DH: {dh}")
                    print("\n")

                new_link = create_link(mishnah_tref, commentary_tref)
                links.append(new_link)

    return data_dict, links


if __name__ == '__main__':
    create_text_data_dict()