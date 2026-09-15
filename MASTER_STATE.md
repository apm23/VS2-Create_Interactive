# MASTER_STATE — VS2 / Create Interactive

GitHub code is the implementation source of truth. This file is the durable project-state ledger. Chat is temporary.

## Project
- Repository: `apm23/VS2-Create_Interactive`
- Milestone: `M1 — movement / collision`
- HARD architecture: Create owns train/carriage gameplay and collision geometry. VS2 must be the actual continuous moving reference-space/transform foundation for player body/camera. Compatibility remains a thin adapter; merely calling an EntityDragger helper after Create movement is not sufficient.

## Current reconciled state — 2026-09-15
- project_state: `ROOT_REDESIGN — CURRENT ADAPTER PROVEN CONTACT/LEASE REANCHOR, NOT CONTINUOUS VS2 REFERENCE OWNERSHIP`
- ledger_basis_head: `6e079d62d0d30e8508ad825ef80791088fa28e5c`
- architecture_diagnostic_commit: `6e079d62d0d30e8508ad825ef80791088fa28e5c` (`Add VS2 reference-frame ownership diagnostic`)
- architecture_diagnostic_run: `34963733838` — SUCCESS
- architecture_diagnostic_result: `current_adapter_is_contact/lease_reanchor_not_continuous_vs2_reference_space`
- gameplay_fix_commit: `fb9520946e1041c1dc0a75a82fcae0a260cceec8` (`Bind Phase205 reanchor to selected carriage owner`)
- automated_m1_proof: `34943410005` — historical automated GREEN, overridden by direct runtime failure
- owner_diagnostic_run: `34943783606` — grounded owner binding GREEN (22 supported ticks, 0 mismatches)
- final_build_run: `34953958207` — historical candidate build SUCCESS
- final_verify_run: `34955884046` — historical candidate verify SUCCESS
- tested_failed_jar_sha256: `96053e314891495fbb4bf16c446023568fed542497e083083dad7ed420dcd7ef`
- final_ready: `false`
- user_runtime_validation: `FAILED`

## Exact-JAR real-user runtime evidence
The user tested exact SHA256 `96053e314891495fbb4bf16c446023568fed542497e083083dad7ed420dcd7ef`:
- floor hard/solid: PASS;
- grounded walking: PASS;
- walls soft: FAIL;
- jump/airborne drags player backward about 2–4 carriages instead of keeping carriage-relative reference space: FAIL;
- turns sweep player/camera, wall can be penetrated, player can be thrown outside: FAIL;
- overall behavior does not feel like standing on a VS2 moving base; view/control is dragged by carriage motion instead of remaining freely controllable in a stable moving frame: FAIL.

Direct runtime evidence overrides all previous automated M1 green. Do not ask the user to retest this SHA.

## Architecture diagnostic proof
Read-only workflow `34963733838` proved all of the following are present in the current implementation:
- Phase83 calls `EntityDragger.reanchorEntityWithExternalFrame`;
- the helper path directly performs `entity.setPos(...)`;
- Phase83 uses a bounded airborne lease (`phase83AirborneNativeLease`, <=20 ticks);
- Phase205 pre-collision bridge is grounded-only;
- Phase205 also calls the external reanchor helper;
- Phase205 samples Create `toLocalVector`/`toGlobalVector` transforms.

Conclusion: current compatibility is a contact/lease-based Create transform sampling + external reanchor system. It is not proof, and is now proven insufficient, as a continuous VS2 governing reference frame.

## Native VS2 root-boundary inspection
Pinned upstream VS2 source (`0bc19eac8f23258bbe03bdccb929c24d13e93838`) shows native `EntityDragger.dragEntitiesWithShips` is keyed by persistent VS2 ship identity/lifecycle (`lastShipStoodOn`, `ticksSinceStoodOnShip`, lookup in `shipObjectWorld.allShips`, current + previous ShipTransform). Native carry therefore has a ship-owner lifecycle that the current Create adapter does not establish; the adapter instead samples Create carriage transforms and invokes an external helper.

This does NOT authorize manufacturing a fake/duplicate physics ship. Create must retain gameplay/collision geometry ownership. The redesign must identify a legitimate thin bridge into VS2 reference ownership/transform lifecycle without giving VS2 duplicate carriage geometry/gameplay authority.

## FROZEN_GREEN / protected
- Kotlin/bootstrap packaging repair `f3d1335c9fc89283d936af039eba34aa9778bd05`.
- Create train + VS2 coexistence.
- Steam 'n' Rails and Copycats preservation.
- selected-carriage Phase205 ownership binding from `fb952094...` for grounded support.
- exact-JAR grounded floor solidity and grounded walking behavior.

Do not modify these merely to chase airborne/camera/wall symptoms.

## FAILED_HYPOTHESES / anti-loop
Do not reintroduce without new direct evidence:
- `EXACT_SHAPES_LOCALPLAYER_0fa4aa`;
- generic extension of frame leases/replay/carry correction;
- synthetic carry velocity / inertia compensation;
- fake gravity;
- manual floor/wall clamps or floor-only collision workaround;
- per-tick teleport/setPos chase/reanchor as the architecture solution;
- direct camera forcing/rotation compensation;
- jump/input timing tuning without input-specific failure evidence;
- sprint/reverse/strafe tuning as a reference-frame fix;
- broad sibling/global suppression instead of exact owner identity;
- duplicate Create/VS2 gameplay or collision authority;
- harness mutation used to manufacture green.

## next_safe_action
Trace the exact native VS2 acquisition/retention ownership path that assigns and consumes `lastShipStoodOn` / ship identity and determines player/body/camera transform continuity. Add the smallest read-only instrumentation/proof answering this question:

`Can one authoritative Create carriage frame participate in VS2's continuous reference-owner lifecycle without creating a duplicate VS2 physics ship or transferring Create collision/gameplay geometry ownership?`

Until that ownership seam is proven, do NOT make another gameplay carry/jump/wall/camera patch. If the seam cannot exist under current VS2 APIs without duplicate authority, perform a root redesign of the adapter boundary rather than stacking leases or corrections.

## Finalization policy — HARD USER RUNTIME GATE
CI/automated proof may produce candidates but cannot restore FINAL_READY. FINAL_READY requires a new exact final JAR that passes real-user runtime for standing, movement, jump+airborne+natural landing, floor/walls/ceiling, turns, speed changes, no sink/throw/drift/lag-behind, and free/stable camera/look, plus watchdog local runtime-gate SHA match.

## Fresh-chat/watchdog protocol
1. Inspect actual HEAD.
2. Read this file completely and reconcile `ledger_basis_head` with actual HEAD (ledger-only commits may advance HEAD without gameplay change).
3. Inspect only latest relevant Actions evidence for the active blocker.
4. Respect FROZEN_GREEN and FAILED_HYPOTHESES.
5. Execute `next_safe_action`; do not stop at narration.
6. HOLD only for genuinely queued/in-progress relevant workflow/evidence.
7. Never FINAL_READY from CI alone.
