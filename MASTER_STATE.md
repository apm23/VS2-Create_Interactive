# MASTER_STATE — VS2 / Create Interactive

GitHub code is the implementation source of truth. This file is the durable project-state ledger. Chat is temporary.

## Project / hard contract
- Repository: `apm23/VS2-Create_Interactive`.
- Milestone: `M1 — movement / collision`.
- Create owns train/carriage gameplay and collision geometry.
- VS2 must be the actual continuous moving reference-space/transform foundation for player body/render/camera, not a helper applied after Create movement.
- Standing/walking/jumping must remain carriage-relative through grounded, airborne, turns, acceleration/deceleration and speed changes while mouse/look remains free.
- Create floor/walls/ceiling remain authoritative solid geometry in that same moving frame.
- Forbidden: fake gravity, synthetic carry velocity/inertia, manual floor/wall clamps, floor-only workarounds, per-tick teleport/setPos chase/reanchor architecture, duplicate Create/VS2 authority, direct camera forcing/rotation compensation, fake/proxy VS2 ships, or workaround chains hiding double ownership.

## Current reconciled state — 2026-09-17
- `current_head`: `18dba7b119dbb4ed5deb97013a505d6ac7c2cc28` immediately before this ledger-only reconciliation commit.
- project_state: `PROVEN_PENDING_CLOSURE_VIDEO — CAMERA EXTERNAL-REFERENCE POSITIONAL BEHAVIOR IS DATA-PROVEN THROUGH A REAL ACTIVE-OWNER 180-DEGREE CARRIAGE TURN ON EXACT SOURCE HEAD 8ed60f1de4c75810073dbb7ed10bee2a89c325e9. RUN 35135734132 MEASURED OWNER 7 AT TICKS 32 AND 42 WITH HEADING SPAN PI AND EXACT 0.0 HORIZONTAL CAMERA-vs-EXPECTED ERROR. NO LOOK/PLAYER/COLLISION/GAMEPLAY STATE WAS MUTATED. CAMERA IS NOT FROZEN_GREEN UNTIL THE ONE-SHOT EXACT-SOURCE VISUAL CLOSE IS JOINTLY REVIEWED.`
- latest gameplay implementation: `9aea12a6114198c33c70d52897eb9d3c29342425` (`Refresh jump owner from exact Create grounded carry contact`).
- exact camera source proof head: `8ed60f1de4c75810073dbb7ed10bee2a89c325e9`.
- camera source proof workflow: `m1-camera-external-reference-active-turn-retry-proof`, run `35135734132`, SUCCESS.
- camera source proof artifact: id `10461944899`, name `camera-external-reference-active-turn-retry-proof`, digest `sha256:69494207606455f0f6ee2f50927d397bbf49300f482ba37d4d28e85d10282fbf`.
- exact camera proof classifier: `CAMERA_EXTERNAL_REFERENCE_POSITIONAL_ALIGNED_WITHIN_0_05`; attempt `1`; owner `7`; samples `2`; unique ticks `2`; heading span `3.141592654 rad / 180.000000 deg`; max/p95/median horizontal error all `0.000000000`; acquisitions `18`; native contacts `25`.
- exact proof rows: tick32 heading `0`, camera=`30.572803,-56.379900,120.699900`, expected identical; tick42 heading `pi`, camera=`25.078990,-56.379900,120.300100`, expected identical.
- camera source basis: `previous_owner_to_current_owner`; look_mutated=false; player_mutated=false; collision_mutated=false; gameplay_mutated=false; harness_semantics_unchanged=true.
- workflow-definition-only commit `18dba7b119dbb4ed5deb97013a505d6ac7c2cc28` adds `.github/workflows/m1-camera-visual-close.yml`; it does not alter gameplay/source proof. The visual workflow explicitly checks out and asserts exact source proof SHA `8ed60f1de4c75810073dbb7ed10bee2a89c325e9` before composing/running the camera candidate.
- active visual-close workflow: `m1-camera-visual-close`, run `35138243767`; queued at this reconciliation point. It records one 15-second Xvfb/FFmpeg capture only after genuine external-owner acquisition, requires the capture interval to contain a same-owner real turn with max horizontal error <=0.05, and uploads MP4 + minimal metadata. No gameplay/fixture/timing semantics are changed for recording.
- camera status is `PROVEN_PENDING_CLOSURE_VIDEO`, not `FROZEN_GREEN`.
- overhead-ceiling response remains the next independent blocker, but MUST NOT start until camera visual review is complete and approved.
- final_ready: `false`.
- exact historical failed user JAR SHA256: `96053e314891495fbb4bf16c446023568fed542497e083083dad7ed420dcd7ef`; never ask user to retest it.
- known invalid workflow noise: `.github/workflows/m1-reference-owner-v2-airborne-drag-boundary-proof-v2.yml` emits instant zero-job failures; ignore it.

