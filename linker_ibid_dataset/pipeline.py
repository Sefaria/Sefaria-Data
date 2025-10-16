# -*- coding: utf-8 -*-
"""
Ibid dataset builder (end-to-end)

- Randomly sample segment refs (en/he)
- GPU citation detection (REST; /recognize-entities?with_span_text=1)
- Tag citations as <ref id="rN">…</ref>
- LLM (LangChain + OpenAI) decides which are IBID (returns {"ibid_ids":[...]})
- Build >= 1000 left-context words for each ibid
- Run linker; save BOTH unresolved and resolved ibids to JSONL

ENV:
  export CITATION_GPU_URL=http://localhost:8000
  export OPENAI_API_KEY=sk-...
  # optional:
  export OPENAI_MODEL=gpt-4o-mini
"""

import os
import re
import json
import time
import random
import requests
import django
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

django.setup()

from tqdm import tqdm
from sefaria.model import VersionSet, Ref, TextChunk, library, LinkSet
from sefaria.system.exceptions import InputError

# ---------- LangChain/OpenAI ----------
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain.globals import set_llm_cache
from langchain.cache import InMemoryCache, SQLiteCache

# =========================
# CONFIG
# =========================
DEBUG_MODE = False
GPU_BASE_URL = os.getenv("CITATION_GPU_URL", "http://localhost:5000")
GPU_TIMEOUT = 30
GPU_RETRIES = 2

MIN_LEFT_CONTEXT_WORDS = 1000
UNRESOLVED_JSONL_PATH = "unresolved_ibids.jsonl"
RESOLVED_JSONL_PATH   = "resolved_ibids.jsonl"


set_llm_cache(SQLiteCache(database_path=".langchain_cache.sqlite"))

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")  # swap to gpt-4.1 / gpt-4o if you prefer

random.seed(613)

# =========================
# DATA STRUCTS
# =========================
@dataclass
class CitationSpan:
    start: int
    end: int
    text: str
    cid: str  # "r1", "r2", ...


@dataclass
class UnresolvedIbidRecord:
    segment_ref: str
    lang: str
    ibid_surface: str
    ibid_start_in_segment: int
    context_seed_ref: str
    context_first_ref: str
    context_text_len: int
    context_words_before_ibid: int
    linker_found: bool
    linker_debug: Optional[Dict[str, Any]] = None


@dataclass
class ResolvedIbidRecord:
    segment_ref: str
    lang: str
    ibid_surface: str
    ibid_start_in_segment: int
    context_seed_ref: str
    context_first_ref: str
    context_text_len: int
    context_words_before_ibid: int
    linker_found: bool
    resolved_ref: Optional[str] = None
    linker_debug: Optional[Dict[str, Any]] = None


