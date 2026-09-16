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
- project_state: `ROOT_REDESIGN — NATURAL JUMP REPRODUCES 21.599-BLOCK AIRBORNE OWNER-LOCAL DRIFT AT TICK 33->34; READ-ONLY EXTERNAL-OWNER DRAG BOUNDARY PROOF ACTIVE`
- ledger_basis_head: `b87a62b3e26c0ebcd8a77059daa4d90cdca20824`
- final_ready: `false`
- exact historical failed user JAR SHA256: `96053e314891495fbb4bf16c446023568fed542497e083083dad7ed420dcd7ef`
- user_runtime_validation: historical candidate FAILED; never ask the user to retest that SHA.
- production scheduler patch: `0ce0dfd4f6f29685eb18b6e3a8c14ddc247bbb9b`.
- production active-owner Create carry authority patch: `652667e887720509f37618641e231f70e8e689c4`.
- current diagnostic workflow commit: `b87a62b3e26c0ebcd8a77059daa4d90cdca20824` (`Trace airborne external-owner drag boundary`).
- current proof workflow: `m1-reference-owner-v2-airborne-drag-boundary-proof`.
- current proof run: `35044076536` — queued when this ledger was written.
- current diagnostic is read-only; production gameplay/physics source is unchanged.

## Historical direct-user runtime gate — authoritative regression evidence
Exact JAR SHA256 `96053e314891495fbb4bf16c446023568fed542497e083083dad7ed420dcd7ef` FAILED:
- floor hard/solid PASS;
- grounded walking PASS;
- walls soft FAIL;
- jump/airborne dragged player backward ~2–4 carriages FAIL;
- turns swept player/camera and could throw player outside FAIL;
- behavior did not feel like a stable VS2 moving base FAIL.
This blocks `FINAL_READY` regardless of old automated GREEN.

## Root architecture proofs
- `6e079d62...`, run `34963733838` SUCCESS: old implementation was contact/lease reanchor, not continuous VS2 reference space.
- `c364910f...`, run `34969572212` SUCCESS: pinned VS2 native owner lifecycle requires registered `ShipId`; no native public non-Ship owner seam. Fake/proxy ship forbidden.
- `abb57fff...`, run `34972926851` SUCCESS: reference-owner redesign boundary mapped.
- `2eeac3f...`, run `34975161200` SUCCESS: M1 core slice bounded to owner state/body drag/relative packet/server resolution/standing render/yaw; Create collision stays separate.
- `ebf4aaf...`, run `34977644889` SUCCESS: Create `6.0.9-1` carriage Entity id + bilateral transforms available. Pinned Create JAR SHA256 `d9c6cb6116d5caa1174a289ecd7d3cdd463ccef6e8db1249ab0bcfcd8c935870`.

## V1/V2 implementation
- V1 chain through run `34984299770` SUCCESS: generalized non-Ship owner state + Entity-id resolver + VS2 EntityDragger lifecycle; acquisition disabled; old reanchor excluded under external owner.
- V2 implementation `5f687aca...`, composefix `ea546f83...`, proof `a3f37d8e...`, run `34994353308` SUCCESS: selected Create carriage owner, bounded lifetime, dedicated `PacketPlayerReferenceMotion`, same-owner client/server/render/yaw path, no fake ship, old Phase83/205 authority removed.
- Initial V2 real-train run `34997330399` FAILURE: jump existed but owner-relative airborne drift ~`93.48251` blocks / max one-tick ~`51.82845`; Create contact carry and VS2 owner body both wrote movement.

## Scheduler / authority — protected production boundaries
- External-owner EntityDragger lifecycle is required: `f81507dd...`, run `35008163064` SUCCESS. This lifecycle requirement is FROZEN_GREEN.
- Runtime order run `35025200849` proved old order on 14 complete ticks was `CREATE_COLLISION_HEAD -> CREATE_COLLISION_RETURN -> VS2_DRAG_BEFORE -> VS2_DRAG_AFTER`.
- Production scheduler `0ce0dfd4...` moves ONLY external-owner LocalPlayer drag to immediately after `ClientLevel.tick(...)`, before Create client collision. Native VS2 Ship postTick scheduling stays native. No setPos chase, synthetic velocity, gravity, clamp, camera mutation, fake ship, or Create geometry takeover.
- Active-owner Create ordinal-1 carry authority production `652667e...`; proof `07dbd852...`, run `35017634522` SUCCESS: exact-owner suppressions `18`, sibling suppressions `3`, no collision-response writer overlap; conclusion `single_reference_body_writer_proven`.
- Authority scope is narrow: LocalPlayer + valid active external owner + Create ordinal-1 material carry only. Create OBB, grounding, damage, floor/wall/ceiling and first collision-response writer remain authoritative.

