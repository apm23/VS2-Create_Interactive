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
- `current_head`: `ff07454329a214a27485c3e4c317c7dadd7818d6` when this ledger was written.
- project_state: `ROOT_REDESIGN — ATTEMPT3 ADMITTED A VALID NATIVE JUMP; EXACT VERIFIERS PROVE THE ORDINARY 25-TICK OWNER CAP EXPIRES TWO TICKS BEFORE SAME-OWNER NATIVE CREATE LANDING AND CAUSES EXACT CARRIAGE-RELATIVE LAG; ONE NARROW JUMP-LANDING OWNER-LIFETIME PATCH LANDED; CURRENT-HEAD NATURAL-LANDING PROOF ACTIVE`.
- production implementation basis: `d6e55e2912d863e831ce088d26785b534a4b200d` (`Keep jump owner through native Create landing`).
- proof-trigger head: `ff07454329a214a27485c3e4c317c7dadd7818d6` (`Trigger natural landing proof for jump owner landing patch`); workflow/test wiring only after the production commit.
- final_ready: `false`.
- exact historical failed user JAR SHA256: `96053e314891495fbb4bf16c446023568fed542497e083083dad7ed420dcd7ef`; never ask user to retest it.
- active blocker workflow: `m1-reference-owner-v2-natural-landing-proof-v2`.
- active blocker run: `35071527097`, exact head `ff074543...`; `queued` when this ledger state was written.
- known invalid workflow noise: `.github/workflows/m1-reference-owner-v2-airborne-drag-boundary-proof-v2.yml` emits instant zero-job failures; ignore it.

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
### First false clear — PROVEN + corrected
- Verifier run `35048427002`: `EXTERNAL_OWNER_CLEARED_BY_GROUNDED_CONTACT_EXPIRY_ON_NATIVE_JUMP_TICK`.
- Production commit `a14260c...` prevented grounded expiry while `deltaMovement.y > 1.0E-5`.

### Ordinary descent support-miss — FROZEN_GREEN
- Run `35051781646`: `EXTERNAL_OWNER_ACTIVE_THROUGH_DESCENT_SUPPORT_MISS_MAX_AGE_EXPIRES_AFTERWARD`.
- This disproved a generic lifecycle/lease extension. The current patch is jump-active/same-owner-native-contact specific; do not reinterpret it as a generic extension.

### Exact strict-support airborne failure — authoritative automated failure
Run `35057564114`, job `104670818465`, exact head `45b0d9d...`, artifact `10431157630`, digest `sha256:006da4712f88e960567ee16f5de835956850fecf064c9fbaba4a3c6cccd35671`:
- jump REQUESTED/AIRBORNE tick47, native deltaY `+0.33319999363422365`;
- intended owner carriage7, no owner handoff before genuine landing;
- genuine same-owner support reacquisition tick56;
- owner-relative airborne drift FAIL `12.328706`;
- owner authority active through tick48;
- tick49 owner cleared and Create ordinal-1 writer applies `(-5.002450315428566,0,-4.299231054387661)`, magnitude ~`6.59605`.

### Exact false-grounded lifecycle proof — GREEN
Verifier-only run `35062047086`, commit `df90ce5...`:
`EXACT_FAILURE_FALSE_GROUNDED_EXPIRY_REOPENS_CREATE_CARRY`.
This authorized only the bounded jump-arc lifecycle correction `c3e7c51...`.

## Previous production hypothesis — `c3e7c51...`
`c3e7c51a0751b542bdc7a0b8144880026a0f6fd8` added `externalReferenceOwnerJumpActive`:
- arm only on genuine native upward motion;
- suppress false-grounded age-3 expiry while jump-active;
- reset on owner refresh/clear;
- ordinary hard cap remained 25.
No motion vector, gravity, teleport/reanchor, collision override, camera mutation, transform change, native-drag-gate change, or body writer was added.

