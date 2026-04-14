# JR INSTRUCTION: Fork LARQL to dereadi GitHub and Add to Federation Repos

**JR ID:** JR-ADD-LARQL-REPO-APR13-2026
**FROM:** TPM (Flying Squirrel / Stoneclad)
**TO:** IT Triad Jr (`it_triad_jr`)
**PRIORITY:** P2
**DATE:** April 13, 2026

## Context

LARQL (github.com/chrishayuk/larql) has been cloned, patched for Linux, and built on redfin. Council approved (12-1, hash 4c53f9f069f19ef5) as v2.0 research direction. We need our own fork on GitHub with the Linux patches committed.

## TASK 1 — Fork LARQL to dereadi/larql on GitHub

```bash
cd /ganuda/services/larql
gh repo fork chrishayuk/larql --clone=false --org="" --fork-name="larql"
```

If fork already exists or command differs, create a new repo:
```bash
gh repo create dereadi/larql --public --description "LARQL fork — Linux port + governance locking. Query transformer weights as a graph database."
git remote add ganuda git@github.com:dereadi/larql.git
git push ganuda main
```

## TASK 2 — Commit the Linux patches

The two Cargo.toml changes (Apple Accelerate → OpenBLAS) need to be committed:

```bash
cd /ganuda/services/larql
git add crates/larql-compute/Cargo.toml crates/larql-inference/Cargo.toml
git commit -m "Linux port: Apple Accelerate → OpenBLAS static

Swap blas-src from accelerate (macOS-only) to openblas with static
linking. Builds clean on Linux without requiring system libopenblas-dev.

Tested on redfin (Ubuntu, Rust 1.94, cargo build --release).

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
git push ganuda main
```

## TASK 3 — Add LARQL fork to all federation repos list

Add `dereadi/larql` to whatever manifest or documentation tracks federation repositories. Check:
- `/ganuda/.gitmodules` (if using submodules)
- Any repo listing in `/ganuda/docs/` or `/ganuda/config/`
- The ganuda-federation repo if it has a manifest

## Acceptance

- Fork exists at github.com/dereadi/larql
- Linux patches committed with proper attribution
- Federation repo list updated

## What this does NOT do

- Does NOT implement the locking mechanism (separate task)
- Does NOT modify any other repos
- Does NOT push vindex files to GitHub (too large, stay local)
