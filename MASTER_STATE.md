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
- project_state: `ROOT_REDESIGN — ACTIVE-OWNER AUTHORITY GREEN; TURN/REFERENCE-POINT TIMING MICRO-PROOF ACTIVE`
- ledger_basis_head: `7bf93e0b8b9c8c9eac56f6f9a5aff2df9394a20d`
- final_ready: `false`
- exact historical failed user JAR SHA256: `96053e314891495fbb4bf16c446023568fed542497e083083dad7ed420dcd7ef`
- user_runtime_validation: historical candidate FAILED; no authority-fixed V2 candidate has been built/tested by the user.
- current diagnostic workflow: `m1-reference-owner-v2-point-timing-microproof`
- current diagnostic commit: `7bf93e0b8b9c8c9eac56f6f9a5aff2df9394a20d`
- current diagnostic run: `35023234306` — in progress when this ledger was written.

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
- artifact showed Create `ContraptionColliderClient.collideEntities:330` applying material contact carry while VS2 external owner was active.

## Scheduler root and proof
- Runtime proved external owner could acquire while LocalPlayer body branch never executed because pinned VS2 `MixinMinecraft.postTick()` scheduled `EntityDragger` only when native VS2 ships existed.
- scheduler fix commit `f81507dd...`: preserves native Ship scheduling and also schedules the drag sweep while LocalPlayer has an external reference owner; no collision/motion/camera algorithm added.
- scheduler proof run `35008163064` SUCCESS: external owner now reaches VS2 EntityDragger body lifecycle. This exposed duplicate movement authority rather than transform absence.

## Active-owner contact-carry authority — FROZEN_GREEN
- Runtime showed VS2 body movement and Create ordinal-1 contact-point carry could both move LocalPlayer in the same tick.
- independent artifact also proved a sibling carriage callback could apply a second material ordinal-1 carry after exact-owner suppression.
- authority fix commit `652667e887720509f37618641e231f70e8e689c4` (`Scope Create contact carry to active VS2 reference owner`).
- authority proof commit `07dbd852712c3c3d81b4d405e253befd4b34ac65`; run `35017634522`, job `104544985035`: SUCCESS.
- proof: exact-owner suppressions `18`; sibling suppressions `3`; sibling pairs `[(8,10),(10,8)]`; `material_line330_overlap=[]`; `collision_response_writer_untouched=true`; conclusion `single_reference_body_writer_proven`.
- scope is narrow: LocalPlayer only, valid active external owner only, Create `collideEntities` ordinal-1 contact carry only. Create first collision-response setPos, OBB, grounding, damage, floor/wall/ceiling geometry remain untouched. No synthetic movement added.
- This boundary is FROZEN_GREEN unless later direct runtime evidence contradicts it.

## Authority-fixed real-train retest — NEW ROOT EVIDENCE
Workflow commit `c7a797d3ba89c43f33365d6d1ded9bad65f6d841`, run `35020203661`:
- attempt 1 failed before source compile/runtime because Maven Central returned HTTP 403 for ordinary dependencies; no gameplay evidence.
- attempt 2: composition PASS, `:fabric:compileJava` PASS, verified r0v3 fixture PASS, assets PASS, then runtime proof timed out waiting for jump.
- carriage present + train moving PASS.
- external owner acquisition PASS: owner carriage 2 initially, then carriage 4; carriage 4 refreshed through player tick 33.
- bounded forward walk PASS (`GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED`).
- native backward PASS at tick 33.
- native right strafe PASS at tick 34.
- jump REQUESTED/AIRBORNE/LANDED markers: all absent. Do NOT treat this as jump-input failure.
- jump arm remained blocked because fresh floor/native-contact prerequisites disappeared before the delay window: last owner acquisition tick 33; last Create native contact application tick 42; later `known_native_fresh=false` and floor support stale.
- legacy Phase83/205 reanchor markers remained absent.

