#!/usr/bin/env python3
"""
Bayesian Pairwise Ranking of CSV rows by ibid-urgency using Claude (Anthropic).

What it does
------------
1) Loads rows from a CSV (expects columns at least: segment_ref, segment_text, ibid_surface, citation_texts).
2) For any pair (A,B), asks Claude: "Which is more urgent to fix (missed ibid)?"
   - Shows only short text: segment_text with <IBID>...</IBID> wrapped around the ibid_surface.
   - Also shows a short "priority guidance" text, plus 2 few-shot examples of missed ibids.
3) Interprets Claude's choice as a Bradley–Terry noisy comparison, and performs an online Laplace/Fisher update:
   - Maintain Gaussian belief over item scores: mean vector m and covariance Sigma.
   - Update per observation along x = e_a - e_b with weight w ≈ p(1-p).
4) Actively selects informative pairs using UV = p(1-p) × s^2 (batch approximation).
5) Outputs a ranking CSV sorted by posterior mean m_i; optional diagnostics files.

Setup
-----
pip install anthropic tqdm numpy

Env
---
export ANTHROPIC_API_KEY=your_key
"""

from __future__ import annotations

import os
import sys
import csv
import json
import math
import time
import random
from typing import Any, Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain.cache import SQLiteCache
from langchain.globals import set_llm_cache
import numpy as np
from tqdm.auto import tqdm

set_llm_cache(SQLiteCache(database_path=".langchain_cache.sqlite"))


# ==============================
# CONFIG — EDIT THESE VALUES
# ==============================
base_csv_file_name = "ibids_en"
CONFIG = {
    # IO
    "input_path": f"{base_csv_file_name}_filtered.csv",
    "output_ranked_path": f"{base_csv_file_name}_ranked_rows.csv",  # ranked by posterior mean m_i
    "save_comparisons_path": "pairwise_votes.jsonl",  # raw A vs B LLM decisions
    "save_posterior_path": "posterior.npz",  # m, Sigma saved as numpy compressed

    # Which columns to use (must exist)
    "col_segment_ref": "segment_ref",
    "col_segment_text": "segment_text",
    "col_ibid_surface": "ibid_surface",
    "col_citation_texts": "citation_texts",  # JSON list (optional; helps LLM)
    "col_linker_found": "linker_found",

    # Claude (Anthropic)
    "anthropic_model": "claude-3-5-sonnet-latest",
    "temperature": 0.0,
    "max_output_tokens": 200,
    "request_timeout": 60.0,
    "retries": 3,
    "backoff": 1.6,

    # Few-shot examples (2) of missed ibid (the linker couldn't resolve)
    # Keep these short; they prime the LLM to know what looks urgent.
    "priority_guidance": (
        "Urgency policy: prioritize rows where the ibid marker should be theoretically easy to resolve, "
        "such as when it clearly points to a nearby or explicit prior citation, especially in core works "
        "of the Jewish canon (Torah, Talmud, Midrash, major commentaries). Give higher priority to cases "
        "a typical reader on the site would reasonably expect to be resolved, since failure there impacts "
        "user experience. "
        "Deprioritize rows where the ibid reference is arcane, unlikely to correspond to texts in Sefaria’s "
        "library, or not truly an ibid citation at all. Short, unambiguous ibids (“ibid.”, “שם”, etc.) next "
        "to a citation are higher priority than vague or contextless repeats. Prefer segments where fixing "
        "one ibid also clarifies multiple nearby lines or prevents cascading ambiguity."
    ),
    "missed_ibid_examples": [
        # {
        #     "segment_text": "… as noted above in Mishnah Berakhot 2:1, <IBID>שם</IBID> continues …",
        #     "why_urgent": "Short, canonical ibid form immediately after an explicit source; linker missed it.",
        # },
        # {
        #     "segment_text": "Rashi cites Exodus 3:14; the next line starts with <IBID>ibid.</IBID> but didn’t resolve.",
        #     "why_urgent": "Direct ibid following a proper citation; likely trivial to link and high impact.",
        # },
    ],

    # Pairwise comparison budget & selection
    "seed": 1337,
    "max_items": 300,  # set 0 for all rows; otherwise cap to this many (helps cost control)
    "total_comparisons": 1500,  # total LLM pairwise matches to run
    "batch_pairs": 60,  # pairs per round (processed in parallel)
    "candidate_pool": 800,  # sample this many random pairs per round, score by UV, take top-k=batch_pairs
    "max_workers": 5,  # parallel Anthropic calls (respect rate limits!)

    # Gaussian prior (Section B)
    "lambda_ridge": 1.0,  # larger = stronger shrinkage
    "fix_first_to_zero": True  # identifiability: hold item 0 at theta=0 (removes one degree of freedom)
}

