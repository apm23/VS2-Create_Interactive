# MASTER_STATE — VS2 / Create Interactive

GitHub code is the implementation source of truth. This file is the durable project-state ledger. Chat is temporary.

## Project / hard contract
- Repository: `apm23/VS2-Create_Interactive`
- Milestone: `M1 — movement / collision`
- Create owns train/carriage gameplay and collision geometry.
- VS2 must be the actual continuous moving reference-space/transform foundation for player body/render/camera.
- Standing/walking/jumping must remain carriage-relative through grounded, airborne, turns, acceleration/deceleration and speed changes while mouse/look remains free.
- Create floor/walls/ceiling remain authoritative solid geometry in that same moving frame.
- Forbidden: fake gravity, synthetic carry velocity/inertia, manual floor/wall clamps, floor-only collision workarounds, per-tick teleport/setPos chase/reanchor architecture, duplicate Create/VS2 gameplay/collision authority, direct camera forcing/rotation compensation, fake/proxy VS2 ships, or workaround chains hiding double ownership.

## Current reconciled state — 2026-09-16
- project_state: `ROOT_REDESIGN — SAME-POINT REFERENCE TRANSFORM GREEN; COLLISION/REFERENCE-CARRY TEMPORAL ORDER MICRO-PROOF ACTIVE`
- ledger_basis_head: `654b1e765c6b0b41137e80edccacee02eda4833d`
- final_ready: `false`
- exact historical failed user JAR SHA256: `96053e314891495fbb4bf16c446023568fed542497e083083dad7ed420dcd7ef`
- user_runtime_validation: historical candidate FAILED; no authority-fixed V2 candidate has been built/tested by the user.
- current diagnostic workflow: `m1-reference-owner-v2-collision-order-microproof`
- current diagnostic commit: `654b1e765c6b0b41137e80edccacee02eda4833d`
- current diagnostic run: `35025200849`
- current diagnostic job: `104570448090`
- current diagnostic status when ledger written: `in_progress`, exact composition + read-only instrumentation prepared successfully; compile running.

## Root architecture proofs
- `6e079d62d0d30e8508ad825ef80791088fa28e5c`, run `34963733838` SUCCESS: old implementation was contact/lease reanchor, not continuous VS2 reference space.
- `c364910f3c9419a5b37b41a3c59fa77124a10b02`, run `34969572212` SUCCESS: pinned VS2 native owner lifecycle requires a registered `ShipId`; there is no native public non-Ship owner seam. Fake/proxy ship is forbidden.
- `abb57fff0d3635f09c9f85aa699df9f88d57abcf`, run `34972926851` SUCCESS: reference-owner redesign boundary mapped.
- `2eeac3f8222931a56e760f05ec62bbe2131e2c43`, run `34975161200` SUCCESS: LocalPlayer M1 core slice bounded to owner state, body drag, relative packet, server resolution, standing render interpolation, and yaw transform. Create collision geometry remains separate.
- `ebf4aaf73a0fb401cfeb77e9017f43af3b6f11c9`, run `34977644889` SUCCESS: Create `6.0.9-1` common carriage Entity id + bilateral transform API exists. Resolved Create JAR SHA256 `d9c6cb6116d5caa1174a289ecd7d3cdd463ccef6e8db1249ab0bcfcd8c935870`.

## V1/V2 core implementation
- V1: `6ef53dab...` -> hardened `655fd1da...` -> composition fix `59e75959...` -> trigger `4aeaf9f5...`; run `34984299770` SUCCESS.
- V1 proved generalized non-Ship owner state + Entity-id resolver + VS2 EntityDragger application lifecycle; acquisition intentionally disabled; historical Phase83/205 reanchor excluded when external owner active.
- V2 implementation `5f687aca0af43ca4783fb915c3aea1651da74dc1`; composefix `ea546f83f3549736aa4ac0dfad23b82005a63cd0`; proof head `a3f37d8e8c896dc05eca1e4b74759a25100a34bc`; run `34994353308` SUCCESS.
- V2 structurally proved: selected Create carriage acquisition, bounded owner lifetime, dedicated `PacketPlayerReferenceMotion`, same-owner client/server/render/yaw path, no fake ship, old Phase83/205 reanchor authority removed, Fabric compile GREEN.

