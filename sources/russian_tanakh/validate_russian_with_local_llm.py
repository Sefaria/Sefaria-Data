import django

django.setup()

superuser_id = 171118
# import statistics
import csv
import os
from tqdm import tqdm
from sefaria.model import *
import requests
from langchain.chat_models import ChatOpenAI, ChatAnthropic
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage

# import requests_cache
# requests_cache.install_cache('my_cache', expire_after=3600*24*14)


books = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
                 "Judges", "I_Samuel", "II_Samuel", "I_Kings", "II_Kings",
                 "Ruth", "Esther"]
def get_validation_prompt(en_verse, ru_verse):
    prompt =  f"""
    Given a pair of English and Russian verses, output "YES" of the Russian is a faithful translation of the English, and "NO" otherwise. Don't output anything other than "YES" or "NO".
    English:
    {en_verse}
    Russian:
    {ru_verse}
    """
    return prompt
def ask_ollama(prompt, model="neural-chat", url="http://localhost:11434/api/generate"):
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

def ask_claude(query):
    llm = ChatAnthropic()
    # user_prompt = PromptTemplate.from_template("# Input\n{text}")
    user_prompt = PromptTemplate.from_template("{text}")
    human_message = HumanMessage(content=user_prompt.format(text=query))
    answer = llm([human_message])

    return answer.content

def write_verdict_to_csv(csv_file, segment_ref, verdict):
    if not os.path.exists(csv_file):
        with open(csv_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Ref', 'Verdict'])

    with open(csv_file, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([segment_ref, verdict])
def get_existing_refs(csv_file):
    if not os.path.exists(csv_file):
        return []

    with open(csv_file, 'r', newline='') as file:
        reader = csv.reader(file)
        existing_segment_refs = [row[0] for row in reader]
        return existing_segment_refs
def russian_semantic_validation(csv_filename="calude_verdicts.csv"):
    existing_segment_refs = get_existing_refs(csv_filename)
    segment_refs = []
    for book in books:
        segment_refs += library.get_index(book).all_segment_refs()
    for segment_ref in tqdm(segment_refs, desc=f"Validating segments", unit="segment"):

        if segment_ref.tref in existing_segment_refs:
            continue

        en_version_text = segment_ref.text().text
        ru_version_text = segment_ref.text(vtitle="Russian Torah translation, by Dmitri Slivniak, Ph.D., edited by Dr. Itzhak Streshinsky [ru]").text
        prompt = get_validation_prompt(en_version_text, ru_version_text)
        # verdict = ask_ollama(prompt)
        verdict = ask_claude(prompt)
        if "NO" in verdict:
            # print(f"possible semantic problem in {segment_ref}")
            verdict = "NO"
        elif "YES" in verdict:
            # print(f"{segment_ref} passed")
            verdict = "YES"
        # else:
        #     print(f"unclear verdict for {segment_ref}: {verdict}")
        write_verdict_to_csv(csv_filename, segment_ref, verdict)


if __name__ == '__main__':
    print("hello world")
    russian_semantic_validation()
    print("end")