# MASTER_STATE — VS2 / Create Interactive

GitHub code is the implementation source of truth. This file is the durable project-state ledger. Chat is temporary.

## Project
- Repository: `apm23/VS2-Create_Interactive`
- Milestone: `M1 — movement / collision`
- HARD architecture: Create owns train/carriage gameplay and collision geometry. VS2 must be the actual continuous moving reference-space/transform foundation for player body/camera. Compatibility remains a thin adapter; merely calling an EntityDragger helper after Create movement is not sufficient.

## Current reconciled state — 2026-09-15
- project_state: `ROOT_REDESIGN — PINNED VS2 NATIVE OWNER REQUIRES REGISTERED SHIP; NO NON-SHIP OWNER API FOUND`
- ledger_basis_head: `c364910f3c9419a5b37b41a3c59fa77124a10b02`
- architecture_diagnostic_commit: `6e079d62d0d30e8508ad825ef80791088fa28e5c` (`Add VS2 reference-frame ownership diagnostic`)
- architecture_diagnostic_run: `34963733838` — SUCCESS
- architecture_diagnostic_result: `current_adapter_is_contact/lease_reanchor_not_continuous_vs2_reference_space`
- native_owner_seam_diagnostic_commit: `c364910f3c9419a5b37b41a3c59fa77124a10b02` (`Fix native owner acquisition diagnostic anchor`)
- native_owner_seam_diagnostic_run: `34969572212` — SUCCESS
- native_owner_seam_result: `native_owner_requires_registered_vs2_ship; external_nonship_reference_owner_seam=false`
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

## Native VS2 root-boundary proof
Pinned upstream VS2 source (`0bc19eac8f23258bbe03bdccb929c24d13e93838`) and read-only workflow `34969572212` prove:
- native acquisition writes a colliding registered VS2 `ShipId` into `draggingInformation.lastShipStoodOn`;
- owner state is `ShipId?` and retention is tied to `ticksSinceStoodOnShip`;
- native dragging resolves that id through `shipObjectWorld.allShips.getById(...)` and uses previous/current `ShipTransform`;
- render interpolation resolves `lastShipStoodOn` through client `getLoadedShips().getById(...)`;
- ship-mounted camera code also requires a real `ClientShip`;
- conservative pinned-source scan found zero explicit external/non-Ship reference-owner APIs.

Conclusion: one authoritative Create carriage cannot participate in the existing pinned VS2 native owner lifecycle through a public non-Ship seam. Registering a fake/proxy VS2 ship merely to obtain `ShipId`/`ClientShip` would create duplicate physics/reference authority and is forbidden. Therefore the redesign target is the VS2 reference-owner abstraction boundary itself, not another Create carry lease/reanchor patch.

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
- fake/proxy VS2 ship registration solely to obtain native drag/camera lifecycle;
- harness mutation used to manufacture green.

## next_safe_action
Map the smallest pinned-VS2 call-site set that couples continuous entity/body/render reference ownership specifically to `ShipId` / registered `Ship` lookup. Add a read-only redesign map that identifies the minimum state/acquisition/drag/render seams that would need a generalized `reference owner` abstraction accepting authoritative previous/current transforms from Create without registering geometry or a physics ship.

Do not implement the abstraction until that map proves the boundary is narrow enough to keep Create collision/gameplay ownership intact. Do not patch jump/wall/camera symptoms in parallel.

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
