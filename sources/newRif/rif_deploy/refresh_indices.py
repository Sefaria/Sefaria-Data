# encoding=utf-8

import sys
import time
import django
django.setup()
from sefaria import model
from sefaria.settings import MULTISERVER_ENABLED, USE_VARNISH
from sefaria.system.multiserver.coordinator import server_coordinator
from sefaria.system.varnish.wrapper import invalidate_title


def reset_ref(tref, reset_text_cache=False):
    oref = model.Ref(tref)
    model.library.refresh_index_record_in_cache(oref.index)
    if reset_text_cache:
        model.library.reset_text_titles_cache()
    vs = model.VersionState(index=oref.index)
    vs.refresh()
    model.library.update_index_in_toc(oref.index)

    if MULTISERVER_ENABLED:
        server_coordinator.publish_event("library", "refresh_index_record_in_cache", [oref.index.title])
        server_coordinator.publish_event("library", "update_index_in_toc", [oref.index.title])
    elif USE_VARNISH:
        invalidate_title(oref.index.title)


if len(sys.argv) >= 2:
    start_from = int(sys.argv[1])
else:
    start_from = 0
indexes = model.library.get_indexes_in_category('Rif', include_dependant=True)
for i, item in enumerate(indexes[start_from:], start_from):
    print('refreshing', i, 'out of', len(indexes))
    if i >= len(indexes) - 1:
        print('last item rebuilding text title cache')
        reset_ref(item, True)
    else:
        reset_ref(item)
    if i % 5 == 4:
        time.sleep(5)
