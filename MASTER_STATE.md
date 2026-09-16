# MASTER_STATE — VS2 / Create Interactive

GitHub code is the implementation source of truth. This file is the durable project-state ledger. Chat is temporary.

## Project / hard contract
- Repository: `apm23/VS2-Create_Interactive`.
- Milestone: `M1 — movement / collision`.
- Create owns train/carriage gameplay and collision geometry.
- VS2 must be the actual continuous moving reference-space/transform foundation for player body/render/camera.
- Standing/walking/jumping must remain carriage-relative through grounded, airborne, turns, acceleration/deceleration and speed changes while mouse/look remains free.
- Create floor/walls/ceiling remain authoritative solid geometry in that same moving frame.
- Forbidden: fake gravity, synthetic carry velocity/inertia, manual floor/wall clamps, floor-only workarounds, per-tick teleport/setPos chase/reanchor architecture, duplicate Create/VS2 authority, direct camera forcing/rotation compensation, fake/proxy VS2 ships, or workaround chains hiding double ownership.

## Current reconciled state — 2026-09-16
- project_state: `ROOT_REDESIGN — JUMP-ARC LIFECYCLE PATCH LANDED; TWO EXACT NATURAL-LANDING REPRO ATTEMPTS BOTH FAIL BEFORE JUMP ADMISSION BECAUSE THE FINITE CI ROUTE EXHAUSTS STRICT CREATE SUPPORT; READ-ONLY ADMISSION-BOUNDARY VERIFIER ACTIVE`.
- production implementation basis: `c3e7c51a0751b542bdc7a0b8144880026a0f6fd8` (`Keep reference owner through native jump arc`).
- proof trigger head: `cb03574bd11d39ba21ef07e18ddfe7fc87c714ce` (`Trigger natural landing proof for lifecycle patch`); this changes only the executable mode of the existing fixture script to satisfy the workflow path trigger and adds no gameplay/harness semantics.
- admission verifier head: `85eaea024912c2a99aa9373002877edc790f41a7` (`Prove repeated pre-jump admission exhaustion`); verifier-only, no production or harness semantics changed.
- latest ledger-only commit may advance actual HEAD beyond the verifier head; always reconcile actual HEAD first.
- final_ready: `false`.
- exact historical failed user JAR SHA256: `96053e314891495fbb4bf16c446023568fed542497e083083dad7ed420dcd7ef`; never ask user to retest it.
- active blocker workflow: `m1-natural-landing-admission-boundary-proof`.
- active blocker run: `35065737938`, exact verifier head `85eaea0...`; `in_progress` when this ledger state was written.

## Historical direct-user runtime gate — authoritative regression evidence
Exact JAR SHA256 `96053e314891495fbb4bf16c446023568fed542497e083083dad7ed420dcd7ef` FAILED:
- floor hard/solid PASS and grounded walking PASS;
- walls soft FAIL;
- jump/airborne dragged player backward ~2–4 carriages FAIL;
- turns swept player/camera, wall could be penetrated, player could be thrown outside FAIL;
- behavior did not feel like a stable VS2 moving base FAIL.
This blocks `FINAL_READY` regardless of automated GREEN.

## Root architecture / protected structural proofs
- `6e079d62...`, run `34963733838`: old implementation was contact/lease reanchor, not continuous VS2 reference space.
- `c364910f...`, run `34969572212`: pinned VS2 native owner requires registered ShipId; fake/proxy ship is forbidden.
- `abb57fff...`, run `34972926851`: reference-owner redesign boundary mapped.
- `2eeac3f...`, run `34975161200`: core slice bounded to owner state/body drag/relative packet/server resolution/render/yaw; Create collision remains separate.
- `ebf4aaf...`, run `34977644889`: Create carriage Entity id + bilateral transforms available; pinned Create JAR SHA256 `d9c6cb6116d5caa1174a289ecd7d3cdd463ccef6e8db1249ab0bcfcd8c935870`.
- V1 run `34984299770`: generalized external owner state + Entity-id resolver + VS2 EntityDragger lifecycle.
- V2 run `34994353308` was structurally green, but later runtime disproved its original body-continuity assumptions.

