"""Test bootstrap: prod-build modules importable, and all default
state (CA key, store DB, work root) pointed at a throwaway tmp dir so
tests never create real state files inside the deliverable tree."""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

_TMP = tempfile.mkdtemp(prefix="ax-prod-test-")
os.environ.setdefault("AXIOMCODE_CA_KEY_FILE", os.path.join(_TMP, "ca_key.pem"))
os.environ.setdefault("AXIOMCODE_DB", os.path.join(_TMP, "axiomcode.db"))
os.environ.setdefault("AXIOMCODE_WORK_ROOT", os.path.join(_TMP, "work"))
Path(os.environ["AXIOMCODE_WORK_ROOT"]).mkdir(parents=True, exist_ok=True)
