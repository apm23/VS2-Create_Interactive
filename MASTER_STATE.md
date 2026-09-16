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
- project_state: `ROOT_REDESIGN — NATURAL JUMP REPRODUCES LARGE OWNER-LOCAL AIRBORNE DRIFT; NATIVE isDraggable/vs$shouldDrag GATE PROVEN OPEN; EXACT VS2 BODY-WRITER APPLICATION PROOF ACTIVE`
- proof_basis_head: `5984d3bc336c2dc31109fcbba24d1c3bdae92447` (`Trace external-owner body writer application`).
- final_ready: `false`.
- exact historical failed user JAR SHA256: `96053e314891495fbb4bf16c446023568fed542497e083083dad7ed420dcd7ef`.
- user_runtime_validation: historical candidate FAILED; never ask the user to retest that SHA.
- production scheduler patch: `0ce0dfd4f6f29685eb18b6e3a8c14ddc247bbb9b`.
- production active-owner Create carry authority patch: `652667e887720509f37618641e231f70e8e689c4`.
- current diagnostic workflow: `m1-reference-owner-v2-drag-apply-proof`.
- current diagnostic run: `35046701119` — `in_progress` when this ledger was written, exact proof head `5984d3bc...`.
- current diagnostic is read-only; production gameplay/physics source is unchanged.

## Historical direct-user runtime gate — authoritative regression evidence
Exact JAR SHA256 `96053e314891495fbb4bf16c446023568fed542497e083083dad7ed420dcd7ef` FAILED:
- floor hard/solid PASS;
- grounded walking PASS;
- walls soft FAIL;
- jump/airborne dragged player backward ~2–4 carriages FAIL;
- turns swept player/camera and could throw player outside FAIL;
- behavior did not feel like a stable VS2 moving base FAIL.
This blocks `FINAL_READY` regardless of automated GREEN.

## Root architecture / implementation proofs
- `6e079d62...`, run `34963733838` SUCCESS: old implementation was contact/lease reanchor, not continuous VS2 reference space.
- `c364910f...`, run `34969572212` SUCCESS: pinned VS2 native owner lifecycle requires registered ShipId; no public non-Ship native owner seam. Fake/proxy ship forbidden.
- `abb57fff...`, run `34972926851` SUCCESS: reference-owner redesign boundary mapped.
- `2eeac3f...`, run `34975161200` SUCCESS: M1 core slice bounded to owner state/body drag/relative packet/server resolution/standing render/yaw; Create collision stays separate.
- `ebf4aaf...`, run `34977644889` SUCCESS: Create carriage entity id + bilateral transforms available. Pinned Create JAR SHA256 `d9c6cb6116d5caa1174a289ecd7d3cdd463ccef6e8db1249ab0bcfcd8c935870`.
- V1 through run `34984299770` SUCCESS: generalized external owner state + Entity-id resolver + VS2 EntityDragger lifecycle.
- V2 `5f687aca...` / composefix `ea546f83...` / run `34994353308` SUCCESS: selected Create owner, dedicated PacketPlayerReferenceMotion, same-owner client/server/render/yaw path, no fake ship, old reanchor authority removed.
- Initial V2 real-train run `34997330399` FAILURE: airborne owner-relative drift ~93.48 blocks and double movement authority.

## Scheduler / authority — protected production boundaries
- External-owner EntityDragger lifecycle required: `f81507dd...`, run `35008163064` SUCCESS — FROZEN_GREEN.
- Runtime order run `35025200849`: old order was Create collision before VS2 drag.
- Production scheduler `0ce0dfd4...` moves ONLY external-owner LocalPlayer drag after ClientLevel.tick and before Create collision; native VS2 ship scheduling stays native.
- Active-owner Create ordinal-1 carry authority `652667e...`; run `35017634522` SUCCESS: `single_reference_body_writer_proven` for the scoped carry boundary.
- Authority scope remains narrow: LocalPlayer + valid external owner + Create ordinal-1 material carry only. Create OBB/grounding/floor/walls/ceiling remain authoritative.

## Transform / camera / look — FROZEN_GREEN
- Same-point transform run `35023234306` SUCCESS: `SAME_POINT_TRANSFORM_MATCHES_NATIVE_POINT_TIMING_DIFFERS`, exact same-point mismatch 0. Do NOT change resolver prev/current/yaw/point semantics absent contrary evidence.
- Camera run `35033671863` SUCCESS: `PLAYER_OWNER_RENDER_WIRED_CAMERA_OWNER_UNWIRED`.
- Look run `35034983734` SUCCESS: `EXTERNAL_OWNER_CAMERA_SPATIAL_FOLLOWS_PLAYER_LOOK_REMAINS_UNCOUPLED`.
- Free look is desired. Do NOT add camera counter-rotation/direct camera transform.

