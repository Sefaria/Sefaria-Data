import unicodecsv
from .main import *

def test_source_sheet_disambiguator():
    ids = [1697,2636,8689,11419,13255,16085,18838,26981,27226,31603,31844,35830,49364,50853,57106,65498,78110,85003,90289,92571,101667,105718]
    rows = []
    start_row = 0
    with open("test.csv", "rb") as fin:
        cin = unicodecsv.DictReader(fin)
        for i, id in enumerate(ids):
            if i % 1 == 0:
                print("{}/{}".format(i, len(ids)))
            sheet = db.sheets.find_one({"id": id})
            if not sheet:
                print("continue")
                continue
            new_rows = mutate_sheet(sheet, refine_ref_by_text)
            rows += new_rows
            for irow in range(start_row, start_row + len(new_rows)):
                csv_row = next(cin)
                assert csv_row == rows[irow]
            start_row += len(new_rows)




