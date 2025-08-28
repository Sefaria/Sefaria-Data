# ibid_llm_marker_only.py
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Iterable

import django
django.setup()

from sefaria.model import Ref, TextChunk, library
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
# --- LangChain cache (SQLite on disk) ---
from langchain.globals import set_llm_cache
from langchain.cache import SQLiteCache

# Creates / reuses a local SQLite file; safe to commit to .gitignore
set_llm_cache(SQLiteCache(database_path="llm_cache.sqlite"))

# ------------ Linker → simple citation rows (current citation only) ------------

@dataclass
class CitationRow:
    idx: int
    start: int
    end: int
    surface: str
    resolved_ref: Optional[str]  # may be None
    raw_entity: Any               # kept for debugging


def _segment_text(ref: Ref, lang: str, max_chars: Optional[int] = None) -> str:
    tc = TextChunk(ref, lang)
    txt = tc.as_string() or ""
    if max_chars and len(txt) > max_chars:
        txt = txt[:max_chars]
    return txt


def _collect_rows_from_doc(doc: Any, passage: str) -> List[CitationRow]:
    rows: List[CitationRow] = []

    def add_from(bucket):
        for h in bucket:
            raw = getattr(h, "raw_entity", None) or getattr(h, "raw_ref", None)
            if not raw:
                continue
            rng = getattr(raw, "char_indices", None)
            if not rng and getattr(raw, "span", None) is not None:
                rng = getattr(raw.span, "range", None)
            if not rng or len(rng) < 2:
                continue
            s, e = int(rng[0]), int(rng[1])

            surf = getattr(raw, "text", None) or getattr(raw, "pretty_text", None)
            if not surf and 0 <= s < e <= len(passage):
                surf = passage[s:e]
            if not surf:
                continue

            resolved = None
            for k in ("ref", "ref_str", "resolved_ref"):
                v = getattr(h, k, None)
                if v:
                    resolved = str(v)
                    break

            rows.append(CitationRow(-1, s, e, surf, resolved, raw))

    add_from(getattr(doc, "all_resolved", []) or [])
    add_from(getattr(doc, "all_unresolved", []) or [])

    rows.sort(key=lambda r: r.start)
    for i, r in enumerate(rows):
        r.idx = i
    return rows


def get_citations_for_segment(ref: Ref or str, *, lang: str) -> Tuple[str, List[CitationRow]]:
    r = ref if isinstance(ref, Ref) else Ref(ref)
    text = _segment_text(r, lang)
    if not text.strip():
        return "", []
    doc = library.get_linker(lang).link(text, type_filter="citation", with_failures=True)
    return text, _collect_rows_from_doc(doc, text)


# ---------------------- LLM: ibid marker classification ----------------------

IBID_SYSTEM = """\
Classify whether the CURRENT citation text is an 'ibid'-style reference: a marker that means
'the same source as previously cited'. Make the decision using ONLY the fields you are given.

Count as ibid if the CURRENT citation itself uses an ibid-style expression.
Common forms:
- English: "ibid", "ibid.", "ib.", "id." (legal), "same source", "same place"
- Hebrew: "שם", "כמבואר שם", "כמ\"ש שם", "כנ\"ל"

Be conservative: if it's ambiguous or a normal explicit citation (like 'Genesis 1:1'), return false.

Return ONLY JSON with keys:
  has_ibid: boolean
  variant: short marker string used ("" if none)
  evidence: short phrase from CURRENT fields that justifies your decision
  confidence: integer 0–100
"""

# Only CURRENT citation info is passed — no previous fields.
IBID_USER_TMPL = """\
LANG: {lang}

CURRENT CITATION:
  index: {idx}
  surface: {surface}
  resolved_ref: {resolved}

Return ONLY JSON.
"""


def make_llm(model: str = "gpt-4o-mini") -> ChatOpenAI:
    return ChatOpenAI(model=model, temperature=0)


def llm_decide_ibid_marker_only(
    *,
    lang: str,
    idx: int,
    surface: str,
    resolved: Optional[str],
    llm: ChatOpenAI,
) -> Dict[str, Any]:
    prompt = ChatPromptTemplate.from_messages([("system", IBID_SYSTEM), ("user", IBID_USER_TMPL)])
    msgs = prompt.format_messages(
        lang=lang,
        idx=idx,
        surface=json.dumps(surface, ensure_ascii=False),
        resolved=json.dumps(resolved or "", ensure_ascii=False),
    )
    raw = llm.invoke(msgs).content
    try:
        out = json.loads(raw)
    except Exception:
        s, e = raw.find("{"), raw.rfind("}")
        out = json.loads(raw[s:e+1]) if (s != -1 and e != -1 and e > s) else {
            "has_ibid": False, "variant": "", "evidence": "", "confidence": 0, "raw": raw
        }
    out.setdefault("has_ibid", False)
    out.setdefault("variant", "")
    out.setdefault("evidence", "")
    out.setdefault("confidence", 0)
    return out


# ---------------- Segment-level orchestration & batching ----------------

def analyze_segment_llm_marker_only(ref: Ref or str, *, lang: str, llm_model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """
    For one segment:
      - run linker once to get ordered citations
      - for each citation, ask LLM (based only on CURRENT citation fields) if it's 'ibid'
      - return two buckets (ibid vs non-ibid) and a flag if any ibid was found
    """
    r = ref if isinstance(ref, Ref) else Ref(ref)
    text, rows = get_citations_for_segment(r, lang=lang)
    if not text or not rows:
        return {"ref": str(r), "lang": lang, "ibid_citations": [], "non_ibid_citations": [], "has_any_ibid": False}

    llm = make_llm(llm_model)
    ibid_hits: List[Dict[str, Any]] = []
    non_ibid: List[Dict[str, Any]] = []

    for row in rows:
        verdict = llm_decide_ibid_marker_only(
            lang=lang,
            idx=row.idx,
            surface=row.surface,
            resolved=row.resolved_ref,
            llm=llm,
        )
        rec = {
            "index": row.idx,
            "surface": row.surface,
            "resolved_ref": row.resolved_ref,
            "llm_has_ibid": bool(verdict.get("has_ibid")),
            "llm_variant": verdict.get("variant", ""),
            "llm_evidence": verdict.get("evidence", ""),
            "llm_confidence": int(verdict.get("confidence", 0)),
        }
        (ibid_hits if rec["llm_has_ibid"] else non_ibid).append(rec)

    return {
        "ref": str(r),
        "lang": lang,
        "ibid_citations": ibid_hits,
        "non_ibid_citations": non_ibid,
        "has_any_ibid": bool(ibid_hits),
    }


def batch_refs_llm_marker_only(refs: Iterable[str or Ref], *, lang: str, llm_model: str = "gpt-4o-mini"):
    """
    Process many refs and return:
      - refs_with_ibid: list of dicts (one per ref) that contain ≥1 LLM-approved ibid
      - refs_without_ibid: list of dicts (one per ref) with none
    """
    refs_with_ibid: List[Dict[str, Any]] = []
    refs_without_ibid: List[Dict[str, Any]] = []

    for r in refs:
        res = analyze_segment_llm_marker_only(r, lang=lang, llm_model=llm_model)
        (refs_with_ibid if res["has_any_ibid"] else refs_without_ibid).append(res)

    return refs_with_ibid, refs_without_ibid
