# MASTER_STATE — VS2 / Create Interactive

GitHub code is the implementation source of truth. This file is the durable project-state ledger; chat is temporary.

## Hard contract
- Repository: `apm23/VS2-Create_Interactive`; milestone: `M1 — movement/collision`.
- Create owns train/carriage gameplay and collision geometry.
- VS2 is the continuous moving reference-space foundation for player body/render/camera through grounded, airborne, turns and speed changes; mouse/look remains free.
- Create floor/walls/ceiling remain authoritative solid geometry in that moving frame.
- Forbidden: fake gravity; synthetic carry velocity/inertia; manual floor/wall clamps; floor-only fixes; per-tick teleport/setPos chase/reanchor architecture; duplicate authority/state; direct camera forcing/counter-rotation; fake/proxy VS2 ships; workaround chains hiding double ownership.

## Current reconciliation — 2026-09-17 V3 airborne-release boundary
- `current_head` source state before this immediate ledger write: `43242a04e42fc0919a07c3d94b594696ff62023a` (`Keep continuous owner through false-grounded jump arc`). This MASTER_STATE-only commit will become the next GitHub HEAD; GitHub HEAD remains authoritative on the next cycle.
- V3 architecture commit `4cf1d9d15f766604a71196fd276d32d524ae30d2` (`Redesign external owner as continuous pose frame`) removed the fixed external-owner TTL/jump flag contract, added one previous-owner -> current-owner body+yaw pose transform in native EntityDragger, and kept Create collision geometry authoritative without a second movement writer, synthetic velocity, gravity, clamp, teleport/reanchor, or camera forcing.
- Exact-head root proof run `35187436101` on `4cf1d9d15f766604a71196fd276d32d524ae30d2` completed FAILURE after source-contract and compile SUCCESS. Artifact `10482619878`, digest `sha256:f2e99450b6a8a6b2ca19eb511ae82c4702536cac32d158983d4e638db01a0cc3`.
- Runtime evidence from pristine attempt 3 is direct root-slice failure, not compile/CI failure: native jump starts tick61 (`delta_y=+0.33319999363422365`) and lands tick72; owner2 V3 pose exists only ticks61-62, then disappears for the remainder of the jump interval.
- The release cause is now concrete: at tick63 LocalPlayer is still physically rising (`requested/velocity Y=+0.24813599859094576`) while vanilla reports `on_ground=true`; the old V3 `onGround && owner_age>2` settled-loss predicate therefore clears a valid owner exactly on the third missed support sample. This is false-grounded airborne release, not evidence for a new TTL/jump lease.
- Commit `43242a04e42fc0919a07c3d94b594696ff62023a` makes the smallest root lifecycle correction: settled grounded contact loss can release only when vanilla ground is true AND vertical motion has stopped; owner age remains only a short contact-loss debounce, never an absolute ownership lifetime. No jump flag/window, movement writer, collision change, camera change, or velocity synthesis was added.
- The current proof parser still filters V3 jump rows by raw `on_ground=false`. Because the same runtime evidence proves raw vanilla `onGround` can remain true during a real upward native jump, a future failure solely at that parser filter is proof-infrastructure evidence only and must be repaired without changing gameplay.
- Direct real-user runtime on rejected candidate JAR SHA256 `96053e314891495fbb4bf16c446023568fed542497e083083dad7ed420dcd7ef` remains authoritative regression evidence: grounded floor hard/walking good, but walls soft; jump drags backward roughly 2–4 carriages; turns sweep body/camera, allow wall penetration, and can throw player outside. Never ask the user to retest this SHA.
- Active blocker remains `ROOT_REFERENCE_FRAME_OWNERSHIP`; downstream ceiling/wall/camera/world-smoke failures stay closed to speculative patching until the V3 owner lifecycle is proven across native jump plus real carriage turn/speed change.
- Project state: `ROOT_REFERENCE_FRAME_V3_RUNTIME_REPROOF; DIRECT_USER_RUNTIME_REJECTED; M1_REOPENED`.
- No video is allowed: root blocker is not closure-ready.
- `final_ready=false`; exact final JAR real-user Minecraft acceptance remains mandatory.

