# Deployment artefacts — revocation snapshot reissue (Slice 4 S1)

These units carry the scheduled leg of the snapshot publication duty
(design §4.1) for the production API service. They live here, beside
the service code they run, and are installed on the service host at
deploy time — nothing in this directory is active until the deploy
step installs it.

| File | Installs as |
|---|---|
| `axiomcode-snapshot-reissue.service` | `/etc/systemd/system/axiomcode-snapshot-reissue.service` |
| `axiomcode-snapshot-reissue.timer` | `/etc/systemd/system/axiomcode-snapshot-reissue.timer` |

Install (deploy step, on the service host):

```bash
sudo cp axiomcode-snapshot-reissue.service axiomcode-snapshot-reissue.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now axiomcode-snapshot-reissue.timer
```

## AXIOMCODE_SNAPSHOT_DIR — set explicitly, in both environments

The publication duty is armed by configuration, not by code defaults.
`snapshot.py`'s reissue path and the `store.py` revoke hook act only
when `AXIOMCODE_SNAPSHOT_DIR` is set; unset, the event leg is a no-op
by design. The code-level default in `verify_api.py` (the CA key
file's directory) is a fallback for the read path only — it is not
the arming mechanism. The deploy therefore sets the variable
explicitly in **both** environments, naming the production state
directory (the value below is the production layout; the variable
name and the two locations are what this package fixes):

1. **The API service environment** — `axiomcode-prod.service` gains:

   ```ini
   Environment=AXIOMCODE_SNAPSHOT_DIR=/home/ubuntu/axiomcode-prod/state
   ```

2. **The operator-CLI environment** — the environment the operator
   runs `services/api/store.py` under. The state directory's
   environment file (`/home/ubuntu/axiomcode-prod/state/prod.env`,
   the `EnvironmentFile` both production services already load)
   gains:

   ```ini
   AXIOMCODE_SNAPSHOT_DIR=/home/ubuntu/axiomcode-prod/state
   ```

   and the operator's shell sources that file for CLI runs, so a
   `store.py revoke …` in an interactive session carries the same
   setting the services have.

The reissue service in this directory already sets the variable
explicitly for the scheduled leg, so all three legs of the duty —
revocation event, weekly timer, on-read bootstrap — resolve to the
one snapshot directory the deploy names.