## Historical exact-JAR user runtime failure — overrides old CI GREEN
User tested exact SHA256 `96053e314891495fbb4bf16c446023568fed542497e083083dad7ed420dcd7ef` after historical build `34953958207` and verify `34955884046` were green:
- floor hard/solid PASS;
- grounded walking PASS;
- walls soft FAIL;
- jump/airborne dragged player backward ~2–4 carriages FAIL;
- turns swept player/camera and could throw player outside FAIL;
- overall behavior did not feel like a stable VS2 moving base FAIL.
Never ask user to retest this SHA.

## V2 initial real-train failure
- gate commit `b1464506b6e0f3635c4d50ecb7615913a87d5ba9`, run `34997330399` FAILURE.
- carriage/train PASS; external owner acquisition PASS; grounded walk PASS; vanilla jump request->airborne->natural landing PASS; legacy Phase83/205 reanchor absent.
- body continuity failed catastrophically: ~`93.48251` blocks airborne owner-relative horizontal drift; ~`51.82845` max one-tick step.
- artifact showed Create `ContraptionColliderClient.collideEntities` applying material contact carry while VS2 external owner was active.

## Scheduler root and proof — FROZEN_GREEN
- Runtime proved external owner could acquire while LocalPlayer body branch never executed because pinned VS2 `MixinMinecraft.postTick()` scheduled `EntityDragger` only when native VS2 ships existed.
- scheduler fix `f81507dd...`: preserves native Ship scheduling and also schedules the drag sweep while LocalPlayer has an external reference owner; no collision/motion/camera algorithm added.
- scheduler proof run `35008163064` SUCCESS: external owner reaches VS2 EntityDragger body lifecycle.
- This exposed duplicate movement authority rather than transform absence.

## Active-owner contact-carry authority — FROZEN_GREEN
- Runtime showed VS2 body movement and Create ordinal-1 contact-point carry could both move LocalPlayer in the same tick.
- independent artifact also proved a sibling carriage callback could apply a second material ordinal-1 carry after exact-owner suppression.
- authority fix commit `652667e887720509f37618641e231f70e8e689c4` (`Scope Create contact carry to active VS2 reference owner`).
- authority proof commit `07dbd852712c3c3d81b4d405e253befd4b34ac65`; run `35017634522`, job `104544985035`: SUCCESS.
- proof: exact-owner suppressions `18`; sibling suppressions `3`; sibling pairs `[(8,10),(10,8)]`; `material_line330_overlap=[]`; `collision_response_writer_untouched=true`; conclusion `single_reference_body_writer_proven`.
- scope is narrow: LocalPlayer only, valid active external owner only, Create ordinal-1 contact carry only. Create first collision-response setPos, OBB, grounding, damage, floor/wall/ceiling geometry remain untouched. No synthetic movement added.
- Do not broaden or retune this boundary without direct runtime evidence.

## Authority-fixed real-train retest — root evidence
Workflow commit `c7a797d3ba89c43f33365d6d1ded9bad65f6d841`, run `35020203661`:
- attempt 1 failed before source compile/runtime because Maven Central returned HTTP 403; no gameplay evidence.
- attempt 2: composition PASS, `:fabric:compileJava` PASS, verified r0v3 fixture PASS, assets PASS, then runtime proof timed out waiting for jump.
- carriage present + train moving PASS.
- external owner acquisition PASS: owner carriage 2 initially, then carriage 4; carriage 4 refreshed through player tick 33.
- bounded forward walk PASS (`GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED`).
- native backward PASS at tick 33.
- native right strafe PASS at tick 34.
- jump REQUESTED/AIRBORNE/LANDED absent. Do NOT treat this as jump-input failure.
- jump arm remained blocked because fresh floor/native-contact prerequisites disappeared before the delay window: last owner acquisition tick 33; last Create native contact application tick 42; later `known_native_fresh=false` and floor support stale.
- legacy Phase83/205 reanchor markers remained absent.

