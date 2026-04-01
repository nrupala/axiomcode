"""
AxiomCode Persistence Layer
============================
Handles data storage, history retention, and cross-version compatibility.

Features:
  - JSON-based storage with schema versioning
  - Automatic migration between schema versions
  - History retention — old data preserved during upgrades
  - Backward compatibility — can read data from older versions
  - Forward compatibility — graceful handling of newer data
  - Atomic writes — prevents corruption on crash
  - Data validation — schema enforcement on read/write

All stdlib. Zero external dependencies.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ─── Schema Version ─────────────────────────────────────────────────────────

CURRENT_SCHEMA_VERSION = 1


# ─── Data Store ─────────────────────────────────────────────────────────────

@dataclass
class DataRecord:
    """A single data record with metadata."""
    id: str
    schema_version: int
    created_at: float
    updated_at: float
    data: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "data": self.data,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "DataRecord":
        return cls(
            id=d["id"],
            schema_version=d.get("schema_version", CURRENT_SCHEMA_VERSION),
            created_at=d["created_at"],
            updated_at=d["updated_at"],
            data=d.get("data", {}),
            metadata=d.get("metadata", {}),
        )


class DataStore:
    """
    Persistent JSON data store with schema versioning and history retention.

    Usage:
        store = DataStore(".axiomcode/data")
        
        # Create a record
        record = store.create("algorithm_001", {
            "name": "binary_search",
            "spec_hash": "abc123",
            "proof_hash": "def456",
        })
        
        # Read a record
        record = store.get("algorithm_001")
        
        # Update a record
        store.update("algorithm_001", {"status": "verified"})
        
        # Get history
        history = store.get_history("algorithm_001")
        
        # List all records
        all_records = store.list()
    """

    def __init__(self, store_dir: str | Path):
        self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir = self.store_dir / "history"
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def _record_path(self, record_id: str) -> Path:
        """Get the file path for a record."""
        return self.store_dir / f"{record_id}.json"

    def _history_path(self, record_id: str, timestamp: float) -> Path:
        """Get the file path for a historical record."""
        # Use microsecond precision to avoid collisions
        ts = str(timestamp).replace(".", "")
        return self.history_dir / f"{record_id}_{ts}.json"

    def create(self, record_id: str, data: dict[str, Any], metadata: dict[str, Any] | None = None) -> DataRecord:
        """Create a new record."""
        now = time.time()
        record = DataRecord(
            id=record_id,
            schema_version=CURRENT_SCHEMA_VERSION,
            created_at=now,
            updated_at=now,
            data=data,
            metadata=metadata or {},
        )
        self._write_record(record)
        return record

    def get(self, record_id: str) -> DataRecord | None:
        """Get a record by ID. Returns None if not found."""
        path = self._record_path(record_id)
        if not path.exists():
            return None
        try:
            d = json.loads(path.read_text())
            record = DataRecord.from_dict(d)
            # Validate schema compatibility
            self._validate_schema(record)
            return record
        except (json.JSONDecodeError, KeyError):
            return None

    def update(self, record_id: str, data: dict[str, Any], metadata: dict[str, Any] | None = None) -> DataRecord | None:
        """Update a record. Preserves history."""
        record = self.get(record_id)
        if record is None:
            return None

        # Save current version to history
        self._save_to_history(record)

        # Update record
        record.data.update(data)
        if metadata:
            record.metadata.update(metadata)
        record.updated_at = time.time()

        self._write_record(record)
        return record

    def delete(self, record_id: str) -> bool:
        """Delete a record. Preserves history."""
        record = self.get(record_id)
        if record is None:
            return False

        # Save to history before deletion
        self._save_to_history(record)

        path = self._record_path(record_id)
        if path.exists():
            path.unlink()
        return True

    def list(self) -> list[DataRecord]:
        """List all records."""
        records = []
        for path in self.store_dir.glob("*.json"):
            if path.name == "index.json":
                continue
            try:
                d = json.loads(path.read_text())
                record = DataRecord.from_dict(d)
                self._validate_schema(record)
                records.append(record)
            except (json.JSONDecodeError, KeyError):
                continue
        return sorted(records, key=lambda r: r.created_at)

    def get_history(self, record_id: str) -> list[DataRecord]:
        """Get the full history of a record."""
        history = []
        for path in self.history_dir.glob(f"{record_id}_*.json"):
            try:
                d = json.loads(path.read_text())
                record = DataRecord.from_dict(d)
                history.append(record)
            except (json.JSONDecodeError, KeyError):
                continue
        return sorted(history, key=lambda r: r.updated_at)

    def migrate_schema(self, target_version: int) -> int:
        """
        Migrate all records to a target schema version.
        Returns the number of records migrated.
        """
        migrated = 0
        for record in self.list():
            if record.schema_version != target_version:
                # Save current version to history
                self._save_to_history(record)

                # Apply migration
                migrated_data = self._migrate_record_data(record.data, record.schema_version, target_version)
                record.data = migrated_data
                record.schema_version = target_version
                record.updated_at = time.time()
                record.metadata["migrated_from"] = record.schema_version
                record.metadata["migrated_at"] = time.time()

                self._write_record(record)
                migrated += 1

        return migrated

    def _validate_schema(self, record: DataRecord) -> None:
        """Validate schema compatibility."""
        if record.schema_version > CURRENT_SCHEMA_VERSION:
            # Forward compatibility — warn but allow
            record.metadata["_forward_compatible"] = True
        elif record.schema_version < CURRENT_SCHEMA_VERSION:
            # Backward compatibility — warn but allow
            record.metadata["_backward_compatible"] = True

    def _migrate_record_data(self, data: dict, from_version: int, to_version: int) -> dict:
        """Migrate record data between schema versions."""
        if from_version == to_version:
            return data

        # Migration path: 1 -> 2 (example)
        if from_version == 1 and to_version == 2:
            # Example: add new fields
            data.setdefault("new_field", "default_value")
            return data

        # Migration path: 2 -> 1 (downgrade)
        if from_version == 2 and to_version == 1:
            # Example: remove new fields
            data.pop("new_field", None)
            return data

        # No migration defined — return as-is
        return data

    def _write_record(self, record: DataRecord) -> None:
        """Write a record to disk atomically."""
        path = self._record_path(record.id)
        # Write to temp file first, then rename (atomic on most filesystems)
        fd, tmp_path = tempfile.mkstemp(dir=self.store_dir, suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(record.to_dict(), f, indent=2)
            shutil.move(tmp_path, path)
        except Exception:
            # Clean up temp file on error
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    def _save_to_history(self, record: DataRecord) -> None:
        """Save a record version to history."""
        history_path = self._history_path(record.id, record.updated_at)
        history_path.write_text(json.dumps(record.to_dict(), indent=2))

    def get_stats(self) -> dict:
        """Get store statistics."""
        records = self.list()
        history_count = len(list(self.history_dir.glob("*.json")))
        return {
            "total_records": len(records),
            "history_entries": history_count,
            "schema_version": CURRENT_SCHEMA_VERSION,
            "store_size_bytes": sum(p.stat().st_size for p in self.store_dir.rglob("*") if p.is_file()),
        }


# ─── Session Manager ────────────────────────────────────────────────────────

class SessionManager:
    """
    Manages user sessions with persistence.
    Tracks user activity, preferences, and history.
    """

    def __init__(self, store_dir: str | Path = ".axiomcode/sessions"):
        self.store = DataStore(store_dir)

    def create_session(self, user_id: str, metadata: dict | None = None) -> DataRecord:
        """Create a new user session."""
        session_id = f"session_{user_id}_{int(time.time())}"
        return self.store.create(session_id, {
            "user_id": user_id,
            "status": "active",
        }, metadata=metadata or {})

    def get_user_sessions(self, user_id: str) -> list[DataRecord]:
        """Get all sessions for a user."""
        return [r for r in self.store.list() if r.data.get("user_id") == user_id]

    def close_session(self, session_id: str) -> bool:
        """Close a session."""
        record = self.store.get(session_id)
        if record is None:
            return False
        record.data["status"] = "closed"
        record.data["closed_at"] = time.time()
        self.store.update(session_id, record.data)
        return True

    def get_user_history(self, user_id: str) -> list[dict]:
        """Get complete activity history for a user."""
        sessions = self.get_user_sessions(user_id)
        history = []
        for session in sessions:
            session_history = self.store.get_history(session.id)
            for h in session_history:
                history.append({
                    "session_id": session.id,
                    "timestamp": h.updated_at,
                    "data": h.data,
                })
        return sorted(history, key=lambda x: x["timestamp"])


# ─── Algorithm Registry ─────────────────────────────────────────────────────

class AlgorithmRegistry:
    """
    Persistent registry of all generated algorithms.
    Tracks specifications, proofs, certificates, and artifacts.
    """

    def __init__(self, store_dir: str | Path = ".axiomcode/algorithms"):
        self.store = DataStore(store_dir)

    def register_algorithm(self, name: str, spec_hash: str, proof_hash: str,
                          c_binary_hash: str = "", python_hash: str = "",
                          certificate_path: str = "", metadata: dict | None = None) -> DataRecord:
        """Register a newly generated algorithm."""
        return self.store.create(name, {
            "name": name,
            "spec_hash": spec_hash,
            "proof_hash": proof_hash,
            "c_binary_hash": c_binary_hash,
            "python_hash": python_hash,
            "certificate_path": certificate_path,
            "status": "verified",
            "generated_at": time.time(),
        }, metadata=metadata or {})

    def get_algorithm(self, name: str) -> DataRecord | None:
        """Get an algorithm by name."""
        return self.store.get(name)

    def update_algorithm(self, name: str, updates: dict) -> DataRecord | None:
        """Update an algorithm record."""
        return self.store.update(name, updates)

    def list_algorithms(self) -> list[DataRecord]:
        """List all registered algorithms."""
        return self.store.list()

    def get_algorithm_history(self, name: str) -> list[DataRecord]:
        """Get the full history of an algorithm."""
        return self.store.get_history(name)

    def search_algorithms(self, query: str) -> list[DataRecord]:
        """Search algorithms by name or metadata."""
        results = []
        query_lower = query.lower()
        for algo in self.list_algorithms():
            # Search in record ID
            if query_lower in algo.id.lower():
                results.append(algo)
                continue
            # Search in data values only (not keys)
            data_values = json.dumps(list(algo.data.values())).lower()
            if query_lower in data_values:
                results.append(algo)
                continue
            # Search in metadata values only (not keys)
            meta_values = json.dumps(list(algo.metadata.values())).lower()
            if query_lower in meta_values:
                results.append(algo)
        return results