# =========================
# SAMPLER (mirrors Prodigy traversal)
# =========================
class _SegmentCollector:
    """
    Collector compatible with Version.walk_thru_contents action signature.
    Handles both (text, tref, heTref, version, ...) and other variants by unpacking args defensively.
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
        text = None
        tref = None
        if len(args) >= 2 and isinstance(args[0], str) and isinstance(args[1], str):
            text = args[0]
            tref = args[1]
        else:
            for a in args:
                if text is None and isinstance(a, str) and a:
                    text = a
            for a in args:
                if isinstance(a, str):
                    try:
                        _ = Ref(a)
                        tref = a
                        break
                    except Exception:
                        continue
        if not (text and tref):
            return None
        try:
            ref = Ref(tref)
            return ref, text
        except Exception:
            return None

    def action(self, *args, **kwargs):
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
                pass
        self._candidates.append((ref, len(text)))

    @property
    def candidates(self) -> List[Ref]:
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
    assert lang in {"en", "he"}, f"lang must be 'en' or 'he', got: {lang}"
    r = rng or random
    versions = VersionSet({"language": lang}).array()
    bracket_suffix = re.compile(r"\[[a-zA-Z]+]$")

    collector = _SegmentCollector(
        prev_tagged_refs=prev_tagged_refs,
        with_links=with_links,
        max_chars=max_chars,
    )
    if DEBUG_MODE and lang == "en":
        # versions = VersionSet({"language": lang, "title": {"$in": ["Abraham Cohen Footnotes to the English Translation of Masechet Berakhot"]}}).array()
        versions = VersionSet({
            "language": "en",
            "title": {"$in": [
                # "English Explanation of Mishnah Keritot",
                # "English Explanation of Mishnah Kelim",
                # "English Explanation of Mishnah Parah",
                # "English Explanation of Mishnah Nazir",
                # "English Explanation of Mishnah Sotah",
                # "English Explanation of Mishnah Niddah",
                # "English Explanation of Mishnah Oholot",
                # "English Explanation of Mishnah Negaim",
                # "English Explanation of Mishnah Zavim",
                # "English Explanation of Mishnah Tevul Yom",
                # "English Explanation of Mishnah Yadayim",
                # "English Explanation of Mishnah Uktzin"
                "Ramban on Genesis","Ramban on Exodus", "Ramban on Leviticus", "Ramban on Numbers", "Ramban on Deuteronomy"
            ]}
        }).array()

    if DEBUG_MODE and lang == "he":
        versions = VersionSet({
            "language": "he",
            # "title": {"$regex": "Kovetz Al Yad HaChazakah", "$options": "i"},
            "title": {"$regex": "Mishnah Berurah", "$options": "i"}
        }).array()


    for version in tqdm(versions, desc=f"Walk versions ({lang})"):
        if bracket_suffix.search(getattr(version, "versionTitle", "") or ""):
            continue
        try:
            version.walk_thru_contents(collector.action)
        except InputError:
            continue
        except Exception:
            continue

    candidates = collector.candidates
    if not candidates:
        return []
    k = min(sample_size, len(candidates))
    if k == len(candidates):
        r.shuffle(candidates)
        return candidates
    return r.sample(candidates, k)


# =========================
# GPU SERVER CLIENT (COMPLIANT)
# =========================
def _post_json(url: str, payload: dict, timeout=GPU_TIMEOUT, retries=GPU_RETRIES):
    last = None
    for attempt in range(1, retries + 1):
        try:
            r = requests.post(url, json=payload, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last = e
            time.sleep(0.3 * attempt)
    raise RuntimeError(f"GPU server error after {retries} retries: {last}")


def gpu_detect_citations_single(text: str, lang: str) -> List[Dict[str, Any]]:
    """
    POST /recognize-entities?with_span_text=1
    Body: {"lang": "he"|"en", "text": "..."}
    Returns: [{"start": int, "end": int, "text": str|None}, ...]  (filtered to citations only)
    """
    if not text or not text.strip():
        return []
    url = f"{GPU_BASE_URL}/recognize-entities?with_span_text=1"
    data = _post_json(url, {"lang": lang, "text": text})
    ents = (data.get("entities") or [])
    out: List[Dict[str, Any]] = []
    for e in ents:
        # Accept either "type":"citation" or label variants
        if e.get("type") != "citation" and e.get("label") not in ("Citation", "מקור"):
            continue
        s = e.get("range")[0]
        t = e.get("range")[-1]
        if (not isinstance(s, int)) or (not isinstance(t, int)):
            span = e.get("span") or {}
            s, t = span.get("start"), span.get("end")
        if isinstance(s, int) and isinstance(t, int) and s < t:
            out.append({"start": s, "end": t, "text": e.get("span_text") or e.get("text")})
    return out


# =========================
# TAGGING + LLM (LangChain + OpenAI)
# =========================
def _merge_overlaps_keep_longer(spans: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    if not spans:
        return []
    spans = sorted(spans, key=lambda x: (x[0], x[1]))
    out: List[Tuple[int, int]] = []
    for s, e in spans:
        if not out:
            out.append((s, e))
            continue
        ps, pe = out[-1]
        if s <= pe:
            if (e - s) > (pe - ps):
                out[-1] = (s, e)
        else:
            out.append((s, e))
    return out


def annotate_with_ref_tags(text: str, spans: List[Tuple[int, int]]) -> Tuple[str, List[CitationSpan]]:
    spans = [(max(0, s), min(len(text), e)) for s, e in spans if s < e]
    spans = _merge_overlaps_keep_longer(spans)

    pieces: List[str] = []
    annotated: List[CitationSpan] = []

    last = 0
    for i, (s, e) in enumerate(sorted(spans, key=lambda x: x[0])):
        cid = f"r{i+1}"
        pieces.append(text[last:s])
        frag = text[s:e]
        pieces.append(f'<ref id="{cid}">')
        pieces.append(frag)
        pieces.append("</ref>")
        annotated.append(CitationSpan(start=s, end=e, text=frag, cid=cid))
        last = e
    pieces.append(text[last:])
    return "".join(pieces), annotated

def linker_detect_citations_single(text: str, lang: str) -> List[Dict[str, Any]]:
    """
    Uses Sefaria's linker to find citation spans inside `text`.
    Returns: [{"start": int, "end": int, "text": str}, ...]
    """
    if not text or not text.strip():
        return []

    linker = library.get_linker(lang)
    # Only ask for citations; ignore failures to keep it fast/noisy-free
    doc = linker.link(text, type_filter="citation", with_failures=True)

    spans: List[Tuple[int, int]] = []

    # Prefer character offsets from the linker (resolved + unresolved)
    refs = []
    for attr in ("resolved_refs", "unresolved_refs"):
        items = getattr(doc, attr, None)
        if isinstance(items, list):
            refs.extend(items)

    for r in refs:
        s = e = None
        try:
            # best source of truth: explicit char range
            s, e = r.raw_entity.span.range
        except Exception:
            # fallback: try surface text search
            surf = getattr(r.raw_entity, "span_text", None) or getattr(r.raw_entity, "text", None)
            if surf:
                s = text.find(surf)
                if s >= 0:
                    e = s + len(surf)

        if isinstance(s, int) and isinstance(e, int) and 0 <= s < e <= len(text):
            spans.append((s, e))

    # Merge overlaps (keep longer) to avoid nested/duplicate tags downstream
    spans = _merge_overlaps_keep_longer(spans)

    # Return with surface text for convenience
    out: List[Dict[str, Any]] = []
    for s, e in spans:
        out.append({"start": s, "end": e, "text": text[s:e]})
    return out



# ---- LLM client (lazy singleton) ----
__LLM_CLIENT = ChatOpenAI(model=OPENAI_MODEL, temperature=0)
__LLM_CLIENT = ChatAnthropic(model="claude-3-5-sonnet-latest", temperature=0)

def _get_llm():
    global __LLM_CLIENT
    if __LLM_CLIENT is None:
        __LLM_CLIENT = ChatOpenAI(model=OPENAI_MODEL, temperature=0)
    return __LLM_CLIENT


def llm_classify_ibids(annotated_segment_text: str, lang: str = "en") -> Set[str]:
    """
    Use ChatGPT via LangChain to decide which <ref id="rN">…</ref> tags are "ibid".
    Returns a set like {"r1","r3"}.
    """
    allowed_ids = set(re.findall(r'<ref id="([A-Za-z0-9]+)">', annotated_segment_text))
    if not allowed_ids:
        return set()

    system_msg = (
        "You are a rigorous citations expert. "
        "The user will provide a passage where citations are wrapped as <ref id=\"rN\">…</ref>. "

        "Definition of IBID: A citation is IBID if resolving it requires looking at the prior citation or the surrounding context, "
        "with indicators such as 'ibid', 'IBID', 'שם', 'שם שם', etc. "
        "IBID does not need to appear immediately after the prior citation. "

        "NOT IBID cases: "
        "- If the citation names a full, self-contained source (e.g., book + chapter/verse), it is NOT IBID. "
        "- If the citation refers to a book or source unlikely to appear in a classical Jewish text library, it is NOT IBID. "
        "- If the reference is actually an entity (person, place, or concept) rather than a bibliographic source, it is NOT IBID. "
        "This includes names like 'Moreh', 'Shechem', 'Torah', 'Midrash', 'Writings', etc., even if they repeat across multiple citations. "
        "Repeated place names or entities are NEVER IBID. "
        "- If the reference is actually a segment number or ordinal marker (e.g., '(טו) מצה שלישית …'), it is NOT IBID. "

        "Examples (NOT IBID): "
        "- 'Has not Rabbi Akiva your student brought a text from the Torah according to which it is unclean…' "
        "→ NOT IBID (too general, not a specific reference). "
        "- '…as it says, \"You shall not bring the hire of a harlot or the price of a dog…\" (Deuteronomy 23:19)' "
        "→ NOT IBID (specific, self-contained citation). "
        "- 'When Israel crossed the Jordan… near the terebinths of Moreh… (Deuteronomy 11:30)' "
        "→ NOT IBID (the citation Deut. 11:30 is complete and can be understood without prior context, even though 'Moreh' is repeated). "
        "- 'Rashi on Genesis 1:1' "
        "→ NOT IBID (explicit commentary citation that stands on its own, no context required). "
        "- 'The remaining four mishnayoth all contain midrashim… the bet midrash… the midrash which began yesterday’s mishnah' "
        "→ NOT IBID (the word 'midrash/midrashim' refers to a genre or institution, not a specific citation). "
        "- 'ובפי\"ז מהל׳ מאכלות אסורות הל׳ כ' "
        "→ NOT IBID (full, self-contained halakhic reference with book name). "
        "- '(טו) מצה שלישית – כדי לקיים מצוה בשלשתן' "
        "→ NOT IBID (the number is a segment marker, not a citation). if the segment starts with a marker, it is NOT IBID. "

        "Examples (IBID): "
        "- Hebrew 'שם' ('ibid') after a Genesis reference → IBID (ambiguous, needs prior context). "
        "- English 'Ibid' after Exodus 1:7 → IBID (ambiguous, could mean Exodus 1:12 or Exodus 12). "
        "- Hebrew 'ב' (verse 2) after Genesis 1 → IBID (ambiguous, could be Genesis 1:2 or Genesis 2). "
        "- Multiple chapter/verse markers like 'ב' and 'ז' with prior refs Genesis 1:3 and Exodus 1:3 → IBID (ambiguous across contexts). "
        "- 'Bereshit … שם' after prior refs → IBID (points back to Genesis context). "
        "- Multiple 'שם' in sequence like 'שם', 'שם', 'ב' → IBID (chain of ibids). "
        "- A bare chapter reference like 'Chapter 4' after Genesis 1 → IBID (needs context to resolve). "
        "- Page or folio references like 'דף כ' (Folio 20) after Berakhot/Shabbat → IBID (depends on prior tractate context). "
        "- Tosafot, Rashi, Ramban, Arukh HaShulchan with 'שם' → IBID (explicit ibid usage in commentaries). "
        "- A prefixed phrase like 'שבפרק ד' (in Chapter 4) after Genesis 1 → IBID (needs context). "
        "- 'Verses 40–45' after Deuteronomy 14 → IBID (continuation from context). "
        "- Numeric shorthand like 'יג א - ב' after Deuteronomy 1:20 → IBID (depends on context). "
        "- 'Berakhot, folio 2' after Rashi on Berakhot 3a → IBID (context not needed when explicit match exists). "
        "- 'Ramban, chapter 16, verse 4' after Exodus 16:32 → IBID (commentary ibid). "
        "- 'בפכ\"ד הל׳ י\"א ובפי\"ז' "
        "→ IBID (shorthand halakhic references that require context to resolve). "
        "- 'Job' when prior ref was Job 1:1 → IBID (context narrows to Job). "

        "Your task: Return STRICT JSON with a single key 'ibid_ids'. "
        "Its value must be a list of citation ids (e.g., ['r1','r3']) that are IBID. "
        "Do not include explanations, markdown, or extra keys. Return JSON only."
    )

    user_msg = f"Language: {lang}\n\nTEXT:\n---\n{annotated_segment_text}\n---\n\nReturn JSON only: {{\"ibid_ids\": [\"r1\",\"r3\"]}}"

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_msg),
        ("user", "{user_text}")
    ])
    chain = prompt | _get_llm()

    last_err = None
    for attempt in range(3):
        try:
            resp = chain.invoke({"user_text": user_msg})
            raw = resp.content if hasattr(resp, "content") else str(resp)

            raw = raw.strip()
            if raw.startswith("```"):
                raw = re.sub(r"^```[a-zA-Z]*\\s*", "", raw)
                raw = re.sub(r"\\s*```\\s*$", "", raw)

            data = json.loads(raw)
            ibids = data.get("ibid_ids", [])
            if not isinstance(ibids, list):
                return set()

            out = {str(x).strip() for x in ibids if isinstance(x, (str, int))}
            out = {x for x in out if x in allowed_ids}
            return out
        except Exception as e:
            last_err = e
            time.sleep(0.3 * (attempt + 1))

    # On failure, be conservative: no ibids
    return set()


# =========================
# CONTEXT BUILDER
# =========================
def _word_count(s: str) -> int:
    return len((s or "").split())


def _safe_textchunk(ref: Ref, lang: str) -> str:
    try:
        return TextChunk(ref, lang).as_string() or ""
    except Exception:
        return ""


def build_left_context(
    ref: Ref, lang: str, ibid_start_in_segment: int, min_left_words: int = MIN_LEFT_CONTEXT_WORDS
) -> Tuple[str, str, int, int]:
    """
    Returns:
      context_text,
      first_context_ref_str,
      new_ibid_start (offset into context_text),
      words_before_ibid
    """
    seg_text = _safe_textchunk(ref, lang)
    left_part = seg_text[:max(0, ibid_start_in_segment)]
    words_before = _word_count(left_part)

    context_text = seg_text
    added_prefix_len = 0
    first_ref = ref
    cur = ref

    while words_before < min_left_words:
        try:
            prev_r = cur.prev_segment_ref()
        except Exception:
            prev_r = None
        if not prev_r:
            break
        prev_text = _safe_textchunk(prev_r, lang)
        if prev_text:
            context_text = prev_text + "\n" + context_text
            added_prefix_len += len(prev_text) + 1
            words_before += _word_count(prev_text)
            first_ref = prev_r
        cur = prev_r if prev_r else cur

    new_ibid_start = ibid_start_in_segment + added_prefix_len
    return context_text, str(first_ref), new_ibid_start, words_before


# =========================
# LINKER RESOLUTION CHECK
# =========================
def linker_resolves_span(
    context_text: str, lang: str, target_start: int, target_end: int, book_context_ref: Optional[str] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Returns (resolved?, debug_info) where debug_info includes minimal JSONable details:
      {
        "resolved_count": int,
        "matched_by": "raw_entity.span.range" | "surface" | None,
        "hit_item": {"ref": "...", "start": int, "end": int} | None
      }
    """
    linker = library.get_linker(lang)
    doc = linker.link(context_text, type_filter="citation", with_failures=False, book_context_ref=book_context_ref)
    dbg: Dict[str, Any] = {"resolved_count": None, "matched_by": None, "hit_item": None}

    resolved = getattr(doc, "resolved_refs", None)
    if not isinstance(resolved, list):
        return False, dbg

    dbg["resolved_count"] = len(resolved)

    # Primary: char-bounds via raw_entity.span.range
    for r in resolved:
        try:
            s, e = r.raw_entity.span.range  # offsets from the raw entity
        except Exception:
            continue
        if (max(s, target_start) < min(e, target_end)) or abs(s - target_start) <= 4 or abs(e - target_end) <= 4:
            hit = {"ref": str(getattr(r, "ref", "")), "start": int(s), "end": int(e)}
            dbg["matched_by"] = "raw_entity.span.range"
            dbg["hit_item"] = hit
            return True, dbg

    # Fallback: surface match
    surface = context_text[target_start:target_end].strip()
    if surface:
        for r in resolved:
            try:
                s, e = r.raw_entity.span.range
                if context_text[s:e].strip() == surface:
                    hit = {"ref": str(getattr(r, "ref", "")), "start": int(s), "end": int(e)}
                    dbg["matched_by"] = "surface"
                    dbg["hit_item"] = hit
                    return True, dbg
            except Exception:
                continue

    return False, dbg