def _truthy(val: Optional[str]) -> bool:
    """Interpret CSV boolean-ish values."""
    if val is None:
        return False
    s = str(val).strip().lower()
    return s in {"1", "true", "t", "yes", "y"}
# ==============================
# Anthropic client
# ==============================
def get_anthropic_client():
    try:
        import anthropic
    except ImportError:
        print("ERROR: anthropic package not found. Install with: pip install anthropic", file=sys.stderr)
        sys.exit(1)
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)
    return anthropic.Anthropic(api_key=api_key)


# ==============================
# Text helpers
# ==============================
def wrap_ibid_in_segment(segment_text: str, start: int, end: int) -> str:
    """
    Wrap substring between start and end indices with <IBID> tags.
    Indices are assumed to be character offsets in segment_text.
    """
    if not segment_text or start is None or end is None:
        return segment_text or ""
    if start < 0 or end > len(segment_text) or start >= end:
        # invalid indices: leave as-is
        return segment_text
    return (
        segment_text[:start]
        + "<IBID>" + segment_text[start:end] + "</IBID>"
        + segment_text[end:]
    )


def safe_citation_list(citation_texts_field: str) -> List[str]:
    """citation_texts often stored as JSON array; fall back gracefully."""
    if not citation_texts_field:
        return []
    try:
        val = json.loads(citation_texts_field)
        if isinstance(val, list):
            return [str(x) for x in val]
        return [str(val)]
    except Exception:
        return []


# ==============================
# LLM prompt + call
# ==============================
SYSTEM_PROMPT = """\
You are an expert annotator working with rows of unresolved ibid citations
extracted from a large corpus of Jewish texts in the Sefaria library.
You are familiar with the Jewish textual canon (Torah, Talmud, Midrash,
major commentaries, halakhic works, etc.) and with how ibid markers
(“ibid.”, “שם”, etc.) function in citation chains. You understand which
references readers expect to be resolved on the Sefaria website and which
are less critical (arcane, obscure, or outside the library).

Your task: compare TWO rows and decide which is more urgent to fix.

Return STRICT JSON ONLY with this schema:
{"choice": "A" | "B", "reason": "<brief reason>"}
No other text. No additional keys.
"""


def build_pair_prompt(
        guidance: str,
        examples: Optional[List[Dict[str, str]]],
        a_text: str,
        a_citations: List[str],
        b_text: str,
        b_citations: List[str]
) -> str:
    """
    Compose user message:
    - Short priority guidance
    - Optionally, few-shot examples of missed ibid rows
    - Two candidates A and B (segment_text with <IBID>…</IBID>), plus short citations list
    """
    ex_lines = []
    if examples:  # only add if non-empty
        for i, ex in enumerate(examples[:2], start=1):
            ex_lines.append(
                f"Example {i} (missed ibid):\n"
                f"{ex.get('segment_text', '')}\n"
                f"Why urgent: {ex.get('why_urgent', '')}\n"
            )

    a_block = " | ".join(a_citations) if a_citations else "(no citations listed)"
    b_block = " | ".join(b_citations) if b_citations else "(no citations listed)"

    return (
        f"Priority guidance:\n{guidance}\n\n"
        + ("\n".join(ex_lines) + "\n" if ex_lines else "")
        + "Now decide which item is MORE URGENT to fix (A or B):\n\n"
        + f"A) {a_text}\nA citations: {a_block}\n\n"
        + f"B) {b_text}\nB citations: {b_block}\n\n"
        + "Respond STRICTLY with JSON: {\"choice\": \"A\"|\"B\", \"reason\": \"...\"}"
    )


