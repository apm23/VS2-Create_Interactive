# MASTER_STATE — VS2 / Create Interactive

GitHub code is the implementation source of truth. This file is the durable project-state ledger. Chat is temporary.

## Project / hard contract
- Repository: `apm23/VS2-Create_Interactive`
- Milestone: `M1 — movement / collision`.
- Create owns train/carriage gameplay and collision geometry.
- VS2 must be the actual continuous moving reference-space/transform foundation for player body/render/camera.
- Standing/walking/jumping must remain carriage-relative through grounded, airborne, turns, acceleration/deceleration and speed changes while mouse/look remains free.
- Create floor/walls/ceiling remain authoritative solid geometry in that same moving frame.
- Forbidden: fake gravity, synthetic carry velocity/inertia, manual floor/wall clamps, floor-only workarounds, per-tick teleport/setPos chase/reanchor architecture, duplicate Create/VS2 authority, direct camera forcing/rotation compensation, fake/proxy VS2 ships, or workaround chains hiding double ownership.

## Current reconciled state — 2026-09-16
- project_state: `ROOT_REDESIGN — STRICT-SUPPORT-QUALIFIED JUMP REPRODUCES 12.328706 OWNER-LOCAL DRIFT; CREATE ORDINAL-1 CONTACT-CARRY WRITER LEAK IS DIRECTLY OBSERVED AT THE FIRST LARGE AIRBORNE DISCONTINUITY; FALSE-GROUNDED LIFECYCLE-CLEAR CAUSE TRACE ACTIVE`.
- diagnostic_basis_head: `b675e45990995ef773da743370e780f6aa8696db` (`Trace false-grounded owner expiry into Create carry`).
- latest ledger-only commit may advance actual HEAD beyond `diagnostic_basis_head`; always reconcile actual HEAD first.
- implementation/harness basis before the diagnostic: `45b0d9dd09cac507165bb5669df25d5a3cfebb44` (`Require strict Create support for fixture locomotion`).
- final_ready: `false`.
- exact historical failed user JAR SHA256: `96053e314891495fbb4bf16c446023568fed542497e083083dad7ed420dcd7ef`; never ask user to retest it.
- production scheduler patch: `0ce0dfd4f6f29685eb18b6e3a8c14ddc247bbb9b`.
- production active-owner Create carry authority patch: `652667e887720509f37618641e231f70e8e689c4`.
- production upward-jump lifecycle correction: `a14260cc76b61e5c6be0de38e634abe9ee7f0800`.
- active proof workflow: `m1-reference-owner-v2-lifecycle-authority-trace`.
- active proof run: `35058550331`, exact diagnostic head `b675e45...`; queued when this ledger state was written.
- `b675e45...` is read-only instrumentation only; no production gameplay/physics behavior changed.

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
- Production scheduler `0ce0dfd4...` moves only external-owner LocalPlayer drag after `ClientLevel.tick` and before Create collision; native VS2 ship scheduling is unchanged.
- Historical active-owner ordinal-1 authority proof `35017634522` was GREEN for its tested boundary.
- **REOPENED/NARROWED by latest direct runtime evidence:** run `35057564114` shows Create's ordinal-1 `singleReferenceOwnerCarryWriter` materially writing the LocalPlayer on airborne tick 49 while the same carriage is still the intended external reference owner. Therefore the older authority proof does not cover this lifecycle-transition seam and must not be treated as a stop signal for this exact failure.
- Create OBB/grounding/floor/walls/ceiling remain authoritative; do not suppress the first collision-response writer or global Create collision behavior.

## Transform / camera / look — FROZEN_GREEN
- Same-point transform run `35023234306`: exact same-point mismatch `0`; do not alter resolver prev/current/yaw/point semantics absent new contrary evidence.
- Camera run `35033671863`: external owner spatial render wired, camera owner unwired.
- Look run `35034983734`: external-owner spatial follow with look uncoupled.
- Free look is desired; no camera counter-rotation/direct camera transform.

## OBB support-loss — FROZEN_GREEN
- Runtime `35031106237`: owner/carriage 7 matched through support loss and Create callbacks continued.
- Semantics runs `35037369180`, `35037534677`, `35039049624`, `35040491258` established valid temporal-only solved response.
- Verifier run `35041914462`: `ACTIVE_OWNER_CREATE_COLLISION_FRAME_CONTINUOUS_TEMPORAL_ONLY`.
- `surface=true + collisionResponse=ZERO + 0<temporal<1` is valid Create behavior. OBB response is not the active blocker.

