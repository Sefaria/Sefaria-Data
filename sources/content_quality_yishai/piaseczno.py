import django
django.setup()
from sefaria.helper.category import move_index_into, create_category
from sefaria.model import *
from sefaria.settings import USE_VARNISH, MULTISERVER_ENABLED
from sefaria.system.multiserver.coordinator import server_coordinator

create_category(['Chasidut', 'Piaseczno Rebbe'], 'Piaseczno Rebbe', 'האדמו"ר מפיאסצנה')
inds = ['Bnei Machshava Tova', 'Chovat HaTalmidim']#,'Mevo HaShearim']
for index in inds:
    move_index_into(index, ['Chasidut', 'Piaseczno Rebbe'])
library.rebuild_toc()
if MULTISERVER_ENABLED:
    server_coordinator.publish_event("library", "rebuild_toc")
if USE_VARNISH:
    from sefaria.system.varnish.wrapper import invalidate_all, invalidate_title
    invalidate_all()
for index in inds:
    oref = Ref(index)
    library.refresh_index_record_in_cache(oref.index)
    library.update_index_in_toc(oref.index)

    if MULTISERVER_ENABLED:
        server_coordinator.publish_event("library", "refresh_index_record_in_cache", [oref.index.title])
        server_coordinator.publish_event("library", "update_index_in_toc", [oref.index.title])
    elif USE_VARNISH:
        invalidate_title(oref.index.title)
library.rebuild()
if MULTISERVER_ENABLED:
    server_coordinator.publish_event("library", "rebuild")
