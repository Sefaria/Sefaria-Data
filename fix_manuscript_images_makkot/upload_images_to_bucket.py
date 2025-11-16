from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

from google.cloud import storage



from sefaria.google_storage_manager import GoogleStorageManager  # noqa: E402


BASE_DIR = Path(__file__).resolve().parent
LOCAL_IMAGES_DIR = BASE_DIR / "makkot_vilna_images"
BACKUP_DIR = BASE_DIR / "makkot_backup"
BUCKET_NAME = "manuscripts.sefaria.org"
REMOTE_PREFIX = "vilna-romm"
RUN_BACKUP = False
RUN_DELETE = True
RUN_UPLOAD = True


def get_bucket() -> storage.bucket.Bucket:
    return GoogleStorageManager.get_bucket(BUCKET_NAME)


def iter_makkot_blobs(bucket: storage.bucket.Bucket) -> Iterable[storage.blob.Blob]:
    for blob in bucket.list_blobs(prefix=REMOTE_PREFIX):
        if "Makkot" in blob.name:
            yield blob


def backup_existing_images(destination_dir: Path = BACKUP_DIR) -> None:
    bucket = get_bucket()
    destination_dir.mkdir(parents=True, exist_ok=True)
    downloaded = 0
    for blob in iter_makkot_blobs(bucket):
        filename = destination_dir / Path(blob.name).name
        with open(filename, "wb") as f:
            f.write(blob.download_as_bytes())
        downloaded += 1
        print(f"Backed up {blob.name} -> {filename}")
    if downloaded == 0:
        print("No existing Makkot images found to back up.")


def delete_existing_images() -> None:
    bucket = get_bucket()
    deleted = 0
    for blob in iter_makkot_blobs(bucket):
        print(f"Deleting {blob.name}")
        blob.delete()
        deleted += 1
    if deleted == 0:
        print("No existing Makkot images found to delete.")


def upload_local_images(local_dir: Path = LOCAL_IMAGES_DIR) -> None:
    if not local_dir.exists():
        raise FileNotFoundError(f"Local images directory does not exist: {local_dir}")

    bucket = get_bucket()
    files = sorted(path for path in local_dir.iterdir() if path.is_file())
    if not files:
        raise RuntimeError(f"No files found in {local_dir} to upload.")

    for file_path in files:
        remote_name = f"{REMOTE_PREFIX}/{file_path.name}"
        print(f"Uploading {file_path} -> {remote_name}")
        blob = bucket.blob(remote_name)
        blob.upload_from_filename(str(file_path))


def main() -> None:
    if RUN_BACKUP:
        backup_existing_images()

    if RUN_DELETE:
        delete_existing_images()

    if RUN_UPLOAD:
        upload_local_images()
    else:
        print("Skipping upload step (RUN_UPLOAD is False).")


if __name__ == "__main__":
    main()