## Authority-fixed real-train retest / transform proof
- Run `35020203661`: train moving, owner acquisition, forward walk, backward, right strafe passed; jump never requested because floor/native-contact prerequisite had gone stale. Turn seam showed reference/support continuity collapse; this was NOT jump-input evidence.
- Same-point transform commit `7bf93e0...`, run `35023234306` SUCCESS: `SAME_POINT_TRANSFORM_MATCHES_NATIVE_POINT_TIMING_DIFFERS`, exact same-point/current-point mismatch `0.000000`.
- Therefore do NOT change resolver prev/current transform, yaw, partial-tick transform, or point-vs-vector semantics without new direct contrary evidence.

## Camera / free-look — FROZEN_GREEN
- `08742d7e...`, run `35033671863` SUCCESS: `PLAYER_OWNER_RENDER_WIRED_CAMERA_OWNER_UNWIRED`.
- `127d85af...`, run `35034983734` SUCCESS: `EXTERNAL_OWNER_CAMERA_SPATIAL_FOLLOWS_PLAYER_LOOK_REMAINS_UNCOUPLED`.
- Standing render follows external owner spatially; direct external camera rotation is absent. This is desired free-look. Do NOT add camera counter-rotation/direct camera transform.

## OBB support-loss proof chain — FROZEN_GREEN
Source runtime run `35031106237`:
- exact external owner/carriage 7 remains matched ticks 24–39;
- physical support true through tick 33, false from 34 onward;
- owner-local Y remains ~`2.0001` through ticks 34–39;
- exact Create owner callback continues; collision-response authority remains preserved.

Semantics chain:
- run `35036337486` originally FAILED `ACTIVE_OWNER_CREATE_OBB_RESPONSE_ZERO_ONLY`; criterion was later proven overstrict.
- run `35037369180` SUCCESS: ticks34–39 response zero but finite descriptors, temporal `0.001275510..0.255244919`.
- run `35037534677` SUCCESS: exact Create bytecode/result semantics mapped.
- run `35039049624` SUCCESS: explicit ZERO producer path + normalized independent consumer.
- run `35040491258` SUCCESS: `CREATE_OBB_SUPPORTS_TEMPORAL_ONLY_SOLVED_RESPONSE`.
- verifier-only `4c0a157...`; run `35041914462` SUCCESS:
  `ACTIVE_OWNER_CREATE_COLLISION_FRAME_CONTINUOUS_TEMPORAL_ONLY`, owner ticks 32–39, airborne 34–39, local_y_spread `0`, 6 temporal-only rows, unresolved_zero_rows `0`, temporal `0.001275510..0.255244919`.
- Conclusion: `surface=true + collisionResponse=ZERO` with `0 < temporal < 1` is valid Create temporal-only resolution. OBB response is NOT the active blocker and must not be patched.

## Natural airborne landing proof — DIRECT CURRENT FAILURE
Workflow `.github/workflows/m1-reference-owner-v2-natural-landing-proof.yml`:
- initial commit `d3d0f885...`, run `35042229755`: invalid workflow/YAML, zero jobs, no gameplay evidence.
- YAML repair commit `b9faf4e25e986328eefacb9d39e7531ee40f4bb4`.
- run `35042299917`, job `104624575166`: composition PASS, fixture-only jump admission PASS, compile PASS, verified r0v3 save PASS, assets PASS, runtime proof FAILURE.
- artifact `reference-owner-v2-natural-landing-log`, artifact id `10425533703`, digest `sha256:9b3a9596b03e31625e7aeadc194b7e2faf21e2d6e9fef45a1329ddd370c07e39`.
- exact verifier failure: `owner-relative airborne drift too large: 21.599091`.

Jump / local-frame evidence:
- jump REQUESTED tick `30`, on_ground=true, walk_confirmed_tick=30;
- AIRBORNE tick `30`, native vertical delta `+0.3331999936` after vanilla jump path;
- harness emitted LANDED tick `37`, but this is NOT carriage landing proof because owner-carriage broadphase/support was already lost; workflow correctly failed before accepting it.
- external owner acquisition stays carriage `7` through ticks 24–29; no new owner acquisition during the failing jump window.
- carriage-7 local feet:
  - tick30 `(4.104064, 2.41999999, 0.006096)`;
  - tick31 `(4.040693, 2.75319998, 0.239880)`;
  - tick32 `(0.990514, 3.00133598, 0.477216)`;
  - tick33 `(-1.282011, 3.16610926, 0.598605)`;
  - tick34 `(23.707201, 3.24918708, 0.684483)` — catastrophic discontinuity begins here;
  - tick35 `(25.689206, 3.25220334, 0.782232)`;
  - tick37 `(24.541961, 3.17675928, 1.087566)` with broadphase false.
