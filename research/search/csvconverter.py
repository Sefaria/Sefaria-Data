import os
import glob
import unicodecsv as csv
import xlwt # from http://www.python-excel.org/

for csvfile in glob.glob(os.path.join('training_files/', '*.csv')):
    wb = xlwt.Workbook()
    ws = wb.add_sheet('data')
    with open(csvfile, 'rb') as f:
        reader = csv.reader(f)
        for r, row in enumerate(reader):
            for c, val in enumerate(row):
                ws.write(r, c, val)
    xlsfile = csvfile.split('/')[-1].split('.')[0]
    wb.save('excel/' + xlsfile + '.xls')