def ask_claude_pairwise(client, model, temperature, max_tokens, timeout, retries, backoff, system_prompt, user_msg) -> \
Tuple[int, str]:
    """
    Returns (y, reason) where:
      y = 1 if A beats B
      y = 0 if B beats A
    """
    import anthropic
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            resp = client.messages.create(
                model=model,
                system=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": user_msg}],
                timeout=timeout,
            )
            parts = resp.content or []
            txt = "".join([p.text for p in parts if getattr(p, "type", None) == "text"]).strip()
            data = json.loads(txt)
            choice = str(data.get("choice", "")).strip().upper()
            reason = str(data.get("reason", "") or "")
            if choice not in ("A", "B"):
                raise ValueError(f"Bad JSON choice: {choice}")
            return (1 if choice == "A" else 0), reason
        except Exception as e:
            last_err = e
            time.sleep(backoff ** (attempt - 1))
    # On failure, default to a tie-break towards B (arbitrary but consistent)
    return 0, f"LLM error: {last_err}"


# ==============================
# Bayesian Pairwise Model (Sections B–D)
# ==============================
class BayesianRanker:
    """
    Maintain Gaussian belief over theta (scores).
    Online Laplace/Fisher update (Option D1).
    """

    def __init__(self, n: int, lambda_ridge: float = 1.0, fix_first_to_zero: bool = True):
        self.n = n
        self.fix_first = fix_first_to_zero
        # Prior: m=0, Sigma = (1/lambda)*I
        self.m = np.zeros(n)
        self.Sigma = (1.0 / lambda_ridge) * np.eye(n)

        if self.fix_first:
            self._pin_first()

    def _pin_first(self):
        # Make item 0 exactly zero and uncoupled (identifiability).
        self.m[0] = 0.0
        self.Sigma[0, :] = 0.0
        self.Sigma[:, 0] = 0.0
        self.Sigma[0, 0] = 1e-12  # tiny variance to keep numerics sane

    @staticmethod
    def _sigmoid(z: float) -> float:
        if z >= 0:
            ez = math.exp(-z)
            return 1.0 / (1.0 + ez)
        else:
            ez = math.exp(z)
            return ez / (1.0 + ez)

    def compare(self, a: int, b: int, y: int):
        """
        Observe outcome y in {0,1} for pair (a,b).
        Online Laplace/Fisher update:
          x = e_a - e_b
          mu = x^T m
          s2 = x^T Sigma x
          p = sigmoid(mu)
          w ~ p(1-p)
          m <- m + Sigma x * (y - p)
          Sigma <- Sigma - (Sigma x x^T Sigma) * (w / (1 + w s2))
        """
        if a == b:
            return

        x = np.zeros(self.n)
        x[a] = 1.0
        x[b] = -1.0

        mu = float(x @ self.m)
        s2 = float(x @ self.Sigma @ x)
        p = self._sigmoid(mu)
        w = p * (1.0 - p)  # Fisher info

        # Mean update
        gain = self.Sigma @ x
        self.m += gain * (y - p)

        # Covariance update (rank-1)
        denom = 1.0 + w * s2
        if denom <= 0:
            denom = 1e-9
        outer = np.outer(gain, gain)
        self.Sigma -= outer * (w / denom)

        if self.fix_first:
            self._pin_first()

    def margin_stats(self, a: int, b: int) -> Tuple[float, float, float]:
        """Return (mu, s2, p) for margin theta_a - theta_b."""
        x = np.zeros(self.n)
        x[a] = 1.0
        x[b] = -1.0
        mu = float(x @ self.m)
        s2 = float(x @ self.Sigma @ x)
        p = self._sigmoid(mu)
        return mu, s2, p


