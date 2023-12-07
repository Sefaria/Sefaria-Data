import django

django.setup()

superuser_id = 171118
# import statistics
import csv
from sefaria.model import *
import requests
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
def russian_semantic_validation():
    for book in books:
        segment_refs = library.get_index(book).all_segment_refs()
        for s_g in segment_refs:
            en_version_text = s_g.text().text
            ru_version_text = s_g.text(vtitle="Russian Torah translation, by Dmitri Slivniak, Ph.D., edited by Dr. Itzhak Streshinsky [ru]").text
            prompt = get_validation_prompt(en_version_text, ru_version_text)
            verdict = ask_ollama(prompt)
            if "NO" in verdict:
                print(f"possible semantic problem in {s_g}")
            if "YES" in verdict:
                print(f"{s_g} passed")
            else:
                print(f"unclear verdict for {s_g}: {verdict}")


if __name__ == '__main__':
    print("hello world")
    russian_semantic_validation()
    print("end")