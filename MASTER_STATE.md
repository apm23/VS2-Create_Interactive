# MASTER_STATE — VS2 / Create Interactive

GitHub code is the implementation source of truth. This file is the durable project-state ledger. Chat is temporary.

## Project
- Repository: `apm23/VS2-Create_Interactive`
- Milestone: `M1 — movement / collision`
- HARD architecture: Create owns train/carriage gameplay and collision geometry. VS2 must be the actual continuous moving reference-space/transform foundation for player body/camera. Compatibility remains a thin adapter; merely calling an EntityDragger helper after Create movement is not sufficient.

## Current reconciled state — 2026-09-16
- project_state: `ROOT_REDESIGN — REFERENCE-OWNER V2 CORE SLICE PROVEN/COMPILED; EXACT V2 REAL-TRAIN RUNTIME PROOF NEXT`
- ledger_basis_head: `a3f37d8e8c896dc05eca1e4b74759a25100a34bc`
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
- reference_owner_v1_composition_fix_commit: `59e75959d8a38f94a637aa1a8120280c2bf2df0a`
- reference_owner_v1_trigger_commit: `4aeaf9f5ba66dedb6a7ac3b14fc81bab371be8f7`
- reference_owner_v1_run: `34984299770` — SUCCESS
- reference_owner_v1_result: `generalized owner state + bilateral Entity-id resolver + native EntityDragger application lifecycle compile; acquisition intentionally disabled; old Phase83/205 reanchor mutually excluded whenever external owner is active`
- reference_owner_v2_implementation_commit: `5f687aca0af43ca4783fb915c3aea1651da74dc1` (`Route M1 through external reference-owner core slice`)
- reference_owner_v2_initial_workflow_commit: `40b68fd3c71857f3ab125b9bd5211f4973897996`
- reference_owner_v2_initial_run: `34991346900` — FAILURE before proof/compile due composition-only Phase83 boundary mismatch; not gameplay/physics evidence
- reference_owner_v2_composefix_commit: `ea546f83f3549736aa4ac0dfad23b82005a63cd0`
- reference_owner_v2_proof_commit: `a3f37d8e8c896dc05eca1e4b74759a25100a34bc` (`Rerun V2 with robust Phase83 composition boundary`)
- reference_owner_v2_run: `34994353308` — SUCCESS
- reference_owner_v2_result: `single non-Ship external owner lifecycle proven across selected Create-owner acquisition, bounded lifetime, VS2 EntityDragger body continuity, dedicated LocalPlayer relative packet, server same-owner resolution, standing render interpolation, and transform-only yaw; old Phase83/205 reanchor authority removed; no fake VS2 ship; Fabric compile GREEN`
- gameplay_fix_commit: `fb9520946e1041c1dc0a75a82fcae0a260cceec8` (`Bind Phase205 reanchor to selected carriage owner`) — historical only; its reanchor authority is removed by V2 composition
- automated_m1_proof: `34943410005` — historical automated GREEN, overridden by direct runtime failure
- owner_diagnostic_run: `34943783606` — grounded owner binding GREEN (22 supported ticks, 0 mismatches)
- final_build_run: `34953958207` — historical candidate build SUCCESS
- final_verify_run: `34955884046` — historical candidate verify SUCCESS
- tested_failed_jar_sha256: `96053e314891495fbb4bf16c446023568fed542497e083083dad7ed420dcd7ef`
- final_ready: `false`
- user_runtime_validation: `FAILED` for the historical exact JAR above; no V2 user-runtime candidate has been built/tested yet

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

## Reference-owner resolver v1 — proven infrastructure
`34984299770` proved V1 composes and compiles against current M1 sources. V1 introduces:
- a VS2-owned `ExternalReferenceFrameResolver` keyed by existing Create carriage entity id;
- separate `externalReferenceOwnerEntityId` state rather than overloading `lastShipStoodOn` with a fake ShipId;
- generalized owner body-frame delta fed into VS2's existing native `EntityDragger` application lifecycle rather than calling the historical external reanchor helper;
- no resolver-side setPos, velocity, gravity, collision, teleport, or camera mutation;
- structural mutual exclusion of old Phase83/Phase205 authority when an external owner exists.

V1 intentionally did not enable acquisition. That limitation is superseded by V2.

## Reference-owner resolver v2 — proven architecture/compile, runtime not yet proven
V2 (`5f687aca...` + composefix `ea546f83...`) promotes the Create carriage Entity id into one VS2-owned non-Ship reference-owner lifecycle. Workflow `34994353308` proved all of the following and compiled successfully:
- bounded external owner lifetime/state exists;
- the already-selected Create carriage with grounded physical support + recent native Create contact acquires/refreshes the owner;
- historical Phase83 lease/reanchor is removed from the V2 composition;
- historical Phase205 pre-collision reanchor and duplicate contact-motion suppression are removed from the V2 composition;
- a dedicated `PacketPlayerReferenceMotion(ownerEntityId, relative position, relative yaw)` is used instead of pretending the carriage is a VS2 ShipId;
- LocalPlayer packet generation, server resolution, standing render interpolation, and yaw all resolve the same external owner entity id;
- transform/yaw paths are transform-only; no synthetic velocity, fake gravity, Create collision takeover, or camera forcing is introduced;
- `:fabric:compileJava` completed `BUILD SUCCESSFUL`.

This GREEN is architecture + compile proof only. It does not prove real moving-train standing/jump/airborne/walls/turn behavior, and it does not satisfy the user runtime gate.

## FROZEN_GREEN / protected
- Kotlin/bootstrap packaging repair `f3d1335c9fc89283d936af039eba34aa9778bd05`.
- Create train + VS2 coexistence.
- Steam 'n' Rails and Copycats preservation.
- exact-JAR grounded floor solidity and grounded walking behavior are protected behavioral criteria.
- Phase205 selected-owner evidence remains useful for owner selection, but its historical reanchor mechanism is not protected architecture and is removed in V2.
- V2 core-slice architecture proof from `34994353308` is frozen unless direct runtime evidence disproves a specific boundary.

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
Run the smallest real-train runtime proof on the exact V2 composition, using the existing verified `r0v3` moving-train fixture without weakening historical acceptance criteria or manufacturing success. Prepare exactly the normal current M1 composition and then apply:
- `prepare_vs2_26_2_phase205.py` as required by the current cumulative composition boundary;
- `prepare_vs2_26_2_reference_owner_v1.py`;
- `prepare_vs2_26_2_reference_owner_v2_composefix.py`.

The dedicated V2 runtime gate should establish at minimum:
- real Create carriage present and train moving;
- `REFERENCE_OWNER_V2_ACQUIRE` occurs for the selected carriage;
- old Phase83/Phase205 reanchor markers do not execute;
- grounded movement fixture still reaches its existing native confirmation;
- a vanilla jump reaches requested -> airborne -> natural landed;
- during that airborne interval, carriage-relative horizontal position does not exhibit the previous multi-carriage backward drift;
- no crash/mixin/linkage failure.

If this runtime gate fails, classify whether the failure is fixture/verifier, acquisition, packet/server identity, body reference continuity, render/yaw, or Create collision authority before changing gameplay. Do not patch jump/walls/camera independently.

If this runtime gate is GREEN, do not declare FINAL_READY. Advance toward the smallest exact V2 test artifact only after broader M1 collision/turn criteria are still demonstrated, and retain the hard real-user exact-JAR gate.

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
