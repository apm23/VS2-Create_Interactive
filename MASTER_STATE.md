# MASTER_STATE — VS2 / Create Interactive

GitHub code is the implementation source of truth. This file is the durable project-state ledger; chat is temporary.

## Hard contract
- Repository: `apm23/VS2-Create_Interactive`; milestone: `M1 — movement/collision`.
- Create owns train/carriage gameplay and collision geometry.
- VS2 is the continuous moving reference-space foundation for player body/render/camera through grounded, airborne, turns and speed changes; mouse/look remains free.
- Create floor/walls/ceiling remain authoritative solid geometry in that moving frame.
- Forbidden: fake gravity; synthetic carry velocity/inertia; manual floor/wall clamps; floor-only fixes; per-tick teleport/setPos chase/reanchor architecture; duplicate authority/state; direct camera forcing/counter-rotation; fake/proxy VS2 ships; workaround chains hiding double ownership.

## Current reconciliation — 2026-09-17 timeout recovery
- Authoritative pre-reconciliation HEAD: `a2a47084eaef292c0ffa840d82bd1eecaad907d2` (`Recover watchdog state and apply collision motion fix`). This commit had already landed before the recovery turn and is preserved; do not blindly repeat it.
- Previous ledger state stopped at proof HEAD `8e3aa250d61103513140dbc9139dd995529514b4`, so `current_head` in the old ledger was stale.
- Targeted proof run `35179359526` on exact proof HEAD `8e3aa250d61103513140dbc9139dd995529514b4` completed SUCCESS after that ledger snapshot. It naturally reached overlap on pristine attempt 1: native airborne tick `39`, Create-contracted ceiling gap `-0.095100039`, no ceiling Y response/normal, with the collision path instead reporting a tiny temporal X contact. Exact-owner external reference ownership was active. This satisfied the prior conditional authorization for the smallest root correction.
- `a2a47084eaef292c0ffa840d82bd1eecaad907d2` therefore changes only the exact-active-owner LocalPlayer Create relative OBB motion term: native `entityMotion - contraptionMotion` remains for all other cases, while exact external-owner LocalPlayer uses `entityMotion` because the carriage reference translation is already represented by VS2 ownership. Create geometry/SAT/OBB/grounding/response writers remain authoritative; sibling carriages and non-LocalPlayer entities remain native.
- Same-HEAD targeted ceiling run `35184002839` completed SUCCESS but did not naturally exercise a ceiling overlap: attempt 1 `READY_NO_OVERLAP`; attempts 2–3 exhausted without a qualifying unchanged-input jump/overlap. Classifier remained effectively `CEILING_NOT_EXERCISED`; this does not close or disprove the correction and does not authorize another gameplay patch.
- Same-HEAD production-world run `35184002626` preserved moving-train carry: `PRODUCTION_CARRY physical_support_stable carriage_id=10 ticks=16-22 samples=7 span=0.000100100`. Its native jump arc remained natural and landed, but the workflow failed because the required ceiling collision signature was still absent. `walk-gate` run `35184298823` then failed only because its production-world source conclusion was failure; it did not independently demonstrate a walking regression.
- Generic `world-smoke` run `35184002621` failed its carry-delta gate and showed a late off-carriage state; keep this as an unresolved regression signal, but do not override the stronger same-HEAD production-isolation carry proof without direct causal evidence. Reconcile it before final freeze if it remains reproducible.
- `held-block-gate` was already failing on parent `b696908e267b3013c2e1f2faa4f069d5a4b0bc1e`; do not misclassify it as a new `a2a470` regression.
- Active blocker remains `CEILING`; current gameplay candidate is the exact-owner collision-motion-frame correction in `a2a47084eaef292c0ffa840d82bd1eecaad907d2`.
- Project state: `CAMERA_DATA_PROVEN_VISUAL_INCONCLUSIVE_MEDIA_PENDING_USER_AUDIT; CEILING_COLLISION_MOTION_CANDIDATE_PENDING_NATURAL_OVERLAP_REPROOF`.
- No ceiling video was recorded because closure-ready data/runtime proof has not yet been obtained on the candidate.
- final_ready: `false`.
- Historical failed user JAR SHA256 `96053e314891495fbb4bf16c446023568fed542497e083083dad7ed420dcd7ef`: grounded floor/walk good, walls soft, jump dragged 2–4 carriages, turns swept player/camera, wall penetration/throw; never retest this SHA.

