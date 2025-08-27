import django
django.setup()
import random
import os
import pickle
from sefaria.model import library
from sefaria.model import Ref
from sefaria.model import IndexSet

CACHE_FILE = "segment_refs_cache.pkl"

# def build_segment_refs_cache():
#     """
#     Build and cache all segment refs from the Sefaria library.
#     """
#     all_index_records = IndexSet()
#     segment_refs = []
#
#     for index in all_index_records:
#         try:
#             top_ref = Ref(index.title)  # e.g. "Genesis"
#             segment_refs.extend(top_ref.all_segment_refs())
#         except Exception:
#             continue
#
#     # Save to cache file
#     with open(CACHE_FILE, "wb") as f:
#         pickle.dump(segment_refs, f)
#
#     return segment_refs
#
#
# def load_segment_refs():
#     """
#     Load segment refs from cache if available, otherwise build it.
#     """
#     if os.path.exists(CACHE_FILE):
#         with open(CACHE_FILE, "rb") as f:
#             return pickle.load(f)
#     else:
#         return build_segment_refs_cache()
#
#
# def sample_segment_refs(n=5, as_strings=True):
#     """
#     Sample random segment refs from cached segment refs.
#     """
#     segment_refs = load_segment_refs()
#     chosen = random.sample(segment_refs, min(n, len(segment_refs)))
#     return [str(r) for r in chosen] if as_strings else chosen

import django
django.setup()

import random
from typing import List, Optional
from sefaria.model import Ref, IndexSet, TextChunk, library


def sample_english_cited_refs(n: int = 5, max_chars: Optional[int] = 4000) -> List[str]:
    """
    Sample n random refs where the English linker (CNN) finds ≥1 citation.
    """
    linker = library.get_linker("en")
    all_refs = []
    for idx in IndexSet():
        try:
            top = Ref(idx.title)
            for seg in top.all_segment_refs():
                try:
                    txt = TextChunk(seg, "en").as_string()
                    if max_chars and len(txt) > max_chars:
                        txt = txt[:max_chars]
                    if not txt.strip():
                        continue
                    doc = linker.link(txt, type_filter="citation", with_failures=False)
                    if doc.resolved_refs:
                        all_refs.append(str(seg))
                except Exception:
                    continue
        except Exception:
            continue
    return random.sample(all_refs, min(n, len(all_refs)))


def sample_hebrew_cited_refs(n: int = 5, max_chars: Optional[int] = 4000) -> List[str]:
    """
    Sample n random refs where the Hebrew linker (BEREL) finds ≥1 citation.
    """
    linker = library.get_linker("he")
    all_refs = []
    for idx in IndexSet():
        try:
            top = Ref(idx.title)
            for seg in top.all_segment_refs():
                try:
                    txt = TextChunk(seg, "he").as_string()
                    if max_chars and len(txt) > max_chars:
                        txt = txt[:max_chars]
                    if not txt.strip():
                        continue
                    doc = linker.link(txt, type_filter="citation", with_failures=False)
                    if doc.resolved_refs:
                        all_refs.append(str(seg))
                except Exception:
                    continue
        except Exception:
            continue
    return random.sample(all_refs, min(n, len(all_refs)))
import django
django.setup()

import random
from typing import List, Optional
from sefaria.model import Ref, IndexSet, TextChunk, library


import django
django.setup()

import random
from typing import Iterable, List, Optional
from sefaria.model import Ref, IndexSet, TextChunk, library


# ---------- basic iterators ----------
def iter_segment_refs(include_commentary: bool = True) -> Iterable[Ref]:
    """
    Yield segment-level Refs across the whole library.
    """
    for idx in IndexSet():
        try:
            if not include_commentary:
                cats = getattr(idx, "categories", []) or []
                if "Commentary" in cats or "Commentary2" in cats:
                    continue
            top = Ref(idx.title)
            for seg in top.all_segment_refs():
                yield seg
        except Exception:
            continue


def reservoir_sample_refs(k: int, include_commentary: bool = True) -> List[Ref]:
    """
    Uniformly sample k refs from the (potentially huge) stream using reservoir sampling.
    """
    reservoir: List[Ref] = []
    for t, ref in enumerate(iter_segment_refs(include_commentary=include_commentary), start=1):
        if t <= k:
            reservoir.append(ref)
        else:
            j = random.randint(1, t)  # inclusive
            if j <= k:
                reservoir[j - 1] = ref
    return reservoir


# ---------- linker helpers ----------
def _has_citation(ref: Ref, lang: str, linker, max_chars: Optional[int]) -> bool:
    try:
        txt = TextChunk(ref, lang).as_string()
        if not txt:
            return False
        if max_chars and len(txt) > max_chars:
            txt = txt[:max_chars]
        if not txt.strip():
            return False
        doc = linker.link(txt, type_filter="citation", with_failures=False)
        return bool(getattr(doc, "resolved_refs", []))
    except Exception:
        return False


# ---------- public apis (ENG/HE separately) ----------
def sample_english_cited_refs(
    n: int = 5,
    *,
    pool_size: int = 5000,
    include_commentary: bool = True,
    max_chars: Optional[int] = 4000,
) -> List[str]:
    """
    1) Uniformly sample `pool_size` random segment refs (cheap).
    2) Run English linker on that pool until `n` hits are found (fast).
    """
    linker_en = library.get_linker("en")
    pool = reservoir_sample_refs(pool_size, include_commentary=include_commentary)
    random.shuffle(pool)  # extra shuffle to avoid category clumping

    hits: List[str] = []
    for ref in pool:
        if _has_citation(ref, "en", linker_en, max_chars):
            hits.append(str(ref))
            if len(hits) >= n:
                break
    return hits


def sample_hebrew_cited_refs(
    n: int = 5,
    *,
    pool_size: int = 5000,
    include_commentary: bool = True,
    max_chars: Optional[int] = 4000,
) -> List[str]:
    """
    1) Uniformly sample `pool_size` random segment refs (cheap).
    2) Run Hebrew linker on that pool until `n` hits are found (fast).
    """
    linker_he = library.get_linker("he")
    pool = reservoir_sample_refs(pool_size, include_commentary=include_commentary)
    random.shuffle(pool)

    hits: List[str] = []
    for ref in pool:
        if _has_citation(ref, "he", linker_he, max_chars):
            hits.append(str(ref))
            if len(hits) >= n:
                break
    return hits




if __name__ == "__main__":
    eng = sample_english_cited_refs(10, pool_size=8000)
    heb = sample_hebrew_cited_refs(10, pool_size=8000)

    print("EN:", eng)
    print("HE:", heb)

    # for ref in sampled_refs:
    #     print(ref)