# =========================
# PIPELINE
# =========================
def find_ibids_and_save(
    lang: str,
    *,
    target_unresolved_count: int = 50,
    sample_pool: int = 5000,
    max_segment_chars: Optional[int] = 4000,
    unresolved_jsonl: str = UNRESOLVED_JSONL_PATH,
    resolved_jsonl: str = RESOLVED_JSONL_PATH,
) -> Tuple[List[UnresolvedIbidRecord], List[ResolvedIbidRecord]]:
    """
    - Samples `sample_pool` segments.
    - Detects citations (GPU).
    - Tags + asks LLM for ibids.
    - For each ibid, builds left-context, runs linker.
    - Saves BOTH unresolved and resolved ibids to JSONL.
    - Stops when it has collected `target_unresolved_count` unresolved items
      (but keeps writing resolved ones it sees along the way).
    """
    pool = sample_segment_refs(lang=lang, sample_size=sample_pool, max_chars=max_segment_chars)
    random.shuffle(pool)

    unresolved: List[UnresolvedIbidRecord] = []
    resolved: List[ResolvedIbidRecord] = []

    ufh = open(unresolved_jsonl, "a", encoding="utf-8")
    rfh = open(resolved_jsonl, "a", encoding="utf-8")

    try:
        for seg_ref in tqdm(pool, desc=f"Scanning {lang} segments"):
            seg_text = _safe_textchunk(seg_ref, lang)
            if not seg_text:
                continue

            # GPU detect (compliant)
            # raw_cits = gpu_detect_citations_single(seg_text, lang=lang)
            raw_cits = linker_detect_citations_single(seg_text, lang=lang)
            spans: List[Tuple[int, int]] = []
            for c in raw_cits:
                s, e = c.get("start"), c.get("end")
                if isinstance(s, int) and isinstance(e, int) and 0 <= s < e <= len(seg_text):
                    spans.append((s, e))
            if not spans:
                continue

            annotated, ann_spans = annotate_with_ref_tags(seg_text, spans)
            ibid_ids = llm_classify_ibids(annotated, lang=lang)
            if not ibid_ids:
                continue

            for cs in ann_spans:
                if cs.cid not in ibid_ids:
                    continue

                context_text, first_ctx_ref, new_start, words_before = build_left_context(
                    seg_ref, lang, cs.start, min_left_words=MIN_LEFT_CONTEXT_WORDS
                )
                new_end = new_start + (cs.end - cs.start)

                ok, debug = linker_resolves_span(context_text, lang, new_start, new_end)

                if ok:
                    resolved_ref = None
                    if debug.get("hit_item") and isinstance(debug["hit_item"], dict):
                        resolved_ref = debug["hit_item"].get("ref")
                    rec = ResolvedIbidRecord(
                        segment_ref=str(seg_ref),
                        lang=lang,
                        ibid_surface=cs.text,
                        ibid_start_in_segment=cs.start,
                        context_seed_ref=str(seg_ref),
                        context_first_ref=first_ctx_ref,
                        context_text_len=len(context_text),
                        context_words_before_ibid=words_before,
                        linker_found=True,
                        resolved_ref=resolved_ref,
                        linker_debug=debug,
                    )
                    resolved.append(rec)
                    rfh.write(json.dumps(rec.__dict__, ensure_ascii=False) + "\n")
                    rfh.flush()
                else:
                    rec = UnresolvedIbidRecord(
                        segment_ref=str(seg_ref),
                        lang=lang,
                        ibid_surface=cs.text,
                        ibid_start_in_segment=cs.start,
                        context_seed_ref=str(seg_ref),
                        context_first_ref=first_ctx_ref,
                        context_text_len=len(context_text),
                        context_words_before_ibid=words_before,
                        linker_found=False,
                        linker_debug=debug,
                    )
                    unresolved.append(rec)
                    ufh.write(json.dumps(rec.__dict__, ensure_ascii=False) + "\n")
                    ufh.flush()

                    if len(unresolved) >= target_unresolved_count:
                        return unresolved, resolved
    finally:
        ufh.close()
        rfh.close()

    return unresolved, resolved