## Camera
- Exact source proof HEAD `8ed60f1de4c75810073dbb7ed10bee2a89c325e9`; run `35135734132` SUCCESS; artifact `10461944899`, digest `sha256:69494207606455f0f6ee2f50927d397bbf49300f482ba37d4d28e85d10282fbf`.
- Classifier `CAMERA_EXTERNAL_REFERENCE_POSITIONAL_ALIGNED_WITHIN_0_05`; owner7; ticks32/42; 180° heading span; max/p95/median horizontal error 0; basis `previous_owner_to_current_owner`; look/player/collision/gameplay unmutated.
- Visual audit preserved but non-blocking: run `35138243767` black; run `35163349899` visible and contained ~54.26° turn with ~0 error but framing aimed mostly floor/lower wall; run `35166011444` nonblack direct-framebuffer capture but no active-owner turn in capture interval, artifact `10474552888` digest `sha256:04cb6bb574625f1836ef341d3ddc1a53498fae79dbefb64efca7ed6df6355e12`.
- Status: `DATA_PROVEN_VISUAL_INCONCLUSIVE_MEDIA_PENDING_USER_AUDIT`. Do not reopen camera gameplay from media timing/framing failure. User prioritizes mod progress; framing cleanup may occur later.

## Autonomous video policy
- Video only after a blocker is data/runtime closure-ready; never during debugging/instrumentation/correction.
- Assistant reviews actual MP4 frames; user presence is not required. Preserve every video/review for later audit.
- PASS => `AUTO_FROZEN_GREEN_PENDING_USER_AUDIT` and continue.
- Visible FAIL => reopen only affected subsystem and diagnose automatically.
- Black/unreadable/missed observation after narrow media repair budget => `VISUAL_INCONCLUSIVE_MEDIA_PENDING_USER_AUDIT`; preserve data proof and continue independent engineering.
- Final exact JAR still requires real-user Minecraft acceptance; CI/video cannot produce `FINAL_READY`.

## Ceiling proof — exact candidate / contracted-gap correlation
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
- Pristine r0v3 save SHA256 `e78bfb854a0f3ad0bfb87ded836ef322335812d303e51223825f3741f7232556`.
- Required timeline: tick; exact Create `worldToLocalPos` local position/overhead geometry; exact simplified collider candidate; Create-contracted head gap; OBB normal; collisionResponse; surfaceCollision; temporalResponse; requested/allowed collide; tick-bearing final Create setPos writer.
- Classifiers:
  - `CEILING_NOT_EXERCISED` => no new gameplay patch; rerun unchanged proof.
  - `CEILING_CONTACT_OBSERVED_CORRELATION_INCOMPLETE` => read-only correlation follow-up only.
  - candidate overlap + proper Create ceiling Y response without penetration => blocker becomes closure-ready and only then allow one-shot video.
- Compile/harness/verifier/telemetry-window/selection failures authorize proof-infra repair only.
- No ceiling video until data/runtime closure-ready.

