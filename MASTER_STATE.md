# MASTER_STATE — VS2 / Create Interactive

GitHub code is the implementation source of truth. This file is the durable project-state ledger. Chat is temporary.

## Project
- Repository: `apm23/VS2-Create_Interactive`
- Milestone: `M1 — movement / collision`
- HARD architecture: Create owns train/carriage gameplay and collision geometry. VS2 must be the actual continuous moving reference-space/transform foundation for player body/camera. Compatibility remains a thin adapter; merely calling an EntityDragger helper after Create movement is not sufficient.

## Current reconciled state — 2026-09-15
- project_state: `ROOT_REDESIGN — BILATERAL CREATE FRAME PROVEN; VS2 EXTERNAL REFERENCE-OWNER RESOLVER V1 AWAITS COMPILE PROOF`
- ledger_basis_head: `655fd1daa67f232a2add7b2d663786759031d02a`
- architecture_diagnostic_commit: `6e079d62d0d30e8508ad825ef80791088fa28e5c` (`Add VS2 reference-frame ownership diagnostic`)
- architecture_diagnostic_run: `34963733838` — SUCCESS
- architecture_diagnostic_result: `current_adapter_is_contact/lease_reanchor_not_continuous_vs2_reference_space`
- native_owner_seam_diagnostic_commit: `c364910f3c9419a5b37b41a3c59fa77124a10b02` (`Fix native owner acquisition diagnostic anchor`)
- native_owner_seam_diagnostic_run: `34969572212` — SUCCESS
- native_owner_seam_result: `native_owner_requires_registered_vs2_ship; external_nonship_reference_owner_seam=false`
- redesign_map_commit: `abb57fff0d3635f09c9f85aa699df9f88d57abcf` (`Map VS2 reference-owner redesign boundary`)
- redesign_map_run: `34972926851` — SUCCESS
- core_slice_commit: `2eeac3f8222931a56e760f05ec62bbe2131e2c43` (`Prove M1 reference-owner core slice`)
- core_slice_run: `34975161200` — SUCCESS
- core_slice_result: `standing-player reference-owner surface bounded to 6 core files; Create collision mutation not required; ship-mounted camera not required; fake VS2 ship not required if owner state + transform resolution are generalized`
- create_bilateral_seam_commit: `ebf4aaf73a0fb401cfeb77e9017f43af3b6f11c9` (`Prove Create bilateral carriage frame seam`)
- create_bilateral_seam_run: `34977644889` — SUCCESS
- create_bilateral_seam_result: `resolved Create 6.0.9-1 JAR exposes common client/server CarriageContraptionEntity identity plus toLocalVector(previous-anchor) and toGlobalVector(current-anchor); fake VS2 ship and geometry registration not required`
- resolved_create_jar_sha256: `d9c6cb6116d5caa1174a289ecd7d3cdd463ccef6e8db1249ab0bcfcd8c935870`
- reference_owner_v1_initial_commit: `6ef53dabf799bb62e8b2d6a2d239b33917f751e4`
- reference_owner_v1_commit: `655fd1daa67f232a2add7b2d663786759031d02a` (`Harden reference-owner v1 self-audit`)
- reference_owner_v1_status: `infrastructure only; external owner acquisition intentionally disabled until compile/proof and packet/render lifecycle follow-up`
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
Read-only workflow `34963733838` proved the previous implementation is contact/lease-based Create transform sampling plus `EntityDragger.reanchorEntityWithExternalFrame`, not a continuous VS2 governing reference space. Phase83 uses a bounded airborne lease; Phase205 is grounded-only; the helper directly performs `entity.setPos(...)`. This architecture is proven insufficient and must not be extended.

## Native VS2 root-boundary proof
Pinned upstream VS2 source (`0bc19eac8f23258bbe03bdccb929c24d13e93838`) and workflow `34969572212` prove native acquisition/state/drag/render are hard-coupled to a registered VS2 `ShipId`/`Ship`. There is no pinned public non-Ship owner seam. Registering a fake/proxy VS2 ship just to obtain the lifecycle would duplicate authority and is forbidden.