## Camera
- Exact source proof HEAD `8ed60f1de4c75810073dbb7ed10bee2a89c325e9`; run `35135734132` SUCCESS; artifact `10461944899`, digest `sha256:69494207606455f0f6ee2f50927d397bbf49300f482ba37d4d28e85d10282fbf`.
- Classifier `CAMERA_EXTERNAL_REFERENCE_POSITIONAL_ALIGNED_WITHIN_0_05`; owner7; ticks32/42; 180° heading span; max/p95/median horizontal error 0; basis `previous_owner_to_current_owner`; look/player/collision/gameplay unmutated.
- Visual audit preserved but non-blocking: run `35138243767` black; run `35163349899` visible and contained ~54.26° turn with ~0 error but framing aimed mostly floor/lower wall; run `35166011444` nonblack direct-framebuffer capture but no active-owner turn in capture interval, artifact `10474552888` digest `sha256:04cb6bb574625f1836ef341d3ddc1a53498fae79dbefb64efca7ed6df6355e12`.
- Historical status was `DATA_PROVEN_VISUAL_INCONCLUSIVE_MEDIA_PENDING_USER_AUDIT`. Media timing/framing failure alone must not reopen camera gameplay, but the direct real-user turn/sweep failure reopens the shared reference-frame architecture beneath camera/body behavior.

## Autonomous video policy
- Video only after a blocker is data/runtime closure-ready; never during debugging/instrumentation/correction.
- Assistant reviews actual MP4 frames; user presence is not required. Preserve every video/review for later audit.
- PASS => `AUTO_FROZEN_GREEN_PENDING_USER_AUDIT` and continue.
- Visible FAIL => reopen only affected subsystem and diagnose automatically.
- Black/unreadable/missed observation after narrow media repair budget => `VISUAL_INCONCLUSIVE_MEDIA_PENDING_USER_AUDIT`; preserve data proof and continue independent engineering.
- Final exact JAR still requires real-user Minecraft acceptance; CI/video cannot produce `FINAL_READY`.