## Preserved evidence / FROZEN boundaries
- bootstrap/Kotlin `f3d1335...`; Create+VS2 coexistence; Steam 'n' Rails + Copycats.
- V1 infra `34984299770`; external-owner lifecycle `35008163064`; same-point transform `35023234306`; free-look boundary `35034983734`; OBB temporal support-loss `35041914462`; native drag gate `35045444238`; existing VS2 body writer `35048234680`; descent support-miss `35051781646`; owner-cap lag `35071088843`; fixture arbitration `35084762923`, `35085286003`.
- Current Create collision-frame continuity run `35100081357`: candidate-vs-Phase131 residual 0; max frame step `0.048467738`; external owner continuous; existing EntityDragger writer runs.
- Wall/ceiling source map run `35101691613`, artifact `10448192299`: current Create `worldToLocalPos` OBB path; X/Z wall clipping; Y vertical clipping; response setPos; surface contact-motion writer; duplicate authority removed.
- Pinned contacts run `35104224078`, artifact `10450080515`: seven horizontal wall rows, no ceiling row.
- Wall semantics run `35104523803`, artifact `10449412710`: all seven wall rows valid temporal-only; `unresolved_zero=0`.
- Valid OBB rule: `surface=true + collisionResponse=ZERO + 0<temporal<1` can be solved Create behavior; zero response alone is not failure.
- Historical native jump run `35089177675`, HEAD `012d92dabb86cac5571d5d320eea9fa77ea539d6`, artifact `10444135201`: native airborne tick46, rise `+0.33319999363422365`, owner7 continuous ticks46..83. Do not reuse its old post-arc lifecycle failure as current ceiling failure.
- Camera external-owner gate reachability `35113644070`; camera active-turn data proof `35135734132`; historical user floor solidity + grounded walking.

## FAILED_HYPOTHESES / anti-loop
Do not reintroduce absent new direct evidence: `EXACT_SHAPES_LOCALPLAYER_0fa4aa`; generic frame lease/replay/carry extension; lifecycle extension beyond proven jump/landing seam; synthetic carry velocity/inertia; fake gravity; manual floor/wall clamp; floor-only workaround; per-tick teleport/setPos chase; direct camera forcing/counter-rotation; jump/input timing production tuning; sprint/reverse/strafe tuning as reference-frame fix; global collider suppression; suppressing Create collision-response writer; duplicate Create/VS2 authority; fake/proxy VS2 ship; harness mutation to manufacture green; blind resolver prev/current/yaw/point changes; old `toLocalVector(...,0)` mismatch as current failure; temporal-only zero response as failure; patching `isDraggable`/`vs$shouldDrag`; adding/replacing body-position writer; Phase64 Y/grounding clip from code location; hardcoded carriage id/block/span/geometry; changing server `firstOrNull` fixture selector; post-release hypothetical camera rows as active mismatch; camera counter-rotation after exact active-turn proof.

## next_safe_action
1. This reconciliation commit is ledger-only; do not add another gameplay change. Its push should rerun the unchanged exact ceiling proof on the same gameplay candidate.
2. Inspect the newest `m1-ceiling-contact-runtime-proof` run first. If queued/in_progress, HOLD and do not stack another patch.
3. If it naturally reaches ceiling overlap, require the same exact candidate/contracted-gap correlation and inspect whether Create now emits a proper ceiling Y response/normal and prevents penetration. If yes, the ceiling blocker becomes data/runtime closure-ready; only then run the one-shot short visual-close workflow and self-review its MP4.
4. If no overlap is naturally exercised, rerun unchanged proof again rather than mutating gameplay, fixture geometry, input sequence, train route/state/timing, or collision semantics.
5. If overlap is exercised and the correction still leaves overlap without proper Y response, preserve the failed proof, classify the exact remaining boundary, and make only the smallest evidence-authorized root action. Do not chain workarounds.
6. Reconcile generic `world-smoke` failure before any final freeze; if a protected/FROZEN regression is directly confirmed, REVERT before workaround.
7. Never patch walls from temporal-only rows. No ceiling video before closure-ready data proof.
8. `FINAL_READY` forbidden until the exact final JAR passes real-user actual Minecraft: no sinking, stable standing, forward/back/strafe/sprint, jump+natural landing, floor/wall/ceiling solidity, stable train movement/speed changes.