# =========================
# CONVENIENCE WRAPPERS (optional quick tests)
# =========================
def sample_english_cited_refs(n: int = 5, *, pool_size: int = 5000, max_chars: Optional[int] = 4000) -> List[str]:
    linker_en = library.get_linker("en")
    pool = sample_segment_refs(lang="en", sample_size=pool_size, max_chars=max_chars)
    random.shuffle(pool)
    hits: List[str] = []
    for ref in pool:
        try:
            txt = TextChunk(ref, "en").as_string()
        except Exception:
            txt = ""
        if not txt:
            continue
        doc = linker_en.link(txt, type_filter="citation", with_failures=False)
        if getattr(doc, "resolved_refs", []):
            hits.append(str(ref))
            if len(hits) >= n:
                break
    return hits


def sample_hebrew_cited_refs(n: int = 5, *, pool_size: int = 5000, max_chars: Optional[int] = 4000) -> List[str]:
    linker_he = library.get_linker("he")
    pool = sample_segment_refs(lang="he", sample_size=pool_size, max_chars=max_chars)
    random.shuffle(pool)
    hits: List[str] = []
    for ref in pool:
        try:
            txt = TextChunk(ref, "he").as_string()
        except Exception:
            txt = ""
        if not txt:
            continue
        doc = linker_he.link(txt, type_filter="citation", with_failures=False)
        if getattr(doc, "resolved_refs", []):
            hits.append(str(ref))
            if len(hits) >= n:
                break
    return hits
