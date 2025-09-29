"""
Filter a CSV using LangChain + Anthropic (Claude) with parallel requests.

- Reads an input CSV
- For each row, asks Claude if it's relevant to your filtering instruction
- Writes ONLY relevant rows to an output CSV
- Optionally writes rejected rows with a brief reason
- Parallelized with ThreadPoolExecutor and a tqdm progress bar
- Uses LangChain cache (SQLite)

Setup:
  pip install langchain langchain-anthropic tqdm pydantic

Env:
  export ANTHROPIC_API_KEY=your_key
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time
from typing import Any, Callable, Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm.auto import tqdm

# LangChain imports
from pydantic import BaseModel, Field
from langchain.cache import SQLiteCache
from langchain.globals import set_llm_cache
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

set_llm_cache(SQLiteCache(database_path=".langchain_cache.sqlite"))

# ==============================
# CONFIG — EDIT THESE VALUES
# ==============================
basic_csv_file_name = "ibids_he"
CONFIG = {
    # Paths
    "input_path": f"{basic_csv_file_name}.csv",
    "output_path": f"{basic_csv_file_name}_filtered.csv",
    "save_rejected_path": f"{basic_csv_file_name}_rejected.csv",  # set to None to skip saving rejects

    # Filtering instruction for Claude
    "filtering_prompt": (
        "Keep only rows that contain an explicit ibid citation. "
        "Rows that only mention generic terms (e.g., 'the Gemara', 'the Torah', "
        "'the Midrash', or similar non-specific references) should NOT be treated as "
        "citations and must be marked NOT relevant.\n"
        "However, if these terms refer to a very specific and well-defined quote from the Mishnah or Gemara, "
        "then they might be considered relevant ibid citations.\n"
        "Remember: an ibid is by definition a citation that requires wider context "
        "to resolve — whether by reference to previous citations in the text, or by "
        "knowledge of the current book or work being discussed.\n"
        "Even if the previous citation is not present in the current row or the provided context, it could still be considered a relevant ibid citation, "
        "as long as it likely refers to an actual reference from the library.\n"
        "If the ibid reference seems unclear, and you're not sure it refers to an actual citation in the library, "
        "mark NOT relevant as well."
    ),

    "model": "claude-3-5-sonnet-latest",
    "temperature": 0.0,
    "max_output_tokens": 150,   # LangChain passes this to Anthropic as max_tokens
    # Concurrency
    "max_workers": 5,
    "request_timeout": 60.0,
    # Retry policy
    "retries": 3,
    "backoff": 1.6,
}

SYSTEM_PROMPT = """\
You are a meticulous data triage assistant. You are given a piece of text in which one substring
(the ibid marker) is wrapped in <IBID>…</IBID> tags. Decide if this substring is a valid ibid
marker referring clearly to a citation in the surrounding context.

Return STRICT JSON ONLY with two keys:
{{"relevant": true|false, "reason": "<brief reason>"}}
"""


# ==============================
# Structured output schema
# ==============================
class FilterDecision(BaseModel):
    relevant: bool = Field(description="Whether the row is relevant (explicit ibid) or not.")
    reason: str = Field(description="A brief reason for the decision.")

# ==============================
# Build LangChain LLM & chain
# ==============================
def build_chain(cfg: Dict[str, Any]):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    llm = ChatAnthropic(
        model=cfg["model"],
        temperature=cfg["temperature"],
        max_tokens=cfg["max_output_tokens"],
        timeout=cfg["request_timeout"],
        max_retries=cfg["retries"],  # built-in retries
        # You can also set default_headers or base_url if needed.
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            (
                "human",
                "{filtering_instruction}\n\nSource: {segment_ref}\nText:\n{text_with_ibid}",
            ),
        ]
    )

    # Ask Claude to produce the exact structured schema; LC handles parsing/repair.
    chain = prompt | llm.with_structured_output(FilterDecision)
    return chain

# ==============================
# Parallel helper
# ==============================
def run_parallel(items: List[Any], unit_func: Callable[[Any], Any], max_workers: int, **tqdm_kwargs) -> List[Any]:
    results: List[Any] = []
    with tqdm(total=len(items), **tqdm_kwargs) as pbar:
        def _wrapped(item):
            out = unit_func(item)
            pbar.update(1)
            return out
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_wrapped, item) for item in items]
            for f in as_completed(futures):
                try:
                    r = f.result()
                except Exception as e:
                    r = None
                if r is not None:
                    results.append(r)
    return results

# ==============================
# Per-row decision using chain
# ==============================
def decide_with_langchain(chain, cfg, filtering_instruction, text_with_ibid, segment_ref) -> Tuple[bool, str]:
    # extra safety loop with manual backoff around the chain, in case you want more control:
    last_err = None
    for attempt in range(1, cfg["retries"] + 1):
        try:
            out: FilterDecision = chain.invoke(
                {
                    "filtering_instruction": filtering_instruction,
                    "segment_ref": segment_ref,
                    "text_with_ibid": text_with_ibid,
                }
            )
            # out is already a validated Pydantic object
            return bool(out.relevant), str(out.reason or "")
        except Exception as e:
            last_err = e
            time.sleep(cfg["backoff"] ** (attempt - 1))
    return False, f"LLM error: {last_err}"

# ==============================
# Main
# ==============================
def main():
    cfg = CONFIG
    chain = build_chain(cfg)

    # ---- Load CSV
    with open(cfg["input_path"], "r", newline="", encoding="utf-8") as fin:
        reader = csv.DictReader(fin)
        header = reader.fieldnames or []
        if not header:
            print("ERROR: CSV appears to have no header.", file=sys.stderr)
            sys.exit(1)
        rows = list(reader)

    # ---- Unit function for parallel execution
    def unit_func(row):
        ibid = row.get("ibid_surface", "")
        seg = row.get("segment_text", "")
        segment_ref = row.get("segment_ref", "")
        tagged = seg.replace(ibid, f"<IBID>{ibid}</IBID>", 1) if ibid else seg
        is_rel, reason = decide_with_langchain(
            chain=chain,
            cfg=cfg,
            filtering_instruction=cfg["filtering_prompt"],
            text_with_ibid=tagged,
            segment_ref=segment_ref,
        )
        return (is_rel, reason, row)

    # ---- Execute
    decisions = run_parallel(
        rows,
        unit_func=unit_func,
        max_workers=cfg["max_workers"],
        desc="Filtering rows with Claude (LangChain)",
    )

    # ---- Split results
    relevant_rows, rejected_rows = [], []
    for is_rel, reason, row in decisions:
        if is_rel:
            relevant_rows.append(row)
        else:
            if cfg["save_rejected_path"]:
                r = dict(row)
                r["_llm_relevant"] = "false"
                r["_llm_reason"] = reason
                rejected_rows.append(r)

    # ---- Write outputs
    with open(cfg["output_path"], "w", newline="", encoding="utf-8") as fout:
        writer = csv.DictWriter(fout, fieldnames=header)
        writer.writeheader()
        writer.writerows(relevant_rows)
    print(f"Wrote {len(relevant_rows)} relevant rows → {cfg['output_path']}")

    if cfg["save_rejected_path"]:
        rej_header = header + ["_llm_relevant", "_llm_reason"]
        with open(cfg["save_rejected_path"], "w", newline="", encoding="utf-8") as frej:
            writer = csv.DictWriter(frej, fieldnames=rej_header)
            writer.writeheader()
            writer.writerows(rejected_rows)
        print(f"Wrote {len(rejected_rows)} rejected rows → {cfg['save_rejected_path']}")

if __name__ == "__main__":
    main()
