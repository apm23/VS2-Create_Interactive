# MASTER_STATE — VS2 / Create Interactive

GitHub code is the implementation source of truth. This file is the durable project-state ledger. Chat is temporary.

## Project
- Repository: `apm23/VS2-Create_Interactive`
- Milestone: `M1 — movement / collision`
- Architecture: Create owns train/carriage gameplay and collision geometry; VS2 supplies moving reference-space/transform foundation; compatibility stays a thin adapter.

## Current reconciled state — 2026-09-15
- project_state: `AUTOMATED_M1_GREEN_AFTER_SELECTED-OWNER FIX — FINAL_READY STILL REVOKED`
- reconciled_head_before_ledger_update: `233e7bbf9cbef726942257f5a80f2e295bc5b7fc`
- gameplay_fix_commit: `fb9520946e1041c1dc0a75a82fcae0a260cceec8` (`Bind Phase205 reanchor to selected carriage owner`)
- proof_trigger_commit: `233e7bbf9cbef726942257f5a80f2e295bc5b7fc` (inert trigger only; no gameplay change)
- latest_current-head_production_proof: `34943410005` (`production-world-smoke #752`, head `233e7bbf...`, SUCCESS)
- owner_diagnostic_run: `34943783606` (`m1-floor-owner-diagnostic #5`, SUCCESS)
- owner_diagnostic_result: `best_supported_streak=22, best_ticks=20-41, phase205_selection_mismatches=0, read_only=true`
- owner_binding_state: `GREEN/FROZEN unless direct new evidence regresses it`
- final_ready: `false`
- user_runtime_validation: `FAILED on older final JAR SHA256 7912822c8aeee0adb461d222cfa9a4aeaf083e8253478a1f4aaf1dd9fab8bc51; this predates the selected-owner fix and remains authoritative against that old candidate only.`
- next_safe_action: `Build a fresh final candidate from the current selected-owner implementation, then integrity-verify it. Do not declare FINAL_READY until the user tests that exact new JAR and the local runtime gate is bound to its exact SHA-256.`

## Current automated M1 proof — production #752
Run `34943410005` checked out exact head `233e7bbf9cbef726942257f5a80f2e295bc5b7fc` and completed successfully.
Its M1 verifier reported:
- carry continuity passed;
- forward/supported sprinting passed;
- reverse passed;
- right strafe passed;
- `floor_solid=true` with 16 floor samples and zero Y span;
- `wall_solid=true` with a three-frame wall impact proof;
- `ceiling_solid=true`;
- `speed_change_stable=true`;
- native jump requested -> airborne -> natural landing passed;
- `natural_fall=true`, `replay_free=true`, `recovery_free=true`;
- 9 post-land stable samples.

This is strong automated evidence for the current implementation but is NOT terminal real-user acceptance.

## Owner/root-boundary resolution
Earlier read-only owner diagnostic found Phase205 reanchor could use a sibling carriage rather than the same-tick Gate E selected carriage. Commit `fb952094...` binds the existing pre-OBB external-frame reanchor to the same-tick selected Create carriage and rejects sibling ownership. It does not add floor clamps, fake gravity, synthetic carry velocity, teleport/setPos carry, or a second collision authority.

The subsequent diagnostic `34943783606` reports 22 consecutive supported samples and zero Phase205/selected-carriage mismatches. Therefore the selected-owner seam is GREEN and must not be tuned further without direct regression evidence.

Diagnostic #5 downloaded artifact from older production run `34943397932`; that source run itself failed a later verifier path, but its artifact still independently proved the owner-binding diagnostic criteria. More importantly, exact-current-head production run `34943410005` separately completed SUCCESS and proved the full automated M1 path. Do not confuse the older source-run conclusion with the current-head production result.

## Direct user runtime regression — retained hard gate
On 2026-09-14 the user tested the then-final runtime-fixed JAR and supplied direct runtime evidence showing the player sinking into/below the Create carriage floor. That revoked FINAL_READY for SHA256 `7912822c8aeee0adb461d222cfa9a4aeaf083e8253478a1f4aaf1dd9fab8bc51`.

The new selected-owner implementation has not yet been built, integrity-verified, and tested by the user as an exact final JAR. Therefore:
- do not restore FINAL_READY from CI;
- do not ask the user to retest the obsolete JAR;
- build and verify a fresh candidate first;
- after that, user runtime confirmation is mandatory.

## Historical floor-order evidence
Production #742 (`34892811793`) showed vanilla `Entity.move` applying a downward step before Create's later collision pass, after which support was lost. This was valid evidence at that revision. Later owner diagnostics isolated sibling/double-owner divergence at the reference-frame boundary, and the selected-owner fix now has current-head automated floor/locomotion/jump proof. Do not reintroduce speculative Entity.move floor patches unless the fresh exact candidate produces new direct evidence of penetration.

## Protected / FROZEN_GREEN
- Kotlin/bootstrap packaging repair `f3d1335c9fc89283d936af039eba34aa9778bd05`.
- Create train + VS2 coexistence.
- Steam 'n' Rails and Copycats preservation.
- selected-carriage Phase205 ownership binding from `fb952094...`.
- current automated forward/reverse/strafe/sprint/jump/floor/wall/ceiling paths unless direct evidence regresses them.

## FAILED_HYPOTHESES / anti-loop — DO NOT REINTRODUCE WITHOUT NEW DIRECT EVIDENCE
- `EXACT_SHAPES_LOCALPLAYER_0fa4aa`.
- generic frame-lease/replay/carry extension.
- synthetic carry velocity / fake inertia compensation.
- fake gravity.
- manual floor/wall clamps or floor-only collision workaround.
- per-tick teleport/setPos carry.
- harness mutation used to manufacture success.
- jump-input tuning without jump-specific evidence.
- sprint/reverse/strafe timing tuning as a floor-support fix.
- broad sibling/global suppression instead of direct owner identity.
- floor-normal-only correction.
- near-zero total local XYZ movement as locomotion prerequisite.
- duplicate Create/VS2 authority/state.

## Architecture contract
Forbidden: fake gravity, synthetic carry velocity, inertia compensation, manual wall clamp, floor-only collision workaround, per-tick teleport/setPos carry, duplicate authority/state, and workaround chains hiding Create+VS2 double ownership.

Preferred order: native Create/Minecraft collision -> authoritative VS2/Create transform -> remove duplicate ownership -> thin adapter.

## Finalization policy — HARD USER RUNTIME GATE
Automated proof can advance a candidate through build and integrity verification. `FINAL_READY` is allowed only when ALL are true:
1. fresh final candidate built from the current implementation;
2. artifact identity/integrity checks pass;
3. no implementation regression is known;
4. user tests that exact candidate in real Minecraft and confirms M1 behavior;
5. watchdog local `USER_RUNTIME_GREEN.txt` is bound to that exact candidate's `final_jar_sha256`.

If CI is green but 4+5 are absent, FINAL_READY is forbidden.

## Fresh-chat/watchdog protocol
1. Inspect actual HEAD.
2. Read this file completely and reconcile its recorded head with actual HEAD.
3. Inspect only latest relevant Actions evidence for the active next step.
4. Respect FROZEN_GREEN and FAILED_HYPOTHESES.
5. Execute `next_safe_action`; do not stop at narration.
6. If a relevant workflow is queued/in_progress, HOLD.
7. Never terminal-finalize from CI alone.
