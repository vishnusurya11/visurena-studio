# Check back

Things parked to come back to, newest first. Each line says what, why it is parked, and what closes it.
Strike a line through (`~~...~~`) with the date when it closes; never delete one.

## Open

- **2026-10-29 Node-pack cleanup.** ~45 custom-node packs no workflow references (about 2.5 GB), plus the failing
  and disabled ones: ComfyUI-LTXVideo (fails to import); `.disabled`, `crt-nodes.disabled`, `songgeneration.disabled`,
  `ComfyUI-GGUF-FantasyTalking.disabled`, `ComfyUI-FlashVSR_Ultra_Fast.disabled`, `ace-step.disabled`; and the
  not-loaded Anomalous_Model_Browser, ComfyUI-Env-Manager, comfyui-imgloader. Owner: do not delete for now. Closes on
  the owner's go; ComfyUI must be idle (restart).
- **2026-10-29 Spark-H3 on 0.43.** The take graphs left Spark (SM89 sparse attention) for CK int8 attention because 0.43
  needs comfy-kitchen 0.2.40. Same speed measured on T14. Check back when Spark-H3 ships a 0.2.40-compatible kitchen
  and bench it again (it was -11 % warm on 0.41.2).
- **2026-10-29 2K regen speed.** Each regen job reloads H3 (~63 s) after the 15 GB text encoder evicts it. To try:
  batch by model (all encodes, then all sampling), the Sol-H3-VAE decode (~3x faster; needs ComfyUI master past 0.43,
  PR 17411), the native H3 latent upscaler (master #17412).
- **2026-10-29 2K regen arms not yet benched.** The official 3-step schedule, the rank-16 LoRA, identity scores against
  the sheets on more takes, wide shots at a lower denoise.
- **2026-10-29 Windows Update auto-restart.** Caused the 4.7 h gap in the Kawajiri ep01 run (2026-10-20). Needs the owner's
  approval for a no-auto-restart policy and the autopilot task at boot.
- **2026-10-29 ep05 public shots.** T02/T03/T06 faults on the published ep05 (PF3YzaSd1vA): owner's call whether to fix.
- **2026-10-29 Sheet-vs-row hard check.** A sheet that contradicts its cast row (offered after the Poole fix): not built.
