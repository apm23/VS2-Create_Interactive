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

## Current reconciled state — 2026-09-17
- `current_head`: `b48dad66de35796bb76375994f39f64122b79078` immediately before this ledger-only reconciliation commit.
- project_state: `ROOT_REDESIGN — CAMERA OWNER-GATE BOUNDARY IS NOW PROVEN REACHABLE, BUT TURN-POSITIONAL BEHAVIOR IS NOT YET CLOSURE-READY. RUN 35113644070 PROVES Camera.update AFTER vanilla alignWithEntity SEES LocalPlayer + dragging provider + active external owner + non-null owner id + resolvable previous/current transforms. THE SAME READ-ONLY GATE ARTIFACT SHOWS CAMERA-vs-EXPECTED HORIZONTAL DELTAS UP TO ~0.793 BLOCK, BUT THAT RUN DID NOT MEASURE OWNER HEADING/TURN SPAN, SO IT DOES NOT YET AUTHORIZE A CAMERA GAMEPLAY PATCH. THE PREVIOUS TURN VERIFIER PRODUCED ZERO ROWS BECAUSE IT DECIMATED THE ALREADY-SPARSE ACTIVE-OWNER Camera.update CALLBACKS. HEAD b48dad66 REPAIRS ONLY THAT VERIFIER: EVERY ACTIVE-OWNER CAMERA CALLBACK IS SAMPLED AND THE MINIMUM SAMPLE GATE IS REDUCED TO A REALISTIC 4 UNIQUE TICKS. NO CAMERA/PLAYER/LOOK/PHYSICS STATE IS MUTATED. VIDEO IS FORBIDDEN UNTIL THIS BLOCKER IS CLOSURE-READY.`
- latest gameplay implementation: `9aea12a6114198c33c70d52897eb9d3c29342425` (`Refresh jump owner from exact Create grounded carry contact`).
- latest camera owner-gate verifier head: `bceeb6ab413f1011cf65cf05a846863adf80c9a4` (`Classify camera external-owner gate after acquisition`).
- camera owner-gate workflow `m1-camera-owner-gate-runtime-proof`, run `35113644070`, SUCCESS; artifact `10454120245`, zip SHA256 `24ba034f1ab60db6a2c1264ba925293ab7a104d2b129d6b4aa3b4e37abecd32f`.
- exact owner-gate result: `CAMERA_EXTERNAL_OWNER_GATE_REACHED`; acquisitions `16`, native contacts `22`, 5 post-acquire camera/player/provider/external-active/owner-nonnull/transform/frame rows; telemetry-only and production unchanged.
- owner-gate frame samples include horizontal camera-vs-expected deltas `0.792871621`, `0.086648547`, `0.000004373`, `0.141226609`, `0.223163582`; these are not yet classified as turn failure because heading span was not recorded in that proof.
- previous camera-turn verifier head `604e01945c99e9e33c40be67f0dda28772a1d75c`, run `35110832310`, produced `NO_CAMERA_OWNER_ROWS` despite acquisitions; that zero-row result is superseded as a verifier sampling/gating limitation by run `35113644070` proving the camera owner gate is reachable.
- latest camera-turn sampling verifier head: `b48dad66de35796bb76375994f39f64122b79078` (`Measure every active-owner camera turn sample`).
- active camera-turn workflow: `m1-camera-turn-positional-runtime-proof`, run `35117703635`, exact head `b48dad66de35796bb76375994f39f64122b79078`, IN_PROGRESS at this reconciliation point.
- latest source-map verifier head: `094218f888702665f337443bedd544dbee6fc04d` (`Map wall ceiling and camera response seams`).
- latest pinned contact classifier head: `c5267cc6b82da1e6be2723bc341c3ab887b1e8c4` (`Classify pinned wall and ceiling OBB contacts`).
- latest wall temporal-response verifier head: `465b517ede2574155a7decbc18e8917de7fe4b9a` (`Classify pinned wall temporal response path`).
- source-map workflow `m1-wall-ceiling-camera-source-map`, run `35101691613`, SUCCESS; artifact `10448192299`, zip SHA256 `c9e19ec866b671a7820e3b80c0b5ad002e7c3cc37c42f48d0aaffafbb12b985d`.
- pinned wall/ceiling contact workflow `m1-pinned-wall-ceiling-contact-proof`, run `35104224078`, SUCCESS; artifact `10450080515`, zip SHA256 `9614041999295ef68bd6e908e394c1954f2394519144b76b2447f632d0221e85`.
- pinned wall temporal/writer workflow `m1-pinned-wall-response-writer-proof`, run `35104523803`, SUCCESS; artifact `10449412710`, zip SHA256 `4ab40a457a756db47bd141510387fad607aad9421de44bd09a9c52b4977d5584`.
- corrected current-frame proof remains workflow `m1-current-create-frame-continuity-proof`, run `35100081357`, SUCCESS.
- final_ready: `false`.
- exact historical failed user JAR SHA256: `96053e314891495fbb4bf16c446023568fed542497e083083dad7ed420dcd7ef`; never ask user to retest it.
- active blocker: finish the exact player-vs-camera positional reference-frame measurement during a real carriage turn, then close it only if data is valid; overhead-ceiling response remains the next independent blocker. Preserve Create collision authority and free look. No video while camera proof is still debugging/correction/proving.
- known invalid workflow noise: `.github/workflows/m1-reference-owner-v2-airborne-drag-boundary-proof-v2.yml` emits instant zero-job failures; ignore it.

