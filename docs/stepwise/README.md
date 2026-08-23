# stepwise — Layer 1

**Status: not designed yet.** Nothing here is decided beyond what
[../ARCHITECTURE.md](../ARCHITECTURE.md) already locks.

The durable, cost-gated step runner. The one component written in-house rather than
adopted, because no agent framework's persistence treats **credits spent** and
**artifact-on-disk** as first-class resume keys.

## Scope

- Step identity and `input_hash`
- The artifact + credit ledger
- `Gate` and its policies (`APPROVE` / `REJECT` / `ESCALATE`)
- `ArtifactStore` and `StepStore` protocols
- Resume, retry, and park semantics

## Intended shape

A standalone package at `packages/stepwise`, imported by the studio — not buried inside
`studio_orchestrator/`. It is generalizable beyond this repo and is the publishable
artifact of the project.

## To be written

Step identity, gate policy, and ledger schema on paper before any code. This is the
expensive-to-reverse layer.
