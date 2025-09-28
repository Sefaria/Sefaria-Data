"""
Filter a CSV using Claude (Anthropic) with parallel requests.

- Reads an input CSV
- For each row, asks Claude if it's relevant to your filtering instruction
- Writes ONLY relevant rows to an output CSV
- Optionally writes rejected rows with a brief reason
- Parallelized with ThreadPoolExecutor and a tqdm progress bar
- All configuration is in CONFIG (no CLI args)

Setup:
  pip install anthropic tqdm

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
from langchain.cache import SQLiteCache
from langchain.globals import set_llm_cache

from tqdm.auto import tqdm
set_llm_cache(SQLiteCache(database_path=".langchain_cache.sqlite"))

# ==============================
# CONFIG — EDIT THESE VALUES
# ==============================
basic_csv_file_name = "ibids_en"
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
        "Remember: an ibid is by definition a citation that requires wider context "
        "to resolve — whether by reference to previous citations in the text, or by "
        "knowledge of the current book or work being discussed.\n"
        "Even if the previous citation is not present in the current row or the provided context, it cold still be considered relevant ibid citation, "
        "as long as it likely refers to an actual reference from the library.\n"
        "If the ibid reference seems unclear, and you're not sure it refers to an actual citation in the library, "
        "mark NOT relevant as well."
    ),

    "model": "claude-3-5-sonnet-latest",
    "temperature": 0.0,
    "max_output_tokens": 150,

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

Return STRICT JSON ONLY:
{"relevant": true|false, "reason": "<brief reason>"}
"""

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
# LLM decision
# ==============================
def decide_with_claude(client, model, filtering_instruction, text_with_ibid,
                       temperature, max_output_tokens, retries, backoff, request_timeout):
    import anthropic
    user_msg = f"{filtering_instruction}\n\nText:\n{text_with_ibid}"
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            resp = client.messages.create(
                model=model,
                system=SYSTEM_PROMPT,
                max_tokens=max_output_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": user_msg}],
                timeout=request_timeout,
            )
            parts = resp.content or []
            text_chunks = [p.text for p in parts if getattr(p, "type", None) == "text"]
            txt = "".join(text_chunks).strip()
            data = json.loads(txt)
            return bool(data.get("relevant", False)), str(data.get("reason", "") or "")
        except Exception as e:
            last_err = e
            time.sleep(backoff ** (attempt - 1))
    return False, f"LLM error: {last_err}"

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
    client = get_anthropic_client()

    with open(cfg["input_path"], "r", newline="", encoding="utf-8") as fin:
        reader = csv.DictReader(fin)
        header = reader.fieldnames or []
        if not header:
            print("ERROR: CSV appears to have no header.", file=sys.stderr)
            sys.exit(1)
        rows = list(reader)

    def unit_func(row):
        ibid = row.get("ibid_surface", "")
        seg = row.get("segment_text", "")
        tagged = seg.replace(ibid, f"<IBID>{ibid}</IBID>", 1) if ibid else seg
        is_rel, reason = decide_with_claude(
            client=client,
            model=cfg["model"],
            filtering_instruction=cfg["filtering_prompt"],
            text_with_ibid=tagged,
            temperature=cfg["temperature"],
            max_output_tokens=cfg["max_output_tokens"],
            retries=cfg["retries"],
            backoff=cfg["backoff"],
            request_timeout=cfg["request_timeout"],
        )
        return (is_rel, reason, row)

    decisions = run_parallel(
        rows,
        unit_func=unit_func,
        max_workers=cfg["max_workers"],
        desc="Filtering rows with Claude",
    )

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
