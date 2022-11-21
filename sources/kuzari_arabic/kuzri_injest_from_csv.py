import csv

if __name__ == '__main__':


    ref_dict = {}

    with open('kuzari aligned.csv', newline='') as csvfile:
        r = csv.reader(csvfile, delimiter=',')

        title = ""
        paragraph_num = 1
        for row in r:
            if row[0] == '':
                ref = title + ", " + str(paragraph_num)
                ref_dict[ref] = row[2]
                paragraph_num += 1
            else:
                title = row[0]
                paragraph_num = 1
                ref = title + ", " + str(paragraph_num)
                ref_dict[ref] = row[2]


    print(ref_dict)





