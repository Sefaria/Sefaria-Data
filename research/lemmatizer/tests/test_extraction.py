import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import unittest
from extraction_core import find_spans, plain_text, ranked_hebrew_versions


class ExtractionTests(unittest.TestCase):
    def test_offsets_and_repetition(self):
        text = 'כִּמְעַט כִּמְעַט'
        spans = find_spans(text, 'כמעט', 'vowel_insensitive')
        self.assertEqual(len(spans), 2)
        self.assertEqual([text[a:b] for a,b in spans], ['כִּמְעַט'] * 2)

    def test_word_boundaries(self):
        self.assertEqual(find_spans('ובני בני־ישראל בניו', 'בני', 'exact'), [(5, 8)])
        self.assertEqual(find_spans('רש״י', 'רש', 'exact'), [])

    def test_exact_does_not_drop_pointing(self):
        self.assertEqual(find_spans('בּ', 'ב', 'exact'), [])

    def test_canonical_order_and_accents(self):
        text = 'בְּרֵאשִׁ֖ית'
        form = 'בְּרֵאשִׁית'
        self.assertEqual(find_spans(text, form, 'cantillation_insensitive'), [(0, len(text))])

    def test_markup(self):
        self.assertEqual(plain_text('<big>ב</big>ראשית<sup>1</sup><i class="footnote">note</i><br>ברא'), 'בראשית ברא')
        self.assertEqual(plain_text('<b>א</b>&nbsp;<b>ב</b>'), 'א ב')

    def test_version_ranking_and_language(self):
        versions = [
            {'_id': 'a', 'language': 'he', 'actualLanguage': 'yi', 'priority': 100},
            {'_id': 'b', 'languageFamilyName': 'hebrew', 'priority': 4, 'isPrimary': False},
            {'_id': 'd', 'actualLanguage': 'he', 'priority': 2, 'isPrimary': True},
            {'_id': 'c', 'actualLanguage': 'he', 'priority': 2, 'isPrimary': True}]
        self.assertEqual([v['_id'] for v in ranked_hebrew_versions(versions)], ['c', 'b', 'd'])


if __name__ == '__main__':
    unittest.main()


class PipelineTests(unittest.TestCase):
    def test_deduplication_and_ambiguous_spans(self):
        import tempfile
        from pathlib import Path
        from build_dataset import Store, extract

        class Ref:
            def __init__(self, value):
                self.value = value
                self.index_node = type('Node', (), {'is_virtual': False})()
            def is_book_level(self):
                return False
            def all_segment_refs(self):
                return [self]
            def normal(self):
                return self.value

        class Backend:
            InputError = ValueError
            def passage(self, ref):
                return {'passage_id': 'p', 'text': 'מעט מעט'}
        Backend.Ref = Ref
        with tempfile.TemporaryDirectory() as directory:
            store = Store(Path(directory))
            for wid, eid in [('w1','e1'),('w2','e2')]:
                store.put('word_forms', wid, {'source_record': {'form':'מעט'},
                    'resolved_lookups':[{'entry_ids':[eid], 'lookup':{'headword':'מעט'}}]})
                store.db.execute('INSERT INTO work VALUES (?,?)', ('Genesis 1:1',wid))
            stats = extract(Backend(), store, 100, ['exact'])
            self.assertEqual(stats['matched_multiple'], 2)
            self.assertEqual(store.db.execute("SELECT count(*) FROM records WHERE kind='occurrences'").fetchone()[0], 2)
            self.assertEqual(store.db.execute('SELECT count(*) FROM associations').fetchone()[0], 4)
            store.db.close()
