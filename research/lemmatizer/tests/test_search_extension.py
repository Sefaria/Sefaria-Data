import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from seed_search_extension import validate_reuse

class ExtensionTests(unittest.TestCase):
    def test_reuse_only_unchanged_complete_documents(self):
        old=[{'doc_id':'a','text_sha256':'one','version':'v1'}]
        annotations=[{'doc_id':'a','text_sha256':'one'}]
        validate_reuse(old,old+[{'doc_id':'b','text_sha256':'two'}],annotations)
        with self.assertRaises(ValueError):validate_reuse(old,[dict(old[0],version='v2')],annotations)
        with self.assertRaises(ValueError):validate_reuse(old,old,[])
        with self.assertRaises(ValueError):validate_reuse(old,old,annotations*2)
        with self.assertRaises(ValueError):validate_reuse(old,old,[dict(annotations[0],text_sha256='changed')])