# ==============================
# Pair selection (Section E)
# ==============================
def sample_candidate_pairs(n: int, k: int, rng: random.Random) -> List[Tuple[int, int]]:
    pairs = set()
    while len(pairs) < k:
        a = rng.randrange(n)
        b = rng.randrange(n)
        if a != b:
            if a > b: a, b = b, a
            pairs.add((a, b))
    return list(pairs)


def pick_informative_pairs(
        ranker: BayesianRanker,
        candidates: List[Tuple[int, int]],
        top_k: int
) -> List[Tuple[int, int, float]]:
    """
    Score pairs by UV = p(1-p) * s^2 and return top_k with scores.
    """
    scored = []
    for (a, b) in candidates:
        _, s2, p = ranker.margin_stats(a, b)
        uv = p * (1.0 - p) * s2
        scored.append((a, b, uv))
    scored.sort(key=lambda t: t[2], reverse=True)
    return scored[:top_k]


# ==============================
# Parallel LLM calls
# ==============================
def run_parallel(items: List[Any], unit_func, max_workers: int, **tqdm_kwargs) -> List[Any]:
    results: List[Any] = []
    with tqdm(total=len(items), **tqdm_kwargs) as pbar:
        def _wrapped(item):
            out = unit_func(item)
            pbar.update(1)
            return out

        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = [ex.submit(_wrapped, it) for it in items]
            for f in as_completed(futures):
                try:
                    r = f.result()
                except Exception:
                    r = None
                if r is not None:
                    results.append(r)
    return results