## Ceiling proof — preserved downstream evidence
- Read-only files: `scripts/prepare_vs2_26_2_ceiling_contact_trace.py`, `.github/workflows/m1-ceiling-contact-runtime-proof.yml`.
- First run `35167469407` on HEAD `61122b80e8e07416af01232e6ac290109f5bf9b2` FAILED in compose only: `ceiling trace could not find LocalPlayer setPos marker`.
- Repair `82766397300abee3a71b2b2fab5e346ee6fd38fd` made GateE/collide/setPos tick anchors idempotent; proof infra only.
- Run `35167683911` then failed because the unchanged native-input sequence did not reach native jump on that launch; this was observation/harness availability, not ceiling gameplay failure.
- Commit `36ef9a4e12908fb9c384cfc9724a66838aa10675` retried identical pristine launches without changing input sequence, fixture geometry, train route/timing, or gameplay. Targeted run `35168785447` SUCCESS and reached native jump.
- Commit `5cec40cc0f417b834209a9a5940cf6086de67790` added read-only inventory of EXISTING simplified-collider floor/ceiling clearances; no player relocation, geometry mutation, fixture selection, input timing, collision, or physics change.
- Targeted run `35169937364` on exact HEAD `5cec40cc0f417b834209a9a5940cf6086de67790` SUCCESS. Exact classifier: `CEILING_NOT_EXERCISED`; native airborne tick `62`; rise `+0.333199994`; `obb_rows=128`; `ceiling_normal_rows=0`; `finite_overhead_rows=29`; nearest observed overhead tick `58`, local feet `(-6.6981282294422755,2.0630680924316422,2.193405150489639)`, ceiling bottom `4.0`, head gap `0.136931955`. No gameplay patch authorized.
- Commit `f5640f368734b7b3eed017dc47db42f72d5dcee1` moved inventory sampling to the first ready player/carriage observation; telemetry only.
- Targeted run `35172916766` on exact HEAD `f5640f368734b7b3eed017dc47db42f72d5dcee1` SUCCESS; artifact `10476979722`, digest `sha256:b04716cf0cdd488761426b08d0ae47768d27a3cb6e39f3ffd27d1b7409b24957`.
- That run naturally reached native jump on pristine attempt 3: airborne tick `69`, rise `+0.333199994`. Existing-geometry inventory observed a 2.0-block floor/ceiling clearance without moving player or changing fixture geometry.
- On that naturally successful attempt, exact Create-frame overhead geometry showed head overlap at apex: tick73 `ceiling_head_gap=-0.049287131060964384`; tick74 `ceiling_head_gap=-0.05230339257001049`. Geometric overlap alone is not gameplay failure evidence.
- Commit `a56feb3c8498dc73fd96275de4aa833887834aa1` extended only CI OBB observation from 128 to 256 calls.
- Targeted run `35174843637` on exact HEAD `a56feb3c8498dc73fd96275de4aa833887834aa1` SUCCESS; artifact `10478157982`, digest `sha256:184bd7717e2e54d9cd694c496b8fc3199a5944e1376190800a092a28fd9f5f1e`. Its winning pristine launch reached native jump (`airborne_tick=49`) but had `finite_overhead_rows=0`, so classifier remained `CEILING_NOT_EXERCISED`. No gameplay patch authorized.
- Commit `8b989700f99af99a160992d8801711d8cad4b853` changed proof selection so a pristine attempt won only after unchanged native jump plus finite Create-frame overhead were naturally observed. This remained proof-only.
- Run `35175493622` on exact HEAD `8b989700f99af99a160992d8801711d8cad4b853` was rerun four times because observation is stochastic. Attempt 2 reached native jump with finite overhead but nearest gap remained about `+1.199899948`; no contact. Attempt 3 did not reach native jump. Attempt 4 SUCCESS artifact `10479646032`, digest `sha256:7fc389c3cd1aad4c903b39da44fade54649b7ac21774875d071e20acb02a39ac`: airborne tick `49`, rise `+0.333199994`, `obb_rows=188`, `ceiling_normal_rows=0`, `finite_overhead_rows=28`, nearest tick `52`, ceiling bottom `5.0`, head gap `+0.113351687`; classifier `CEILING_NOT_EXERCISED`. These runs do not authorize gameplay changes.
- Commit `a2d9dfdbd2b363bc0443e2e69639e1cc2a1133fe` changed proof selection again so a pristine attempt wins only after a naturally reached geometric overlap (`ceiling_head_gap <= 0`) and prints exact overlap tick collide/Create-setPos correlation even if no downward ceiling normal is emitted.
- Run `35178003561` attempt 1 on exact HEAD `a2d9dfdb...` SUCCESS but no overlap across three pristine launches. Attempt 2 SUCCESS; artifact `10479880159`, digest `sha256:111538c73e9c0fe57c4fbc81d6aba152bc276794ed4ec4f07e1eb50c75eda3a0`; naturally reached overlap on pristine attempt 2.
- Exact attempt-2 overlap evidence: airborne tick `53`; tick52 full-height head gap `+0.215331970`; tick53 local feet Y `2.404668077792742`, ceiling bottom `4.0`, full-height head gap `-0.204668030`; `ceiling_normal_rows=0`; overlap tick had LocalPlayer zero collide `requested=0,0,0 allowed=0,0,0` plus the horizontal carriage-motion collide, and the Create `ContraptionColliderClient#collideEntities` setPos writer was a no-op. The player had already moved upward by `+0.4199999869` before that Create pass. Classification remained `CEILING_CONTACT_OBSERVED_CORRELATION_INCOMPLETE`; no gameplay patch authorized yet.
- Exact upstream Create-Fly pin `12c75509e16dd4f33c5f6260bd0330f1ed094bb5` confirms `ContraptionColliderClient` contracts client-player height by `2/16`, then builds the OBB from that contracted bounds and passes entity motion minus contraption motion to `ContinuousOBBCollider.collideMany`. Phase66 reads the same `getSimplifiedEntityColliders()` list in the same Create `worldToLocalPos` frame.
- Commit `8e3aa250d61103513140dbc9139dd995529514b4` added read-only telemetry for the exact `lowestBottomOverHeadIndex`, candidate center/extents/bottom, Create client collision height, and `create_client_collision_head_gap`; it did not alter collision or gameplay.
- Run `35179359526` on exact HEAD `8e3aa250d61103513140dbc9139dd995529514b4` SUCCESS. Pristine attempt 1 reached native jump with finite overhead and true Create-contracted overlap. At tick39 the contracted head gap was `-0.095100039`; no ceiling Y response/normal was emitted; exact-owner VS2 reference ownership was already active; the native Create query still used `entityMotion - contraptionMotion` and correlated with a tiny temporal X contact. This directly authorized the smallest exact-owner collision-motion-frame correction.
- Candidate commit `a2a47084eaef292c0ffa840d82bd1eecaad907d2` removes only the duplicate contraption-motion subtraction for exact active-owner LocalPlayer collision queries; no geometry, input, train, camera, gravity, wall clamp, teleport, or response writer is replaced.
- Candidate proof run `35184002839` did not naturally overlap ceiling, so no closure result exists yet. Production-world run `35184002626` proves carry remains stable but still reports missing ceiling collision signature.
- Run `35186045898` on exact HEAD `09b295b583c6844b0017d64c5de2485da89e8f96` later reached true overlap again (`overlap_rows=2`) but still had `ceiling_normal_rows=0`; classifier `CEILING_CONTACT_OBSERVED_CORRELATION_INCOMPLETE`. Preserve this as downstream evidence only until root ownership is rebuilt.
- Pristine r0v3 save SHA256 `e78bfb854a0f3ad0bfb87ded836ef322335812d303e51223825f3741f7232556`.
- Required timeline: tick; exact Create `worldToLocalPos` local position/overhead geometry; exact simplified collider candidate; Create-contracted head gap; OBB normal; collisionResponse; surfaceCollision; temporalResponse; requested/allowed collide; tick-bearing final Create setPos writer.
- Compile/harness/verifier/telemetry-window/selection failures authorize proof-infra repair only.
- No ceiling video until the root architecture is closure-ready and the exact ceiling behavior is reproven.

