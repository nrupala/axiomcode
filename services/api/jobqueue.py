"""AxiomCode proof queue (gate F-AX-5, owner's directive 2026-10-23).

Certification requests are processed in the order received. When every
proof slot is busy, a submission does not pile onto the host or wait in
silence: it joins a durable FIFO queue and the caller gets a job id
and a position it can check (GET /verify/jobs/{job_id}).

Admission is owned here, for both the synchronous and the queued path,
so the invariants cannot drift:

  * at most `global_slots` proofs run at once on this host
    (AXIOMCODE_MAX_GLOBAL_PROOFS, default 4 — the host has 4 cores);
  * at most `per_key_limit` proofs per API key run at once
    (AXIOMCODE_MAX_CONCURRENT_PROOFS, default 2 — the bound the old
    per-key ConcurrencyGate enforced);
  * fairness: a new submission may start immediately only when nobody
    is waiting; otherwise it takes its place at the back of the line.

Jobs live in the same SQLite database as the durable store, in their
own table (JobStore below — store.py itself is untouched by this
package). A job's submitted code is cleared from the database the
moment the job finishes; the code hash and the result are kept. If
the process restarts, jobs left in `running` return to `queued` and
drain in order — no accepted job is silently dropped.

The admission counters are per-process by design (single-host launch
topology, the same bound limits.py documents); the database is what
makes positions and results durable across the process.
"""

import hashlib
import json
import os
import secrets
import sqlite3
import threading
import time
from pathlib import Path

GLOBAL_PROOF_SLOTS = int(os.environ.get("AXIOMCODE_MAX_GLOBAL_PROOFS", "4"))
PER_KEY_PROOF_LIMIT = int(os.environ.get("AXIOMCODE_MAX_CONCURRENT_PROOFS", "2"))

QUEUE_NOTE = (
    "Your request is in line and will be verified in order. Check its position and result at GET /verify/jobs/{job_id}."
)