- selected Create support/collision candidate switches from carriage `7` to carriage `5` at tick34 while persistent external owner remains `7`.
- tick33 Phase205 read-only state for carriage7 still shows exact baseline, airborne native lease, native-frame eligible, external-frame lease, collision eligible, broadphase true.
- tick34 candidate carriage5 has no native/external-frame lease; owner7 is no longer the selected support candidate.
- Phase171 same-point telemetry had zero residual on carriage7 at ticks32–33. No carriage7 Phase171 row exists ticks34–43; when carriage7 reappears at tick44 its frame/contact values diverge materially.
- This is direct gameplay failure evidence. It authorizes root-boundary diagnosis, NOT an OBB/gravity/camera/generic-lease workaround.

## Active root question / current read-only proof
At tick33->34 one of these boundaries must be distinguished before a production patch:
1. persistent external owner 7 remained active but its VS2 body drag was not actually applied at the turn boundary;
2. external-owner drag executed, but owner7 previous->current transform itself contains the large discontinuity for this tick;
3. drag executed but actual player displacement diverges from the owner transform; or
4. articulated carriage/reference ownership requires a transition seam not yet represented by the single persistent owner.

Commit `b87a62b3e26c0ebcd8a77059daa4d90cdca20824` adds `m1-reference-owner-v2-airborne-drag-boundary-proof` only. It instruments the exact pre-Create external-owner scheduler call read-only, logging owner id/age, player world position, previous-owner-local -> current-world expected transform, and actual drag delta around the reproduced jump. It does not mutate gameplay/physics. Run `35044076536` is the active proof.

## FROZEN_GREEN / protected
- bootstrap/Kotlin packaging `f3d1335...`;
- Create train + VS2 coexistence;
- Steam 'n' Rails + Copycats preservation;
- V1 infrastructure run `34984299770`;
- V2 structural/core run `34994353308` except runtime body-continuity assumptions already disproved;
- external-owner EntityDragger lifecycle requirement run `35008163064`;
- active-owner ordinal-1 authority boundary `652667e...` / run `35017634522`;
- same-point transform equivalence run `35023234306`;
- camera/free-look boundary runs `35033671863`, `35034983734`;
- OBB temporal-only support-loss slice run `35041914462`;
- historical user-proven floor solidity and grounded walking are protected behavioral criteria, not current completion proof.

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
- treating `surface=true + collisionResponse=ZERO` alone as a collision failure after runs `35039049624`, `35040491258`, `35041914462`.

## next_safe_action
1. Inspect run `35044076536` first.
2. If queued/in_progress: HOLD and stack no additional hypothesis.
3. If compile/instrumentation/verifier mechanics fail before useful runtime evidence: repair only this proof harness.
4. If `EXTERNAL_OWNER_DRAG_CALL_EXECUTED_BUT_BODY_STEP_MISSED`: inspect/patch only the proven external-owner EntityDragger branch/lifecycle boundary, then run the same smallest jump proof.
5. If `EXTERNAL_OWNER_DRAG_APPLIED_OWNER_TRANSFORM_DISCONTINUITY`: do NOT change transform math blindly; map owner7 transform lifecycle versus articulated Create carriage identity at tick33->34, read-only first.
6. If `EXTERNAL_OWNER_DRAG_APPLIED_BUT_DIVERGES_FROM_OWNER_TRANSFORM`: instrument the exact EntityDragger external-owner calculation/writer before a production patch.
7. Only after natural airborne landing continuity is GREEN advance to wall/ceiling solidity, then turn/speed-change stability. Preserve free-look camera boundary.
8. Any production patch must be one evidence-backed hypothesis and must preserve FROZEN_GREEN subsystems.

## Finalization policy — HARD USER RUNTIME GATE
Automated proof may advance candidate build/verify but can never alone set `FINAL_READY`. A new exact JAR must pass direct user runtime for stable standing, forward/back/strafe/sprint, jump+airborne+natural landing, floor/walls/ceiling, turns, acceleration/deceleration/speed changes, no sink/throw/drift/lag-behind, and free/stable camera/look. Watchdog local SHA gate must match that exact accepted JAR.

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