## Native drag gate / body writer — FROZEN_GREEN
- Run `35045444238`: `EXTERNAL_OWNER_NATIVE_GATE_NOT_REJECTING`; `should_drag=true`, rejected=0 through airborne ticks. Do not patch `isDraggable` / `vs$shouldDrag`.
- Verifier run `35048234680` over source run `35046701119`: `EXTERNAL_OWNER_BODY_WRITER_APPLIES_CALCULATED_STEP`, missed=0, max writer residual=0.0. Existing VS2 boundingBox/setPos writer applies its calculated frame step exactly when reached. Do not add or replace a body writer.

## Lifecycle evidence
### First false clear — PROVEN + production correction exists
Verifier run `35048427002`: `EXTERNAL_OWNER_CLEARED_BY_GROUNDED_CONTACT_EXPIRY_ON_NATIVE_JUMP_TICK`.
Production commit `a14260c...` changed only grounded expiry so `onGround=true` cannot clear while native vertical motion is genuinely upward (`deltaMovement.y > 1.0E-5`). It added no movement vector, gravity, reanchor, collision override, or body writer.

### Descent support-miss boundary — FROZEN_GREEN for that exact boundary
Run `35051781646`: `EXTERNAL_OWNER_ACTIVE_THROUGH_DESCENT_SUPPORT_MISS_MAX_AGE_EXPIRES_AFTERWARD`.
Owner5 stayed actively dragged through a support-miss plateau until the normal bounded drag cap. This disproved generic lifecycle extension as a fix for that older plateau.
This proof does **not** cover the newly observed false-`onGround` age-3 transition in run `35057564114`; do not conflate the two boundaries.

## Headless fixture false-landing boundary — PROVEN HARNESS ISSUE
- Static workflow run `35051955516` mapped `vs2$runNativeAiStepWhenHeadlessTickSkippedIt`.
- Correlation run `35052085653`: `HEADLESS_FALSE_LANDING_DISARMS_JUMP_FALLBACK_AT_STRAFE_END_BEFORE_REAL_SUPPORT`.
- Commit `618da46...` keeps native `aiStep` fallback alive for a bounded 40-tick jump arc and requires genuine Phase131 support reacquisition; fixture only, no direct player movement mutation.

## Natural-landing proof chain
### Sequencing / support qualification
- Run `35052376394` was invalid for production inference because jump occurred before intended reverse/strafe sequencing completed.
- Commit `d284e7a...` restored sequence `forward/walk -> backward -> strafe -> settle -> jump`.
- Run `35054065739` attempt1 showed pre-jump fixture/support nondeterminism (`ACQUIRE=0`, strict support=0), so it could not authorize physics changes.
- Attempt2 reacquired owner/support but showed the fixture could mark backward/strafe confirmed after strict support was already gone.
- Verifier-only commits `b32ec95...` / `f2cbeaf...` isolated that acceptance seam.
- Commit `45b0d9d...` is fixture/acceptance-only and now requires strict Create support freshness for backward/strafe confirmations. No production physics change.

### Latest valid strict-support-qualified jump — ACTIVE FAILURE EVIDENCE
Run `35057564114`, job `104670818465`, exact head `45b0d9d...`:
- compile, harness and runtime all succeeded;
- jump REQUESTED/AIRBORNE tick47; deltaY `+0.33319999363422365`;
- intended external owner is carriage7; no owner handoff before genuine landing;
- strict owner7 support was true at ticks45–46 before jump;
- genuine same-owner Phase131 support reacquisition occurs at tick56;
- verifier FAILS `owner-relative airborne drift too large: 12.328706`.
Artifact id `10431157630`, digest `sha256:006da4712f88e960567ee16f5de835956850fecf064c9fbaba4a3c6cccd35671`.

Critical owner-local rows for carriage7:
- tick47: `(3.701223, 2.420100, 2.548361)`
- tick48: `(3.201225, 2.425273, 2.630091)`
- tick50: `(5.101225, 2.425273, 2.630091)`
- tick51: `(-5.034572, 2.324900, -1.801512)` — first measured giant discontinuity
- tick56: `(-7.834616, 2.012868, -1.801512)` with genuine support reacquired.
Largest measured owner-local step tick50->51 is about 11.058 blocks.

### Direct writer evidence at the discontinuity
Exact run `35057564114` log proves:
- tick47 and tick48: VS2 EntityDragger applies the expected carriage-frame step and Create ordinal-1 contact carry is suppressed while external owner7 is active.
- tick49: no external-owner EntityDragger application is observed before Create collision; Create native contact application on carriage7 reports motion `(-5.002450315428566, 0.0, -4.299231054387661)` even though carriage7 frame step is only about `(+1.4000005722045898, 0, 0)`.
- tick49 LocalPlayer writer log identifies `ContraptionColliderClient ... vs2$singleReferenceOwnerCarryWriter` and materially applies exactly `(-5.002450315428566, 0.0, -4.299231054387661)`.
- there is no `REFERENCE_OWNER_V2_CREATE_CONTACT_CARRY_SUPPRESSED` marker for tick49.
Conclusion: the active blocker is no longer an unexplained transform mismatch. The external-owner authority gate becomes inactive before Create's ordinal-1 contact-carry writer on the failure tick, allowing duplicate/incorrect reference carry back in.