## Current visual-close gate
- Video is a blocker-closing validation only, never a debugging tool.
- Current camera video is allowed because data proof `35135734132` is closure-ready.
- The tested source/build composition for visual close is pinned to exact proof head `8ed60f1de4c75810073dbb7ed10bee2a89c325e9`, even though the workflow definition itself was introduced by `18dba7b...`.
- Visual scenario: real active external owner + real carriage turn; observational recording only; no camera/player/look/collision/input/train mutation for media capture.
- If visual run is queued/in_progress: HOLD.
- If MP4 artifact is ready: STOP before ceiling and report exactly `VIDEO_REVIEW_REQUIRED: camera head=8ed60f1de4c75810073dbb7ed10bee2a89c325e9 run=<visual-run-id> artifact=<artifact-name-or-id>`, then `WATCHDOG_DECISION: BLOCKED_USER`.
- Camera becomes FROZEN_GREEN only after user + assistant approve that exact-source video.
- Visible failure overrides telemetry green and reopens camera only.
- If recording infrastructure fails, allow at most one narrow media-infra repair; never change gameplay to get footage.

## Historical direct-user runtime gate — authoritative regression evidence
Exact JAR SHA256 `96053e314891495fbb4bf16c446023568fed542497e083083dad7ed420dcd7ef` FAILED:
- floor hard/solid PASS and grounded walking PASS;
- walls soft FAIL;
- jump/airborne dragged player backward ~2–4 carriages FAIL;
- turns swept player/camera, wall could be penetrated, player could be thrown outside FAIL;
- behavior did not feel like a stable VS2 moving base FAIL.
This direct runtime evidence overrides automated M1 green and blocks `FINAL_READY` until a new exact final JAR passes direct user runtime.

## Camera proof history / superseded diagnostics
- run `35113644070`, head `bceeb6ab413f1011cf65cf05a846863adf80c9a4`: `CAMERA_EXTERNAL_OWNER_GATE_REACHED`; proves Camera.update after vanilla alignWithEntity sees LocalPlayer, dragging provider, active external owner, owner id and resolvable transforms. Gate reachability is protected.
- run `35110832310`, head `604e01945c99e9e33c40be67f0dda28772a1d75c`: `NO_CAMERA_OWNER_ROWS`; superseded as sparse verifier sampling limitation.
- commit `b48dad66de35796bb76375994f39f64122b79078`: samples every active-owner camera callback.
- run `35117703635`: parser failed because tuple unpack expected six fields after regex emitted seven; verifier-only bug.
- commit `8218314549e2bd94b5819ec5c228502eb66f5b54`: fixed camera progress parser only.
- run `35120320374`: only one active-owner row, no heading span; no gameplay conclusion. It exposed support loss shortly after owner acquisition but did not justify lease extension.
- commit `9209662aa07472db1d7eca434e7c07b0fda3ce25`: added read-only last-owner heading timeline after release.
- later read-only lifecycle/turn work established that turn coverage rather than a camera positional mismatch was the missing evidence.
- run `35134284295`, head `dc810e982646ce02b5d19a1ff5c02ad803343e98`: production camera hypothesis compiled and active rows were exactly aligned, but no active-owner heading span was exercised (`TURN_NOT_EXERCISED_WHILE_OWNER_ACTIVE`); not a gameplay failure.
- commit `8ed60f1de4c75810073dbb7ed10bee2a89c325e9`: added retry-only pristine proof workflow with unchanged gameplay/harness semantics so nondeterministic fixture execution could observe the already-existing real turn.
- run `35135734132` then closed the data blocker with exact 180-degree active-owner turn and zero positional error.

