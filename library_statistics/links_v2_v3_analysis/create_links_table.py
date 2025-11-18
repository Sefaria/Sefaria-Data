import os
import sys
import csv
from pathlib import Path
from sshtunnel import SSHTunnelForwarder
from pymongo import MongoClient
import paramiko
from contextlib import contextmanager
from connection_settings import CONNECTION
from sources.local_settings import SEFARIA_PROJECT_PATH

# Wire up Sefaria project so we can resolve Ref → Index
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sefaria.settings")
import django
django.setup()
from sefaria.model import Ref


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


def aggregate_links_by_index(col):
    """
    Aggregate link counts by index title for generated_by='add_links_from_text'.
    Both refs in each link are counted (each side counts toward its index).
    """
    pipeline = [
        {"$match": {"generated_by": "add_links_from_text"}},
        {"$unwind": "$refs"},
        {"$group": {"_id": "$refs", "count": {"$sum": 1}}},
    ]
    counts = {}
    for doc in col.aggregate(pipeline, allowDiskUse=True):
        ref_str = doc["_id"]
        try:
            idx_title = Ref(ref_str).index.title
        except Exception:
            continue
        counts[idx_title] = counts.get(idx_title, 0) + doc["count"]
    return counts


if __name__ == "__main__":
    output_csv = os.getenv("OUTPUT_CSV", os.path.join(os.path.dirname(__file__), "link_distribution.csv"))

    print("Aggregating remote (v3)...")
    with remote_links_collection() as remote_col:
        remote_counts = aggregate_links_by_index(remote_col)
    print(f"Found {len(remote_counts)} index titles remotely")

    print("Aggregating local (v2)...")
    with local_links_collection() as local_col:
        local_counts = aggregate_links_by_index(local_col)
    print(f"Found {len(local_counts)} index titles locally")

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
