"""Central paths for external data/model storage."""

from __future__ import annotations

import os


EXTERNAL_ROOT = os.environ.get("DLSE_EXTERNAL_ROOT", "/mnt/sda/gzx")
DATA_ROOT = os.environ.get("DLSE_DATA_ROOT", f"{EXTERNAL_ROOT}/data/deeplearning2se")
MODEL_ROOT = os.environ.get("DLSE_MODEL_ROOT", f"{EXTERNAL_ROOT}/models/deeplearning2se")
HF_CACHE_DIR = os.environ.get("HF_HOME", f"{EXTERNAL_ROOT}/models/huggingface")

