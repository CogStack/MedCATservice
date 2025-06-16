#!/usr/bin/env python3
import os
import sys
import requests
from pathlib import Path
from zipfile import ZipFile

# Required environment variables
required_vars = {
    "MODEL_NAME": "name of the model",
    "MODEL_VOCAB_URL": "URL to vocab file",
    "MODEL_CDB_URL": "URL to CDB file",
    "MODEL_META_URL": "URL to meta file"
}

# Check for missing env vars
missing = [var for var in required_vars if not os.getenv(var)]
if missing:
    print("MedCAT Model Downloader.\n")
    print("Usage: set these environment variables before running the script:")
    for var, desc in required_vars.items():
        print(f"  {var:<16} - {desc}")
    print("\nMissing Arguments:")
    for var in missing:
        print(f"  {var}")
    sys.exit(1)

# Load env vars
model_name = os.environ["MODEL_NAME"]
vocab_url = os.environ["MODEL_VOCAB_URL"]
cdb_url = os.environ["MODEL_CDB_URL"]
meta_url = os.environ["MODEL_META_URL"]

# Prepare paths
script_dir = Path(__file__).resolve().parent
model_dir = script_dir.parent / "models" / model_name
model_dir.mkdir(parents=True, exist_ok=True)

vocab_file = model_dir / "vocab.dat"
cdb_file = model_dir / "cdb.dat"
meta_zip = model_dir / "mc_status.zip"
meta_dir = model_dir / "Status"


def download_file(url, dest_path):
    print(f"Downloading from {url}")
    resp = requests.get(url, stream=True)
    resp.raise_for_status()
    total = int(resp.headers.get('content-length', 0))
    downloaded = 0
    chunk_size = 8192

    with open(dest_path, 'wb') as f:
        for chunk in resp.iter_content(chunk_size):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    done = int(50 * downloaded / total)
                    percent = (downloaded / total) * 100
                    sys.stdout.write(f"\r[{'=' * done:<50}] {percent:5.1f}%")
                    sys.stdout.flush()
    print("\nDownload complete.")


# Download vocab and cdb if missing
if vocab_file.exists() and cdb_file.exists():
    print(f"{model_name} model already present -- skipping download")
else:
    if not vocab_file.exists():
        download_file(vocab_url, vocab_file)
    if not cdb_file.exists():
        download_file(cdb_url, cdb_file)

# Download and unzip meta if missing
if not meta_dir.exists():
    print("Downloading meta model: status")
    download_file(meta_url, meta_zip)
    with ZipFile(meta_zip, 'r') as zip_ref:
        zip_ref.extractall(model_dir)
    meta_zip.unlink()
else:
    print("Meta model already present -- skipping download")

print(f"Completed downloading model '{model_name}'")
