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
    version_query = {"versionTitle": "Mischnajot mit deutscher Übersetzung und Erklärung. Berlin 1887-1933 [de]",
                     "title": {"$regex": "^Mishnah"}}
    hoffman_version = VersionSet(version_query)
    for v in hoffman_version:
        v.walk_thru_contents(action)


def create_text_data_dict():
    retrieve_version_text()
    data_dict = {}

    for mishnah_tref in text:
        commentary_ref_counter = 1
        mishnah_text = text[mishnah_tref]

        # Patching Mishnahs missing </i> at the end
        if mishnah_tref in ["Mishnah Eruvin 7:3", "Mishnah Niddah 6:14", "Mishnah Bava Metzia 4:1"]:
            mishnah_text = f"{mishnah_text}</i>"

        # TODO - unskip, deal with image issues
        if mishnah_tref == "Mishnah Chagigah 3:4" or mishnah_tref == "Mishnah Eruvin 5:4":
            continue

        res = re.findall(r"(.*?)<sup.*?>(.*?)<\/sup><i class=\"footnote\">(.*?)</i>",
                         mishnah_text)

        if res:
            for each_comment in res:
                bolded_main_text = f"{each_comment[0]}"
                marker = f"{each_comment[1]}"
                footnote_text = each_comment[2]

                if marker == "*":
                    dh = [""]  # No Dibbur HaMatchil for Asterisk cases
                    bolded_main_text = ""
                    if "<ftnote>" in footnote_text:
                        footnote_text = footnote_text.replace("<ftnote>", "")

                # Extract Dibbur HaMatchil based on Punctuation
                if bolded_main_text and re.search(r"\)[^A-Za-z]?$", bolded_main_text):
                    dh = re.findall(
                        r"[:;.,?!()«»]([a-zA-ZäöüÄÖÜßáéíóúàèìòùâêîôûÂÊÎÔÛ\u0590-\u05FF<>\/= \"«]*[:;.,?!()«» ]*?[a-zA-ZäöüÄÖÜßáéíóúàèìòùâêîôûÂÊÎÔÛ\u0590-\u05FF<>\/= \"«.:]*)$",
                        bolded_main_text)
                elif bolded_main_text and bolded_main_text[-1] in ["?", ".", ",", ";", ":"]:
                    dh = re.findall(r"[:;.,?!()«»]([a-zA-ZäöüÄÖÜßáéíóúàèìòùâêîôûÂÊÎÔÛ\u0590-\u05FF<>\/= \"«]*[?.,:;])$",
                                    bolded_main_text)
                elif bolded_main_text == "":
                    dh = ""
                else:
                    bolded_main_text = f"{bolded_main_text}."  ## Period added for DH anchor in regex
                    dh = re.findall(r"[:;.,?!()«»]([a-zA-ZäöüÄÖÜßáéíóúàèìòùâêîôûÂÊÎÔÛ\u0590-\u05FF<>\/= \"«]*\.)$",
                                    bolded_main_text)

                # Case where first phrase etc
                if not dh:
                    dh = [bolded_main_text]

                # Process DH
                dh = dh[0].strip()
                dh = dh.strip("«» ")

                commentary_tref = f"German Commentary on {mishnah_tref}:{commentary_ref_counter}"  # Use the footnote to create specific segment ref
                data_dict[commentary_tref] = f"<b>{dh}</b> {footnote_text}" if dh else f"{footnote_text}"
                commentary_ref_counter += 1

                if dh == [] or dh == [""]:
                    print(f"{mishnah_tref}")
                    print(f"Main text: {bolded_main_text}")
                    print(f"Parsed DH: {dh}")
                    print("\n")

    return data_dict


if __name__ == '__main__':
    create_text_data_dict()