## Root architecture / protected structural proofs
- run `34963733838`: old implementation was contact/lease reanchor, not continuous VS2 reference space.
- run `34969572212`: native VS2 owner requires registered ShipId; fake/proxy ship is forbidden.
- run `34972926851`: reference-owner redesign boundary mapped.
- run `34975161200`: core slice bounded to owner state/body drag/relative packet/server resolution/render/yaw; Create collision remains separate.
- run `34977644889`: Create carriage Entity id + bilateral transforms available; pinned Create JAR SHA256 `d9c6cb6116d5caa1174a289ecd7d3cdd463ccef6e8db1249ab0bcfcd8c935870`.
- V1 run `34984299770`: generalized external owner state + Entity-id resolver + VS2 EntityDragger lifecycle.
- V2 run `34994353308` was structurally green, but later direct user runtime disproved its original overall continuity assumption.

## Scheduler / authority — protected
- external-owner EntityDragger lifecycle requirement run `35008163064` remains protected.
- production scheduler `0ce0dfd4...` applies only external-owner LocalPlayer drag after `ClientLevel.tick` and before Create collision; native VS2 ship scheduling remains separate.
- active-owner ordinal-1 authority proof `35017634522` remains valid for its tested boundary.
- Create OBB/grounding/floor/walls/ceiling remain authoritative. Do not suppress Create's first collision-response writer or global Create collision behavior.

## Transform / body / look — protected boundaries
- same-point transform run `35023234306`: exact same-point mismatch `0`; no blind resolver prev/current/yaw/point changes.
- camera mapping run `35033671863`: external-owner spatial render wired; historical camera owner seam was absent before later camera hypothesis.
- look run `35034983734`: external-owner spatial follow with look uncoupled; free look required; direct camera counter-rotation forbidden.
- native drag gate run `35045444238`: `EXTERNAL_OWNER_NATIVE_GATE_NOT_REJECTING`; do not patch `isDraggable` / `vs$shouldDrag`.
- body writer verifier `35048234680`: existing VS2 boundingBox/setPos writer applies calculated step exactly; do not add/replace body-position writer.
- corrected current-frame run `35100081357`: current Create collision-frame coordinates remain continuous through observed jump-arc rotation updates; resolver rewrite not authorized.
- camera active-turn positional data run `35135734132` is green and closure-ready, but not FROZEN_GREEN until visual approval.

## OBB / collision semantics — protected boundaries
- runtime `35031106237`: owner/carriage matched through support loss and Create callbacks continued.
- runs `35037369180`, `35037534677`, `35039049624`, `35040491258`: temporal-only solved response is valid.
- verifier `35041914462`: `ACTIVE_OWNER_CREATE_COLLISION_FRAME_CONTINUOUS_TEMPORAL_ONLY`.
- `surface=true + collisionResponse=ZERO + 0<temporal<1` is valid Create behavior; do not reinterpret it as failure.
- source-map run `35101691613`, artifact `10448192299`, zip SHA256 `c9e19ec866b671a7820e3b80c0b5ad002e7c3cc37c42f48d0aaffafbb12b985d`: Create current-world-to-local OBB path, horizontal X/Z clipping, vertical Y clipping, response setPos, surface contact-motion writer present; legacy duplicate authority removed.
- pinned contact run `35104224078`, artifact `10450080515`, zip SHA256 `9614041999295ef68bd6e908e394c1954f2394519144b76b2447f632d0221e85`: 7 horizontal wall-direction rows; no overhead ceiling row.
- pinned wall-response run `35104523803`, artifact `10449412710`, zip SHA256 `4ab40a457a756db47bd141510387fad607aad9421de44bd09a9c52b4977d5584`: all seven wall rows valid temporal-only, unresolved_zero=0, all near LocalPlayer collide consumption. No wall response rewrite authorized from these rows.
- same wall artifact had no tick-bearing final Create setPos neighborhood correlation; if wall is revisited later, add only that read-only correlation first.
- ceiling contact remains unexercised in pinned valid-jump artifact and is the next blocker after camera visual approval.