### Exact turn/reference-frame seam from retest
- tick 43 carriage 4 local feet approximately `(2.6657, 1.2315, 3.3001)`.
- tick 44 carriage 4 frame center step approximately `(+20.5294, 0, 0)` while Create contact-point motion at its sampled point is approximately `(-24.8609, 0, -5.6394)`.
- the VS2 body transform at the same period materially changes world position and support disappears.
- carriage-local feet flip around the transition and later return; support/contact continuity collapses before fixture jump.
- this is turn/reference-frame evidence; it does not authorize jump-input tuning, gravity, wall clamps, camera forcing, or generic carry leases.

## Same-point transform micro-proof — FROZEN_GREEN
- commit `7bf93e0b8b9c8c9eac56f6f9a5aff2df9394a20d`.
- workflow `m1-reference-owner-v2-point-timing-microproof`.
- run `35023234306`, job `104563915092`: SUCCESS.
- exact result:
  `REFERENCE_OWNER_V2_POINT_TIMING_PROOF classification=SAME_POINT_TRANSFORM_MATCHES_NATIVE_POINT_TIMING_DIFFERS sample_count=25 turn_ticks=[14,15,16,17,18,19,23,24,25,27,28,29,33,36,37,38,39,43] turn_tick=15 turn_same_point_mismatch=0.000000 turn_current_point_mismatch=0.000000 max_same_point_mismatch=0.000000 max_current_point_mismatch=0.000000 read_only=true final_ready=false`
- conclusion: V2 previous-world -> owner-local -> current-world transform math matches Create `getContactPointMotion()` at the same reference point.
- Do NOT patch resolver transform math, prev/current anchor flags, yaw transform, partial-tick transform math, or point-vs-vector math without new direct contrary evidence.
- same runtime still shows LocalPlayer owner-local Y falling from about `2.0001` through `1.9217`, `1.766`, `1.5359`, `1.2316`, `0.855`, `0.4075`, `-0.109`, `-0.694`, to about `-1`, while external-owner carry remains live.
- Therefore current blocker is not bilateral transform correctness; it is the collision/reference-carry lifecycle/order in which Create authoritative geometry is evaluated relative to VS2 reference carry.

## Static scheduling/collision boundary
Pinned Create-Fly source shows:
- `MinecraftMixin.tickPost`, injected at `Minecraft.tick` TAIL, calls `ContraptionHandlerClient.tick(level)`.
- that path executes `ContraptionColliderClient.collideEntities` and Create authoritative OBB/floor/wall/ceiling collision.
Pinned VS2 source plus scheduler fix shows:
- VS2 external-owner `EntityDragger` sweep is scheduled from `MixinMinecraft.postTick()` at `Minecraft.tick` RETURN.
- Static TAIL/RETURN placement strongly suggests an order issue, but mixin runtime ordering must be measured rather than assumed.
Create source also confirms `getAnchorVec() = position()`, `getPrevAnchorVec() = previous position`, and its contact-point transform semantics are consistent with the now-GREEN same-point proof.

## Current collision/reference-carry temporal-order micro-proof
- first workflow commit `56f451acacd923fe0d0dfe31f1e192fafea72e91` contained invalid YAML due embedded heredoc indentation; run `35024773928` failed instantly with zero jobs. This is harness-only failure and carries no gameplay evidence.
- repaired workflow commit `654b1e765c6b0b41137e80edccacee02eda4833d`.
- run `35025200849`, job `104570448090` is the active proof.
- exact V2 composition is preserved: phase2..54 + phase98 + phase205 + V1 + V2 composefix + scheduler fix + FROZEN_GREEN authority fix.
- new instrumentation is read-only and records monotonically ordered:
  - `CREATE_COLLISION_HEAD`
  - `CREATE_COLLISION_RETURN`
  - `VS2_DRAG_BEFORE`
  - `VS2_DRAG_AFTER`
  with player tick, active external owner Entity id, callback carriage Entity id, owner age, world position/xo, owner-local coordinates, and onGround.
- no movement, velocity, gravity, collision response, camera, owner acquisition, or Create geometry is mutated by this probe.
- expected classifications:
  - `CREATE_COLLISION_COMPLETES_BEFORE_VS2_REFERENCE_CARRY`
  - `VS2_REFERENCE_CARRY_COMPLETES_BEFORE_CREATE_COLLISION`
  - `MIXED_OR_INTERLEAVED_COLLISION_REFERENCE_ORDER`
