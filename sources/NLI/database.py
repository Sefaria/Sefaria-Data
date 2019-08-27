# encoding = utf-8

import tqdm
import sqlite3
import unicodecsv
from path_to_db_file import DB_FILE_LOCATION

# conn = sqlite3.connect(DB_FILE_LOCATION)
# conn.row_factory = sqlite3.Row
#
# cursor = conn.cursor()
#
# cursor.execute('''
# SELECT Tal.Fr_Name, Trac.Tr_Name, Pe.Pe_ab, Mi.Mi_ab, IR.sfrom im_start, IR.sto im_end, Images.Ma_Name, Images.Im_ImRun,
# Images.Ma_LibName, Images.Ma_NameDescription, Images.Ma_Description
# FROM TblFullRef FR
# JOIN TblTractates Trac ON Fr_Tr = Trac.Tr_code
# JOIN TblPerek Pe ON Fr_F1 = Pe.Pe_code
# JOIN TblMishna Mi ON Fr_F2 = Mi.Mi_code
# JOIN TblTalmod Tal ON FR.Fr_Co = Tal.Fr_Co
# JOIN TblImgRef IR ON FR.Fr_Img = IR.Ir_Img
# JOIN (
#     SELECT Im.Im_Id, Mans.Ma_Name, Mans.Ma_LibName, Mans.Ma_NameDescription, Mans.Ma_Description, Im.Im_ImRun
#     FROM TblImages Im
#     JOIN (
#         SELECT MS.Ma_Name, Li.Ma_LibName, MS.Ma_NameDescription, MS.Ma_Description, MS.Ma_ID
#         FROM TblManuscripts MS
#         JOIN TblLibraries Li ON MS.Ma_LibID = Li.Li_ID
#         ) Mans ON Im.Im_Ms = Mans.Ma_ID
# ) Images ON FR.Fr_Img = Images.Im_Id
# LIMIT 300
# ''')
#
# with open('iiif.csv', 'w') as fp:
#     writer = None
#     while True:
#         row = cursor.fetchone()
#         if not row:
#             break
#         if not writer:
#             writer = unicodecsv.DictWriter(fp, fieldnames=row.keys())
#             writer.writeheader()
#         dict_row = {key: value for key, value in zip(row.keys(), row)}
#         writer.writerow(dict_row)


"""
Obtain urls for Ref (works for Vatican):
Start with the manifest:
https://difi.vatlib.it/iiif/MSS_Vat.{man-id (lowercase)}/manifest.json

Use TblImages.Im_ImRun to get the page
Within the manifest, search for @id: "https://digi.vatlib.it/iiif/MSS_Vat.{man-id}/canvas/p{TblImages.Im_ImRun (pad to 4 digits)}",

Once you've found this, get service.@id.
From there, you'll have to supply the iiif parameters {region}/{rotation}/{quality}.{format}

For manual testing, to open a file in a browser, try:
webbrowser.open('file://' + os.path.realpath(<filename>))


How to find a Ref:
First, let's export that crazy query as a stand alone table -- Done

For each image, we'll want to keep track of the following data:
{
    full_ref                Ref that encompasses the entirety of the image. Can be a range
    expanded_refs           List of segment refs within the full ref
    image_url               Basic url - without iiif parameters.
    Institution             Name of library hosting this image
    Manuscript ID           Not sure exactly what field should go here. For now, make this the NLI manuscript ID
    English Desc            Leave this blank for now
    Hebrew Desc             We can get this from the NLI database
}   

Write a class for working out the urls. The class will hold a database instance. It will also hold a mapping of
Libraries -> base library url.

For a given manuscript, we'll first load the manifest. For each manifest make a mapping of Im_ImRun -> image url 
(without iiif parameters).

We might want to consider multithreading here. For that we need this process to be thread safe. We'll look at two types
of locks -> a lock for manuscripts and a general write lock.
For the manuscript lock, we'll make a default dict that will create a unique lock for each manuscript. Then we'll use a
general write lock for adding new manifests.
"""


class RefImageUrlMap(object):

    def __init__(self):
        self.database = Database()


class Database(object):

    def __init__(self):
        conn = sqlite3.connect(DB_FILE_LOCATION)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        self.connection = conn
        self.cursor = cursor

    @staticmethod
    def get_major_query_string():
        return '''
            SELECT Tal.Fr_Name, Trac.Tr_Name, Pe.Pe_ab, Mi.Mi_ab, IR.sfrom im_start, IR.sto im_end, Images.Ma_Name,
            Images.Im_ImRun, Images.Ma_LibName, Images.Ma_NameDescription, Images.Ma_Description
            FROM TblFullRef FR
            JOIN TblTractates Trac ON Fr_Tr = Trac.Tr_code
            JOIN TblPerek Pe ON Fr_F1 = Pe.Pe_code
            JOIN TblMishna Mi ON Fr_F2 = Mi.Mi_code
            JOIN TblTalmod Tal ON FR.Fr_Co = Tal.Fr_Co
            JOIN TblImgRef IR ON FR.Fr_Img = IR.Ir_Img
            JOIN (
                SELECT Im.Im_Id, Mans.Ma_Name, Mans.Ma_LibName, Mans.Ma_NameDescription, Mans.Ma_Description, Im.Im_ImRun
                FROM TblImages Im
                JOIN (
                    SELECT MS.Ma_Name, Li.Ma_LibName, MS.Ma_NameDescription, MS.Ma_Description, MS.Ma_ID
                    FROM TblManuscripts MS
                    JOIN TblLibraries Li ON MS.Ma_LibID = Li.Li_ID
                    ) Mans ON Im.Im_Ms = Mans.Ma_ID
            ) Images ON FR.Fr_Img = Images.Im_Id
            '''

    def create_aggreagte_table(self):
        try:
            self.cursor.execute('DROP TABLE aggregation')
        except sqlite3.OperationalError as e:
            print e

        self.cursor.execute("CREATE TABLE aggregation (Book_Type, Tractate, Chapter, Verse, image_start, image_end, "
                            "Manuscript, Image_ID, Library, Manuscript_Description, Extended_Manuscript_Description)")

        self.cursor.execute('INSERT INTO aggregation {}'.format(self.get_major_query_string()))
        self.connection.commit()

    def export_aggregate_table(self):
        rows = self.cursor.execute('SELECT * FROM aggregation').fetchall()

        with open('iiif.csv', 'w') as fp:
            writer = unicodecsv.DictWriter(fp, fieldnames=rows[0].keys())
            writer.writeheader()
            for row in rows:
                dict_row = {key: value for key, value in zip(row.keys(), row)}
                writer.writerow(dict_row)

