import django

django.setup()

from sefaria.model import *

import csv

def read_csv_to_data_list(file_path):
    result_data = []

    # Open the CSV file and read its contents
    with open(file_path, 'r') as csv_file:
        # Create a CSV reader object
        csv_reader = csv.reader(csv_file)

        # Skip the header row
        next(csv_reader)

        # Iterate through each row in the CSV file
        for row in csv_reader:
            # Assuming the CSV has two columns, store each value in a variable
            beeri_ref, prod_ref = row
            # Add values to respective lists
            beeri_text = Ref(beeri_ref).text(lang='he').text
            prod_text = Ref(prod_ref).text(lang='he').text

            result_data.append([beeri_ref, beeri_text, prod_ref, prod_text])

    return result_data

def write_to_csv(file_path, data):
    # Open the CSV file in write mode
    with open(file_path, 'w', newline='') as csv_file:
        # Create a CSV writer object
        csv_writer = csv.writer(csv_file)

        # Write header if needed (uncomment the line below and replace fieldnames with your header)
        csv_writer.writerow(['beeri_ref', 'beeri_text', 'prod_ref', 'prod_text'])

        # Write data to the CSV file
        for row in data:
            csv_writer.writerow(row)


data = read_csv_to_data_list("full_mapping.csv")
write_to_csv('full_mapping_with_text_he.csv', data)


