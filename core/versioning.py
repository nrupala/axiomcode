"""
AxiomCode Versioning & Data Migration System
==============================================
Handles upgrades and downgrades between any versions (v1 <-> v2 <-> vN).
Ensures data persistence, backward compatibility, and zero data loss.

All stdlib. Zero external dependencies.
"""

from __future__ import annotations

import json
import os
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

# ─── Version Constants ──────────────────────────────────────────────────────

CURRENT_VERSION = "0.1.0"
VERSION_FILE = ".axiomcode/version.json"
MIGRATION_LOG = ".axiomcode/migrations.log"
BACKUP_DIR = ".axiomcode/backups"
DATA_DIR = ".axiomcode"


@dataclass
class VersionInfo:
    """Metadata about an AxiomCode version."""
    version: str
    released_at: str
    schema_version: int
    data_format: str
    breaking_changes: list[str] = field(default_factory=list)
    new_features: list[str] = field(default_factory=list)
    deprecated_features: list[str] = field(default_factory=list)
    migration_notes: str = ""

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "released_at": self.released_at,
            "schema_version": self.schema_version,
            "data_format": self.data_format,
            "breaking_changes": self.breaking_changes,
            "new_features": self.new_features,
            "deprecated_features": self.deprecated_features,
            "migration_notes": self.migration_notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VersionInfo":
        return cls(**data)


# ─── Version Registry ───────────────────────────────────────────────────────

# All known versions and their metadata
VERSION_REGISTRY: dict[str, VersionInfo] = {
    "0.1.0": VersionInfo(
        version="0.1.0",
        released_at="2026-03-31",
        schema_version=1,
        data_format="json-v1",
        new_features=[
            "Initial release",
            "Natural language to Lean 4 spec generation",
            "Proof engine with Pantograph integration",
            "C binary extraction via lean --c",
            "Python package generation with cffi bindings",
            "Cryptographic proof certificates",
            "Zero-trust security model",
            "Encrypted key store",
            "Tamper-evident audit log",
            "Interactive proof visualization (2D/3D)",
            "LLM caching for reduced latency",
            "Sandboxed code execution",
            "Rate limiting for API calls",
            "13 CLI commands",
            "Zero external dependencies",
        ],
        migration_notes="Initial version. No migration required.",
    ),
    # Future versions added here:
    # "0.2.0": VersionInfo(
    #     version="0.2.0",
    #     released_at="2026-06-01",
    #     schema_version=2,
    #     data_format="json-v2",
    #     breaking_changes=["Certificate format changed from v1 to v2"],
    #     new_features=["Domain-specific libraries", "Coq backend support"],
    #     deprecated_features=["Legacy proof format"],
    #     migration_notes="Certificates will be automatically upgraded. Downgrade requires re-verification.",
    # ),
}


# ─── Migration Functions ────────────────────────────────────────────────────

def migrate_v1_to_v2(data_dir: Path) -> dict:
    """Migration: v0.1.0 -> v0.2.0 (example)."""
    changes = []
    # Example: migrate certificate format
    cert_dir = data_dir.parent / "build" / "certs"
    if cert_dir.exists():
        for cert_file in cert_dir.glob("*.cert.json"):
            cert_data = json.loads(cert_file.read_text())
            if cert_data.get("version") == 1:
                cert_data["version"] = 2
                cert_data["migrated_from"] = "0.1.0"
                cert_data["migrated_at"] = time.time()
                cert_file.write_text(json.dumps(cert_data, indent=2))
                changes.append(f"Upgraded certificate: {cert_file.name}")
    return {"status": "success", "changes": changes}


def migrate_v2_to_v1(data_dir: Path) -> dict:
    """Downgrade: v0.2.0 -> v0.1.0 (example)."""
    changes = []
    cert_dir = data_dir.parent / "build" / "certs"
    if cert_dir.exists():
        for cert_file in cert_dir.glob("*.cert.json"):
            cert_data = json.loads(cert_file.read_text())
            if cert_data.get("version") == 2:
                # Strip v2-only fields
                cert_data.pop("migrated_from", None)
                cert_data.pop("migrated_at", None)
                cert_data["version"] = 1
                cert_file.write_text(json.dumps(cert_data, indent=2))
                changes.append(f"Downgraded certificate: {cert_file.name}")
    return {"status": "success", "changes": changes}


# Registry of migration functions
MIGRATIONS: dict[tuple[str, str], Callable[[Path], dict]] = {
    ("0.1.0", "0.2.0"): migrate_v1_to_v2,
    ("0.2.0", "0.1.0"): migrate_v2_to_v1,
}


# ─── Version Manager ────────────────────────────────────────────────────────

