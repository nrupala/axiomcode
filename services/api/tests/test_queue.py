"""Queue behaviour (gate F-AX-5) — a submission that cannot start
immediately joins a durable FIFO queue and returns a position the
caller can check, instead of a silent wait or an unbounded pile-on.

The Lean prover is stubbed like the wiring tests. Queueing is made
deterministic by holding the proof slots directly through the queue's
own admission API — the same state a busy host would be in.
"""

import time

import pytest
import verify_api
from fastapi.testclient import TestClient
from store import hash_api_key

CODE = "theorem t : True := trivial"


def _fast_search(writer, proj, code, *args, **kwargs):
    writer(code)
    return True, code, 1, "stubbed prover log"


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(verify_api, "iterative_proof_search", _fast_search)
    monkeypatch.setattr(verify_api, "lean_version", lambda: "lean-test")
    monkeypatch.setattr(verify_api.QUEUE, "global_slots", 1)
    verify_api.QUEUE.start()
    return TestClient(verify_api.app)


def _wait_for_status(client, job_id, auth, want, timeout=10.0):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        r = client.get(f"/verify/jobs/{job_id}", headers=auth)
        assert r.status_code == 200
        last = r.json()
        if last["status"] == want:
            return last
        time.sleep(0.05)
    raise AssertionError(f"job {job_id} never reached {want}: last={last}")


def test_submission_queues_with_position_and_drains(client):
    key1 = verify_api.STORE.create_api_key("queue-first")
    key2 = verify_api.STORE.create_api_key("queue-second")
    auth1, auth2 = {"X-Api-Key": key1}, {"X-Api-Key": key2}

    # Hold the only proof slot: the host is busy.
    assert verify_api.QUEUE.acquire_immediate("filler-key-hash") is True
    try:
        # A submission now cannot start — it queues, with a position.
        r = client.post("/verify", json={"code": CODE}, headers=auth1)
        assert r.status_code == 202
        body = r.json()
        assert body["status"] == "queued"
        assert body["position"] == 1
        job1 = body["job_id"]

        # A second submission takes the next place in line (fairness:
        # it may not jump the queue even though it is a different key).
        r = client.post("/verify", json={"code": CODE}, headers=auth2)
        assert r.status_code == 202
        assert r.json()["position"] == 2
        job2 = r.json()["job_id"]

        # Positions are checkable by the owning key…
        r = client.get(f"/verify/jobs/{job1}", headers=auth1)
        assert r.status_code == 200
        assert r.json()["status"] == "queued"
        assert r.json()["position"] == 1

        # …and invisible to any other key.
        r = client.get(f"/verify/jobs/{job1}", headers=auth2)
        assert r.status_code == 404
        r = client.get("/verify/jobs/job_nonexistent", headers=auth1)
        assert r.status_code == 404
    finally:
        verify_api.QUEUE.release("filler-key-hash")

    # Once the host frees up, the queue drains in order and results
    # are retrievable by their owners.
    done1 = _wait_for_status(client, job1, auth1, "done")
    assert done1["result"]["verified"] is True
    assert done1["result"]["certificate"] is None  # trial: no certificate
    done2 = _wait_for_status(client, job2, auth2, "done")
    assert done2["result"]["verified"] is True

    # The submitted code is not retained after completion.
    job = verify_api.JOBS.get_job(job1)
    assert job["code"] == ""
    assert job["code_sha256"]


def test_payment_required_never_queues(client):
    key = verify_api.STORE.create_api_key("queue-broke")
    auth = {"X-Api-Key": key}
    key_hash = hash_api_key(key)
    # Exhaust the trial without running proofs: record trial meter rows.
    import billing

    for _ in range(verify_api.TRIAL_CASES):
        billing.meter(verify_api.STORE, key_hash, "0" * 64, True, 0.1, trial=True)
    r = client.post("/verify", json={"code": CODE}, headers=auth)
    assert r.status_code == 402
    assert verify_api.JOBS.count_jobs("queued") == 0


def test_immediate_path_still_synchronous(client):
    # With slots free and nobody waiting, /verify answers inline as
    # it always has — the queue changes nothing for an unloaded host.
    key = verify_api.STORE.create_api_key("queue-immediate")
    r = client.post("/verify", json={"code": CODE}, headers={"X-Api-Key": key})
    assert r.status_code == 200
    assert r.json()["verified"] is True
