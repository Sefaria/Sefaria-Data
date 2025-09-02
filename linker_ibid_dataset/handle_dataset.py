import django
django.setup()
import random
from sefaria.model import IndexSet
from typing import Iterable, List, Optional, Set, Dict
from sefaria.model import VersionSet, Ref, Index
from sefaria.model.link import LinkSet
from sefaria.system.exceptions import InputError
from tqdm import tqdm
import re
from functools import lru_cache


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


# def reservoir_sample_refs(k: int, include_commentary: bool = True) -> List[Ref]:
#     """
#     Uniformly sample k refs from the (potentially huge) stream using reservoir sampling.
#     """
#     reservoir: List[Ref] = []
#     for t, ref in enumerate(iter_segment_refs(include_commentary=include_commentary), start=1):
#         if t <= k:
#             reservoir.append(ref)
#         else:
#             j = random.randint(1, t)  # inclusive
#             if j <= k:
#                 reservoir[j - 1] = ref
#     return reservoir
import random
import re
from typing import Iterable, List, Optional, Set, Tuple

from sefaria.model import VersionSet, Ref, LinkSet
try:
    # Older/newer Sefaria versions may place InputError in different modules
    from sefaria.system.exceptions import InputError
except Exception:  # pragma: no cover
    class InputError(Exception):
        pass


class _SegmentCollector:
    """
    Collector compatible with Version.walk_thru_contents action signature.
    Handles both (text, tref, heTref, version, ...) and other variants
    by unpacking args defensively.
    """
    def __init__(
        self,
        prev_tagged_refs: Optional[Iterable[str]] = None,
        with_links: bool = False,
        max_chars: Optional[int] = None,
    ):
        self.prev: Set[str] = set(prev_tagged_refs or [])
        self.with_links = with_links
        self.max_chars = max_chars
        self._candidates: List[Tuple[Ref, int]] = []  # (ref, text_len)

    def _extract(self, *args, **kwargs) -> Optional[Tuple[Ref, str]]:
        """
        Try to normalize the various callback forms to (Ref, text).
        Expected modern Sefaria form: (segment_text, segment_tref, segment_heTref, version, ...)
        But we also accept variants; we just need a tref (string) and the text.
        """
        text = None
        tref = None

        # Common case: first 3 are (text, tref, heTref)
        if len(args) >= 2 and isinstance(args[0], str) and isinstance(args[1], str):
            text = args[0]
            tref = args[1]
        else:
            # Fallback: scan args for a plausible text and tref
            for a in args:
                if text is None and isinstance(a, str) and len(a) > 0:
                    # Heuristic: pick the first long-ish string as text,
                    # but we'll prefer the *first* argument as text when the standard form is used.
                    text = text or a
            # For tref, prefer a string that Ref(...) accepts
            for a in args:
                if isinstance(a, str):
                    try:
                        _r = Ref(a)
                        tref = a
                        break
                    except Exception:
                        continue

        if tref is None or text is None:
            return None

        try:
            ref = Ref(tref)
        except Exception:
            return None

        return ref, text

    def action(self, *args, **kwargs):
        """
        Callback invoked by Version.walk_thru_contents. We unpack to (Ref, text)
        and then apply our filters.
        """
        unpacked = self._extract(*args, **kwargs)
        if unpacked is None:
            return
        ref, text = unpacked

        if not ref.is_segment_level():
            return
        if not text:
            return
        if self.max_chars is not None and len(text) > self.max_chars:
            return

        norm = ref.normal()
        if norm in self.prev:
            return

        if self.with_links:
            try:
                if len(LinkSet(ref)) == 0:
                    return
            except Exception:
                # If LinkSet lookup fails, skip link-filtering rather than crash
                pass

        self._candidates.append((ref, len(text)))

    @property
    def candidates(self) -> List[Ref]:
        # Deduplicate while preserving traversal order
        seen: Set[str] = set()
        out: List[Ref] = []
        for r, _ in self._candidates:
            n = r.normal()
            if n not in seen:
                seen.add(n)
                out.append(r)
        return out



