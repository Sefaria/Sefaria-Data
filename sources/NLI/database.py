# encoding = utf-8

import tqdm
import sqlite3
import requests
import unicodecsv
from threading import Lock
from collections import defaultdict
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
https://digi.vatlib.it/iiif/MSS_Vat.{man-id (lowercase)}/manifest.json

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

Manuscript class:
We'll want a class that can accept a Manuscript Id, load a manifest, then create a mapping of Im_Run values to urls.

For each image, we'll use the Manuscript class to get the image url.
"""


class Database(object):

    def __init__(self):
        conn = sqlite3.connect(DB_FILE_LOCATION, check_same_thread=False)
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


database = Database()


class ManuscriptException(Exception):
    pass


class LibraryException(Exception):
    pass


class Manuscript(object):

    def __init__(self, manuscript_id=None):
        self._manifest = None
        self._manuscript_id = None
        self._image_map = None
        self.manifest_url = None

        if manuscript_id:
            self.manuscript_id = manuscript_id

    def _process_manifest(self):
        pass

    def _load_manifest(self):
        if self._manuscript_id is None:
            raise ManuscriptException("Manuscript id not set")

        database.cursor.execute('SELECT Ma.Ma_Name, Li.base_url FROM TblManuscripts Ma '
                                'JOIN TblLibraries Li ON Ma.Ma_LibID = Li.Li_ID '
                                'WHERE Ma.Ma_ID = ?', (self._manuscript_id,))

        result = database.cursor.fetchone()
        base_url, manuscript_name = result['base_url'], result['Ma_Name']

        if base_url is None:
            raise LibraryException("Url has not been set for this Library")

        self.manifest_url = u'{}{}/manifest.json'.format(base_url, manuscript_name.lower().replace(' ', ''))
        self._manifest = requests.get(self.manifest_url).json()

    def _get_manuscript(self):
        return self._manuscript_id

    def _set_manuscript(self, manuscript_id):
        self._manuscript_id = manuscript_id
        self._load_manifest()
        self._process_manifest()

    def _del_manuscript(self):
        self._manifest = None
        self._manuscript_id = None
        self._image_map = None
        self.manifest_url = None

    def get_url_for_image(self, image):
        pass

    manuscript_id = property(_get_manuscript, _set_manuscript, _del_manuscript)


ma = Manuscript()
ma.manuscript_id = 356
print ma.manifest_url
