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
    server, client, mongo_uri = connect_via_ssh_tunnel()
    try:
        doc = client[CONNECTION["mongo_db"]][CONNECTION["mongo_collection"]].find_one()
        print(doc)
    finally:
        server.stop()
