import django, json, srsly, csv
import Levenshtein
django.setup()
import re
from sefaria.model import *
import csv
from bs4 import BeautifulSoup
import base64

csv.field_size_limit(1000000)


def fix_part_1():
    with open('MorehNevukhim_French_1.xml', 'r') as f:
        xml_data = f.read()


    soup = BeautifulSoup(xml_data, 'xml')
    sup_tags = soup.find_all('sup', recursive=True)
    sup_tags_with_xref = [tag for tag in sup_tags if tag.find('xref')]
    ftnotes = [soup.find_all('ftnote', recursive=True)][0]

    ft_index = 6;

    # Open the CSV file
    with open('Moreh Nevukhim, FR - Moreh Wout Footnotes 1.csv', 'r') as file_r:
        with open('part1_fixed.csv', 'w', newline='') as file_w:
            # Create a CSV writer object
            writer = csv.writer(file_w)
            reader = csv.reader(file_r)

            # Iterate over the rows in the CSV file
            for row in reader:
                match = re.search(r'<i class="footnote">(.+?)</i>', row[2])
                if match:
                    row[2] = re.sub(r'<i class="footnote">(.+?)</i>', 'fn1', row[2])

                pattern = r"fn\d+"
                match = re.search(pattern, row[2])
                if match:
                    while match:
                        a = '<sup class="footnote-marker">' + sup_tags_with_xref[ft_index].get_text() + '</sup><i class="footnote">' + ftnotes[ft_index].decode_contents() + '</i>'
                        row[2] = re.sub(pattern, str(a), row[2], count=1)
                        ft_index += 1
                        match = re.search(pattern, row[2])

                print(row[2])
                writer.writerow(row)
                print('###################')

def fix_part_2():
    with open('MorehNevukhim_French_2.xml', 'r') as f:
        xml_data = f.read()

    soup = BeautifulSoup(xml_data, 'xml')
    sup_tags = soup.find_all('sup', recursive=True)
    sup_tags_with_xref = [tag for tag in sup_tags if tag.find('xref')]
    ftnotes = [soup.find_all('ftnote', recursive=True)][0]

    ft_index = 1;

    # Open the CSV file
    with open('Moreh Nevukhim, FR - Moreh Wout Footnotes 2.csv', 'r') as file_r:
        with open('part2_fixed.csv', 'w', newline='') as file_w:
            # Create a CSV writer object
            writer = csv.writer(file_w)
            reader = csv.reader(file_r)

            for row in reader:
                match = re.search(r'<i class="footnote">(.+?)</i>', row[2])
                if match:
                    row[2] = re.sub(r'<i class="footnote">(.+?)</i>', 'fn1', row[2])

                pattern = r"fn\d+"
                match = re.search(pattern, row[2])
                if match:
                    while match:
                        a = '<sup class="footnote-marker">' + sup_tags_with_xref[ft_index].get_text() + '</sup><i class="footnote">' + ftnotes[ft_index].decode_contents() + '</i>'
                        row[2] = re.sub(pattern, str(a), row[2], count=1)
                        if "différentes démonstrations de l’existence d’un Dieu unique et immatériel" in ftnotes[ft_index+1].get_text():
                            ft_index += 2
                        elif "L’auteur aborde ici les preuves directes qu’on peut alléguer en faveur de la création" in ftnotes[ft_index+1].get_text():
                            ft_index += 2
                        else:
                            ft_index += 1
                        match = re.search(pattern, row[2])

                print(row[2])
                writer.writerow(row)
                print('###################')


def fix_part_3():
    with open('MorehNevukhim_French_3.xml', 'r') as f:
        xml_data = f.read()

    soup = BeautifulSoup(xml_data, 'xml')
    sup_tags = soup.find_all('sup', recursive=True)
    sup_tags_with_xref = [tag for tag in sup_tags if tag.find('xref')]
    ftnotes = [soup.find_all('ftnote', recursive=True)][0]


    ft_index = 2;

    # Open the CSV file
    with open('Moreh Nevukhim, FR - Moreh Wout Footnotes 3.csv', 'r') as file_r:
        with open('part3_fixed.csv', 'w', newline='') as file_w:
            # Create a CSV writer object
            writer = csv.writer(file_w)
            reader = csv.reader(file_r)

            for row in reader:
                match = re.search(r'<i class="footnote">(.+?)</i>', row[2])
                if match:
                    row[2] = re.sub(r'<i class="footnote">(.+?)</i>', 'fn1', row[2])

                pattern = r"fn\d+"
                match = re.search(pattern, row[2])
                if match:
                    while match:
                        a = '<sup class="footnote-marker">' + sup_tags_with_xref[ft_index].get_text() + '</sup><i class="footnote">' + ftnotes[ft_index].decode_contents() + '</i>'
                        row[2] = re.sub(pattern, str(a), row[2], count=1)
                        ft_index += 1
                        match = re.search(pattern, row[2])

                print(row[2])
                writer.writerow(row)
                print('###################')
    a = 5+7

def append_csvs(out_filename, *filenames):
  # Open the output CSV file in write mode
  with open(out_filename, 'w', newline='') as out_file:
    # Create a CSV writer object
    writer = csv.writer(out_file)

    # Iterate over the input filenames
    for filename in filenames:
      # Open the input CSV file in read mode
      with open(filename, 'r') as infile:
        # Create a CSV reader object
        reader = csv.reader(infile)

        # Iterate over the rows in the CSV file
        for row in reader:
          # Write the row to the output file
          if row[0] != "":
            writer.writerow(row)




def add_base64_imgs(csv_file_name_no_csv_at_the_end, path_to_images_folder):
    with open(csv_file_name_no_csv_at_the_end + '.csv', 'r') as file_r:
        with open(csv_file_name_no_csv_at_the_end + '_with_imgs.csv', 'w', newline='') as file_w:
            # Create a CSV writer object
            writer = csv.writer(file_w)
            reader = csv.reader(file_r)

            for row in reader:

                pattern = r'<img\s+(?:alt="[^"]+"\s+)?src="([^"]+)"\s*(?:alt="[^"]+")?\s*\/?>'                   #r'<img\s+(?:alt="[^"]+"\s+)?src="[^"]+"\s*(?:alt="[^"]+")?\s*\/?>'
                matches = re.finditer(pattern, row[2])
                for match in matches:
                    path = match.group(1)

                    if "P284" in path and "French_2" in path_to_images_folder:
                        path = path.replace("P284", "P247")


                    # Open the image file
                    with open(path_to_images_folder + path, 'rb') as f:
                        # Read the image file content in binary
                        image_content = f.read()

                    # Encode the binary image data using base64
                    base64_image = base64.b64encode(image_content)
                    print(match.group())  # prints 'some_string'
                    # Construct the replacement string using the src value
                    replacement = f'<img src="{base64_image}"/>'
                    # Use re.sub() to perform the replacement
                    row[2] = re.sub(pattern, replacement, row[2])
                writer.writerow(row)


if __name__ == "__main__":
    print("hello world")
    fix_part_1()
    fix_part_2()
    fix_part_3()
    print("images part 1:")
    add_base64_imgs("part1_fixed", "MorehNevukhim_French_1/")
    print("images part 2:")
    add_base64_imgs("part2_fixed", "MorehNevukhim_French_2/")
    print("images part 3:")
    add_base64_imgs("part3_fixed", "MorehNevukhim_French_3/")

    append_csvs("moreh_fixed_all_parts_with_imgs.csv", "part1_fixed_with_imgs.csv", "part2_fixed_with_imgs.csv", "part3_fixed_with_imgs.csv")





# Print the list of sup tags with ref tags

