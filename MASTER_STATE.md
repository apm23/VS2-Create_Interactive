# MASTER_STATE — VS2 / Create Interactive

GitHub code is the implementation source of truth. This file is the durable project-state ledger. Chat is temporary.

## Project
- Repository: `apm23/VS2-Create_Interactive`
- Milestone: `M1 — movement / collision`
- Architecture: Create owns train/carriage gameplay and collision geometry; VS2 supplies moving reference-space/transform foundation; compatibility stays a thin adapter.

## Current reconciled state — 2026-09-15
- project_state: `REAL-USER EXACT-JAR M1 FAILED — AIRBORNE/CARRIAGE-WALL ROOT BOUNDARY OPEN`
- reconciled_head_before_ledger_update: `ebb7f1a675f11bed3ba743a0f3206896a3f3e0a6`
- gameplay_fix_commit: `fb9520946e1041c1dc0a75a82fcae0a260cceec8` (`Bind Phase205 reanchor to selected carriage owner`)
- automated_m1_proof: `34943410005` (`production-world-smoke #752`, SUCCESS)
- owner_diagnostic_run: `34943783606` (SUCCESS: best_supported_streak=22, phase205_selection_mismatches=0)
- final_build_run: `34953958207` (SUCCESS)
- final_verify_run: `34955884046` (SUCCESS)
- tested_final_jar_sha256: `96053e314891495fbb4bf16c446023568fed542497e083083dad7ed420dcd7ef`
- final_ready: `false`
- user_runtime_validation: `FAILED`

## Exact-JAR user runtime evidence — 2026-09-15
The user tested exact final candidate SHA256 `96053e314891495fbb4bf16c446023568fed542497e083083dad7ed420dcd7ef` in real Minecraft/Create runtime and reported:
- floor is hard/solid: PASS;
- grounded walking feels good: PASS;
- walls are soft: FAIL;
- on jump/airborne, player is dragged backward by roughly 2–4 carriages instead of remaining in the moving carriage reference frame: FAIL;
- on turns the player can pass through the wall and be thrown out of the train: FAIL.

This direct runtime evidence overrides automated M1 green. FINAL_READY remains revoked. Do not rebuild/reverify the same implementation and do not ask the user to retest this SHA.

## Root classification / next safe action
The active blocker is `airborne reference-frame/carry + native carriage wall collision ownership during turns`, not grounded floor support. Grounded floor and walking are runtime-proven and now protected.

`next_safe_action`: inspect the existing jump/airborne and carriage wall/turn ownership boundaries read-only. Compare why grounded selected-carriage ownership remains stable while airborne loses carriage-relative motion and why native wall solidity is not retained on turns. Add the smallest read-only instrumentation/root-boundary proof first; do not add gameplay compensation until direct evidence isolates the missing native owner/transform path.

## Protected / FROZEN_GREEN
- Kotlin/bootstrap packaging repair `f3d1335c9fc89283d936af039eba34aa9778bd05`.
- Create train + VS2 coexistence.
- Steam 'n' Rails and Copycats preservation.
- selected-carriage Phase205 ownership binding from `fb952094...` for grounded support.
- exact-JAR grounded floor solidity and grounded walking for SHA `96053e...`.

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
Automated proof can advance a candidate through build and integrity verification, but FINAL_READY requires the exact final JAR to pass real-user runtime M1 and the local watchdog runtime gate to bind to that exact SHA. Direct runtime failure always overrides CI green.

## Fresh-chat/watchdog protocol
1. Inspect actual HEAD.
2. Read this file completely and reconcile its recorded head with actual HEAD.
3. Inspect only latest relevant Actions evidence for the active blocker.
4. Respect FROZEN_GREEN and FAILED_HYPOTHESES.
5. Execute next_safe_action; do not stop at narration.
6. If a relevant workflow is queued/in_progress, HOLD.
7. Never terminal-finalize from CI alone.