## OBB support-loss chain — FROZEN_GREEN
Source runtime `35031106237`: owner/carriage 7 matched ticks24–39, support true through33 then false34+, local Y stayed ~2.0001, Create collision callbacks continued.
- `35036337486` originally classified zero response as failure; this verifier criterion was overstrict.
- `35037369180`: zero response with finite descriptors and positive temporal.
- `35037534677`: Create result semantics mapped.
- `35039049624`: explicit producer paths + independent normalized consumer.
- `35040491258`: `CREATE_OBB_SUPPORTS_TEMPORAL_ONLY_SOLVED_RESPONSE`.
- verifier-only `4c0a157...`; run `35041914462` SUCCESS: `ACTIVE_OWNER_CREATE_COLLISION_FRAME_CONTINUOUS_TEMPORAL_ONLY`.
Conclusion: `surface=true + collisionResponse=ZERO + 0<temporal<1` is valid Create behavior. OBB response is NOT the active blocker.

## Natural airborne proof — current direct gameplay failure
Workflow `m1-reference-owner-v2-natural-landing-proof`:
- YAML-only failures were repaired; no gameplay conclusion from invalid workflow runs.
- run `35042299917`, job `104624575166`: composition/compile/fixture/runtime reached real jump; verifier FAILED `owner-relative airborne drift too large: 21.599091`.
- artifact id `10425533703`, digest `sha256:9b3a9596b03e31625e7aeadc194b7e2faf21e2d6e9fef45a1329ddd370c07e39`.
- jump REQUESTED tick30; AIRBORNE tick30 with vanilla +0.3331999936 vertical delta.
- apparent LANDED tick37 is not carriage landing because support/broadphase already lost.
- carriage7 local feet were continuous through tick33 then jumped catastrophically at tick34 (~+25 local X); selected Create candidate switched 7->5 while persistent external owner remained 7.
- This is direct gameplay failure evidence and authorizes root-boundary diagnosis only.

## Airborne drag boundary evidence
Read-only boundary proof chain ultimately established at the jump boundary:
- external owner 7 remains active;
- scheduler calls EntityDragger;
- expected owner-frame step is material while observed owner-relative continuity still fails.
Harness-only failures in early diagnostic revisions are not gameplay evidence.

## Native drag-gate proof — RESOLVED
Commit chain ended at head `7bdffa8bab3f9b41fa4c1dcac3cbadf25efc015c`; run `35045444238` completed with workflow conclusion failure ONLY because the verifier expected the gate-rejection hypothesis.
Useful runtime classification:
`REFERENCE_OWNER_V2_DRAG_GATE_PROOF classification=EXTERNAL_OWNER_NATIVE_GATE_NOT_REJECTING focus_tick=59 rows=28 rejected=0 airborne_rejected=0 branch_ticks=[52,53,54,55,56,57,58,59] apply_ticks=[] read_only=true gameplay_mutation=false final_ready=false`
Runtime rows show `shipyard=false provider=true should_drag=true result=true` across grounded and airborne ticks. Therefore:
- `isDraggable` / `vs$shouldDrag` is NOT the active blocker;
- external-owner branch executes while airborne;
- `apply_ticks=[]` is not evidence that the writer failed because that prior repaired trace intentionally removed the brittle application-marker hook.
Do NOT patch the native gate.

## Exact VS2 body-writer boundary — ACTIVE
Pinned upstream EntityDragger apply path is now explicitly mapped:
1. external owner computes `addedMovement = currentWorld - entityReferencePos`;
2. guard requires `dragTheEntity && addedMovement != null && finite`;
3. existing VS2 writer moves boundingBox then calls existing `entity.setPos(entity + addedMovement)`;
4. addedMovementLastTick is then published.
This existing writer is production code; no new movement writer was added.