- only after this runtime ordering evidence may scheduling/ownership be changed.

## FROZEN_GREEN / protected
- bootstrap/Kotlin packaging repair `f3d1335c9fc89283d936af039eba34aa9778bd05`.
- Create train + VS2 coexistence.
- Steam 'n' Rails + Copycats preservation.
- V1 infrastructure run `34984299770`.
- V2 structural/core run `34994353308` except old body-continuity assumptions disproved by runtime.
- scheduler boundary run `35008163064`, unless later direct ordering evidence proves its hook placement must move while preserving its lifecycle semantics.
- active-owner ordinal-1 contact-carry authority boundary `652667e...` / run `35017634522`.
- same-point Create/V2 transform equivalence run `35023234306`.
- historical user-proven floor solidity and grounded walking are protected behavioral criteria, not current completion proof.

## FAILED_HYPOTHESES / anti-loop
Do not reintroduce without new direct evidence:
- `EXACT_SHAPES_LOCALPLAYER_0fa4aa`;
- generic frame lease/replay/carry extension;
- synthetic carry velocity / inertia compensation;
- fake gravity;
- manual floor/wall clamps or floor-only collision workaround;
- per-tick teleport/setPos chase/reanchor as architecture;
- direct camera forcing/rotation compensation;
- jump/input timing tuning without input-specific evidence;
- sprint/reverse/strafe tuning as a reference-frame fix;
- unscoped/global collider suppression, ownerless broad suppression, or suppression of Create's collision-response writer;
- duplicate Create/VS2 gameplay/collision authority;
- fake/proxy VS2 ship solely for native lifecycle;
- harness mutation used to manufacture GREEN;
- changing V2 resolver prev/current transform semantics after run `35023234306` without new contrary evidence.

Clarification: proven authority arbitration is not forbidden global suppression. It is LocalPlayer-only, active-reference-owner scoped, ordinal-1 contact-carry-only while Create collision response remains authoritative.

## next_safe_action
1. Inspect run `35025200849` first.
2. If queued/in_progress: HOLD; stack no physics/scheduling patch.
3. If it fails before runtime due workflow/compile/instrumentation/verifier: repair harness only.
4. If runtime proves `CREATE_COLLISION_COMPLETES_BEFORE_VS2_REFERENCE_CARRY`, inspect the smallest scheduler hook boundary that lets the already-proven VS2 reference transform be established before Create evaluates collision, while retaining VS2 as sole reference-body writer and Create as sole collision/geometry authority. Use a read-only hook-boundary proof before moving execution if more than one safe hook exists.
5. If runtime proves `VS2_REFERENCE_CARRY_COMPLETES_BEFORE_CREATE_COLLISION` yet owner-local floor still sinks, instrument Create OBB/support geometry evaluation against the active owner frame; do not alter resolver/carry math.
6. If mixed/interleaved, map exact mixin callback order and priorities read-only before any patch.
7. Only after turn-local floor continuity is GREEN may the real-train sequence advance again to jump/airborne/landing, then wall/ceiling, turns/speed changes, and free stable camera/look.

## Finalization policy — HARD USER RUNTIME GATE
Automated proof may advance to candidate build/verify but can never alone set `FINAL_READY`. A new exact JAR must pass direct user runtime for stable standing, forward/back/strafe/sprint, jump+airborne+natural landing, floor/walls/ceiling, turns, acceleration/deceleration/speed changes, no sink/throw/drift/lag-behind, and free/stable camera/look. Watchdog local SHA gate must match that exact accepted JAR.

## Fresh-chat/watchdog protocol
1. Inspect actual HEAD.
2. Read this file completely and reconcile `ledger_basis_head` with actual HEAD; ledger-only commits may advance HEAD without gameplay change.
3. Inspect only latest relevant Actions evidence for the active blocker.
4. Respect FROZEN_GREEN and FAILED_HYPOTHESES.
5. Execute `next_safe_action`; do not stop at narration.
6. HOLD only for a genuinely queued/in-progress relevant workflow/evidence.
7. No failure evidence = no symptom gameplay patch.
8. One commit = one hypothesis.
9. Never `FINAL_READY` from CI alone.
