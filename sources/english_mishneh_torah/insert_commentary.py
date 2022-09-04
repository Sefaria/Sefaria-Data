import csv
import re


def clean_dibbur_hamatchil(text):
    clean_dhm = re.findall(r"(.*?)[ -.]*?-$", text, re.DOTALL)
    if not clean_dhm:
        return text
    return clean_dhm[0]


def remove_all_html_punct(text):
    cleaned = re.sub(r"[^A-Za-z <>'\[\]\?\.,]|<i>|</i>|<br>", "", text)
    return cleaned


def clean_dhm_links(text):
    links = re.findall(r"<a href=.*?>(.*?)<\/a>", text)
    for link in links:

        # Add escape characters to links data for matching
        if ")" in link or "(" in link:
            re_link = re.sub(r"\)", "\\)", link)
            re_link = re.sub(r"\(", "\\(", re_link)
        else:
            re_link = link
        clean_link = re.sub(r"[^A-Za-z :0-9]", " ", link)
        patt = f"<a href=.*?>{re_link}<\/a>"
        text = re.sub(patt, clean_link, text)
    return text


# Ingest cleaned MT as a dict
mt_dict = {}
with open('mishneh_torah_data_cleaned.csv', newline='') as csvfile:
    r = csv.reader(csvfile, delimiter=',')
    for row in r:
        ref = row[0]
        mt_dict[ref] = row[1]

count = 0
with open('commentary.csv', newline='') as csvfile:
    r = csv.reader(csvfile, delimiter=',')
    for row in r:
        ref = row[0]
        dhm = clean_dibbur_hamatchil(row[1])
        dhm = clean_dhm_links(dhm)
        com_txt = row[2]
        body_text = mt_dict[ref]
        # print(ref, mt_dict[ref])
        # print(ref, dhm, txt)
        if dhm in body_text:
            insert_footnote_index = body_text.index(dhm) + len(dhm)

        if dhm not in body_text:
            # If so, why is the shofar not sounded? Because of a decree [of the Sages] lest a person take it in his hands and carry it to a colleague so that the latter can blow for him
            body_no_html_punct = remove_all_html_punct(body_text)
            if dhm in body_no_html_punct:
                insert_footnote_index = body_no_html_punct.index(dhm) + len(dhm) - 1
                if body_text[insert_footnote_index:insert_footnote_index + 4] == '</i>':
                    insert_footnote_index = insert_footnote_index + 4
                if body_text[insert_footnote_index:insert_footnote_index + 3] == '<br>':
                    insert_footnote_index = insert_footnote_index + 3
            dhm_no_html = remove_all_html_punct(dhm)
            if dhm_no_html in body_no_html_punct:
                insert_footnote_index = body_no_html_punct.index(dhm_no_html) + len(dhm_no_html) - 1
                if body_text[insert_footnote_index:insert_footnote_index + 4] == '</i>':
                    insert_footnote_index = insert_footnote_index + 4

            else:
                count += 1
                print(f"flagging {ref}, not dhm perfect match")
                print(f"dhm: {dhm}, text: {mt_dict[ref]}")
                print()
    print(f"{count} not perfect matches")
