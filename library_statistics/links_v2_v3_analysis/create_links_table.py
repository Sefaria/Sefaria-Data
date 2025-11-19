import os
import sys
import csv
from pathlib import Path
from sshtunnel import SSHTunnelForwarder
from pymongo import MongoClient
from bson import ObjectId
import paramiko
from contextlib import contextmanager
from connection_settings import CONNECTION
from sources.local_settings import SEFARIA_PROJECT_PATH

# Wire up Sefaria project (keeps Django settings available for shared configuration).
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sefaria.settings")
import django
django.setup()


def connect_via_ssh_tunnel():
    """
    Open an SSH tunnel to the remote host and return (server, MongoClient).
    Caller must close server when done.
    """
    # sshtunnel references paramiko.DSSKey (removed in paramiko 4); shim for compatibility.
    if not hasattr(paramiko, "DSSKey"):
        paramiko.DSSKey = paramiko.RSAKey

    server = SSHTunnelForwarder(
        (CONNECTION["ssh_host"], CONNECTION["ssh_port"]),
        ssh_username=CONNECTION["ssh_user"],
        ssh_pkey=os.path.expanduser(CONNECTION["ssh_pkey"]),
        remote_bind_address=(CONNECTION["remote_bind_host"], CONNECTION["remote_bind_port"]),
    )
    server.start()
    mongo_uri = f"mongodb://127.0.0.1:{server.local_bind_port}"
    client = MongoClient(mongo_uri)
    return server, client, mongo_uri


@contextmanager
def remote_links_collection():
    """Context manager yielding the remote links collection via SSH tunnel."""
    server, client, _ = connect_via_ssh_tunnel()
    try:
        col = client[CONNECTION["mongo_db"]][CONNECTION["mongo_collection"]]
        yield col
    finally:
        server.stop()


@contextmanager
def local_links_collection():
    """Context manager yielding the local links collection (no tunnel)."""
    local_uri = os.getenv(
        "LOCAL_MONGO_URI",
        "mongodb://localhost:27017/?retryWrites=true&loadBalanced=false&serverSelectionTimeoutMS=5000&connectTimeoutMS=10000",
    )
    local_db_name = os.getenv("LOCAL_MONGO_DB", "sefaria")
    local_collection_name = os.getenv("LOCAL_MONGO_COLLECTION", CONNECTION["mongo_collection"])
    client = MongoClient(local_uri)
    try:
        yield client[local_db_name][local_collection_name]
    finally:
        client.close()


def normalize_version_id(val):
    """
    Normalize a version id (ObjectId or string) to a hex string so we can match
    regardless of whether the links store source_text_oid as ObjectId or string.
    """
    if isinstance(val, ObjectId):
        return val.binary.hex()
    s = str(val)
    if s.startswith("ObjectId('") and s.endswith("')"):
        return s[len("ObjectId('"):-2]
    return s


def aggregate_links_by_index(col):
    """
    Aggregate link counts by the index title that sourced the citation (from source_text_oid)
    for generated_by='add_links_from_text'.
    Returns (counts_by_index, missing_version_ids).
    """
    # Build a lookup of Version _id → Index title from the texts collection.
    version_title_map = {
        key: doc.get("title")
        for doc in col.database["texts"].find({}, {"_id": 1, "title": 1})
        if doc.get("title")
        for key in (doc["_id"], normalize_version_id(doc["_id"]))
    }
    pipeline = [
        {"$match": {"generated_by": "add_links_from_text", "source_text_oid": {"$exists": True}}},
        {"$group": {"_id": "$source_text_oid", "count": {"$sum": 1}}},
    ]
    counts = {}
    missing_version_ids = set()
    for doc in col.aggregate(pipeline, allowDiskUse=True):
        version_id_raw = doc["_id"]
        version_id_norm = normalize_version_id(version_id_raw)
        idx_title = version_title_map.get(version_id_raw) or version_title_map.get(version_id_norm)
        if not idx_title:
            missing_version_ids.add(version_id_norm)
            continue
        counts[idx_title] = counts.get(idx_title, 0) + doc["count"]
    return counts, missing_version_ids


def write_unmapped_links_table(col, version_ids, output_path):
    """
    Write a debug CSV of links whose source_text_oid is not mapped to an index title.
    """
    version_ids = list(version_ids)
    if not version_ids:
        return
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    projection = {"_id": 1, "refs": 1, "source_text_oid": 1}
    with open(output_path, "w", newline="") as fout:
        writer = csv.DictWriter(fout, fieldnames=["link_id", "source_text_oid", "refs"])
        writer.writeheader()
        # Chunk the $in list to avoid oversized BSON queries.
        chunk_size = 1000
        for i in range(0, len(version_ids), chunk_size):
            chunk = version_ids[i:i + chunk_size]
            chunk_objids = []
            for vid in chunk:
                try:
                    chunk_objids.append(ObjectId(vid))
                except Exception:
                    continue
            or_clauses = [{"source_text_oid": {"$in": chunk}}]
            if chunk_objids:
                or_clauses.append({"source_text_oid": {"$in": chunk_objids}})
            cursor = col.find(
                {
                    "generated_by": "add_links_from_text",
                    "$or": or_clauses,
                },
                projection,
            )
            for doc in cursor:
                refs = doc.get("refs") or []
                writer.writerow(
                    {
                        "link_id": str(doc.get("_id")),
                        "source_text_oid": str(doc.get("source_text_oid")),
                        "refs": "; ".join(refs),
                    }
                )


if __name__ == "__main__":
    output_csv = os.getenv("OUTPUT_CSV", os.path.join(os.path.dirname(__file__), "link_distribution.csv"))
    debug_dir = os.getenv("DEBUG_OUTPUT_DIR", os.path.dirname(output_csv))

    print("Aggregating remote (v3)...")
    with remote_links_collection() as remote_col:
        remote_counts, remote_missing = aggregate_links_by_index(remote_col)
        if remote_missing:
            remote_debug_csv = os.path.join(debug_dir, "unmapped_remote_links.csv")
            write_unmapped_links_table(remote_col, remote_missing, remote_debug_csv)
            print(f"Wrote {len(remote_missing)} unmapped version IDs (remote) to {remote_debug_csv}")
    print(f"Counted {sum(remote_counts.values())} links across {len(remote_counts)} index titles remotely")

    print("Aggregating local (v2)...")
    with local_links_collection() as local_col:
        local_counts, local_missing = aggregate_links_by_index(local_col)
        if local_missing:
            local_debug_csv = os.path.join(debug_dir, "unmapped_local_links.csv")
            write_unmapped_links_table(local_col, local_missing, local_debug_csv)
            print(f"Wrote {len(local_missing)} unmapped version IDs (local) to {local_debug_csv}")
    print(f"Counted {sum(local_counts.values())} links across {len(local_counts)} index titles locally")

    all_indexes = sorted(set(remote_counts) | set(local_counts))
    rows = []
    for idx in all_indexes:
        v3 = remote_counts.get(idx, 0)
        v2 = local_counts.get(idx, 0)
        pct_change = None
        if v2 != 0:
            pct_change = (v3 - v2) / v2
        rows.append({
            "Index Title": idx,
            "Num Linker v3 Links": v3,
            "Num Linker v2 Links": v2,
            "% Change": "" if pct_change is None else f"{pct_change:.4f}",
        })

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    with open(output_csv, "w", newline="") as fout:
        writer = csv.DictWriter(fout, fieldnames=["Index Title", "Num Linker v3 Links", "Num Linker v2 Links", "% Change"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {output_csv}")
