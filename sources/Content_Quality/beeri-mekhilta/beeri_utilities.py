import django

django.setup()

from sefaria.model import *
import csv

def write_to_csv(file_path, dict_list):
    # Open the CSV file in write mode
    with open(file_path, 'w', newline='') as csv_file:
        # Specify the order of columns based on headers or dictionary keys
        fieldnames = dict_list[0].keys()

        # Create a CSV writer object
        csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        # Write data to the CSV file
        csv_writer.writerows(dict_list)

    print(f"Data has been written to {file_path}")