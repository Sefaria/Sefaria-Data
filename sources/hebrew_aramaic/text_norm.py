import django
from pymongo.errors import DuplicateKeyError
import csv
from sefaria.helper.normalization import TableReplaceNormalizer, RegexNormalizer, NormalizerComposer
django.setup()

with open('abbr.csv') as fp:
    abbr = sorted(list(csv.DictReader(fp))[65:], key=lambda i: len(i['from']))
    abbr = {row['from']: row['to'] for row in abbr}
ref_replacement_table = {**abbr}
table_normalizer = TableReplaceNormalizer(ref_replacement_table)
yerushalmi_normalizer = RegexNormalizer('(ירושלמי (?:[^ ]+ ){1,2}?)פ(?:״[א-כ]|[ט-כ]״[א-ט]) ', r'\1 דף ')
normalizer = NormalizerComposer(steps=[table_normalizer, yerushalmi_normalizer])

text = 'ירוש׳ שבת פ״ב ה׳ ע״ב׃ כפר אגין. 2) ע׳ בָּאייָן. תנח׳ אמור י״ח׃ מי'
ref_text = 'תנחומא אמור י״ח'
normalized_text = normalizer.normalize(text)
mapping, subst_end_indices = normalizer.get_mapping_after_normalization(text)
norm_ind_start = normalized_text.find(ref_text)
norm_range = (norm_ind_start, norm_ind_start + len(ref_text))
orig_range = normalizer.norm_to_unnorm_indices_with_mapping([norm_range], mapping, subst_end_indices)[0]

orig_text = text[slice(*orig_range)]

print(orig_text)