# ==============================
# Main
# ==============================
def main():
    cfg = CONFIG
    rng = random.Random(cfg["seed"])
    client = get_anthropic_client()

    # Load rows
    with open(cfg["input_path"], "r", newline="", encoding="utf-8") as fin:
        reader = csv.DictReader(fin)
        header = reader.fieldnames or []
        must_have = [cfg["col_segment_ref"], cfg["col_segment_text"], cfg["col_ibid_surface"]]
        for col in must_have:
            if col not in header:
                print(f"ERROR: CSV missing required column: {col}", file=sys.stderr)
                sys.exit(1)
        rows = list(reader)
    # Keep ONLY rows where the linker did NOT find a resolution
    col_found = cfg.get("col_linker_found", "linker_found")
    if col_found in (reader.fieldnames or []):
        before = len(rows)
        rows = [r for r in rows if not _truthy(r.get(col_found))]
        print(f"Filtered by '{col_found}': kept {len(rows)}/{before} unresolved rows")
    else:
        print(f"WARNING: column '{col_found}' not found — no linker-based filtering applied.")

    # if cfg["max_items"] and len(rows) > cfg["max_items"]:
    #     rows = rows[:cfg["max_items"]]

    # Prepare short texts for LLM
    items = []
    for i, row in enumerate(rows):
        seg = row.get(cfg["col_segment_text"], "") or ""
        # ibid = row.get(cfg["col_ibid_surface"], "") or ""
        start = int(row.get("ibid_start_in_segment", -1))
        end = int(row.get("ibid_end_in_segment", -1))
        tagged = wrap_ibid_in_segment(seg, start, end)
        ctexts = safe_citation_list(row.get(cfg["col_citation_texts"], ""))
        items.append({
            "idx": i,
            "segment_ref": row.get(cfg["col_segment_ref"], ""),
            "tagged_segment": tagged,
            "citation_texts": ctexts,
            "row": row
        })

    n = len(items)
    ranker = BayesianRanker(n, lambda_ridge=cfg["lambda_ridge"], fix_first_to_zero=cfg["fix_first_to_zero"])

    total_done = 0
    all_votes: List[Dict[str, Any]] = []

    # Active rounds until budget exhausted
    pbar_outer = tqdm(total=cfg["total_comparisons"], desc="Pairwise comparisons (total)")
    while total_done < cfg["total_comparisons"]:
        batch_remaining = min(cfg["batch_pairs"], cfg["total_comparisons"] - total_done)

        # Candidate pairs
        candidates = sample_candidate_pairs(n, cfg["candidate_pool"], rng)
        top_pairs = pick_informative_pairs(ranker, candidates, batch_remaining)

        # Build prompts for the batch
        batch_payloads = []
        for (a, b, uv) in top_pairs:
            A = items[a]
            B = items[b]
            user_msg = build_pair_prompt(
                guidance=cfg["priority_guidance"],
                examples=cfg["missed_ibid_examples"],
                a_text=A["tagged_segment"],
                a_citations=A["citation_texts"],
                b_text=B["tagged_segment"],
                b_citations=B["citation_texts"]
            )
            batch_payloads.append((a, b, user_msg))

        # Parallel ask Claude
        def unit_func(payload):
            a, b, user_msg = payload
            y, reason = ask_claude_pairwise(
                client=client,
                model=cfg["anthropic_model"],
                temperature=cfg["temperature"],
                max_tokens=cfg["max_output_tokens"],
                timeout=cfg["request_timeout"],
                retries=cfg["retries"],
                backoff=cfg["backoff"],
                system_prompt=SYSTEM_PROMPT,
                user_msg=user_msg,
            )
            return (a, b, y, reason)

        results = run_parallel(
            batch_payloads,
            unit_func=unit_func,
            max_workers=cfg["max_workers"],
            desc="Claude pairwise batch",
            leave=False
        )

        # Update posterior from results
        for (a, b, y, reason) in results:
            ranker.compare(a, b, y)
            all_votes.append({
                "a": a, "b": b, "winner": "A" if y == 1 else "B",
                "a_ref": items[a]["segment_ref"],
                "b_ref": items[b]["segment_ref"],
                "reason": reason
            })

        total_done += len(results)
        pbar_outer.update(len(results))

    pbar_outer.close()

    # Final ranking (Section F — point ranking by m_i)
    order = np.argsort(-ranker.m)  # descending
    ranked = []
    for rnk, idx in enumerate(order, start=1):
        it = items[idx]
        ranked.append({
            "rank": rnk,
            "index": idx,
            "segment_ref": it["segment_ref"],
            "posterior_mean": float(ranker.m[idx]),
            "posterior_var": float(ranker.Sigma[idx, idx]),
        })

    # Write ranked CSV (keep original row fields for convenience)
    out_fields = ["rank", "index", "posterior_mean", "posterior_var"] + header
    with open(cfg["output_ranked_path"], "w", newline="", encoding="utf-8") as fout:
        writer = csv.DictWriter(fout, fieldnames=out_fields)
        writer.writeheader()
        for r in ranked:
            full = {**{k: r[k] for k in ["rank", "index", "posterior_mean", "posterior_var"]},
                    **items[r["index"]]["row"]}
            writer.writerow(full)
    print(f"Wrote ranked rows → {cfg['output_ranked_path']}")

    # Save comparisons
    if cfg["save_comparisons_path"]:
        with open(cfg["save_comparisons_path"], "w", encoding="utf-8") as f:
            for v in all_votes:
                f.write(json.dumps(v, ensure_ascii=False) + "\n")
        print(f"Wrote pairwise decisions → {cfg['save_comparisons_path']}")

    # Save posterior (optional)
    if cfg["save_posterior_path"]:
        np.savez_compressed(cfg["save_posterior_path"], m=ranker.m, Sigma=ranker.Sigma, order=order)
        print(f"Saved posterior → {cfg['save_posterior_path']}")


if __name__ == "__main__":
    main()