## Natural-landing run `35062245886` on `c3e7c51...`
### Attempts1/2 — PRE-JUMP NON-ADMISSION ONLY
Admission verifier run `35067811102` SUCCESS:
`REPRODUCIBLE_PRE_JUMP_ADMISSION_ROUTE_EXHAUSTS_STRICT_SUPPORT`.
- attempt1 artifact `10433880714`, digest `sha256:2bf9e1598489ea73cefaa87627345a20b9087ae397ef1c69a6488b8c4530b370`;
- attempt2 artifact `10433634322`, digest `sha256:9f36a7b465de1f3d4b8776c02806c1ef43e751ef4e47032fbf9073863177d96d`;
- neither reached jump; no production physics inference.
- harness blob is exactly the same `f8aad6e7425a37251f670f5e15c79b82c56e5472` as historical strict-support jump-admit run `35057564114`, so `+15` settle timing is not a dead path and must not be shortened merely to manufacture admission.

### Attempt3 — VALID JUMP, OWNER-CAP FAILURE BOUNDARY
Run `35062245886` attempt3, artifact `10434807961`, digest `sha256:ee7da59e8eebd01e017c023175e1845db04ed5ffd0dca8ab8d4720c98d4a236a`:
- jump REQUESTED/AIRBORNE tick45, deltaY `+0.33319999363422365`;
- owner8 final pre-jump refresh tick43;
- external-owner authority remains active through tick67;
- ordinary 25-tick owner cap expires tick68;
- native Create landing boundary for same owner8 occurs tick70;
- original natural-landing verifier failed `no genuine Create support reacquisition owner=8` because Phase131 heuristic reports `physical_support=false` at tick70 with vertical gap `0.062619575477541`, slightly above its hard `0.05` threshold.

Verifier-only run `35069183590` SUCCESS classified:
`HEADLESS_ARC_REACHES_OWNER_CAP_BEFORE_NATIVE_CREATE_LANDING_PHASE131_GAP_FALSE_NEGATIVE`.
Pinned tick70 landing evidence:
- Create OBB surface=true and LocalPlayer onGround=true;
- native Create contact application owner8 motion `(+0.16304755210876465,0,0)`;
- Create setOnGround requested/applied true;
- local owner state remains settled through ticks70–75 despite Phase131's false-negative threshold.

## Exact owner-cap frame-lag proof — GREEN
Verifier-only commit `e103a7ca5aa63f2d12571d93957ac963d293d255`, workflow `m1-natural-landing-owner-cap-lag-proof`, run `35071088843` SUCCESS.
Classification:
`OWNER_CAP_EXPIRES_BEFORE_NATIVE_CREATE_LANDING_AND_CAUSES_EXACT_FRAME_RELATIVE_LAG`.
Pinned result:
- owner8 refresh tick43; generic cap=25; expiry tick68; last authority tick67;
- carriage8 frame step tick68 + tick69 totals `0.330086470` blocks;
- owner-local X lag from tick67 to tick69 is exactly `0.330086470` blocks; residual `0.000000000`;
- native same-owner Create landing/contact begins tick70;
- therefore the two-tick loss of VS2 owner authority directly causes the exact carriage-relative lag. This is production failure evidence, not verifier noise.

## Grounding/source map — READ-ONLY GREEN
Commit `699247d89734a3473a566ac919fa75497ecc8f66`, run `35069989978` SUCCESS:
`EXISTING_GROUNDING_GUARD_AND_FINAL_MOTION_WRITES_LOCATED`.
- Phase64 owns the existing Create `setOnGround` guard and grounded negative-Y final-motion clip.
- This source map alone does NOT authorize modifying Phase64; no Phase64 gameplay patch was made.