## Scheduler / authority
- External-owner EntityDragger lifecycle requirement run `35008163064` remains protected.
- Production scheduler `0ce0dfd4...` applies only external-owner LocalPlayer drag after `ClientLevel.tick` and before Create collision; native VS2 ship scheduling remains separate.
- Historical active-owner ordinal-1 authority proof `35017634522` remains valid for its tested boundary.
- Run `35057564114` reopened only the lifecycle-transition seam: Create's ordinal-1 `singleReferenceOwnerCarryWriter` materially wrote the LocalPlayer after external-owner authority was cleared during the jump arc.
- Create OBB/grounding/floor/walls/ceiling remain authoritative. Do not suppress Create's first collision-response writer or global Create collision behavior.

## Transform / camera / look — FROZEN_GREEN
- Same-point transform run `35023234306`: exact same-point mismatch `0`; do not alter resolver prev/current/yaw/point semantics absent new contrary evidence.
- Camera run `35033671863`: external-owner spatial render wired, camera owner unwired.
- Look run `35034983734`: external-owner spatial follow with look uncoupled.
- Free look is desired; no camera counter-rotation/direct camera transform.

## OBB support-loss — FROZEN_GREEN
- Runtime `35031106237`: owner/carriage matched through support loss and Create callbacks continued.
- Semantics runs `35037369180`, `35037534677`, `35039049624`, `35040491258` established valid temporal-only solved response.
- Verifier run `35041914462`: `ACTIVE_OWNER_CREATE_COLLISION_FRAME_CONTINUOUS_TEMPORAL_ONLY`.
- `surface=true + collisionResponse=ZERO + 0<temporal<1` is valid Create behavior. OBB response is not the active blocker.

## Native drag gate / body writer — FROZEN_GREEN
- Run `35045444238`: `EXTERNAL_OWNER_NATIVE_GATE_NOT_REJECTING`; `should_drag=true`, rejected=0 through airborne ticks. Do not patch `isDraggable` / `vs$shouldDrag`.
- Verifier run `35048234680` over source run `35046701119`: `EXTERNAL_OWNER_BODY_WRITER_APPLIES_CALCULATED_STEP`, missed=0, max writer residual=0.0. Existing VS2 boundingBox/setPos writer applies its calculated frame step exactly when reached. Do not add or replace a body writer.

## Lifecycle evidence
### First false clear — PROVEN + previous production correction
- Verifier run `35048427002`: `EXTERNAL_OWNER_CLEARED_BY_GROUNDED_CONTACT_EXPIRY_ON_NATIVE_JUMP_TICK`.
- Production commit `a14260c...` prevented grounded expiry while `deltaMovement.y > 1.0E-5`.
- It added no movement vector, gravity, reanchor, collision override, camera mutation, or body writer.

### Descent support-miss boundary — FROZEN_GREEN for that exact boundary
- Run `35051781646`: `EXTERNAL_OWNER_ACTIVE_THROUGH_DESCENT_SUPPORT_MISS_MAX_AGE_EXPIRES_AFTERWARD`.
- This disproved a generic lifecycle extension for ordinary support-loss plateaus. Do not reinterpret the new jump-specific latch as a generic lease extension.

## Headless fixture false-landing boundary — PROVEN HARNESS ISSUE
- Static run `35051955516` mapped the headless native-aiStep fallback.
- Correlation run `35052085653`: `HEADLESS_FALSE_LANDING_DISARMS_JUMP_FALLBACK_AT_STRAFE_END_BEFORE_REAL_SUPPORT`.
- Commit `618da46...` keeps native aiStep alive for a bounded 40-tick jump arc and requires genuine Phase131 support reacquisition; fixture only.
- Commit `d284e7a...` restored intended locomotion sequencing.
- Verifier-only `b32ec95...` / `f2cbeaf...` and fixture commit `45b0d9d...` require strict Create support for reverse/strafe acceptance.

## Exact strict-support airborne failure — authoritative automated failure evidence
Run `35057564114`, job `104670818465`, exact head `45b0d9d...`, artifact `10431157630`, digest `sha256:006da4712f88e960567ee16f5de835956850fecf064c9fbaba4a3c6cccd35671`:
- jump REQUESTED/AIRBORNE tick47, native deltaY `+0.33319999363422365`;
- intended owner carriage7, no owner handoff before genuine landing;
- genuine same-owner support reacquisition tick56;
- owner-relative airborne drift FAIL `12.328706`;
- VS2 EntityDragger and authority suppression are active through tick48;
- tick49 Create contact motion and the direct ordinal-1 writer both apply exactly `(-5.002450315428566, 0.0, -4.299231054387661)`, magnitude about `6.59605`, while no external-owner suppression remains.

