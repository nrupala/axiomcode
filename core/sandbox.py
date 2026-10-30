"""AxiomCode — OS-level containment for Lean elaboration of untrusted code.

Second line of defence behind core/proof_policy.py. The policy screen
rejects the constructs we know run code at elaboration time; this module
assumes the screen will one day miss something and contains the damage.

Modes (AXIOMCODE_SANDBOX):
  required  (set by the hosted API) — run under bubblewrap with no
            network, a read-only root, a private /tmp, and the project dir
            as the only writable path. If bubblewrap is missing, REFUSE to
            run: fail closed.
  auto      (library default) use bubblewrap when present, otherwise rlimits only, and say so
            in the log. For local/dev use.
  none      rlimits only. For tests and trusted local runs.

Resource limits apply in every mode (POSIX only): address space, process
count, file size and CPU seconds — so a fork bomb, a memory bomb or a
disk-filling proof is bounded even when bubblewrap is unavailable.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

MODE_ENV = "AXIOMCODE_SANDBOX"
DEFAULT_MODE = "auto"  # the hosted API sets "required" (services/api/verify_service.py)

MEM_LIMIT_BYTES = int(os.environ.get("AXIOMCODE_SANDBOX_MEM_BYTES", str(8 * 1024**3)))
NPROC_LIMIT = int(os.environ.get("AXIOMCODE_SANDBOX_NPROC", "256"))
FSIZE_LIMIT_BYTES = int(os.environ.get("AXIOMCODE_SANDBOX_FSIZE_BYTES", str(512 * 1024**2)))
CPU_LIMIT_S = int(os.environ.get("AXIOMCODE_SANDBOX_CPU_S", "900"))


class SandboxUnavailableError(RuntimeError):
    """`required` mode was requested but no sandbox could be built."""


def mode() -> str:
    m = os.environ.get(MODE_ENV, DEFAULT_MODE).strip().lower()
    return m if m in {"required", "auto", "none"} else DEFAULT_MODE


def _limits() -> None:  # pragma: no cover - runs in the child process
    import resource

    for res, val in (
        (resource.RLIMIT_AS, MEM_LIMIT_BYTES),
        (resource.RLIMIT_NPROC, NPROC_LIMIT),
        (resource.RLIMIT_FSIZE, FSIZE_LIMIT_BYTES),
        (resource.RLIMIT_CPU, CPU_LIMIT_S),
    ):
        try:
            resource.setrlimit(res, (val, val))
        except (ValueError, OSError):
            pass
    os.setsid()


def preexec():
    """preexec_fn for subprocess.run (None on non-POSIX platforms)."""
    return _limits if os.name == "posix" else None


def wrap(cmd: list[str], project_dir: str | Path) -> tuple[list[str], str]:
    """Return (command, note). The note is appended to the verification log
    so every certificate's log says how the run was contained."""
    m = mode()
    bwrap = shutil.which("bwrap")
    if m != "none" and bwrap and sys.platform.startswith("linux"):
        proj = str(Path(project_dir).resolve())
        wrapped = [
            bwrap,
            "--unshare-all",  # includes network: no egress at all
            "--die-with-parent",
            "--new-session",
            "--ro-bind",
            "/",
            "/",  # whole host read-only
            "--dev",
            "/dev",
            "--proc",
            "/proc",
            "--tmpfs",
            "/tmp",
            "--bind",
            proj,
            proj,  # the only writable path
            "--chdir",
            proj,
            "--setenv",
            "HOME",
            "/tmp",
            "--",
            *cmd,
        ]
        return wrapped, f"sandbox: bubblewrap (no network, read-only root, rw={proj}) + rlimits"
    if m == "required":
        raise SandboxUnavailableError(
            "AXIOMCODE_SANDBOX=required but bubblewrap (bwrap) is not available on this host; "
            "refusing to elaborate untrusted Lean without containment"
        )
    return cmd, f"sandbox: rlimits only (mode={m}; bubblewrap {'absent' if not bwrap else 'unused'})"
