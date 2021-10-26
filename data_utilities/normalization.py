import re
from typing import Dict, List
from functools import reduce
from bs4 import BeautifulSoup, Tag
from data_utilities.util import get_mapping_after_normalization, convert_normalized_indices_to_unnormalized_indices
"""
Tools for normalizing text
"""

UNIDECODE_TABLE = {
    "ḥ": "h",
    "Ḥ": "H",
    "ă": "a",
    "ǎ": "a",
    "ġ": "g",
    "ḫ": "h",
    "ḳ": "k",
    "Ḳ": "K",
    "ŏ": "o",
    "ṭ": "t",
    "ż": "z",
    "Ż": "Z",
    "’": "'",
    '\u05f3': "'",
    "\u05f4": '"',
    "”": '"',
    "“": '"'
}

class AbstractNormalizer:

    def __init__(self):
        pass

    def normalize(self, s: str, **kwargs) -> str:
        return s

    def find_text_to_remove(self, s:str, **kwargs) -> list:
        return []

class ITagNormalizer(AbstractNormalizer):

    def __init__(self, repl):
        super().__init__()
        self.repl = repl

    @staticmethod
    def _find_itags(tag):
        """
        Copied from sefaria.model.text.AbstractTextRecord to avoid making this file dependent on sefaria project
        """
        if isinstance(tag, Tag):
            is_footnote = tag.name == "sup" and isinstance(tag.next_sibling, Tag) and tag.next_sibling.name == "i" and 'footnote' in tag.next_sibling.get('class', '')
            is_inline_commentator = tag.name == "i" and len(tag.get('data-commentator', '')) > 0
            return is_footnote or is_inline_commentator
        return False

    @staticmethod
    def _get_all_itags(s):
        """
        Copied from sefaria.model.text.AbstractTextRecord to avoid making this file dependent on sefaria project
        Originally called `_strip_itags`
        """
        all_itags = []
        soup = BeautifulSoup(f"<root>{s}</root>", 'lxml')
        itag_list = soup.find_all(ITagNormalizer._find_itags)
        for itag in itag_list:
            all_itags += [itag]
            try:
                all_itags += [itag.next_sibling]  # it's a footnote
            except AttributeError:
                pass  # it's an inline commentator
        return all_itags, soup

    def normalize(self, s: str, **kwargs) -> str:
        all_itags, soup = ITagNormalizer._get_all_itags(s)
        for itag in all_itags:
            itag.decompose()
        return soup.root.encode_contents().decode()  # remove divs added

    def find_text_to_remove(self, s:str, **kwargs) -> list:
        all_itags, _ = ITagNormalizer._get_all_itags(s)
        prev_end = 0
        text_to_remove = []
        for itag in all_itags:
            itag_text = itag.decode()
            start = s.find(itag_text, prev_end)
            end = start+len(itag_text)
            if start == -1:
                raise Exception(f"Couldn't find itag with text '{itag_text}' in\n{s}\nprev_end = {prev_end}")
            text_to_remove += [((start, end), self.repl)]
            prev_end = end
        return text_to_remove

class ReplaceNormalizer(AbstractNormalizer):

    def __init__(self, old, new):
        super().__init__()
        self.old = old
        self.new = new

    def normalize(self, s, **kwargs):
        return s.replace(self.old, self.new)

    def find_text_to_remove(self, s, **kwargs):
        return [((m.start(), m.end()), self.new) for m in re.finditer(re.escape(self.old), s)]

class RegexNormalizer(AbstractNormalizer):

    def __init__(self, reg, repl) -> None:
        super().__init__()
        self.reg = reg
        self.repl = repl

    def normalize(self, s, **kwargs):
        return re.sub(self.reg, self.repl, s)

    def find_text_to_remove(self, s, **kwargs):
        return [((m.start(), m.end()), self.repl) for m in re.finditer(self.reg, s)]

