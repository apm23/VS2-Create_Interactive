# MASTER_STATE — VS2 / Create Interactive

GitHub code is the implementation source of truth. This file is the durable project-state ledger. Chat is temporary.

## Project
- Repository: `apm23/VS2-Create_Interactive`
- Milestone: `M1 — movement / collision`
- HARD architecture: Create owns train/carriage gameplay and collision geometry. VS2 must be the actual continuous moving reference-space/transform foundation for player body/camera. Compatibility remains a thin adapter; merely calling an EntityDragger helper after Create movement is not sufficient.

## Current reconciled state — 2026-09-15
- project_state: `ROOT_REDESIGN — M1 REFERENCE-OWNER CORE SLICE BOUNDED; CREATE BILATERAL FRAME-RESOLVER PROOF NEXT`
- ledger_basis_head: `2eeac3f8222931a56e760f05ec62bbe2131e2c43`
- architecture_diagnostic_commit: `6e079d62d0d30e8508ad825ef80791088fa28e5c` (`Add VS2 reference-frame ownership diagnostic`)
- architecture_diagnostic_run: `34963733838` — SUCCESS
- architecture_diagnostic_result: `current_adapter_is_contact/lease_reanchor_not_continuous_vs2_reference_space`
- native_owner_seam_diagnostic_commit: `c364910f3c9419a5b37b41a3c59fa77124a10b02` (`Fix native owner acquisition diagnostic anchor`)
- native_owner_seam_diagnostic_run: `34969572212` — SUCCESS
- native_owner_seam_result: `native_owner_requires_registered_vs2_ship; external_nonship_reference_owner_seam=false`
- redesign_map_commit: `abb57fff0d3635f09c9f85aa699df9f88d57abcf` (`Map VS2 reference-owner redesign boundary`)
- redesign_map_run: `34972926851` — SUCCESS
- redesign_map_result: `global coupling mapped read-only; owner-state tokens span 28 files, registered-ship resolution 9 files, camera/render binding 11 files; most are peripheral to M1 local-player standing/carry`
- core_slice_commit: `2eeac3f8222931a56e760f05ec62bbe2131e2c43` (`Prove M1 reference-owner core slice`)
- core_slice_run: `34975161200` — SUCCESS
- core_slice_result: `standing-player reference-owner surface bounded to 6 core files; Create collision mutation not required; ship-mounted camera not required; fake VS2 ship not required if owner state + transform resolution are generalized`
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

## M1 reference-owner core-slice proof
Read-only workflow `34975161200` proved the standing/walking/jump local-player path is a bounded surface:
- `EntityDraggingInformation`: central persistent owner lifecycle/state;
- `EntityDragger`: body application from previous owner transform to current owner transform;
- `MixinLocalPlayer`: client -> server relative position/yaw packet path uses the same owner;
- `VSGamePackets`: server relative position -> current world transform resolution uses the same owner;
- `MixinGameRenderer`: standing-player render interpolation uses previous/current owner render transforms;
- `EntityLerper`: relative/world yaw conversion is transform-only;
- native ship collision acquisition is separate and can remain untouched for real VS2 ships;
- Create edge/backoff collision is not part of the generalized owner core and remains Create-owned;
- standing-player render path is distinct from ship-mounted camera mode, so M1 does not require pretending the player is mounted to a VS2 ship.

The proof explicitly reported:
- `core_file_count=6`;
- `create_collision_geometry_mutation_required=false`;
- `ship_mount_camera_required=false`;
- `fake_vs2_ship_required=false_if_owner_state_and_transform_resolution_are_generalized`.

This authorizes design/implementation of a smallest generalized VS2-owned reference-owner lifecycle for this core slice only. It does NOT authorize reintroducing Phase83/Phase205 lease/reanchor behavior alongside it; the new lifecycle must replace that architecture for Create carriage ownership.

## FROZEN_GREEN / protected
- Kotlin/bootstrap packaging repair `f3d1335c9fc89283d936af039eba34aa9778bd05`.
- Create train + VS2 coexistence.
- Steam 'n' Rails and Copycats preservation.
- selected-carriage Phase205 ownership binding from `fb952094...` remains useful evidence for grounded owner selection, but its reanchor mechanism is not the target architecture.
- exact-JAR grounded floor solidity and grounded walking behavior are protected behavioral criteria, not proof that the old carry architecture should be preserved.

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
Before writing the generalized resolver, prove that the exact Create dependency used by the pinned 26.2 VS2 build exposes a bilateral/common carriage frame surface suitable for one owner lifecycle on client and server:
- carriage is a normal networked `Entity` type with a stable synchronized entity identity suitable as an external-owner key;
- `AbstractContraptionEntity.toLocalVector(..., prevAnchor=true)` can express previous-frame world -> carriage-local;
- `AbstractContraptionEntity.toGlobalVector(..., prevAnchor=false)` can express carriage-local -> current-frame world;
- the relevant carriage entity and transform methods are in the common Create artifact, not a client-only class;
- no geometry registration, fake VS2 ship, synthetic velocity, gravity, or camera compensation is required.

Use the exact dependency resolved by the real Gradle build where possible; do not rely only on a moving upstream Create source branch. If this bilateral frame-resolver proof is GREEN, implement the smallest VS2-owned generalized reference-owner state + transform resolver for the six-file M1 core slice, with Create supplying selected carriage identity and previous/current transforms. Replace/disable Phase83/Phase205 external reanchor ownership when the generalized Create owner is active; do not stack both.

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
