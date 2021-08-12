import django, re, requests, json
django.setup()
from research.quotation_finder.dicta_api import *
import cProfile


def run_ys_torah():
    title = "Yalkut Shimoni on Torah"
    ys_peared = get_zip_ys()
    peared = []
    [peared.extend(e) for e in ys_peared] # beacuse ys_peared returned a list of lists (per chumash)
    priority = dict([(r.normal(),item[0]) for item in peared if item[1] for r in item[1].all_segment_refs()])
    run_offline(title, 'Midrash', min_thresh=25, post=False, mongopost=True, priority_tanakh_chunk_type=priority, max_word_number=None)
    log.close()


def run_ys_Nach(title):
    title = title
    peared = get_zip_alt_struct(title, 'Book')
    priority = dict([(r.normal(), item[0]) for item in peared if item[1] for r in item[1].all_segment_refs()])
    run_offline(title, 'Midrash', min_thresh=25, post=False, mongopost=True, priority_tanakh_chunk_type=priority,
                max_word_number=None)
    log.close()


if __name__ == '__main__':
    run_ys_Nach("Yalkut Shimoni on Nach")
    # cProfile('run_ys_Nach("Yalkut Shimoni on Nach")')