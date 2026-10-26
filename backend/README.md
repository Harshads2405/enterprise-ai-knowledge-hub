# Backend

FastAPI backend foundation.

Implementation will be added phase-by-phase.

## Evaluation organization

Evaluation runners require an explicit organization scope. Set
`EVALUATION_ORGANIZATION_ID` to a positive integer before running a runner,
for example in PowerShell: `$env:EVALUATION_ORGANIZATION_ID = "12"`.
Runners fail closed when it is absent or invalid.