import csv

def find_ibids_and_save_csv(
    lang: str,
    *,
    target_unresolved_count: int = 50,
    sample_pool: int = 5000,
    max_segment_chars: Optional[int] = 4000,
    out_csv: str = "ibids_results.csv",
) -> None:
    """
    - Samples `sample_pool` segments.
    - Detects citations (GPU).
    - Tags + asks LLM for ibids.
    - For each ibid, builds left-context, runs linker.
    - Saves ALL ibids (resolved + unresolved) to a single CSV file.
    - Stops once it has collected at least `target_unresolved_count` unresolved.
    """

    pool = sample_segment_refs(lang=lang, sample_size=sample_pool, max_chars=max_segment_chars)
    random.shuffle(pool)

    # open CSV writer
    fieldnames = [
        "segment_ref", "lang", "segment_text",
        "ibid_start_in_segment", "ibid_end_in_segment",
        "ibid_start_in_context", "ibid_end_in_context",
        "citation_spans", "citation_texts",
        "ibid_surface", "context_text", "context_first_ref",
        "linker_found", "resolved_ref", "linker_debug"
    ]
    with open(out_csv, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()

        unresolved_count = 0

        for seg_ref in tqdm(pool, desc=f"Scanning {lang} segments"):
            seg_text = _safe_textchunk(seg_ref, lang)
            if not seg_text:
                continue

            # GPU detect
            # raw_cits = gpu_detect_citations_single(seg_text, lang=lang)
            raw_cits = linker_detect_citations_single(seg_text, lang=lang)
            spans: List[Tuple[int, int]] = []
            texts: List[str] = []
            for c in raw_cits:
                s, e = c.get("start"), c.get("end")
                if isinstance(s, int) and isinstance(e, int) and 0 <= s < e <= len(seg_text):
                    spans.append((s, e))
                    texts.append(c.get("text") or seg_text[s:e])
            if not spans:
                continue

            annotated, ann_spans = annotate_with_ref_tags(seg_text, spans)
            ibid_ids = llm_classify_ibids(annotated, lang=lang)
            if not ibid_ids:
                continue

            for cs in ann_spans:
                if cs.cid not in ibid_ids:
                    continue

                context_text, first_ctx_ref, new_start, words_before = build_left_context(
                    seg_ref, lang, cs.start, min_left_words=MIN_LEFT_CONTEXT_WORDS
                )
                new_end = new_start + (cs.end - cs.start)

                ok, debug = linker_resolves_span(context_text, lang, new_start, new_end, book_context_ref=seg_ref)
                resolved_ref = None
                if ok and debug.get("hit_item"):
                    resolved_ref = debug["hit_item"].get("ref")

                writer.writerow({
                    "segment_ref": str(seg_ref),
                    "lang": lang,
                    "segment_text": seg_text,
                    "citation_spans": json.dumps(spans, ensure_ascii=False),
                    "citation_texts": json.dumps(texts, ensure_ascii=False),
                    "ibid_surface": cs.text,
                    "ibid_start_in_segment": cs.start,
                    "ibid_end_in_segment": cs.end,
                    "ibid_start_in_context": new_start,
                    "ibid_end_in_context": new_end,
                    "context_text": context_text,
                    "context_first_ref": first_ctx_ref,
                    "linker_found": ok,
                    "resolved_ref": resolved_ref,
                    "linker_debug": json.dumps(debug, ensure_ascii=False),
                })

                if not ok:
                    unresolved_count += 1
                    if unresolved_count >= target_unresolved_count:
                        return


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    # # Example: gather EN + HE unresolved ibids (and log ALL resolved too)
    # print("Starting EN pass...")
    # unen, ren = find_ibids_and_save(
    #     "en",
    #     target_unresolved_count=20,
    #     sample_pool=10_000,
    #     max_segment_chars=1000000,
    #     unresolved_jsonl=UNRESOLVED_JSONL_PATH,
    #     resolved_jsonl=RESOLVED_JSONL_PATH,
    # )
    # print(f"EN -> unresolved: {len(unen)}, resolved (logged): {len(ren)}")
    #
    # print("Starting HE pass...")
    # unhe, rhe = find_ibids_and_save(
    #     "he",
    #     target_unresolved_count=20,
    #     sample_pool=2000,
    #     max_segment_chars=4000,
    #     unresolved_jsonl=UNRESOLVED_JSONL_PATH,
    #     resolved_jsonl=RESOLVED_JSONL_PATH,
    # )
    # print(f"HE -> unresolved: {len(unhe)}, resolved (logged): {len(rhe)}")
    #
    # print(f"Saved unresolved to {UNRESOLVED_JSONL_PATH} and resolved to {RESOLVED_JSONL_PATH}")
    find_ibids_and_save_csv("en", target_unresolved_count=1_000, sample_pool=1_000*100, out_csv="ibids_en.csv")
    # find_ibids_and_save_csv("he", target_unresolved_count=1_000, sample_pool=1_000*100, out_csv="ibids_he.csv")
    print("Done! Saved CSVs.")

