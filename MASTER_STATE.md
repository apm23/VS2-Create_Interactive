# MASTER_STATE — VS2 / Create Interactive

GitHub code is the implementation source of truth. This file is the durable project-state ledger. Chat is temporary.

## Project
- Repository: `apm23/VS2-Create_Interactive`
- Milestone: `M1 — movement / collision`
- HARD architecture: Create owns train/carriage gameplay and collision geometry. VS2 must be the actual continuous moving reference-space/transform foundation for player body/camera. Compatibility remains a thin adapter; merely calling an EntityDragger helper after Create movement is not sufficient.

## Current reconciled state — 2026-09-15
- project_state: `ROOT_REDESIGN — NATIVE VS2 SHIP-ID COUPLING MAPPED; M1 PLAYER CORE-SLICE PROOF NEXT`
- ledger_basis_head: `abb57fff0d3635f09c9f85aa699df9f88d57abcf`
- architecture_diagnostic_commit: `6e079d62d0d30e8508ad825ef80791088fa28e5c` (`Add VS2 reference-frame ownership diagnostic`)
- architecture_diagnostic_run: `34963733838` — SUCCESS
- architecture_diagnostic_result: `current_adapter_is_contact/lease_reanchor_not_continuous_vs2_reference_space`
- native_owner_seam_diagnostic_commit: `c364910f3c9419a5b37b41a3c59fa77124a10b02` (`Fix native owner acquisition diagnostic anchor`)
- native_owner_seam_diagnostic_run: `34969572212` — SUCCESS
- native_owner_seam_result: `native_owner_requires_registered_vs2_ship; external_nonship_reference_owner_seam=false`
- redesign_map_commit: `abb57fff0d3635f09c9f85aa699df9f88d57abcf` (`Map VS2 reference-owner redesign boundary`)
- redesign_map_run: `34972926851` — SUCCESS
- redesign_map_result: `global coupling mapped read-only; owner-state tokens span 28 files, registered-ship resolution 9 files, camera/render binding 11 files; most are peripheral to M1 local-player standing/carry`
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

## Reference-owner redesign map
Read-only workflow `34972926851` mapped the global native coupling surface:
- owner-state symbols occur in 28 source files / 94 hits;
- registered-ship lookup occurs in 9 source files / 18 hits;
- transform-use tokens occur in 18 files / 36 hits;
- camera/render-binding tokens occur in 11 files / 22 hits;
- native acquisition remains collision-coupled in `EntityShipCollisionUtils`.

The raw global counts are intentionally broader than M1 because they include mobs, AI, armor stands, sounds, ship mounting, debug UI, Forge compatibility and other peripheral systems. They do NOT mean M1 needs a 28-file rewrite.

Targeted pinned-source inspection narrows the standing/walking/jump player path to these concerns:
- `EntityDraggingInformation`: persistent reference-owner lifecycle/state;
- `EntityDragger`: previous->current reference transform application for entity body;
- `MixinLocalPlayer`: client->server relative player position/yaw packet path;
- `VSGamePackets`: server-side relative player state -> world resolution;
- `MixinGameRenderer`: standing-player drag render interpolation (distinct from ship-mounted camera mode);
- `EntityLerper`: transform-direction helpers for relative/world yaw;
- `EntityShipCollisionUtils`: native VS2-ship acquisition only; Create acquisition must remain in the thin adapter rather than transferring Create collision ownership into VS2.

`MixinPlayer` ship-edge crouch/backoff is collision-specific and is not a required reference-owner primitive for the Create carriage path; Create remains collision authority.

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
Prove the M1 local-player `reference owner` core slice is actually narrow enough for a VS2-owned generalized lifecycle without registering a VS2 ship and without touching Create collision geometry. The read-only proof must trace, as one lifecycle, owner state -> previous/current transform application -> LocalPlayer relative packet -> server relative/world resolution -> standing-player render interpolation, and separately prove ship-mounted camera mode is not required for a standing player.

If that proof is GREEN, the next implementation hypothesis may introduce the smallest VS2-side generalized reference-owner/transform resolver used only by that M1 path, with Create supplying authoritative previous/current carriage transforms and selected carriage identity. It must replace, not stack on top of, the Phase83/Phase205 lease/reanchor architecture. Do not implement that abstraction before the core-slice proof is complete.

Do not patch jump/wall/camera symptoms in parallel.

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