## Exact source-failure lifecycle proof — GREEN
Verifier-only commit `df90ce5a44e92c3afe43905dfd9a5ee0e1743912`, workflow `m1-reference-owner-v2-source-failure-lifecycle-proof`, run `35062047086` SUCCESS.
Classification:
`EXACT_FAILURE_FALSE_GROUNDED_EXPIRY_REOPENS_CREATE_CARRY`.
Pinned evidence:
- source run `35057564114`, source head `45b0d9d...`, artifact id `10431157630`, exact digest above;
- owner7 refresh tick46 occurs after that tick's scheduler writer, leaving owner age 0;
- no owner refresh ticks47–49; single scheduler progression derives ages 1,2,3;
- tick49 `onGround=true`, vertical motion `0.0`, strict Create support=false, genuine support only returns tick56;
- owner7 is still resolvable and age3 is far below the pinned VS2 drag cap `25`;
- current production predicate therefore sets `grounded_expired=true`, `owner_expired=false` and clears the owner;
- authority then falls through and the exact 6.59605-block Create ordinal-1 carry writer is applied with writer residual `0.0`.
This classification authorizes only a narrowly scoped jump-arc lifecycle correction, not transform/collision/camera changes or generic lease extension.

## Current production hypothesis — `c3e7c51...`
`prepare_vs2_26_2_reference_owner_v2_composefix.py` now composes one bounded jump-arc lifecycle state:
- `externalReferenceOwnerJumpActive` defaults false;
- genuine native upward motion (`deltaMovement.y > 1.0E-5`) arms it while the external owner is active;
- genuine Create owner refresh resets it false and age to 0;
- explicit owner clear also resets it false;
- grounded-contact expiry is disabled only while this jump latch is active;
- the existing `TICKS_TO_DRAG_ENTITIES = 25` hard cap remains unchanged and still bounds ownership if genuine support never returns.
No synthetic carry vector, gravity, teleport/reanchor, collision override, camera mutation, transform-math change, native-drag-gate change, or additional body writer is introduced.

## Natural-landing repro after jump-arc patch
Run `35062245886`, exact proof head `cb03574...`.
### Attempt1 — PRE-JUMP NON-ADMISSION; no gameplay inference
Artifact `10433880714`, digest `sha256:2bf9e1598489ea73cefaa87627345a20b9087ae397ef1c69a6488b8c4530b370`:
- production composition, harness composition, compile, world reconstruction and runtime launch all succeeded;
- owner/carriage5: walk confirmed tick20; backward confirmed at player tick25 for strict support tick24; strafe requested tick25 and confirmed tick26 for strict support tick25;
- strict Phase131 support for owner5 remained true through tick33 and becomes false at tick34;
- current jump admission requires `self.tickCount >= vs2$strafeStartTick + 15`, so earliest possible jump is tick40;
- jump request/airborne markers are absent; the route loses strict support before jump eligibility;
- therefore attempt1 never exercised the patched jump lifecycle and cannot classify production physics success/failure.
### Attempt2 — PRE-JUMP NON-ADMISSION; no gameplay inference
Artifact `10433634322`, digest `sha256:9f36a7b465de1f3d4b8776c02806c1ef43e751ef4e47032fbf9073863177d96d`:
- production composition, harness composition, compile, world reconstruction and runtime launch all succeeded;
- owner/carriage10: walk confirmed tick38; backward confirmed player tick43 for strict support tick42; right-strafe requested tick43;
- strict Phase131 support is true through tick42 and false from tick43; strafe confirmation never occurs and repeated `GATE_E_M1_NATIVE_STRAFE_REJECTED_NO_CREATE_SUPPORT` begins at player tick44 for motion/support tick43;
- jump request/airborne markers are absent; jump gate cannot open because support is already gone at strafe admission;
- therefore attempt2 also never exercised the patched jump lifecycle and cannot classify production physics success/failure.

## Repeated pre-jump admission boundary verifier — ACTIVE
Verifier-only commit `85eaea024912c2a99aa9373002877edc790f41a7`, workflow `m1-natural-landing-admission-boundary-proof`, run `35065737938`.
- Pins attempt1 artifact `10433880714` + exact digest and attempt2 artifact `10433634322` + exact digest.
- Verifies current harness admission anchors without changing them.
- Intended classification: `REPRODUCIBLE_PRE_JUMP_ADMISSION_ROUTE_EXHAUSTS_STRICT_SUPPORT`.
- This proof is explicitly verifier-only: no harness mutation, no production physics inference, no gameplay patch authorization.
- Run was `in_progress` when this ledger state was written.