class VersionManager:
    """Manages version upgrades, downgrades, and data persistence."""

    def __init__(self, base_dir: str | Path = "."):
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / DATA_DIR
        self.version_file = self.base_dir / VERSION_FILE
        self.migration_log = self.base_dir / MIGRATION_LOG
        self.backup_dir = self.base_dir / BACKUP_DIR

    def get_current_version(self) -> str:
        """Get the current installed version."""
        if self.version_file.exists():
            data = json.loads(self.version_file.read_text())
            return data.get("version", CURRENT_VERSION)
        return CURRENT_VERSION

    def get_schema_version(self) -> int:
        """Get the current schema version."""
        if self.version_file.exists():
            data = json.loads(self.version_file.read_text())
            return data.get("schema_version", 1)
        return 1

    def set_version(self, version: str) -> None:
        """Set the current version."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        info = VERSION_REGISTRY.get(version)
        if not info:
            info = VersionInfo(version=version, released_at=time.strftime("%Y-%m-%d"), schema_version=1, data_format="json-v1")
        self.version_file.write_text(json.dumps(info.to_dict(), indent=2))

    def initialize(self) -> None:
        """Initialize version tracking for a new installation."""
        if not self.version_file.exists():
            self.set_version(CURRENT_VERSION)
            self._log_migration("INIT", "0.1.0", "Initial installation")

    def _log_migration(self, direction: str, from_ver: str, to_ver: str, details: str = "") -> None:
        """Log a migration event."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": time.time(),
            "direction": direction,
            "from_version": from_ver,
            "to_version": to_ver,
            "details": details,
        }
        with open(self.migration_log, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def _create_backup(self, version: str) -> Path:
        """Create a backup of all data before migration."""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = self.backup_dir / f"backup_{version}_{int(time.time())}"
        backup_path.mkdir(parents=True, exist_ok=True)

        # Backup keys
        keys_dir = self.data_dir / "keys"
        if keys_dir.exists():
            shutil.copytree(keys_dir, backup_path / "keys")

        # Backup certificates
        certs_dir = self.base_dir / "build" / "certs"
        if certs_dir.exists():
            shutil.copytree(certs_dir, backup_path / "certs")

        # Backup audit log
        audit_log = self.data_dir / "audit.log"
        if audit_log.exists():
            shutil.copy2(audit_log, backup_path / "audit.log")

        # Backup version file
        if self.version_file.exists():
            shutil.copy2(self.version_file, backup_path / "version.json")

        return backup_path

    def _restore_backup(self, backup_path: Path) -> None:
        """Restore from a backup."""
        keys_dir = self.data_dir / "keys"
        backup_keys = backup_path / "keys"
        if backup_keys.exists():
            if keys_dir.exists():
                shutil.rmtree(keys_dir)
            shutil.copytree(backup_keys, keys_dir)

        certs_dir = self.base_dir / "build" / "certs"
        backup_certs = backup_path / "certs"
        if backup_certs.exists():
            if certs_dir.exists():
                shutil.rmtree(certs_dir)
            shutil.copytree(backup_certs, certs_dir)

        backup_audit = backup_path / "audit.log"
        if backup_audit.exists():
            shutil.copy2(backup_audit, self.data_dir / "audit.log")

        backup_version = backup_path / "version.json"
        if backup_version.exists():
            shutil.copy2(backup_version, self.version_file)

    def migrate(self, target_version: str) -> dict:
        """
        Migrate data to a target version.
        Handles both upgrades and downgrades.
        Returns migration result with status and details.
        """
        current = self.get_current_version()
        if current == target_version:
            return {"status": "no-op", "message": f"Already at version {target_version}"}

        if target_version not in VERSION_REGISTRY and target_version != CURRENT_VERSION:
            return {"status": "error", "message": f"Unknown version: {target_version}"}

        # Check for breaking changes
        target_info = VERSION_REGISTRY.get(target_version)
        if target_info and target_info.breaking_changes:
            print(f"  [!] Breaking changes in {target_version}:")
            for change in target_info.breaking_changes:
                print(f"      - {change}")

        # Create backup before migration
        backup_path = self._create_backup(current)

        # Find migration path
        migration_key = (current, target_version)
        if migration_key in MIGRATIONS:
            # Direct migration
            result = MIGRATIONS[migration_key](self.data_dir)
            self.set_version(target_version)
            self._log_migration("MIGRATE", current, target_version, json.dumps(result))
            return {
                "status": "success",
                "from_version": current,
                "to_version": target_version,
                "backup": str(backup_path),
                "changes": result.get("changes", []),
            }
        else:
            # Multi-step migration: find path through intermediate versions
            path = self._find_migration_path(current, target_version)
            if not path:
                # No migration path found -- force version update
                self.set_version(target_version)
                self._log_migration("FORCE", current, target_version, "No migration path, version updated without data changes")
                return {
                    "status": "warning",
                    "from_version": current,
                    "to_version": target_version,
                    "message": "No migration path found. Version updated but data format unchanged.",
                    "backup": str(backup_path),
                }

            # Execute multi-step migration
            all_changes = []
            for i in range(len(path) - 1):
                step_key = (path[i], path[i + 1])
                if step_key in MIGRATIONS:
                    result = MIGRATIONS[step_key](self.data_dir)
                    all_changes.extend(result.get("changes", []))
                self._log_migration("STEP", path[i], path[i + 1])

            self.set_version(target_version)
            self._log_migration("MIGRATE", current, target_version, json.dumps({"changes": all_changes}))
            return {
                "status": "success",
                "from_version": current,
                "to_version": target_version,
                "path": path,
                "backup": str(backup_path),
                "changes": all_changes,
            }

    def _find_migration_path(self, from_ver: str, to_ver: str) -> list[str] | None:
        """Find a migration path between two versions using BFS."""
        known_versions = list(VERSION_REGISTRY.keys())
        if from_ver not in known_versions or to_ver not in known_versions:
            return None

        # Build adjacency graph from migration keys
        graph: dict[str, list[str]] = {v: [] for v in known_versions}
        for (src, dst) in MIGRATIONS:
            if src in graph:
                graph[src].append(dst)

        # BFS
        from collections import deque
        queue = deque([(from_ver, [from_ver])])
        visited = {from_ver}

        while queue:
            current, path = queue.popleft()
            if current == to_ver:
                return path
            for neighbor in graph.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None

    def rollback(self) -> dict:
        """Rollback to the previous version using the latest backup."""
        if not self.backup_dir.exists():
            return {"status": "error", "message": "No backups found"}

        backups = sorted(self.backup_dir.glob("backup_*"))
        if not backups:
            return {"status": "error", "message": "No backups found"}

        latest_backup = backups[-1]
        self._restore_backup(latest_backup)

        # Read version from restored backup
        restored_version = self.get_current_version()
        self._log_migration("ROLLBACK", "unknown", restored_version, f"Restored from {latest_backup.name}")

        return {
            "status": "success",
            "rolled_back_to": restored_version,
            "backup_used": str(latest_backup),
        }

    def list_backups(self) -> list[dict]:
        """List all available backups."""
        if not self.backup_dir.exists():
            return []
        backups = []
        for b in sorted(self.backup_dir.glob("backup_*")):
            parts = b.name.split("_")
            backups.append({
                "name": b.name,
                "version": parts[1] if len(parts) > 1 else "unknown",
                "timestamp": int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0,
                "path": str(b),
            })
        return backups

    def get_migration_history(self) -> list[dict]:
        """Get the full migration history."""
        if not self.migration_log.exists():
            return []
        entries = []
        for line in self.migration_log.read_text().strip().split("\n"):
            if line.strip():
                entries.append(json.loads(line))
        return entries

    def get_version_info(self, version: str | None = None) -> VersionInfo:
        """Get version info for a specific version or current."""
        ver = version or self.get_current_version()
        return VERSION_REGISTRY.get(ver, VersionInfo(version=ver, released_at="unknown", schema_version=1, data_format="json-v1"))

    def list_versions(self) -> list[VersionInfo]:
        """List all known versions."""
        return list(VERSION_REGISTRY.values())

    def validate_data_integrity(self) -> dict:
        """Validate that all data is consistent with the current version."""
        issues = []
        current = self.get_current_version()
        schema = self.get_schema_version()

        # Check version file
        if not self.version_file.exists():
            issues.append("Version file missing")

        # Check key store
        keys_dir = self.data_dir / "keys"
        if keys_dir.exists():
            for key_file in keys_dir.glob("*.key"):
                try:
                    data = json.loads(key_file.read_text())
                    if data.get("version") != schema:
                        issues.append(f"Key file {key_file.name} has schema version {data.get('version')}, expected {schema}")
                except Exception:
                    issues.append(f"Key file {key_file.name} is corrupted")

        # Check certificates
        certs_dir = self.base_dir / "build" / "certs"
        if certs_dir.exists():
            for cert_file in certs_dir.glob("*.cert.json"):
                try:
                    data = json.loads(cert_file.read_text())
                    if data.get("version") != schema:
                        issues.append(f"Certificate {cert_file.name} has schema version {data.get('version')}, expected {schema}")
                except Exception:
                    issues.append(f"Certificate {cert_file.name} is corrupted")

        return {
            "version": current,
            "schema_version": schema,
            "valid": len(issues) == 0,
            "issues": issues,
        }