## Historical direct-user runtime gate — authoritative regression evidence
Exact JAR SHA256 `96053e314891495fbb4bf16c446023568fed542497e083dad7ed420dcd7ef` FAILED:
- floor hard/solid PASS and grounded walking PASS;
- walls soft FAIL;
- jump/airborne dragged player backward ~2–4 carriages FAIL;
- turns swept player/camera, wall could be penetrated, player could be thrown outside FAIL;
- behavior did not feel like a stable VS2 moving base FAIL.
This direct runtime evidence overrides automated M1 green and blocks `FINAL_READY`.

## Root architecture / protected structural proofs
- run `34963733838`: old implementation was contact/lease reanchor, not continuous VS2 reference space.
- run `34969572212`: native VS2 owner requires registered ShipId; fake/proxy ship is forbidden.
- run `34972926851`: reference-owner redesign boundary mapped.
- run `34975161200`: core slice bounded to owner state/body drag/relative packet/server resolution/render/yaw; Create collision remains separate.
- run `34977644889`: Create carriage Entity id + bilateral transforms available; pinned Create JAR SHA256 `d9c6cb6116d5caa1174a289ecd7d3cdd463ccef6e8db1249ab0bcfcd8c935870`.
- V1 run `34984299770`: generalized external owner state + Entity-id resolver + VS2 EntityDragger lifecycle.
- V2 run `34994353308` was structurally green, but later runtime disproved its original overall continuity assumption.

## Scheduler / authority — protected
- external-owner EntityDragger lifecycle requirement run `35008163064` remains protected.
- production scheduler `0ce0dfd4...` applies only external-owner LocalPlayer drag after `ClientLevel.tick` and before Create collision; native VS2 ship scheduling remains separate.
- active-owner ordinal-1 authority proof `35017634522` remains valid for its tested boundary.
- Create OBB/grounding/floor/walls/ceiling remain authoritative. Do not suppress Create's first collision-response writer or global Create collision behavior.

## Transform / body / look — FROZEN_GREEN for the proven boundary
- same-point transform run `35023234306`: exact same-point mismatch `0`; no blind resolver prev/current/yaw/point changes.
- camera run `35033671863`: external-owner spatial render wired, camera owner unwired.
- look run `35034983734`: external-owner spatial follow with look uncoupled; free look is required and direct camera counter-rotation is forbidden.
- native drag gate run `35045444238`: `EXTERNAL_OWNER_NATIVE_GATE_NOT_REJECTING`; do not patch `isDraggable` / `vs$shouldDrag`.
- body writer verifier `35048234680` over `35046701119`: existing VS2 boundingBox/setPos writer applies its calculated step exactly; do not add or replace a body-position writer.
- corrected current-frame run `35100081357`: current Create collision-frame coordinates remain continuous through observed jump-arc rotation updates; resolver patch is not authorized from the old partial-0 mismatch.
- source-map run `35101691613`: Create current-world-to-local OBB path, horizontal wall-axis clipping, vertical Y clipping, response `setPos`, and surface contact-motion writer are present; legacy Phase205 duplicate authority is removed; external-owner render interpolation is present; camera owner files remain absent (`camera_owner_files=0`).
- camera owner-gate run `35113644070`: immediately after vanilla `Camera.alignWithEntity`, LocalPlayer camera can observe the active external owner and resolve previous/current transforms. This freezes only the reachability/gate boundary; it does NOT freeze positional alignment through turns.