## Diagnostic runtime attempts superseded by exact verifier
Read-only trace commit `b675e45...`, run `35058550331`:
- attempt1 reached a different healthy owner10 jump route and did not reproduce the material leak;
- attempt2 timed out before jump because strict-support fixture acceptance repeatedly rejected reverse movement;
- neither attempt authorized gameplay changes.
The exact source-failure verifier `35062047086` replaces nondeterministic reruns as the causal proof for this specific seam.

## FROZEN_GREEN / protected
- bootstrap/Kotlin packaging `f3d1335...`;
- Create train + VS2 coexistence;
- Steam 'n' Rails + Copycats preservation;
- V1 infrastructure `34984299770`;
- V2 structural/core `34994353308` except later-disproved runtime-continuity assumptions;
- external-owner lifecycle requirement `35008163064`;
- same-point transform `35023234306`;
- camera/free-look `35033671863`, `35034983734`;
- OBB temporal-only support-loss `35041914462`;
- native drag gate `35045444238`;
- exact existing VS2 body writer `35048234680` over `35046701119`;
- ordinary descent support-miss lifecycle `35051781646`;
- historical user-proven floor solidity and grounded walking.

## FAILED_HYPOTHESES / anti-loop
Do not reintroduce without new direct evidence:
- `EXACT_SHAPES_LOCALPLAYER_0fa4aa`;
- generic frame lease/replay/carry extension;
- generic lifecycle extension beyond evidence;
- synthetic carry velocity / inertia compensation;
- fake gravity;
- manual floor/wall clamps or floor-only workaround;
- per-tick teleport/setPos chase/reanchor architecture;
- direct camera forcing/rotation compensation;
- jump/input timing tuning as a production reference-frame fix;
- sprint/reverse/strafe tuning as reference-frame fix;
- unscoped/global collider suppression or suppression of Create's collision-response writer;
- duplicate Create/VS2 gameplay/collision authority;
- fake/proxy VS2 ship;
- harness mutation used to manufacture physics GREEN;
- resolver prev/current/yaw/point semantic changes after `35023234306` absent contrary evidence;
- treating temporal-only zero collisionResponse as failure;
- patching `isDraggable`/`vs$shouldDrag` after `35045444238`;
- adding/replacing a body-position writer after `35048234680`.

## next_safe_action
1. Inspect only `m1-natural-landing-admission-boundary-proof` run `35065737938` first.
2. If queued/in_progress: HOLD and stack no production or harness hypothesis.
3. If verifier GREEN with `REPRODUCIBLE_PRE_JUMP_ADMISSION_ROUTE_EXHAUSTS_STRICT_SUPPORT`, treat both natural-landing reruns as proof-route non-admission only. Then inspect the smallest fixture/admission boundary needed to obtain a valid strict-support-qualified jump without manufacturing physics success; do not patch production from this verifier.
4. If verifier fails because an artifact or marker contradicts the proposed classification, inspect only that exact contradiction and repair/verifier-classify it before any harness change.
5. Once a valid strict-support-qualified jump actually runs on production basis `c3e7c51...`: if `natural_landing_real_support_green`, freeze natural landing and advance to smallest wall/ceiling solidity proof; if owner-relative drift remains, inspect exact owner lifecycle/authority markers before any second gameplay hypothesis.
6. Revert `c3e7c51...` before stacking any workaround if a valid runtime proves it regresses a FROZEN_GREEN criterion.
7. Do not change transform math, native drag gate, VS2 body writer, OBB semantics, camera, gravity, or Create collision-response authority from this pre-jump CI admission seam.

## Finalization policy — HARD USER RUNTIME GATE
Automated proof can never alone set `FINAL_READY`. A new exact JAR must pass direct user runtime for stable standing, forward/back/strafe/sprint, jump+airborne+natural landing, floor/walls/ceiling, turns, acceleration/deceleration/speed changes, no sink/throw/drift/lag-behind, and free/stable camera/look. The watchdog local SHA gate must match that exact accepted JAR.

## Fresh-chat/watchdog protocol
1. Inspect actual HEAD.
2. Read this file completely and reconcile ledger/implementation/proof basis with actual HEAD.
3. Inspect only the latest relevant Actions evidence for the active blocker.
4. Respect FROZEN_GREEN and FAILED_HYPOTHESES.
5. Execute `next_safe_action`; do not stop at narration.
6. Keep watchdog turns compact and always end with exactly one valid standalone `WATCHDOG_DECISION:` line.
