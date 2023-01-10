import django, json, srsly, csv
import Levenshtein
django.setup()
import re
from sefaria.model import *
import csv
from bs4 import BeautifulSoup
import base64
import PIL
from PIL import Image, ImageFilter
from io import BytesIO

csv.field_size_limit(1000000)


def find_closing_i_tag(start_index, string):
    num_of_opennings_i_saw = 1
    num_of_closings_i_saw = 0
    for i in range(start_index+1, len(string)):
        if string[i] == '>' and string[i - 1] == 'i' and string[i - 2] == "/":
            num_of_closings_i_saw += 1
            if num_of_opennings_i_saw == num_of_closings_i_saw:
                return i
        elif string[i] == '>' and string[i - 1] == "i":
            num_of_opennings_i_saw += 1



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
                # match = re.search(r'<i class="footnote">(.+?)</i>', row[2])
                match = re.search(r'<i class="footnote">(.+?)', row[2])
                while match:
                    closing_tag_index = find_closing_i_tag(match.start()+21, row[2])
                    row[2] = row[2][:match.start()] + "fn1" + row[2][closing_tag_index+1:]
                    # row[2] = re.sub(r'<i class="footnote">(.+?)</i>', 'fn1', row[2])
                    match = re.search(r'<i class="footnote">(.+?)', row[2])
                match2 = re.search(r'<sup>\((\d+)\)</sup>', row[2])
                while match2:
                    row[2] = row[2][:match2.start()-1] + "" + row[2][match2.end():]
                    match2 = re.search(r'<sup>\((\d+)\)</sup>', row[2])

                pattern = r"fn\d+"
                match = re.search(pattern, row[2])
                while match:
                    a = '<sup class="footnote-marker">' + sup_tags_with_xref[ft_index].get_text() + '</sup><i class="footnote">' + ftnotes[ft_index].decode_contents()[4:] + '</i>'
                    row[2] = re.sub(pattern, str(a), row[2], count=1)
                    if "[[query]]" in row[2]:
                        row[2] = row[2].replace("[[query]]", "")
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
                # match = re.search(r'<i class="footnote">(.+?)</i>', row[2])
                match = re.search(r'<i class="footnote">(.+?)', row[2])
                while match:
                    closing_tag_index = find_closing_i_tag(match.start() + 21, row[2])
                    row[2] = row[2][:match.start()] + "fn1" + row[2][closing_tag_index + 1:]
                    # row[2] = re.sub(r'<i class="footnote">(.+?)</i>', 'fn1', row[2])
                    match = re.search(r'<i class="footnote">(.+?)', row[2])
                match2 = re.search(r'<sup>\((\d+)\)</sup>', row[2])
                while match2:
                    row[2] = row[2][:match2.start() - 1] + "" + row[2][match2.end():]
                    match2 = re.search(r'<sup>\((\d+)\)</sup>', row[2])

                pattern = r"fn\d+"
                match = re.search(pattern, row[2])

                while match:
                    if "différentes démonstrations de l’existence d’un Dieu unique et immatériel" in ftnotes[ft_index].get_text():
                        a = '<sup class="footnote-marker">' + sup_tags_with_xref[ft_index].get_text() + '</sup><i class="footnote">' + ftnotes[ft_index].decode_contents()[4:] + '</i>'
                        row[2] = a + row[2]
                        ft_index += 1
                    elif "L’auteur aborde ici les preuves directes qu’on peut alléguer en faveur de la création" in ftnotes[ft_index].get_text():
                        a = '<sup class="footnote-marker">' + sup_tags_with_xref[ft_index].get_text() + '</sup><i class="footnote">' + ftnotes[ft_index].decode_contents()[4:] + '</i>'
                        row[2] = a + row[2]
                        ft_index += 1
                    else:
                        a = '<sup class="footnote-marker">' + sup_tags_with_xref[ft_index].get_text() + '</sup><i class="footnote">' + ftnotes[ft_index].decode_contents()[4:] + '</i>'
                        row[2] = re.sub(pattern, str(a), row[2], count=1)
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
                # match = re.search(r'<i class="footnote">(.+?)</i>', row[2])
                match = re.search(r'<i class="footnote">(.+?)', row[2])
                while match:
                    closing_tag_index = find_closing_i_tag(match.start() + 21, row[2])
                    row[2] = row[2][:match.start()] + "fn1" + row[2][closing_tag_index + 1:]
                    # row[2] = re.sub(r'<i class="footnote">(.+?)</i>', 'fn1', row[2])
                    match = re.search(r'<i class="footnote">(.+?)', row[2])
                match2 = re.search(r'<sup>\((\d+)\)</sup>', row[2])
                while match2:
                    row[2] = row[2][:match2.start() - 1] + "" + row[2][match2.end():]
                    match2 = re.search(r'<sup>\((\d+)\)</sup>', row[2])

                pattern = r"fn\d+"
                match = re.search(pattern, row[2])
                while match:
                    a = '<sup class="footnote-marker">' + sup_tags_with_xref[ft_index].get_text() + '</sup><i class="footnote">' + ftnotes[ft_index].decode_contents()[4:] + '</i>'
                    row[2] = re.sub(pattern, str(a), row[2], count=1)
                    ft_index += 1
                    match = re.search(pattern, row[2])

                print(row[2])
                writer.writerow(row)
                print('###################')

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
                        img = Image.open(BytesIO(f.read()))

                    orig_height = img.size[1]
                    orig_width = img.size[0]
                    if orig_width > 40:
                        percent = 40 / float(orig_width)
                        height = int(float(orig_height) * float(percent))
                        img = img.resize((40, height), PIL.Image.ANTIALIAS)

                    img = img.convert('L')
                    img = img.save("abc.jpg")
                    file = open("abc.jpg", 'rb')
                    data = file.read()
                    file.close()

                    # Encode the binary image data using base64
                    base64_image = base64.b64encode(data)

                    print(match.group())  # prints 'some_string'
                    # Construct the replacement string using the src value
                    replacement = '<img src="data:image/{};base64,{}"> </img >'.format('jpg', str(base64_image)[2:-1])
                    # replacement = f'<img src=data:image/jpg;base64,"{str(base64_image)[2:-1]}"/>'
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

