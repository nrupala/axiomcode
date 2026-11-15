> Canonical: https://axiom-code.com/docs/reference/status-schema/ · Type: Reference · Audience: Developers, ops, regulators · Role packs: Developers · Ops · Regulators · Version: Docs set 2026-11-14 · Last verified: 2026-11-14 · Source: site/status_data.py (canonical source)

# Status schema

[status.json](/status.json) is the machine-readable form of the [status page](/status/) — both generated from one canonical source, along with the service record's `surfaces[]` and the llms.txt status section.

## Document shape

```
{
  "meta": {
    "service": "AxiomCode",
    "as_of": "2026-11-14",
    "timezone": "America/Edmonton",
    "source": "site/status_data.py",
    "status_page": "https://axiom-code.com/status/"
  },
  "surfaces": [ { "surface_id": "rest_api", "name": "REST API",
    "availability": "live", "lifecycle": "in_soak",
    "public_since": "2026-11-09", "graduates_on": "2026-11-16",
    "canonical_url": "https://api.axiom-code.com",
    "summary": "…", "evidence": [{"label": "…", "url": "…"}],
    "known_limits": ["…"] } ]
}
```

## Vocabularies

| Field | Values |
| --- | --- | --- |
| availability | live · paused · unavailable — can you use it now? |
| lifecycle | live · paused · in_soak · in_design · not_built — where it stands in its release process. |

The two fields are independent by design: `live` + `in_soak` is the normal state of a recent release. `graduates_on` is a scheduled decision date, present only while a soak is open; the graduation itself is recorded in the [changelog](/changelog/) when the gate decides.

## Rules for consumers

- Read `meta.as_of` before trusting a cached copy.

- Absence is information: a surface not in the list does not exist; an unavailable surface is listed, never omitted.

- CI drift checks fail our build when any rendering disagrees with the source — if you ever catch a disagreement, that is a reportable error ([GitHub Issues](https://github.com/nrupala/axiomcode/issues)).