class NormalizerComposer(AbstractNormalizer):

    def __init__(self, step_keys=None, steps=None) -> None:
        super().__init__()
        if steps is not None:
            self.steps = steps
        else:
            self.steps = NormalizerFactory.get_all(step_keys)

    def normalize(self, s, **kwargs):
        for step in self.steps:
            s = step.normalize(s)
        return s

    def find_text_to_remove(self, s, **kwargs):
        """
        this is a bit mind-boggling.
        apply normalization steps one-by-one and keep track of mapping from one step to the next
        iteratively apply mappings (in reverse) on each step's removal inds to get inds in original string
        """
        all_text_to_remove = []
        mappings = []
        snorm = s
        for step in self.steps:
            temp_text_to_remove = step.find_text_to_remove(snorm)
            if len(temp_text_to_remove) == 0:
                text_to_remove_inds, text_to_remove_repls = [], []
            else:
                text_to_remove_inds, text_to_remove_repls = zip(*temp_text_to_remove)
            for mapping in reversed(mappings):
                text_to_remove_inds = convert_normalized_indices_to_unnormalized_indices(text_to_remove_inds, mapping)
            temp_text_to_remove = list(zip(text_to_remove_inds, text_to_remove_repls))
            all_text_to_remove += [temp_text_to_remove]
            mappings += [get_mapping_after_normalization(snorm, step.find_text_to_remove)]
            snorm = step.normalize(snorm)
        # merge any overlapping ranges
        # later edits should override earlier ones
        final_text_to_remove = reduce(lambda a, b: self.merge_removal_inds(a, b), all_text_to_remove)
        final_text_to_remove.sort(key=lambda x: x[0])
        return final_text_to_remove

    def merge_removal_inds(self, curr_removal_inds, new_removal_inds):
        merged_inds = curr_removal_inds[:]
        for new_inds, new_repl in new_removal_inds:
            new_inds_set = set(range(new_inds[0], new_inds[1]))
            inds_are_final = True
            for i, (curr_inds, curr_repl) in enumerate(curr_removal_inds):
                curr_inds_set = set(range(curr_inds[0], curr_inds[1]))
                if curr_inds_set.issubset(new_inds_set):
                    # if earlier inds are a subset of later inds, later inds override
                    merged_inds.remove((curr_inds, curr_repl))
                elif len(curr_inds_set & new_inds_set) > 0:
                    # if later inds overlap and earlier inds are not a subset, merge
                    if new_inds_set.issubset(curr_inds_set):
                        merged_repl = curr_repl[:new_inds[0] - curr_inds[0]] + new_repl + curr_repl[new_inds[1] -
                                                                                                curr_inds[1]:]
                        merged_inds[i] = (curr_inds, merged_repl)
                        inds_are_final = False
                        break
                    else:
                        # overlap that's not a subset. more complicated merge that I don't want to deal with now
                        pass
            if inds_are_final:
                merged_inds += [(new_inds, new_repl)]
        return merged_inds

class TableReplaceNormalizer(AbstractNormalizer):

    def __init__(self, table):
        super().__init__()
        replace_pairs = sorted(table.items(), key=lambda x: len(x[0]), reverse=True)
        steps = [ReplaceNormalizer(old, new) for old, new in replace_pairs]
        self.step_composer = NormalizerComposer(steps=steps)

    def normalize(self, s, **kwargs):
        return self.step_composer.normalize(s)

    def find_text_to_remove(self, s, **kwargs):
        return self.step_composer.find_text_to_remove(s)

class NormalizerFactory:
    key_normalizer_map = {
        "html": RegexNormalizer(r"\s*<[^>]+>\s*", " "),
        "cantillation": RegexNormalizer("[\u0591-\u05bd\u05bf-\u05c5\u05c7]+", ""),
        "parens-plus-contents": RegexNormalizer(r"\([^)]+\)", ""),
        "brackets": RegexNormalizer(r"[\[\]]", ""),
        "unidecode": TableReplaceNormalizer(UNIDECODE_TABLE),
        "maqaf": ReplaceNormalizer('־', ' '),
        "itag": ITagNormalizer(''),
        "br-tag": ReplaceNormalizer('<br>', '<br/>'),
    }

    @classmethod
    def get(cls, normalizer_key):
        return cls.key_normalizer_map[normalizer_key]

    @classmethod
    def get_all(cls, step_keys: List[str]):
        cls.validate_keys(step_keys)
        return [cls.get(key) for key in step_keys]

    @classmethod
    def validate_keys(cls, step_keys):
        if step_keys is None:
            raise Exception("step_keys and steps cannot both be None")
        nonexistant_keys = []
        for key in step_keys:
            if key not in cls.key_normalizer_map:
                nonexistant_keys += [key]
        if len(nonexistant_keys) > 0:
            raise Exception(f"Couldn't find the following keys in NormalizerComposer.key_normalizer_map:", ", ".join(nonexistant_keys))

class NormalizerByLang(AbstractNormalizer):

    def __init__(self, normalizers_by_lang: Dict[str, AbstractNormalizer]):
        super().__init__()
        self.normalizers_by_lang = normalizers_by_lang

    def normalize(self, s: str, **kwargs) -> str:
        lang = kwargs.get('lang')
        if lang not in self.normalizers_by_lang: return s
        return self.normalizers_by_lang[lang].normalize(s, **kwargs)

    def find_text_to_remove(self, s:str, **kwargs) -> list:
        lang = kwargs.get('lang')
        if lang not in self.normalizers_by_lang: return []
        return self.normalizers_by_lang[lang].find_text_to_remove(s, **kwargs)