## Current production hypothesis — `d6e55e2...`
One hypothesis only: **an already-armed jump owner must remain authoritative until same-owner native Create landing, then return immediately to the ordinary grounded lifecycle.**
Implementation in `prepare_vs2_26_2_reference_owner_v2_composefix.py`:
- ordinary external-owner lifetime remains `TICKS_TO_DRAG_ENTITIES = 25` when not jump-active;
- jump-active lifetime has a separate bounded safety limit of 40 ticks;
- both `isEntityBeingDraggedByExternalReference()` and lifecycle expiry use the same state-derived lifetime limit, so drag eligibility and expiry cannot disagree;
- strict Phase81 support remains required for new acquisition/handoff;
- when strict support is false, only an already-existing same owner can refresh from native Create contact;
- during jump-active state, that fallback is admitted only after the ordinary 25-tick boundary, preventing early false-grounded contact from disarming the jump latch;
- after native grounded same-owner refresh, jumpActive resets false; subsequent same-owner grounded native Create contacts may refresh the existing owner even when Phase131's `0.05` heuristic is false-negative;
- if native contact ceases, ordinary grounded expiry again releases the owner quickly; generic shore-release behavior is preserved.
No synthetic motion, gravity, setPos chase/reanchor, collision override, transform math change, camera mutation, native drag gate change, or new body writer.

## Active current-head proof
- workflow `m1-reference-owner-v2-natural-landing-proof-v2` now includes the composefix path so a production lifecycle change automatically runs the exact fixture.
- active run `35071527097`, exact head `ff07454329a214a27485c3e4c317c7dadd7818d6`.
- The workflow's historical final classifier still uses Phase131 `physical_support=true` as the landing predicate; attempt3 proved that predicate can false-negative at a real native Create landing. Therefore, if this run reaches runtime and fails only with the same `no genuine Create support reacquisition` message, do NOT infer production failure or success from that message alone: inspect the exact artifact for owner continuity, `REFERENCE_OWNER_V2_NATIVE_GROUNDED_REFRESH`, native Create landing markers, and carriage-relative drift before changing gameplay again.

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
- adding/replacing a body-position writer after `35048234680`;
- changing Phase64 grounding/Y-clip behavior merely because the source-map workflow located it.

## next_safe_action
1. Inspect only current-head natural-landing run `35071527097` first.
2. If queued/in_progress: HOLD; stack no gameplay, harness, transform, collision, or verifier hypothesis.
3. If compile/composition fails: repair only the current jump-landing lifecycle patch mechanics; do not change physics semantics from a compile failure.
4. If runtime reaches a valid strict-support-qualified jump: inspect the exact artifact before any further gameplay change.
5. If `REFERENCE_OWNER_V2_NATIVE_GROUNDED_REFRESH` occurs at same-owner native landing and owner-relative continuity remains within proof thresholds through landing, create/repair only the exact artifact verifier as needed; do not stack a second gameplay hypothesis because the historical Phase131 landing predicate is known false-negative.
6. If owner authority still drops before same-owner native landing or material carriage-relative drift remains, classify the exact lifecycle/authority marker sequence before any second gameplay patch.
7. Revert `d6e55e2...` before stacking a workaround if a valid runtime proves it regresses a FROZEN_GREEN criterion.
8. Only after natural landing is genuinely GREEN advance to smallest wall/ceiling solidity proof, then turns/speed changes.
9. Do not alter transform math, native drag gate, VS2 body writer, OBB semantics, camera, gravity, Phase64 grounding/Y-clip, or Create collision-response authority from this lifecycle seam without new direct evidence.

## Finalization policy — HARD USER RUNTIME GATE
Automated proof can never alone set `FINAL_READY`. A new exact JAR must pass direct user runtime for stable standing, forward/back/strafe/sprint, jump+airborne+natural landing, floor/walls/ceiling, turns, acceleration/deceleration/speed changes, no sink/throw/drift/lag-behind, and free/stable camera/look. The watchdog local SHA gate must match that exact accepted JAR.

## Fresh-chat/watchdog protocol
1. Inspect actual HEAD.
2. Read this file completely and reconcile `current_head`/implementation/proof basis with actual HEAD.
3. Inspect only the latest relevant Actions evidence for the active blocker.
4. Respect FROZEN_GREEN and FAILED_HYPOTHESES.
5. Execute `next_safe_action`; do not stop at narration.
6. Keep watchdog turns compact and always end with exactly one valid standalone `WATCHDOG_DECISION:` line.
