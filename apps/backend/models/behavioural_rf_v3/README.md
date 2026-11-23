# Behavioural Random Forest v3 — Model Provisioning

## Purpose

This directory contains the deployment location for the frozen behavioural Random Forest v3 model used for optional shadow inference.

The serialized model is deliberately excluded from Git and Docker build contexts.

## Approved artifact

- Filename: `model.joblib`
- Model: `behavioural_random_forest_v3`
- Feature schema: Frozen behavioural v2 schema (22 features)
- Decision threshold: `0.6244841045172164`
- SHA-256: `a73683e95d48cfe8d98fbc24dd58baca5063ce46b7d23dbf898c54081ce8a53f`

## Provisioning

1. Obtain the original frozen artifact from the project's trusted, access-controlled research artifact storage.
2. Place it at `apps/backend/models/behavioural_rf_v3/model.joblib`.
3. Verify its SHA-256 checksum before enabling shadow inference.

On macOS:

```bash
shasum -a 256 apps/backend/models/behavioural_rf_v3/model.joblib
```

On Linux:

```bash
sha256sum apps/backend/models/behavioural_rf_v3/model.joblib
```

The digest must match the approved value above exactly.

Never download or deserialize an untrusted `.joblib` file. Python pickle-based serialization can execute arbitrary code during loading.

## Docker deployment

The development Compose configuration bind-mounts `apps/backend` to `/app`, so a locally provisioned artifact is accessible to the backend container.

Production images intentionally exclude the model. A production deployment must supply the verified artifact through a trusted, read-only runtime mount or an equivalent controlled provisioning mechanism.

## Operational safety

- `BEHAVIOURAL_RF_SHADOW_ENABLED=false` by default.
- Missing or invalid artifacts must produce an unavailable inference result.
- Shadow predictions must not generate alerts, block authentication or replace the existing detection engine.
- The frozen model and feature schema must not be retrained or modified as part of provisioning.

The artifact must be independently validated before enabling shadow mode in a new environment.