## Preserved evidence / FROZEN boundaries
- bootstrap/Kotlin `f3d1335...`; Create+VS2 coexistence; Steam 'n' Rails + Copycats.
- V1 infra `34984299770`; external-owner lifecycle `35008163064`; same-point transform `35023234306`; free-look boundary `35034983734`; OBB temporal support-loss `35041914462`; native drag gate `35045444238`; existing VS2 body writer `35048234680`; descent support-miss `35051781646`; owner-cap lag `35071088843`; fixture arbitration `35084762923`, `35085286003`.
- Current Create collision-frame continuity run `35100081357`: candidate-vs-Phase131 residual 0; max frame step `0.048467738`; external owner continuous; existing EntityDragger writer runs. This is preserved diagnostic evidence, not proof that the hard continuous-reference architecture is satisfied.
- Wall/ceiling source map run `35101691613`, artifact `10448192299`: current Create `worldToLocalPos` OBB path; X/Z wall clipping; Y vertical clipping; response setPos; surface contact-motion writer; duplicate authority removed.
- Pinned contacts run `35104224078`, artifact `10450080515`: seven horizontal wall rows, no ceiling row.
- Wall semantics run `35104523803`, artifact `10449412710`: all seven wall rows valid temporal-only; `unresolved_zero=0`.
- Valid OBB rule: `surface=true + collisionResponse=ZERO + 0<temporal<1` can be solved Create behavior; zero response alone is not failure.
- Historical native jump run `35089177675`, HEAD `012d92dabb86cac5571d5d320eea9fa77ea539d6`, artifact `10444135201`: native airborne tick46, rise `+0.33319999363422365`, owner7 continuous ticks46..83. Do not reuse its old post-arc lifecycle failure as current ceiling failure.
- Camera external-owner gate reachability `35113644070`; camera active-turn data proof `35135734132`; historical user floor solidity + grounded walking.
- No user-visible M1 subsystem is currently `FROZEN_GREEN`: the rejected user-runtime JAR reopens shared ownership/airborne/turn/wall/camera behavior despite earlier automated green signals.