## Lifecycle history / current production
- verifier `35048427002`: first false clear was grounded-contact expiry on native jump tick; production `a14260c...` corrected that narrow failure.
- run `35051781646`: ordinary descent support-miss lifecycle protected; generic lease extension disproven.
- run `35057564114`: exact strict-support airborne failure had owner carriage7, jump tick47, owner cleared tick49 and large Create carry reopened.
- verifier `35062047086`: grounded-contact expiry on native jump authorized only bounded jump-active correction.
- commit `c3e7c51...`: jump-active owner state.
- run `35071088843`: owner cap expired tick68, landing began tick70, two-frame carriage lag `0.330086470` blocks.
- production `d6e55e2...`: extends already-armed jump owner only until same-owner native Create landing, bounded safety limit, no synthetic motion/camera/collision override.
- latest gameplay `9aea12a...`: refreshes jump owner from exact Create grounded carry contact and remains gameplay basis.

## Valid-jump / current-frame evidence
- run `35089177675`, head `012d92dabb86cac5571d5d320eea9fa77ea539d6`, artifact `10444135201`, digest `sha256:62dc537d525cf2f5375892157583e024cfa2c03b314df98a33aca0d09f8810ce`: native airborne tick46, rise `+0.33319999363422365`, owner7 continuous ticks46..83.
- verifier `134f31df...` / run `35099171565` originally reported ~2.5055-block mismatch using old `toLocalVector(...,0)` previous-rotation semantics; that conclusion is superseded.
- corrected verifier `5d66fdc4...`, run `35100081357`: current Create collision-frame maximum horizontal step on those rotation updates only `0.048467738`; candidate current-frame vs Phase131 residual exactly `0`; external owner continuous; existing EntityDragger writer executes; resolver patch not authorized.

## Fixture / harness boundaries — protected from blind tuning
- run `35067811102`: pre-jump non-admission; no physics inference.
- run `35079785697`: identical harness diverges by selected carriage runway.
- runs `35084762923`, `35085286003`: admitted/current start same physical server fixture; later client candidate arbitration can diverge; nearest-center selection feeds contact baseline. Never hardcode carriage id/size/span or mutate server `firstOrNull` selector.
- Do not shorten/tune input merely to manufacture GREEN.
- Current camera retry/visual workflows reconstruct the same verified r0v3 save (`sha256:e78bfb854a0f3ad0bfb87ded836ef322335812d303e51223825f3741f7232556`) and preserve harness/gameplay semantics.

## FROZEN_GREEN / protected summary
- bootstrap/Kotlin packaging `f3d1335...`;
- Create train + VS2 coexistence;
- Steam 'n' Rails + Copycats preservation;
- V1 infrastructure `34984299770`;
- external-owner lifecycle requirement `35008163064`;
- same-point transform `35023234306`;
- look/free-look structural boundary `35034983734`;
- OBB temporal-only support-loss `35041914462`;
- native drag gate `35045444238`;
- existing VS2 body writer `35048234680`;
- ordinary descent support-miss lifecycle `35051781646`;
- owner-cap lag evidence `35071088843`;
- fixture arbitration boundaries `35084762923`, `35085286003`;
- current Create collision-frame continuity across observed jump-arc rotations `35100081357`;
- pinned wall temporal-only response semantics `35104523803`;
- camera external-owner gate reachability after `alignWithEntity` `35113644070`;
- historical user-proven floor solidity and grounded walking.
- Camera active-turn positional alignment run `35135734132` is PROVEN_PENDING_CLOSURE_VIDEO, not yet FROZEN_GREEN.

