import django
django.setup()
from sefaria.helper.normalization import TableReplaceNormalizer
from sefaria.model import *

linker = library.get_linker('he')
table = {'זב׳': 'זבחים', 'תוס׳': 'תוספתא', 'נד': 'נדרים'}
normalizer = TableReplaceNormalizer(table)
my_string = 'תוס׳ זב׳ ג ד'
my_string_norm = normalizer.normalize(my_string)
doc = linker.link(my_string_norm, with_failures=True)
ref_text = doc.resolved_refs[0].raw_entity.span.text
norm_ind_start = my_string_norm.find(ref_text)
norm_range = (norm_ind_start, norm_ind_start + len(ref_text))
mapping, subst_end_indices = normalizer.get_mapping_after_normalization(my_string)
orig_range = normalizer.norm_to_unnorm_indices_with_mapping([norm_range], mapping, subst_end_indices)[0]
print(orig_range)