def sample_segment_refs(
    lang: str,
    *,
    prev_tagged_refs: Optional[Iterable[str]] = None,
    with_links: bool = False,
    sample_size: int = 100,
    max_chars: Optional[int] = None,
    rng: Optional[random.Random] = None,
) -> List[Ref]:
    """
    Traverse Sefaria library versions in the given language and return a random sample
    of segment-level Refs.

    Mirrors the traversal style of `make_random_prodigy_input`:
      - Iterate VersionSet({"language": lang})
      - Skip 'sidecar' titles that end with a bracketed language tag like "...[en]" / "...[he]"
      - For each version, call `walk_thru_contents` with a simple collector callback
      - Optionally filter to segments that already have links (LinkSet(ref) non-empty)
      - Optionally filter by max character length of the segment's text
      - Exclude any refs listed in `prev_tagged_refs`
      - Sample up to `sample_size` unique segment refs

    Args:
        lang: "en" or "he" – the Version language to traverse.
        prev_tagged_refs: Refs (strings) to exclude from sampling.
        with_links: If True, only include segments that have at least one existing Link.
        sample_size: Maximum number of refs to return.
        max_chars: If provided, exclude segments whose text length exceeds this number.
        rng: Optional random.Random instance for deterministic tests.

    Returns:
        List[Ref]: random sample (unique, order-agnostic) of segment-level Refs.
    """
    assert lang in {"en", "he"}, f"lang must be 'en' or 'he', got: {lang}"
    r = rng or random

    versions = VersionSet({"language": lang}).array()

    # Same skip rule as the Prodigy script: ignore titles ending with bracketed suffixes like "[en]" or "[he]"
    bracket_suffix = re.compile(r"\[[a-zA-Z]+]$")

    collector = _SegmentCollector(
        prev_tagged_refs=prev_tagged_refs,
        with_links=with_links,
        max_chars=max_chars,
    )

    for version in tqdm(versions):
        # Version.versionTitle is a string like "Some Title [en]" in some collections—skip those sidecars.
        if bracket_suffix.search(getattr(version, "versionTitle", "") or ""):
            continue
        try:
            # Walk through all segment-level contents of this Version.
            # The callback receives (ref, text, **kwargs)
            version.walk_thru_contents(collector.action)
        except InputError:
            # Some versions can fail to iterate; match the resilient behavior in the original script.
            continue
        except Exception:
            # Be robust: a single bad version shouldn't kill the whole sampling process.
            continue

    candidates = collector.candidates
    if not candidates:
        return []

    # Random sample without replacement (cap by population size)
    k = min(sample_size, len(candidates))
    if k == len(candidates):
        # Shuffle to avoid bias from traversal order and return all
        r.shuffle(candidates)
        return candidates
    return r.sample(candidates, k)




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
    from ibid_llm_marker import *

    # out = analyze_segment_llm_marker_only("Abraham_Cohen_Footnotes_to_the_English_Translation_of_Masechet_Berakhot.48b.6", lang="en")
    # print(out["has_any_ibid"], out["ibid_citations"])

    # rows = analyze_ref_for_ibid_and_resolution("Abraham_Cohen_Footnotes_to_the_English_Translation_of_Masechet_Berakhot.48b.6", lang="en")
    # llm_ibids, linker_ibids = split_llm_vs_linker(rows)
    # cands = sample_hebrew_cited_refs(100, pool_size=100000)
    # yes, no = batch_refs_llm_marker_only(cands, lang="he")
    # print("with ibid:", len(yes), "without:", len(no))

    # eng = sample_english_cited_refs(10, pool_size=200)
    # heb = sample_hebrew_cited_refs(10, pool_size=200)
    #
    # print("EN:", eng)
    # print("HE:", heb)

    # for ref in sampled_refs:
    #     print(ref)

    refs = sample_segment_refs(lang="en", sample_size=200)
    print(refs)
