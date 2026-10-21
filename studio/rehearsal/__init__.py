"""The ep02 proof harness (docs/audit/2026-10-21_ep02_proof/DESIGN.md): a rehearsal runs the
real step code against a sandbox library, fenced so it can never write the real one.

Nothing here does anything unless a sandbox manifest exists: `activate.install()` is the
one line studio/__init__.py calls, and it returns at once without a manifest."""
