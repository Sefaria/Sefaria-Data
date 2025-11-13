#!/usr/bin/env python3
"""
Rewrite legacy `ref_resolver_context_swaps` declarations into the newer
`ref_resolver_context_mutations` format so Linker.v3 can pick them up.

Usage:
    Adjust `PARAMS` at the bottom of this file and run:
        python data_alignments/turn_linker_context_swpas_into_mutations.py
By default the script scans every Index and only saves those that actually change.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Iterator, List, Sequence, Tuple

import django

django.setup()

from sefaria.model import library
from sefaria.model.schema import SchemaNode
from sefaria.model.text import Index


def _iter_schema_nodes(root: SchemaNode) -> Iterator[SchemaNode]:
    """Yield every node in a schema tree (pre-order)."""
    stack = [root]
    while stack:
        node = stack.pop()
        yield node
        children = list(getattr(node, "children", []) or [])
        stack.extend(reversed(children))


def _iter_index_nodes(index: Index) -> Iterator[SchemaNode]:
    """Iterate through the main schema tree plus any alt-structure trees."""
    if getattr(index, "nodes", None):
        yield from _iter_schema_nodes(index.nodes)
    struct_objs = getattr(index, "struct_objs", {}) or {}
    for struct_root in struct_objs.values():
        yield from _iter_schema_nodes(struct_root)


def _convert_swaps(swaps: Mapping[str, Sequence[str]]) -> List[dict]:
    """
    Turn a {slug: [replacement...]} mapping into swap mutations.
    """
    mutations: List[dict] = []
    for input_slug, output_terms in swaps.items():
        if not isinstance(input_slug, str) or not input_slug:
            raise ValueError(f"Invalid context slug: {input_slug!r}")
        if not isinstance(output_terms, Sequence) or isinstance(output_terms, (str, bytes)):
            raise ValueError(f"Swap targets for {input_slug!r} must be a list/tuple")
        outputs = [term for term in output_terms if term]
        if not outputs:
            raise ValueError(f"Swap targets for {input_slug!r} cannot be empty")
        mutations.append({
            "op": "swap",
            "input_terms": [input_slug],
            "output_terms": outputs,
        })
    return mutations


def _process_node(node: SchemaNode) -> Tuple[int, int]:
    swaps = getattr(node, "ref_resolver_context_swaps", None)
    if not swaps:
        return 0, 0
    if not isinstance(swaps, Mapping):
        raise TypeError(f"Unexpected ref_resolver_context_swaps payload on {node.full_title('en')}")
    converted = _convert_swaps(swaps)
    existing = list(getattr(node, "ref_resolver_context_mutations", []) or [])
    node.ref_resolver_context_mutations = existing + converted
    delattr(node, "ref_resolver_context_swaps")
    return 1, len(converted)


def _resolve_indexes(titles: Sequence[str] | None) -> Iterable[Index]:
    if titles:
        for title in titles:
            index = library.get_index(title)
            if index is None:
                raise ValueError(f"Unknown index title: {title}")
            yield index
    else:
        yield from library.all_index_records()


def convert_swaps(dry_run: bool = False, titles: Sequence[str] | None = None) -> None:
    total_indexes = 0
    total_nodes = 0
    total_mutations = 0

    for index in _resolve_indexes(titles):
        nodes_changed = 0
        mutations_created = 0
        for node in _iter_index_nodes(index):
            changed, new_mutations = _process_node(node)
            nodes_changed += changed
            mutations_created += new_mutations
        if nodes_changed:
            total_indexes += 1
            total_nodes += nodes_changed
            total_mutations += mutations_created
            status = "DRY-RUN" if dry_run else "UPDATED"
            print(f"[{status}] {index.title}: {nodes_changed} nodes -> {mutations_created} swap mutations")
            if not dry_run:
                index.save(override_dependencies=True)

    if total_indexes == 0:
        print("No indexes still declare ref_resolver_context_swaps.")
    else:
        action = "would be" if dry_run else "were"
        print(f"{total_nodes} nodes across {total_indexes} indexes {action} rewritten "
              f"into {total_mutations} context mutations.")


def main() -> None:
    convert_swaps(**PARAMS)


# ---------------------------------------------------------------------------
# Edit the values below to control what the migration runs against.
# - dry_run: if True, prints planned changes without saving.
# - titles: optional list of Index titles to limit the scope (leave empty to scan everything).
# ---------------------------------------------------------------------------
PARAMS = {
    "dry_run": False,
    "titles": [
        # "Yerushalmi Peah",
        # "Yerushalmi Shekalim",
    ],
}


if __name__ == "__main__":
    main()
