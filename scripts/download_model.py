#!/usr/bin/env python3
import os
import sys
import requests
import logging
from pathlib import Path
from zipfile import ZipFile

# Required environment variables
required_vars = {
    "MODEL_NAME": "name of the model",
    "MODEL_VOCAB_URL": "URL to vocab file",
    "MODEL_CDB_URL": "URL to CDB file",
    "MODEL_META_URL": "URL to meta file"
}

# Setup logging
logging.basicConfig(
    format='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
    level=logging.INFO,
)
log = logging.getLogger()

log.info("Running MedCAT Model Downloader")

# Check for missing env vars
missing = [var for var in required_vars if not os.getenv(var)]
if missing:
    log.error("Missing Required environment variables:")
    for var in missing:
        log.error(f"  {var}")
    log.info("Usage: set these environment variables before running the script:")
    for var, desc in required_vars.items():
        log.info(f"  {var:<16} - {desc}")

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
    log.info(f"Downloading from {url} to {dest_path}")
    resp = requests.get(url, stream=True)
    resp.raise_for_status()
    total = int(resp.headers.get('content-length', 0))
    downloaded = 0
    chunk_size = 8192
    last_logged_percent = 0

    with open(dest_path, 'wb') as f:
        # Print status bar to the console
        for chunk in resp.iter_content(chunk_size):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    percent = int(downloaded * 100 / total)
                    if percent - last_logged_percent >= 10 or percent == 100:
                        last_logged_percent = percent
                        done = int(50 * percent / 100)
                        downloaded_mb = downloaded / (1024 * 1024)
                        total_mb = total / (1024 * 1024)
                        log.info(f"[{'=' * done:<50}] {percent:3d}% {downloaded_mb:.2f} MB / {total_mb:.2f} MB")

    os.chmod(dest_path, 0o644)
    log.info(f"Download complete to {dest_path}")


# Download vocab and cdb if missing
if vocab_file.exists() and cdb_file.exists():
    log.info(f"{model_name} model already present in Vocabulary: '{vocab_file}' and CDB: '{cdb_file}'. Skipping download")
else:
    log.info(f"Starting download of MedCAT Model '{model_name}'")
    if not vocab_file.exists():
        download_file(vocab_url, vocab_file)
    if not cdb_file.exists():
        download_file(cdb_url, cdb_file)

# Download and unzip meta if missing
if not meta_dir.exists():
    log.info("Downloading meta model: status")
    download_file(meta_url, meta_zip)
    with ZipFile(meta_zip, 'r') as zip_ref:
        zip_ref.extractall(model_dir)
    meta_zip.unlink()
else:
    log.info(f"Meta model already present in {meta_dir} -- skipping download")

log.info(f"Completed downloading model '{model_name}'")
