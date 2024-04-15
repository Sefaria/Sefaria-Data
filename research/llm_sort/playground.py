import django
django.setup()

from langchain.schema import HumanMessage, SystemMessage
from langchain.chat_models import ChatOpenAI

# from tqdm import tqdm
from sefaria.model import *
from sefaria.helper.normalization import NormalizerComposer

from pprint import pprint


def get_normalizer():
    return NormalizerComposer(['unidecode', 'br-tag', 'itag', 'html', 'maqaf', 'cantillation', 'double-space'])


normalizer = get_normalizer()
def get_gpt_compare(system_prompt, human_prompt_generator, llm):
    content_to_val = {"1":-1, "2":1, "0":0}
    def gpt_compare(a, b) -> int:
        response = llm([system_prompt, human_prompt_generator(a, b)])
        print(a)
        print(b)
        print(response.content, content_to_val.get(response.content, 0))
        return content_to_val.get(response.content, 0)

    return gpt_compare


def sort_by_instruction(documents: list[str], comparison_instruction):
    from functools import cmp_to_key
    message_suffix = " The only output should be either '1' or '2' or '0'"
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    system = SystemMessage(
        content=
        comparison_instruction
        +message_suffix)
    human_generator = lambda a, b: HumanMessage(content=f"1) {a}\n2) {b}")
    documents.sort(key=cmp_to_key(get_gpt_compare(system, human_generator, llm)))
    # for document in documents:
    #     print(document)
    return documents


if __name__ == "__main__":
    hamez_and_mazza_halachot = library.get_index("Mishneh Torah, Leavened and Unleavened Bread").all_segment_refs()
    hamez_and_mazza_halachot = [ref.tref + ":\n" + normalizer.normalize(ref.text().as_string()) for ref in hamez_and_mazza_halachot]
    # sorted_halachot = sort_by_instruction(hamez_and_mazza_halachot,
    #                         "We are a Jewish religious family, and we are about to hold a Passsover Seder. My dad asked me to introduce the concept of the Seder night to our guests, whose background in Judaism is not as strong."
    #                         "Given 2 Halakhot taken form Rambam's Mishne Torah, output the index of the one which presents a more introductory-level information about the Passover Seder, which might be suitable for our guests. If both are equally fundamental and introductory-level with regards to the Passover seder, output 0. ")
    sorted_halachot = sort_by_instruction(hamez_and_mazza_halachot,
                                          "You are an expert in Jewish laws and traditions, specifically interested in laws pertaining to unleavened bread (Matzah) during Passover."
                                          "Given 2 Halakhot taken form Rambam's Mishne Torah, output the index of the one which presents a more interesting, sophisticated and non-trivial information regarding the Matzah (unleavened bread), which might be of interest to you as a learned expert. If both are equally non-trivial and interesting with regards to the Matzah, output 0. ")


    for h in sorted_halachot:
        print(h)

    print("bye")

