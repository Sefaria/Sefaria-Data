import os
from sshtunnel import SSHTunnelForwarder
from pymongo import MongoClient
import paramiko
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


if __name__ == "__main__":
    # Remote via SSH
    server, client, mongo_uri = connect_via_ssh_tunnel()
    try:
        db = client[CONNECTION["mongo_db"]][CONNECTION["mongo_collection"]]
        print(f"Remote count: {db.estimated_document_count()}")
        print("Remote doc:", db.find_one())
    finally:
        server.stop()

    # Local direct connection (no tunnel).
    local_uri = os.getenv(
        "LOCAL_MONGO_URI",
        "mongodb://localhost:27017/?retryWrites=true&loadBalanced=false&serverSelectionTimeoutMS=5000&connectTimeoutMS=10000",
    )
    local_db_name = os.getenv("LOCAL_MONGO_DB", "sefaria")
    local_collection_name = os.getenv("LOCAL_MONGO_COLLECTION", CONNECTION["mongo_collection"])
    local_client = MongoClient(local_uri)
    local_col = local_client[local_db_name][local_collection_name]
    print(f"Local count: {local_col.estimated_document_count()}")
    print("Local doc:", local_col.find_one())
