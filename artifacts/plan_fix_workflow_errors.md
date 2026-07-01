# Plan: Fix JoJoTrading GitHub Actions workflow errors

## Scope
Investigate and fix current failing workflows for `Jnocode/JoJoTrading` on branch `main`.

## Evidence sources
- GitHub Actions recent runs via `gh run list`
- Failed job logs via `gh run view --log-failed`
- Local workflow YAML and repository code

## Steps
1. Capture latest failed workflow logs under `artifacts/logs/`.
2. Identify root cause per workflow/job.
3. Reproduce formatting/lint/test failures locally where practical.
4. Patch smallest root-cause changes only.
5. Run local verification gates.
6. Commit and push fixes.
7. Re-check GitHub Actions latest run status/logs.