## FAILED_HYPOTHESES / anti-loop
Do not reintroduce absent new direct evidence: `EXACT_SHAPES_LOCALPLAYER_0fa4aa`; generic frame lease/replay/carry extension; lifecycle extension beyond proven jump/landing seam; synthetic carry velocity/inertia; fake gravity; manual floor/wall clamp; floor-only workaround; per-tick teleport/setPos chase; direct camera forcing/counter-rotation; jump/input timing production tuning; sprint/reverse/strafe tuning as reference-frame fix; global collider suppression; suppressing Create collision-response writer; duplicate Create/VS2 authority; fake/proxy VS2 ship; harness mutation to manufacture green; blind resolver prev/current/yaw/point changes; old `toLocalVector(...,0)` mismatch as current failure; temporal-only zero response as failure; patching `isDraggable`/`vs$shouldDrag`; adding/replacing body-position writer; Phase64 Y/grounding clip from code location; hardcoded carriage id/block/span/geometry; changing server `firstOrNull` fixture selector; post-release hypothetical camera rows as active mismatch; camera counter-rotation after exact active-turn proof.
- Explicit anti-loop: do not fix the direct runtime failure by increasing the old 40-tick jump window, restoring a jump flag, adding an absolute owner TTL, adding only yaw/camera compensation, or stacking another Create collision-motion exception.
- Raw vanilla `onGround=true` by itself is not sufficient evidence of a settled grounded owner exit during a real jump; run `35187436101` proves it can remain true while LocalPlayer is rising at +0.24813599859094576 Y/tick.

## next_safe_action
1. Reconcile actual HEAD first; expected source+ledger lineage is gameplay fix `43242a04e42fc0919a07c3d94b594696ff62023a` followed immediately by this MASTER_STATE write.
2. Run/inspect the smallest `m1-reference-owner-v3-continuous-pose-proof` on the exact latest HEAD. No video.
3. Primary criterion: the same external owner must remain present throughout the native jump interval tick-to-tick, not disappear at the old third missed-support sample. Preserve natural landing and require the same owner across a real carriage heading/speed change.
4. If pose continuity now persists but the job fails only because the verifier filters by raw `on_ground=false`, repair that verifier to use the already-emitted native jump start/land interval rather than raw vanilla ground state. That is proof infrastructure only; do not alter gameplay for it.
5. If ownership still drops, inspect the exact new release boundary and make one root-lifecycle change only. Do not touch Create wall/ceiling/collision or camera compensation while the root owner is red.
6. After root ownership + turn proof is genuinely green, reprobe floor/walls/ceiling with Create-native geometry and reconcile generic `world-smoke`; only then consider blocker-closure video.
7. `FINAL_READY` remains forbidden until the exact final JAR passes real-user actual Minecraft: no sinking, stable standing, forward/back/strafe/sprint, jump+natural landing, floor/wall/ceiling solidity, stable train movement/turn/speed changes, and free stable look.