## OBB / collision semantics — FROZEN_GREEN for the proven boundary
- runtime `35031106237`: owner/carriage matched through support loss and Create callbacks continued.
- runs `35037369180`, `35037534677`, `35039049624`, `35040491258`: temporal-only solved response is valid.
- verifier `35041914462`: `ACTIVE_OWNER_CREATE_COLLISION_FRAME_CONTINUOUS_TEMPORAL_ONLY`.
- `surface=true + collisionResponse=ZERO + 0<temporal<1` is valid Create behavior; do not reinterpret it as failure.
- pinned contact run `35104224078`: 128 OBB rows, 53 surface rows, 7 horizontal wall-direction rows at ticks `[26,27,28,29,31,52,60]`; no overhead ceiling-direction row was observed.
- pinned wall-response run `35104523803`: all 7 wall rows are valid temporal-only responses; `temporal_only_rows=7`, `unresolved_zero_rows=0`, `nonzero_response_rows=0`, temporals `[0.710437968,0.710017131,0.7097019,0.711176538,0.483729387,0.984695356,0.821042984]`; all 7 have nearby LocalPlayer `collide` consumption telemetry. No gameplay wall response rewrite is authorized from these rows.
- the same artifact had `create_setpos_neighborhood_rows=0`, so exact final Create position-writer correlation for those wall rows is not yet proven by this artifact.
- ceiling contact remains unexercised in the pinned valid-jump artifact (`ceiling_rows=0`).
- The direct-user wall/ceiling/turn regression is NOT globally frozen green; only the tested current-frame and temporal-response semantics above are protected.

## Lifecycle history / current production
- verifier `35048427002`: first false clear was grounded-contact expiry on native jump tick; production `a14260c...` corrected that narrow failure.
- run `35051781646`: ordinary descent support-miss lifecycle is frozen green; generic lease extension is disproven.
- run `35057564114`: exact strict-support airborne failure had owner carriage7, jump tick47, owner cleared tick49 and large Create carry reopened.
- verifier `35062047086`: `EXTERNAL_OWNER_CLEARED_BY_GROUNDED_CONTACT_EXPIRY_ON_NATIVE_JUMP_TICK` authorized only the bounded jump-active correction.
- commit `c3e7c51...` introduced jump-active state; later natural-landing attempt3 reached owner cap before same-owner Create landing.
- run `35071088843`: exact owner-cap frame-lag proof — owner expired tick68, landing began tick70, two-frame carriage lag exactly `0.330086470` blocks.
- production `d6e55e2...` extended an already-armed jump owner only until same-owner native Create landing, with bounded safety limit and no motion/camera/collision override.
- latest gameplay `9aea12a...` refreshes jump owner from exact Create grounded carry contact; it remains the current gameplay basis pending valid direct boundary evidence.

## Fixture / harness history — protected from blind tuning
- run `35067811102`: pre-jump non-admission classification; no physics inference.
- run `35079785697`: identical harness diverges by selected carriage runway.
- run `35084762923`: admitted/current runs begin on same physical server fixture carriage; divergence begins at post-move client candidate arbitration.
- run `35085286003`: nearest-center selected carriage feeds first contact baseline then fixture walk. Entity-id/size/span hardcoding is forbidden.
- do not shorten input timing or mutate the harness merely to manufacture GREEN.

## Valid-jump current-frame correction — READ-ONLY GREEN
Pinned historical valid-jump source artifact:
- run `35089177675`, exact head `012d92dabb86cac5571d5d320eea9fa77ea539d6`;
- artifact `10444135201`, digest `sha256:62dc537d525cf2f5375892157583e024cfa2c03b314df98a33aca0d09f8810ce`;
- native airborne tick46, rise `+0.33319999363422365`;
- external owner `7` remains active/jump-active continuously through ticks46..83.

Verifier-only commit `134f31df2bf678e367786b53e22cfb0726710809`, run `35099171565`, initially classified a `2.505534403`-block mismatch by comparing old `toLocalVector(...,0)` telemetry/body displacement against current Create collision/origin movement. That classifier is retained as history but its resolver-failure conclusion is superseded by the corrected proof below.

Corrected verifier `5d66fdc4...`, run `35100081357` SUCCESS:
- source semantics prove old post-arc `owner_local` calls `toLocalVector(...,0)`, which uses previous rotation interpolation, while Create `ContinuousOBBCollider` evaluates geometry in current `worldToLocalPos` / current rotation state;
- the old diagnostic diverges on ticks `[50,52,63,67]`, max `2.505534403`, but this is not the current Create collision frame;
- in the actual Create current collision frame the maximum horizontal step on those same rotation updates is only `0.048467738` blocks;
- candidate current-frame coordinates and Phase131 `worldToLocalPos` coordinates agree exactly: max residual `0`;
- ceiling geometry is observed continuously across ticks46..69;
- external owner lifecycle is continuous and the existing EntityDragger writer executes on the rotation-update ticks;
- conclusion: `old_toLocalVector_partial0_diagnostic_is_not_current_Create_collision_frame_and_does_not_prove_resolver_failure`;
- conclusion: `current_Create_collision_frame_remains_continuous_through_observed_rotation_updates=true`;
- conclusion: `resolver_patch_not_authorized_from_old_mismatch=true`.
This does not negate the user's wall/turn/camera failure. It only prevents a false resolver rewrite and narrows the next inspection to collision response and render/camera reference-frame behavior.

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
- owner-cap lag proof `35071088843`;
- fixture arbitration boundaries `35084762923`, `35085286003`;
- current Create collision-frame continuity across observed jump-arc rotations `35100081357`;
- pinned wall temporal-only response semantics `35104523803`;
- camera external-owner gate reachability after `alignWithEntity` `35113644070`;
- historical user-proven floor solidity and grounded walking.

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
- unscoped/global collider suppression or suppression of Create's collision-response writer;
- duplicate Create/VS2 gameplay/collision authority;
- fake/proxy VS2 ship;
- harness mutation used to manufacture physics GREEN;
- blind resolver prev/current/yaw/point semantic changes after `35023234306` and corrected proof `35100081357`;
- treating the old `toLocalVector(...,0)` diagnostic mismatch as a current Create collision-frame failure;
- treating temporal-only zero collisionResponse as failure, including the exact pinned wall rows proven in `35104523803`;
- patching `isDraggable`/`vs$shouldDrag` after `35045444238`;
- adding/replacing a body-position writer after `35048234680`;
- changing Phase64 grounding/Y-clip merely because its source location is known;
- hardcoding carriage entity id, block count, span, or guessed geometry;
- changing the server `firstOrNull` initial fixture carriage selector from the admitted/current divergence.