## Reference-owner redesign map and bounded M1 slice
Workflow `34972926851` mapped broad global coupling, then `34975161200` proved the standing/walking/jump local-player path can be bounded to six core concerns:
- `EntityDraggingInformation`: persistent owner lifecycle/state;
- `EntityDragger`: previous-owner -> current-owner body transform application;
- `MixinLocalPlayer`: client -> server relative player packet path;
- `VSGamePackets`: server relative -> current-world resolution;
- `MixinGameRenderer`: standing-player render interpolation;
- `EntityLerper`: transform-only relative/world yaw conversion.

Native VS2 ship acquisition remains separate. Create collision/edge handling remains Create-owned. Ship-mounted camera mode is not required for standing-player M1. The proof explicitly reported `core_file_count=6`, `create_collision_geometry_mutation_required=false`, `ship_mount_camera_required=false`, and `fake_vs2_ship_required=false_if_owner_state_and_transform_resolution_are_generalized`.

## Bilateral Create frame seam proof
Workflow `34977644889` used the exact Create dependency resolved by the real Gradle build, not only an upstream source guess. It proved:
- mod/version: `create 6.0.9-1`;
- resolved JAR SHA256: `d9c6cb6116d5caa1174a289ecd7d3cdd463ccef6e8db1249ab0bcfcd8c935870`;
- `CarriageContraptionEntity` is a normal common `Entity`, so the synchronized vanilla entity id can be the external reference-owner key on both client and server;
- public common `toLocalVector(Vec3,float,boolean)` supports previous-frame world -> carriage-local using `prevAnchor=true`;
- public common `toGlobalVector(Vec3,float,boolean)` supports carriage-local -> current-frame world using `prevAnchor=false`;
- `getContactPointMotion` remains Create collision/motion territory and is not required by the generalized resolver;
- no fake VS2 ship, geometry registration, synthetic velocity, gravity, or camera compensation is needed for the transform seam.

## Reference-owner resolver v1 hypothesis
`prepare_vs2_26_2_reference_owner_v1.py` introduces infrastructure only:
- a VS2-owned `ExternalReferenceFrameResolver` keyed by existing Create carriage entity id;
- separate `externalReferenceOwnerEntityId` state rather than overloading `lastShipStoodOn` with a fake ShipId;
- generalized owner body-frame delta is fed into VS2's existing native `EntityDragger` application lifecycle rather than calling the historical external reanchor helper;
- the resolver itself contains no `setPos`, velocity, gravity, collision, teleport, or camera mutation API;
- Phase83 and Phase205 old reanchor paths are mutually excluded whenever the generalized owner is active, preventing stacked/double ownership;
- acquisition is intentionally NOT enabled in v1, so this infrastructure commit alone is not a runtime candidate and should not alter user gameplay.

If compile/proof is GREEN, the next hypothesis is to route acquisition + LocalPlayer relative packet/server resolution + standing-player render/yaw through the same generalized owner lifecycle, then remove the obsolete lease/reanchor authority instead of extending it.

## FROZEN_GREEN / protected
- Kotlin/bootstrap packaging repair `f3d1335c9fc89283d936af039eba34aa9778bd05`.
- Create train + VS2 coexistence.
- Steam 'n' Rails and Copycats preservation.
- exact-JAR grounded floor solidity and grounded walking behavior are protected behavioral criteria.
- Phase205 selected-owner evidence remains useful for owner selection, but its historical reanchor mechanism is not protected architecture.

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
Compile/prove `reference_owner_v1` against the current M1 production composition (`phase2..54 + phase98`) and the Phase205 ownership seam. The proof must establish:
- generated common/fabric sources compile;
- generalized owner state and bilateral resolver exist on common client/server code;
- external-owner branch feeds only VS2's existing native drag application lifecycle;
- no external helper reanchor is invoked by that new branch;
- Phase83/Phase205 old reanchor authority is structurally excluded when generalized owner is active;
- acquisition remains disabled so no runtime gameplay behavior is changed yet.

If GREEN, proceed to the smallest next core-slice implementation for acquisition + relative packet/server resolution + standing-player render/yaw, using the same external owner key and replacing old lease/reanchor authority. Do not patch jump/wall/camera symptoms independently.

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
