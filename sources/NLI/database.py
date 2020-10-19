# encoding=utf-8

import re
import sqlite3
import requests
import unicodecsv
from threading import Lock as threadLock
from collections import defaultdict
from concurrent.futures.thread import ThreadPoolExecutor
from sources.NLI.path_to_db_file import DB_FILE_LOCATION


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
            Images.Im_ImRun, Images.Im_File, Images.Ma_LibName, Images.Ma_NameDescription, Images.Ma_Description, Images.Ma_ID, 
            Images.Li_ID 
            FROM TblFullRef FR
            JOIN TblTractates Trac ON Fr_Tr = Trac.Tr_code
            JOIN TblPerek Pe ON Fr_F1 = Pe.Pe_code
            JOIN TblMishna Mi ON Fr_F2 = Mi.Mi_code
            JOIN TblTalmod Tal ON FR.Fr_Co = Tal.Fr_Co
            JOIN TblImgRef IR ON FR.Fr_Img = IR.Ir_Img
            JOIN (
                SELECT Im.Im_Id, Mans.Ma_Name, Mans.Ma_LibName, Mans.Ma_NameDescription, Mans.Ma_Description, 
                Im.Im_File, Im.Im_ImRun, Mans.Ma_ID, Mans.Li_ID 
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
            print(e)

        self.cursor.execute("CREATE TABLE aggregation (Book_Type, Tractate, Chapter, Verse, image_start, image_end, "
                            "Manuscript, Im_Run, Filename, Library, Manuscript_Description, "
                            "Extended_Manuscript_Description, Manuscript_ID, Library_ID)")

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


u"""
go for Tosefta in and Berlin (Munich? We probably meant Vienna). 
Vienna Manuscript ID - 7658
Berlin Manuscript ID - 1484

Harley 5508 from British Museum - Bavli, Manuscript ID = 4752
Might also be worth looking at Add. 25,717 from the British Museum. Manuscript ID = 4754


Leiden - תלמוד ירושלמי. Manuscript Id 1721
"""