## next_safe_action
1. Preserve the proven external-owner lifecycle, resolver prev/current pairing, native drag gate, existing VS2 body writer, Create collision authority, free-look boundary, and pinned wall temporal-only semantics.
2. Inspect only camera-turn run `35117703635` first. It is the smallest relevant proof and samples every sparse active-owner camera callback while measuring owner heading and camera-vs-external-owner expected position.
3. If the run measures `CAMERA_POSITIONAL_OWNER_MISMATCH_MEASURED` during actual turn rows, use those exact rows to identify the smallest ownership/transform integration boundary. Do not counter-rotate/force camera and do not extend a generic lease.
4. If it reports `CAMERA_POSITIONAL_OWNER_ALIGNED_WITHIN_0_05` with a real heading span and no open correction, the camera blocker becomes closure-ready for ONE exact-head short visual-close smoke. Do not record video before that point. Stop for joint video review before freezing the subsystem.
5. If it reports insufficient turn/sampling/owner change, repair only read-only verifier/fixture observation; do not mutate gameplay to manufacture the proof.
6. After the camera blocker is visually approved/frozen, add the smallest read-only runtime instrumentation/harness that genuinely exercises an overhead ceiling contact in Create's current `worldToLocalPos` frame. Record OBB normal/response/surface/temporal, final `collide` result, and final Create position/motion writer with player tick.
7. If wall behavior must be revisited later, first add tick-bearing final Create `setPos` correlation; current pinned artifact has all seven wall rows near `collide` consumption but no direct final Create `setPos` neighborhood proof.
8. Only a direct current-frame invariance failure, missing/incorrect Create ceiling response, or measured player-camera positional-frame mismatch may authorize one gameplay hypothesis. One commit = one hypothesis.
9. If a gameplay patch regresses any frozen-green criterion, revert before stacking another workaround.
10. Automated proof alone can never set `FINAL_READY`; exact final JAR still requires direct user runtime acceptance.

## Video validation gate — blocker closure only
- Video is NOT a debugging tool and is forbidden on ordinary runs, failed runs, instrumentation/correction loops, compile checks, hypothesis tests, and intermediate telemetry green.
- One short visual-close capture is allowed only after the active blocker is closure-ready from exact data/runtime proof and no correction remains open.
- Use exact same proof HEAD/build, real exercised event, existing Xvfb path plus minimal FFmpeg; do not alter gameplay/fixture/timing to help capture.
- One narrow media-infrastructure repair maximum. No screenshot hunting or media-tool loop.
- A subsystem becomes FROZEN_GREEN only after user + assistant approve the exact-head closing video. Visible failure overrides telemetry green.

## Finalization policy — HARD USER RUNTIME GATE
Automated proof can never alone set `FINAL_READY`. A new exact JAR must pass direct user runtime for stable standing, forward/back/strafe/sprint, jump+airborne+natural landing, floor/walls/ceiling, turns, acceleration/deceleration/speed changes, no sink/throw/drift/lag-behind, and free/stable camera/look. The watchdog local SHA gate must match that exact accepted JAR.

## Fresh-chat/watchdog protocol
1. Inspect actual HEAD.
2. Read this file completely and reconcile `current_head`/implementation/proof basis with actual HEAD.
3. Inspect only the latest relevant Actions evidence for the active blocker.
4. Respect FROZEN_GREEN and FAILED_HYPOTHESES.
5. Execute `next_safe_action`; do not stop at narration.
6. Keep watchdog turns compact and always end with exactly one valid standalone `WATCHDOG_DECISION:` line.
