import os
from sshtunnel import SSHTunnelForwarder
from pymongo import MongoClient
import paramiko
from contextlib import contextmanager
from connection_settings import CONNECTION


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


if __name__ == "__main__":
    with remote_links_collection() as remote_col:
        print(f"Remote count: {remote_col.estimated_document_count()}")
        print("Remote doc:", remote_col.find_one())

    with local_links_collection() as local_col:
        print(f"Local count: {local_col.estimated_document_count()}")
        print("Local doc:", local_col.find_one())
