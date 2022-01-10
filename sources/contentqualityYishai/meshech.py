import django
django.setup()
from sefaria.model import *
from sefaria.helper.schema import cascade

old_title = 'Balak '
new_title = 'Balak'
def rewriter(string):
    return string.replace(old_title, new_title)

def needs_rewrite(string, *args):
    return string.find(old_title) >= 0 and node.index.title in string

node = library.get_index('Meshech Hochma').nodes.all_children()[47]
node.add_title(new_title, 'en', replace_primary=True, primary=True)
node.index.save()
cascade(node.index.title, rewriter=rewriter, needs_rewrite=needs_rewrite)
node.remove_title(old_title, 'en')
node.index.save(override_dependencies=True)
library.refresh_index_record_in_cache(node.index)
