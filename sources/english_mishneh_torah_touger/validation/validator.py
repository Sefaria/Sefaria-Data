import django

django.setup()

import csv
import re
from bs4 import BeautifulSoup
import pprint
import difflib



from sefaria.model import *

def normalize_line(raw_text):
    soup = BeautifulSoup(raw_text, 'html.parser')

    # sup_tag = soup.find_all('sup')
    # a_tag = soup.find_all('a')
    # i_tag = soup.find_all('i')


    for sup_tag in soup.find_all('sup'):
        sup_tag.extract()

    for a_tag in soup.find_all('a'):
        if a_tag.has_attr('name'):
            a_tag.extract()

    for i_tag in soup.find_all('i'):
        i_tag.extract()

    for br_tag in soup.find_all('br'):
        br_tag.replace_with(" ")
    # if sup_tag:
    #     sup_tag.extract()
    # if a_tag:
    #     a_tag.extract()
    # if i_tag:
    #     i_tag.extract()

    # Extract the text content from the HTML
    text = soup.get_text()

    # Remove any remaining HTML tags using regular expressions
    text = re.sub('<[^>]*>', '', text)

    # Normalize the text
    # .text = text.lower()
    text = text.strip()
    text = text.replace('\n', ' ')
    return text

def mark_differnces(string1, string2):
    diff = list(difflib.ndiff(string1, string2))
    # Iterate through the list of differences and highlight the ones that are different
    result = ''
    for i in range(len(diff)):
        if diff[i][0] == ' ':
            # If the difference is a space, print the character as is
            print(diff[i][-1], end='')
            result += diff[i][-1]
        elif diff[i][0] == '-':
            # If the difference is a deletion, print the character with a red background
            print('\033[41m' + diff[i][-1] + '\033[0m', end='')
            result += '<span style="background-color: red;">' + diff[i][-1] + '</span>'
        elif diff[i][0] == '+':
            # If the difference is an insertion, print the character with a green background
            print('\033[42m' + diff[i][-1] + '\033[0m', end='')
            result += '<span style="background-color: #green;">' + diff[i][-1] + '</span>'
    print("")
    return result



def write_to_csv(list):
    with open('discrepancies.csv', 'w', newline='') as csvfile:
        # Create a CSV writer object
        writer = csv.writer(csvfile)

        # Write the list to the CSV file
        scheme = ("ref", "sefaria normal", "chabad normal", "sefaria raw", "chabad raw")
        writer.writerow(scheme)
        for r in list:
            writer.writerow(r)
def tuples_to_html_table(data):
    # Start building the table
    html = '<table>\n'

    # Add a row for each tuple in the list
    for row in data:
        html += '  <tr>\n'
        for cell in row:
            html += f'    <td>{cell}</td>\n'
        html += '  </tr>\n'

    # Close the table
    html += '</table>'

    # Return the finished HTML table
    return html

if __name__ == '__main__':
    print("hello world")
    chabad_data = {}
    sefaria_data = {}
    sefaria_raw = {}
    chabad_raw = {}
    with open('chabad_data_sefaria_refs.csv', 'r') as f_chabad:
        reader = csv.reader(f_chabad)
        # Iterate over the rows of the CSV file
        for row in reader:
            row[0] = row[0].replace(".", ":")
            row[0] = row[0].replace(" ", "")

            # Append each row to the list
            chabad_data[row[0]] = row[1]
            chabad_raw[row[0]] = row[1]
    with open('12_22_2022_mishneh_torah_data.csv', 'r') as f_sefaria:
        reader_sefaria = csv.reader(f_sefaria)
        reader = csv.reader(f_sefaria)
        # Iterate over the rows of the CSV file
        for row in reader:
            # Append each row to the list
            sefaria_data[row[0]] = row[1]
            sefaria_raw[row[0]] = row[1]




    match_count = 0
    not_match_count = 0
    not_match_list = []

    diff_list = []

    # for ref in sefaria_data.keys():
    #     ref = ref.replace(".", ":")
    #     ref = ref.replace(" ", "")
    #     if ref in chabad_data:
    #         match_count += 1
    #     else:
    #         not_match_count += 1
    #         not_match_list.append(ref)
    #
    # pprint.pprint(not_match_list)
    for ref in sefaria_data.keys():
        c_ref = ref.replace(".", ":")
        c_ref = ref.replace(" ", "")
        if c_ref in chabad_data:
            s_text = normalize_line(sefaria_data.get(ref))
            c_text = normalize_line(chabad_data.get(c_ref))

            if s_text == c_text:
                # print("match!")
                a= 1
            else:
                # print("not match!")
                print("sefaria:")
                print(s_text)
                print("chabad:")
                print(c_text)
                diff = mark_differnces(s_text, c_text)
                tuple = (ref, s_text, c_text, sefaria_raw[ref], chabad_raw[c_ref])
                tuple2 = (ref, diff, s_text, c_text)
                not_match_list.append(tuple)
                diff_list.append(tuple2)

    write_to_csv(not_match_list)
    diff_list.insert(0, ("Ref", "Difference", "Sefaria Text", "Chabad Text"))
    html = tuples_to_html_table(diff_list)
    with open('differences.html', 'w') as f:
        # Write the HTML to the file
        f.write(html)


            # rows_chabad = sorted(list(reader_chabad), key=lambda r: r[0].replace(" ", ""))
            # rows_sefaria = sorted(list(reader_sefaria), key=lambda a: a[0].replace(" ", ""))
            #
            # c = 0
            # for row_sefaria, row_chabad in zip(rows_sefaria, rows_chabad):
            #
            #     s_normal = normalize_line(row_sefaria[1])
            #     c_normal = normalize_line(row_chabad[1])
            #     print("*******sefaria*******: " + row_sefaria[0])
            #     print("*******chabad*******: " + row_chabad[0])