### Exact turn/reference-frame seam from attempt 2
The first concrete rotational/frame discontinuity appears before any jump can be requested:
- tick 43 carriage 4 local feet approximately `(2.6657, 1.2315, 3.3001)`.
- tick 44 carriage 4 frame center step approximately `(+20.5294, 0, 0)` while Create contact-point motion at its sampled point is approximately `(-24.8609, 0, -5.6394)`.
- the VS2 EntityDragger body setPos at tick 44 applies approximately `(+24.8609, 0, +5.6002)`.
- carriage-local feet flip to approximately `(-1.6657, 1.1531, -2.3197)` on tick 44, then return near `(2.6657, 0.9979, 3.3571)` on tick 45.
- this is turn/reference-transform evidence and explains why support/contact continuity collapses before the fixture can arm jump. It does not authorize jump-input tuning, gravity, wall clamps, camera forcing, or generic carry leases.

### Exact Create transform semantics checked against source
Public Create-Fly source at the runtime package seam shows:
- `toGlobalVector(local, partialTicks, prevAnchor)` chooses `getPrevAnchorVec()` only when `prevAnchor=true`, rotates at requested partial tick, then adds anchor.
- `toLocalVector(global, partialTicks, prevAnchor)` performs the inverse.
- base `getAnchorVec() = position()` and `getPrevAnchorVec() = getPrevPositionVec()`.
- Create `getContactPointMotion(globalContactPoint)` computes current rotation of the point derived from previous frame, then adds entity anchor/position movement.
Therefore the next distinction is not a guessed anchor flag. The proof must compare V2 and Create-native movement at the SAME reference point and expose whether `EntityDragger` postTick's `entity.xo/yo/zo` reference differs from the current point Create later evaluates during collision.

## Current read-only point/timing micro-proof
- commit `7bf93e0b8b9c8c9eac56f6f9a5aff2df9394a20d` adds workflow `m1-reference-owner-v2-point-timing-microproof` only; no production physics mutation.
- run `35023234306` was in progress when ledger written.
- exact composition includes V2 + scheduler fix + FROZEN_GREEN authority fix on the verified r0v3 train.
- diagnostic instruments EntityDragger at the existing `addedMovement` computation and compares:
  - V2 body delta;
  - Create `getContactPointMotion()` evaluated at the exact same `entityReferencePos`;
  - Create motion evaluated at current LocalPlayer position;
  - `entityReferencePos` vs current position vs `xo/yo/zo`;
  - owner age and previous/current carriage yaw.
- expected classification is evidence-driven: same-point transform matches native => point/timing ownership bug; same-point transform diverges => resolver transform semantics bug.

## FROZEN_GREEN / protected
- bootstrap/Kotlin packaging repair `f3d1335c9fc89283d936af039eba34aa9778bd05`.
- Create train + VS2 coexistence.
- Steam 'n' Rails + Copycats preservation.
- V1 infrastructure run `34984299770`.
- V2 structural/core run `34994353308` except the old body-continuity assumption disproved by runtime.
- scheduler boundary proved by `35008163064` unless later direct regression evidence contradicts it.
- active-owner ordinal-1 contact-carry authority boundary `652667e...` / run `35017634522`.
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
- harness mutation used to manufacture GREEN.

Clarification: the proven authority arbitration is not forbidden global suppression. It is LocalPlayer-only, active-reference-owner scoped, and ordinal-1 contact-carry-only while Create collision response remains authoritative.

## next_safe_action
1. Inspect run `35023234306` first.
2. If queued/in_progress: HOLD; stack no patch.
3. If it succeeds, use its same-point classification to patch only the proven reference-point/transform boundary, one hypothesis, then rerun the smallest real-train turn proof before attempting jump.
4. If it fails due workflow/compile/verifier only, repair harness only.
5. If runtime same-point transform matches Create native but current-point motion differs materially on turn ticks, inspect/patch EntityDragger's reference-point/tick application semantics; do not change Create collision or authority suppression.
6. If runtime same-point transform itself diverges materially, inspect/patch resolver previous/current transform semantics; do not alter movement input, gravity, support leases, walls, or camera.
7. Only after turn-local continuity is GREEN may the real-train sequence advance again to jump/airborne/landing, then wall/ceiling, turns/speed changes, and free stable camera/look.

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
