# encoding=utf-8

import re
import sqlite3
import requests
import unicodecsv
from threading import Lock as threadLock
from collections import defaultdict
from concurrent.futures.thread import ThreadPoolExecutor
from path_to_db_file import DB_FILE_LOCATION

import django
django.setup()
from sefaria.model import *



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

        # lock for multithreading
        self.lock = threadLock()

    @staticmethod
    def get_major_query_string():
        return '''
            SELECT Tal.Fr_Name, Trac.Tr_Name, Pe.Pe_ab, Mi.Mi_ab, IR.sfrom im_start, IR.sto im_end, Images.Ma_Name,
            Images.Im_ImRun, Images.Ma_LibName, Images.Ma_NameDescription, Images.Ma_Description, Images.Ma_ID, 
            Images.Li_ID 
            FROM TblFullRef FR
            JOIN TblTractates Trac ON Fr_Tr = Trac.Tr_code
            JOIN TblPerek Pe ON Fr_F1 = Pe.Pe_code
            JOIN TblMishna Mi ON Fr_F2 = Mi.Mi_code
            JOIN TblTalmod Tal ON FR.Fr_Co = Tal.Fr_Co
            JOIN TblImgRef IR ON FR.Fr_Img = IR.Ir_Img
            JOIN (
                SELECT Im.Im_Id, Mans.Ma_Name, Mans.Ma_LibName, Mans.Ma_NameDescription, Mans.Ma_Description, 
                Im.Im_ImRun, Mans.Ma_ID, Mans.Li_ID 
                FROM TblImages Im
                JOIN (
                    SELECT MS.Ma_Name, Li.Ma_LibName, MS.Ma_NameDescription, MS.Ma_Description, MS.Ma_ID, Li.Li_ID 
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
                            "Manuscript, Im_Run, Library, Manuscript_Description, Extended_Manuscript_Description, "
                            "Manuscript_ID, Library_ID)")

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


nli_db = Database()


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
        """
        Load im_run values into a set
        Walk through manifest.
            For each image in manifest, derive im_run for image
            If that im_run is in the set of im_run values, set the url for that image
        :return:
        """
        def derive_im_run(canvas_id):
            return int(re.search(u'p(\d+)$', canvas_id).group(1))

        if not self._manifest or not self.manuscript_id:
            raise ManuscriptException("manuscript_id not set")

        image_map = {}

        with nli_db.lock:
            nli_db.cursor.execute('SELECT IM.Im_ImRun ir FROM TblImages IM '
                                  'WHERE IM.Im_Ms = ?', (self.manuscript_id,))
            image_values = set([r['ir'] for r in nli_db.cursor.fetchall()])

        for canvas in self._manifest['sequences'][0]['canvases']:
            im_run = derive_im_run(canvas['@id'])
            if im_run in image_values:
                image_map[im_run] = canvas['images'][0]['resource']['service']['@id']

        self._image_map = image_map

    def _load_manifest(self):
        if self._manuscript_id is None:
            raise ManuscriptException("Manuscript id not set")

        with nli_db.lock:  # make sure only one manuscript is accessing the db at any given time (sqlite requirement)
            nli_db.cursor.execute('SELECT Ma.Ma_Name, Li.base_url FROM TblManuscripts Ma '
                                  'JOIN TblLibraries Li ON Ma.Ma_LibID = Li.Li_ID '
                                  'WHERE Ma.Ma_ID = ?', (self._manuscript_id,))

            result = nli_db.cursor.fetchone()
            base_url, manuscript_name = result['base_url'], result['Ma_Name']
            # manuscript_name = re.match(u'^[^0-9]+[0-9]+', manuscript_name).group(0)

        if base_url is None:
            raise LibraryException("Url has not been set for this Library")

        self.manifest_url = u'{}{}/manifest.json'.format(base_url, manuscript_name.lower().replace(' ', ''))
        try:
            self._manifest = requests.get(self.manifest_url).json()
        except ValueError:
            print "Could not load manifest url {} for manuscript {}".format(self.manifest_url, self.manuscript_id)
            # del self.manuscript_id
            raise ManuscriptException

    def _get_manuscript(self):
        return self._manuscript_id

    def _set_manuscript(self, manuscript_id):
        self._manuscript_id = manuscript_id
        try:
            self._load_manifest()
            self._process_manifest()
        except ManuscriptException:
            del self.manuscript_id

    def _del_manuscript(self):
        self._manifest = None
        self._manuscript_id = None
        self._image_map = None
        self.manifest_url = None

    def get_url_for_image(self, image):
        if self.manuscript_id is None:
            raise ManuscriptException("Manuscript id not set")

        try:
            return self._image_map[image]
        except KeyError:
            raise ManuscriptException("Image not found in this manuscript")

    manuscript_id = property(_get_manuscript, _set_manuscript, _del_manuscript)


"""
Get url for Ref:
Important to note that the Image_ID is a unique ID in the database, while the ImRun is unique per manifest.

If we can derive the Ref from an aggregation row, then we should be able to use the row's Im_Run and Manuscript ID
to get the url from a Manuscript instance.
"""


def derive_ref(book_type, tractate, chapter, verse):
    base_ref = u'{} {}, {}'.format(tractate, chapter, verse)
    if book_type == u'תלמוד בבלי':
        return Ref(base_ref).normal()
    elif book_type == u'משנה':
        return Ref(u'{} {}'.format(u'משנה', base_ref)).normal()
    else:
        return None


def derive_ref_from_row_data(row_data):
    return derive_ref(row_data['Book_Type'], row_data['Tractate'], row_data['Chapter'], row_data['Verse'])


if __name__ == '__main__':
    nli_db.cursor.execute('SELECT ma.Ma_ID FROM TblManuscripts ma WHERE ma.Ma_LibID = 11')
    results = [r['Ma_ID'] for r in nli_db.cursor.fetchall()]

    with ThreadPoolExecutor() as executor:
        manuscripts = executor.map(Manuscript, results)

    manuscripts = {man.manuscript_id: man for man in manuscripts if man.manuscript_id}

    nli_db.cursor.execute('SELECT * FROM aggregation WHERE Library_ID=11')
    ref_mapping = []
    for row in nli_db.cursor.fetchall():
        if manuscripts.get(row['Manuscript_ID'], None):
            ref_mapping.append({
                'full_ref': derive_ref_from_row_data(row),
                'image_url': manuscripts[row['Manuscript_ID']].get_url_for_image(row['Im_Run']),
                'Institution': row['Library'],
                'Manuscript ID': row['Manuscript_ID'],
                'desc': row['Extended_Manuscript_Description']
            })

    import random
    for _ in range(10):
        foo = random.choice(ref_mapping)
        print foo['full_ref'], u'{}/full/1600,/0/default.jpg'.format(foo['image_url'])