## FAILED_HYPOTHESES / anti-loop
Do not reintroduce without new direct evidence:
- `EXACT_SHAPES_LOCALPLAYER_0fa4aa`;
- generic frame lease/replay/carry extension;
- generic lifecycle extension beyond the proven jump/landing seam;
- synthetic carry velocity / inertia compensation;
- fake gravity;
- manual floor/wall clamps or floor-only workaround;
- per-tick teleport/setPos chase/reanchor architecture;
- direct camera forcing/rotation compensation;
- jump/input timing tuning as a production reference-frame fix;
- sprint/reverse/strafe tuning as reference-frame fix;
- unscoped/global collider suppression or suppression of Create collision-response writer;
- duplicate Create/VS2 gameplay/collision authority;
- fake/proxy VS2 ship;
- harness mutation used to manufacture physics GREEN;
- blind resolver prev/current/yaw/point semantic changes after `35023234306` and corrected `35100081357`;
- treating old `toLocalVector(...,0)` mismatch as current Create collision-frame failure;
- treating temporal-only zero collisionResponse as failure, including pinned wall rows in `35104523803`;
- patching `isDraggable`/`vs$shouldDrag` after `35045444238`;
- adding/replacing body-position writer after `35048234680`;
- changing Phase64 grounding/Y clip merely because source location is known;
- hardcoding carriage entity id, block count, span, geometry;
- changing server `firstOrNull` initial fixture carriage selector;
- extending owner lifetime generically just to keep camera proof alive;
- using post-release hypothetical camera rows as proof of active production camera behavior;
- adding camera counter-rotation after exact active-turn alignment proof.

## next_safe_action
1. Inspect visual-close run `35138243767` first. Do not patch gameplay while it is queued/in_progress.
2. If run succeeds and artifact contains MP4 + metadata, verify metadata pins `source_proof_head=8ed60f1de4c75810073dbb7ed10bee2a89c325e9`, source proof run `35135734132`, scenario active external owner real carriage turn, and a non-empty MP4. Then STOP before ceiling and emit `VIDEO_REVIEW_REQUIRED` + `BLOCKED_USER` for joint visual review.
3. If visual capture fails only because FFmpeg/Xvfb/media infrastructure, permit at most one narrow recording-only repair. Never alter gameplay, physics, collision, input semantics, train route/state/timing, or fixture geometry to make footage pass.
4. If capture interval lacks the already-proven turn, treat it as visual observation/capture failure, not gameplay failure; preserve source proof and do not stack gameplay changes.
5. After user + assistant approve exact-source video, mark camera FROZEN_GREEN and only then proceed to overhead-ceiling blocker.
6. Ceiling next action: smallest read-only runtime instrumentation/harness that genuinely exercises an overhead contact in Create current `worldToLocalPos` frame, recording player tick, local position, OBB normal, collisionResponse, surfaceCollision, temporalResponse, final requested/allowed collide result, and tick-bearing final Create position/motion writer.
7. Only direct current-frame invariance failure, missing/incorrect Create ceiling response, or future measured player-camera frame mismatch may authorize one gameplay hypothesis. One commit = one hypothesis.
8. Any regression of FROZEN_GREEN must be reverted before workaround stacking.
9. Automated proof alone can never set `FINAL_READY`; exact final JAR still requires direct user runtime acceptance.

## Finalization policy — HARD USER RUNTIME GATE
Automated proof can advance through build/verify only. `FINAL_READY` requires BOTH repository final verification and direct real-user acceptance of the exact final JAR SHA-256 on the user's actual Minecraft setup. Required runtime acceptance: no sinking through floor; stable standing; forward/back/strafe/sprint; jump+airborne+natural landing; wall/ceiling/floor solidity; stable turns and speed changes; no sink/throw/drift/lag-behind; free/stable camera/look. The historical failed SHA can never satisfy this gate.

## Fresh-chat / watchdog protocol
1. Inspect actual HEAD.
2. Read this file completely and reconcile `current_head` / implementation / proof basis with actual HEAD.
3. Inspect only latest relevant Actions evidence for active blocker.
4. Respect FROZEN_GREEN and FAILED_HYPOTHESES.
5. Execute `next_safe_action`; do not stop at narration.
6. Keep watchdog turns compact and always end with exactly one valid standalone `WATCHDOG_DECISION:` line.
