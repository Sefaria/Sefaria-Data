import django


django.setup()
from sefaria.model import *
from sefaria.tracker import modify_bulk_text
import os
from bs4 import BeautifulSoup
import re
import csv
superuser_id = 171118
import requests
# from langchain.chat_models import ChatOpenAI, ChatAnthropic
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage

def get_classification_prompt(title, first_verse, second_verse):
    prompt =  f"""
    Given a verse and a title, output 1 is the title matches or can apply to the verse, and output "0" it doesn't apply.
    Don't output anything other than "1" or "0". Don't explain your logic, just output "1" or "0".
    
    Verse:
    {first_verse}  
    Title:
    {title}
    """
    return prompt
def ask_claude(query):
    llm = OpenAI(model="gpt-3.5-turbo-instruct")
    # user_prompt = PromptTemplate.from_template("# Input\n{text}")
    # user_prompt = PromptTemplate.from_template("{text}")
    # human_message = HumanMessage(content=user_prompt.format(text=query))
    answer = llm.invoke(query)
    return answer

def ask_ollama(prompt, model="llama3.2", url="http://localhost:11434/api/generate"):
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        return response.json()["response"]
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

if __name__ == '__main__':
    books = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]
    classifications = []
    with open('output.csv', 'r') as file:
        reader = csv.reader(file)
        ref_verse_list = [tuple(row) for row in reader]
    for index, verse_ref in enumerate(ref_verse_list):
        if verse_ref[0].startswith("title"):
            print(verse_ref[1])
            classifications.append({
                "title": verse_ref[1],
                "title_num": verse_ref[0],
                "option_1": ref_verse_list[index - 1][0],
                "option_2": ref_verse_list[index + 1][0],
                "option_1_text": ref_verse_list[index - 1][1],
                "option_2_text": ref_verse_list[index + 1][1],
            })
    for classification in classifications:
        prompt = get_classification_prompt(classification["title"], classification["option_1_text"], classification["option_2_text"])
        print(prompt)
        verdict = ask_ollama(prompt)
        if '0' in verdict:
            halt = True
        if "0" in verdict:
            classification["verdict"] = "option2"
        if "1" in verdict:
            classification["verdict"] = "option1"
    csv_file = 'titles_matches.csv'
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=classifications[0].keys())
        writer.writeheader()
        writer.writerows(classifications)


    print('hi')
    # for book in books:
    #     seg_refs = library.get_index(book).all_segment_refs()
    #     for ref in seg_refs:
    #         if ref.text(vtitle="The Torah; Chabad House Publications, Los Angeles, 2015-2023").text == "":
    #             print(ref)