_JOBS_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    key_hash TEXT NOT NULL,
    code TEXT NOT NULL,
    code_sha256 TEXT NOT NULL,
    max_attempts INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'queued',
    result_json TEXT,
    error TEXT,
    created_at INTEGER NOT NULL,
    started_at INTEGER,
    finished_at INTEGER
);
CREATE INDEX IF NOT EXISTS jobs_status_created ON jobs (status, created_at, id);
"""


class JobStore:
    """Durable FIFO job table in the service's SQLite database.

    Opens its own connection (WAL + busy timeout) so store.py — the
    crown-jewel file — needs no changes for the queue. All writes are
    short transactions under a lock, the same discipline as Store.
    """

    def __init__(self, db_path: str | Path | None = None):
        from store import DEFAULT_DB

        self.path = Path(db_path or DEFAULT_DB)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._db = sqlite3.connect(self.path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA busy_timeout=5000")
        self._db.executescript(_JOBS_SCHEMA)
        self._db.commit()

    def close(self) -> None:
        with self._lock:
            self._db.close()

    def create_job(self, key_hash: str, code: str, max_attempts: int) -> str:
        job_id = "job_" + secrets.token_urlsafe(18)
        with self._lock:
            self._db.execute(
                "INSERT INTO jobs (id, key_hash, code, code_sha256, max_attempts, status, created_at)"
                " VALUES (?, ?, ?, ?, ?, 'queued', ?)",
                (
                    job_id,
                    key_hash,
                    code,
                    hashlib.sha256(code.encode()).hexdigest(),
                    max_attempts,
                    int(time.time()),
                ),
            )
            self._db.commit()
        return job_id

    @staticmethod
    def _row(r) -> dict | None:
        if r is None:
            return None
        job = dict(r)
        job["result"] = json.loads(job.pop("result_json")) if job.get("result_json") else None
        return job

    def get_job(self, job_id: str) -> dict | None:
        with self._lock:
            r = self._db.execute("SELECT rowid AS _rowid, * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return self._row(r)

    def set_job_status(self, job_id: str, status: str, result: dict | None = None, error: str | None = None) -> None:
        """Transition a job. Terminal transitions clear the submitted
        code — the store keeps the hash and the outcome, not the code."""
        now = int(time.time())
        with self._lock:
            if status == "running":
                self._db.execute(
                    "UPDATE jobs SET status = 'running', started_at = ? WHERE id = ?",
                    (now, job_id),
                )
            elif status in ("done", "failed"):
                self._db.execute(
                    "UPDATE jobs SET status = ?, result_json = ?, error = ?, finished_at = ?, code = '' WHERE id = ?",
                    (
                        status,
                        json.dumps(result, sort_keys=True) if result is not None else None,
                        error,
                        now,
                        job_id,
                    ),
                )
            else:
                self._db.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))
            self._db.commit()

    def queued_jobs(self) -> list[dict]:
        # FIFO order is insertion order (rowid): created_at has only
        # second resolution and job ids are random tokens, so neither
        # can order two jobs submitted in the same second.
        with self._lock:
            rows = self._db.execute(
                "SELECT rowid AS _rowid, * FROM jobs WHERE status = 'queued' ORDER BY rowid"
            ).fetchall()
        return [job for job in (self._row(r) for r in rows) if job is not None]

    def job_position(self, job_id: str) -> int | None:
        """1-based place in line among waiting jobs, or None when the
        job is not waiting (running / finished / unknown)."""
        job = self.get_job(job_id)
        if job is None or job["status"] != "queued":
            return None
        with self._lock:
            r = self._db.execute(
                "SELECT COUNT(*) AS n FROM jobs WHERE status = 'queued' AND rowid <= ?",
                (job["_rowid"],),
            ).fetchone()
        return int(r["n"])

    def count_jobs(self, status: str) -> int:
        with self._lock:
            r = self._db.execute("SELECT COUNT(*) AS n FROM jobs WHERE status = ?", (status,)).fetchone()
        return int(r["n"])

    def reset_running_jobs(self) -> None:
        """Startup recovery: a job left `running` by a dead process
        goes back in line. No accepted job is dropped."""
        with self._lock:
            self._db.execute("UPDATE jobs SET status = 'queued' WHERE status = 'running'")
            self._db.commit()


class ProofQueue:
    """FIFO admission + background drain for verification jobs.

    `runner(job)` is called by the dispatcher thread for each queued
    job and must return the verification response dict. The immediate
    path in the API layer uses acquire_immediate()/release() so both
    paths share one set of counters.
    """

    def __init__(
        self, jobs: JobStore, runner, global_slots: int = GLOBAL_PROOF_SLOTS, per_key_limit: int = PER_KEY_PROOF_LIMIT
    ):
        self.jobs = jobs
        self.runner = runner
        self.global_slots = global_slots
        self.per_key_limit = per_key_limit
        self._cond = threading.Condition()
        self._in_flight = 0
        self._per_key: dict[str, int] = {}
        self._thread: threading.Thread | None = None

    def _can_start_locked(self, key_hash: str) -> bool:
        return self._in_flight < self.global_slots and self._per_key.get(key_hash, 0) < self.per_key_limit

    def acquire_immediate(self, key_hash: str) -> bool:
        """Reserve a slot for a synchronous run. Refused when any job
        is already waiting (no queue-jumping) or no slot is free."""
        with self._cond:
            if self.jobs.count_jobs("queued") > 0:
                return False
            if not self._can_start_locked(key_hash):
                return False
            self._in_flight += 1
            self._per_key[key_hash] = self._per_key.get(key_hash, 0) + 1
            return True

    def release(self, key_hash: str) -> None:
        with self._cond:
            self._in_flight = max(self._in_flight - 1, 0)
            n = self._per_key.get(key_hash, 0)
            if n <= 1:
                self._per_key.pop(key_hash, None)
            else:
                self._per_key[key_hash] = n - 1
            self._cond.notify_all()

    def enqueue(self, key_hash: str, code: str, max_attempts: int) -> tuple[str, int]:
        """Persist a job and return (job_id, 1-based position)."""
        job_id = self.jobs.create_job(key_hash, code, max_attempts)
        position = self.jobs.job_position(job_id)
        assert position is not None  # a just-created job is always waiting
        with self._cond:
            self._cond.notify_all()
        return job_id, position

    def start(self) -> None:
        """Recover interrupted jobs and start the drain thread."""
        self.jobs.reset_running_jobs()
        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._drain_loop, name="ax-proof-queue", daemon=True)
            self._thread.start()

    def _next_runnable_locked(self):
        """Oldest queued job whose key has a free per-key slot."""
        for job in self.jobs.queued_jobs():
            if self._per_key.get(job["key_hash"], 0) < self.per_key_limit:
                return job
        return None

    def _drain_loop(self) -> None:
        while True:
            with self._cond:
                job = None
                while job is None:
                    if self._in_flight < self.global_slots:
                        job = self._next_runnable_locked()
                    if job is None:
                        self._cond.wait(timeout=5.0)
                self.jobs.set_job_status(job["id"], "running")
                self._in_flight += 1
                kh = job["key_hash"]
                self._per_key[kh] = self._per_key.get(kh, 0) + 1
            try:
                result = self.runner(job)
                self.jobs.set_job_status(job["id"], "done", result=result)
            except Exception as e:  # a failed job must never kill the drain
                self.jobs.set_job_status(job["id"], "failed", error=f"{type(e).__name__}: {e}")
            finally:
                self.release(job["key_hash"])