Proof commit `5984d3bc336c2dc31109fcbba24d1c3bdae92447` adds only:
- `scripts/prepare_vs2_26_2_reference_owner_v2_drag_apply_trace.py`;
- `.github/workflows/m1-reference-owner-v2-drag-apply-proof.yml`.
The trace logs calculated movement, pre-writer position, and immediate post-setPos position without changing setPos/boundingBox writer counts.
Verifier classifications:
- `EXTERNAL_OWNER_BODY_WRITER_APPLIES_CALCULATED_STEP`;
- `EXTERNAL_OWNER_BODY_WRITER_MISSES_CALCULATED_STEP`;
- `EXTERNAL_OWNER_BODY_WRITER_DIVERGES_FROM_CALCULATED_STEP`;
- unresolved only for insufficient runtime evidence.
Active run: `35046701119`.

## FROZEN_GREEN / protected
- bootstrap/Kotlin packaging `f3d1335...`;
- Create train + VS2 coexistence;
- Steam 'n' Rails + Copycats preservation;
- V1 infrastructure run `34984299770`;
- V2 structural/core run `34994353308` except runtime body-continuity assumptions already disproved;
- external-owner EntityDragger lifecycle requirement run `35008163064`;
- active-owner ordinal-1 authority boundary `652667e...` / run `35017634522`;
- same-point transform equivalence run `35023234306`;
- camera/free-look runs `35033671863`, `35034983734`;
- OBB temporal-only support-loss slice run `35041914462`;
- historical user-proven floor solidity and grounded walking as protected behavioral criteria.

## FAILED_HYPOTHESES / anti-loop
Do not reintroduce without new direct evidence:
- `EXACT_SHAPES_LOCALPLAYER_0fa4aa`;
- generic frame lease/replay/carry extension;
- synthetic carry velocity / inertia compensation;
- fake gravity;
- manual floor/wall clamps or floor-only workaround;
- per-tick teleport/setPos chase/reanchor architecture;
- direct camera forcing/rotation compensation;
- jump/input timing tuning without input-specific evidence;
- sprint/reverse/strafe tuning as reference-frame fix;
- unscoped/global collider suppression or suppression of Create collision-response writer;
- duplicate Create/VS2 gameplay/collision authority;
- fake/proxy VS2 ship solely for lifecycle;
- harness mutation used to manufacture GREEN;
- resolver prev/current/yaw/point semantic changes after run `35023234306` absent contrary evidence;
- treating temporal-only zero collisionResponse as failure after runs `35039049624`, `35040491258`, `35041914462`;
- patching `isDraggable`/`vs$shouldDrag` after run `35045444238` proved that gate open.

## next_safe_action
1. Inspect only run `35046701119` first.
2. If queued/in_progress: HOLD and stack no new hypothesis.
3. If compile/instrumentation/verifier mechanics fail before useful runtime evidence: repair only this proof harness.
4. If `EXTERNAL_OWNER_BODY_WRITER_MISSES_CALCULATED_STEP`: inspect/patch only the proven VS2 external-owner apply guard/lifecycle seam, then rerun the same smallest jump proof.
5. If `EXTERNAL_OWNER_BODY_WRITER_DIVERGES_FROM_CALCULATED_STEP`: instrument the exact writer inputs/position mutation ordering before any gameplay patch.
6. If `EXTERNAL_OWNER_BODY_WRITER_APPLIES_CALCULATED_STEP`: freeze writer application as healthy and move read-only to owner7 transform lifecycle / articulated carriage identity at the exact discontinuity; do NOT change transform math blindly.
7. Only after natural airborne landing continuity is GREEN advance to wall/ceiling solidity, then turn/speed-change stability.
8. Any production patch must be one evidence-backed hypothesis and preserve FROZEN_GREEN subsystems.

## Finalization policy — HARD USER RUNTIME GATE
Automated proof may advance candidate build/verify but can never alone set `FINAL_READY`. A new exact JAR must pass direct user runtime for stable standing, forward/back/strafe/sprint, jump+airborne+natural landing, floor/walls/ceiling, turns, acceleration/deceleration/speed changes, no sink/throw/drift/lag-behind, and free/stable camera/look. Watchdog local SHA gate must match that exact accepted JAR.

## Fresh-chat/watchdog protocol
1. Inspect actual HEAD.
2. Read this file completely; ledger-only commits may advance HEAD beyond `proof_basis_head` without gameplay changes.
3. Inspect only latest relevant Actions evidence for the active blocker.
4. Respect FROZEN_GREEN and FAILED_HYPOTHESES.
5. Execute `next_safe_action`; do not stop at narration.
6. HOLD only for a genuinely queued/in-progress relevant workflow/evidence.
7. No failure evidence = no symptom gameplay patch.
8. One commit = one hypothesis.
9. Never `FINAL_READY` from CI alone.