## Active read-only root-boundary trace
Commit `b675e45990995ef773da743370e780f6aa8696db` adds only read-only instrumentation plus a narrow workflow:
- `REFERENCE_OWNER_V2_LIFECYCLE_TRACE` immediately before the existing lifecycle-clear decision logs owner id, age, `onGround`, deltaY, upward flag, resolvability, grounded-expiry, cap-expiry, and `will_clear`.
- `REFERENCE_OWNER_V2_AUTHORITY_STATE` immediately before the ordinal-1 authority redirect's pass-through/suppress decision logs owner id, owner age, active state, carriage id, and requested delta.
- no production gameplay/physics behavior changes.
Workflow `m1-reference-owner-v2-lifecycle-authority-trace`, run `35058550331`, is the only active blocker proof to inspect next.
Target classification:
`FALSE_GROUNDED_LIFECYCLE_CLEAR_REOPENS_CREATE_CARRY`.
It must prove the same failure tick is: genuine jump already airborne; owner still resolvable; vanilla `onGround=true`; upward=false; grounded expiry true; cap expiry false; lifecycle clears owner; authority becomes inactive; material Create ordinal-1 carry is then applied.

## FROZEN_GREEN / protected
- bootstrap/Kotlin packaging `f3d1335...`;
- Create train + VS2 coexistence;
- Steam 'n' Rails + Copycats preservation;
- V1 infrastructure run `34984299770`;
- V2 structural/core run `34994353308` except later disproved runtime-continuity assumptions;
- external-owner lifecycle requirement run `35008163064`;
- same-point transform run `35023234306`;
- camera/free-look runs `35033671863`, `35034983734`;
- OBB temporal-only support-loss run `35041914462`;
- native drag gate open run `35045444238`;
- exact existing VS2 body writer run `35048234680` over source `35046701119`;
- descent support-miss lifecycle run `35051781646` for that exact boundary;
- historical user-proven floor solidity and grounded walking as protected behavioral criteria.
- Historical active-owner ordinal-1 authority run `35017634522` remains historical evidence but is **not frozen for the newly exposed lifecycle-transition seam** after run `35057564114`.

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
- resolver prev/current/yaw/point semantic changes after run `35023234306` absent contrary evidence;
- treating temporal-only zero collisionResponse as failure;
- patching `isDraggable`/`vs$shouldDrag` after run `35045444238`;
- adding/replacing a body-position writer after run `35048234680`.

## next_safe_action
1. Inspect only `m1-reference-owner-v2-lifecycle-authority-trace` run `35058550331` first.
2. If queued/in_progress: HOLD and stack no new production/harness hypothesis.
3. If compile/instrumentation/verifier mechanics fail before useful runtime evidence: repair this diagnostic only; no production physics patch.
4. If it proves `FALSE_GROUNDED_LIFECYCLE_CLEAR_REOPENS_CREATE_CARRY`, make exactly one narrowly scoped production lifecycle/authority patch backed by that classification, preserving bounded ownership and avoiding generic lifecycle extension; then rerun the same strict-support natural-landing proof.
5. If it disproves grounded-expiry as the clear cause, inspect only the exact `activeExternalOwner` ingredients on the leak tick (owner id, age/cap, mounted state, resolver) before any production patch.
6. Do not change transform math, native drag gate, VS2 body writer, OBB semantics, camera, gravity, or collision-response authority from this evidence.
7. Only after strict-support natural landing is GREEN advance to wall/ceiling solidity, then turns/speed-change stability.

## Finalization policy — HARD USER RUNTIME GATE
Automated proof can never alone set `FINAL_READY`. A new exact JAR must pass direct user runtime for stable standing, forward/back/strafe/sprint, jump+airborne+natural landing, floor/walls/ceiling, turns, acceleration/deceleration/speed changes, no sink/throw/drift/lag-behind, and free/stable camera/look. The watchdog local SHA gate must match that exact accepted JAR.

## Fresh-chat/watchdog protocol
1. Inspect actual HEAD.
2. Read this file completely and reconcile diagnostic/implementation basis with actual HEAD; ledger-only/diagnostic commits may advance HEAD without gameplay mutation.
3. Inspect only the latest relevant Actions evidence for the active blocker.
4. Respect FROZEN_GREEN and FAILED_HYPOTHESES.
5. Execute `next_safe_action`; do not stop at narration.
6. Keep watchdog turns compact and always end with exactly one valid standalone `WATCHDOG_DECISION:` line.
