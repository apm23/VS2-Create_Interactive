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
- project_state: `ROOT_REDESIGN — PRE-COLLISION EXTERNAL OWNER IS ACTIVE; OBB ZERO-RESPONSE FALSE-POSITIVE VERIFIER UNDER RECHECK`
- ledger_basis_head: `4c0a15784fd004cf582bfe04617fb2aa411253fe`
- final_ready: `false`
- exact historical failed user JAR SHA256: `96053e314891495fbb4bf16c446023568fed542497e083083dad7ed420dcd7ef`
- user_runtime_validation: historical candidate FAILED; never ask user to retest that SHA.
- production scheduler patch: `0ce0dfd4f6f29685eb18b6e3a8c14ddc247bbb9b`
- active verifier-only commit: `4c0a15784fd004cf582bfe04617fb2aa411253fe` (`Accept Create temporal-only OBB responses in frame proof`).
- current proof workflow: `m1-reference-owner-v2-collision-frame-window-proof`.
- current proof run: pending Actions registration when this ledger update was written.
- no gameplay/physics production source changed by the OBB semantics/verifier commits `09e9cea...`, `2c8d765...`, `60dd46ca...`, `c580e0ec...`, `4c0a157...`.

## Root architecture proofs
- `6e079d62d0d30e8508ad825ef80791088fa28e5c`, run `34963733838` SUCCESS: old implementation was contact/lease reanchor, not continuous VS2 reference space.
- `c364910f3c9419a5b37b41a3c59fa77124a10b02`, run `34969572212` SUCCESS: pinned VS2 native owner lifecycle requires a registered `ShipId`; there is no native public non-Ship owner seam. Fake/proxy ship is forbidden.
- `abb57fff0d3635f09c9f85aa699df9f88d57abcf`, run `34972926851` SUCCESS: reference-owner redesign boundary mapped.
- `2eeac3f8222931a56e760f05ec62bbe2131e2c43`, run `34975161200` SUCCESS: LocalPlayer M1 core slice bounded to owner state, body drag, relative packet, server resolution, standing render interpolation, and yaw transform. Create collision geometry remains separate.
- `ebf4aaf73a0fb401cfeb77e9017f43af3b6f11c9`, run `34977644889` SUCCESS: Create `6.0.9-1` common carriage Entity id + bilateral transform API exists. Pinned Create JAR SHA256 `d9c6cb6116d5caa1174a289ecd7d3cdd463ccef6e8db1249ab0bcfcd8c935870`.

## V1/V2 core implementation
- V1: `6ef53dab...` -> `655fd1da...` -> `59e75959...` -> `4aeaf9f5...`; run `34984299770` SUCCESS.
- V1 proved generalized non-Ship owner state + Entity-id resolver + VS2 EntityDragger lifecycle; acquisition intentionally disabled; historical Phase83/205 reanchor excluded when external owner active.
- V2 implementation `5f687aca0af43ca4783fb915c3aea1651da74dc1`; composefix `ea546f83f3549736aa4ac0dfad23b82005a63cd0`; proof `a3f37d8e8c896dc05eca1e4b74759a25100a34bc`; run `34994353308` SUCCESS.
- V2 structurally proved selected Create carriage acquisition, bounded owner lifetime, dedicated `PacketPlayerReferenceMotion`, same-owner client/server/render/yaw path, no fake ship, old Phase83/205 reanchor authority removed, Fabric compile GREEN.

## Historical exact-JAR user runtime failure — overrides old CI GREEN
Exact SHA256 `96053e314891495fbb4bf16c446023568fed542497e083083dad7ed420dcd7ef` FAILED direct user runtime:
- floor hard/solid PASS;
- grounded walking PASS;
- walls soft FAIL;
- jump/airborne dragged player backward ~2–4 carriages FAIL;
- turns swept player/camera and could throw player outside FAIL;
- behavior did not feel like a stable VS2 moving base FAIL.
This remains authoritative regression evidence and blocks `FINAL_READY`.

## Initial V2 real-train body-continuity failure
- gate commit `b1464506b6e0f3635c4d50ecb7615913a87d5ba9`, run `34997330399` FAILURE.
- carriage/train, owner acquisition, grounded walk, vanilla jump request/airborne/landing all appeared, but body continuity failed catastrophically (~93.48 blocks owner-relative horizontal drift; ~51.83 max one-tick step).
- artifact showed Create contact carry and VS2 external-owner body transform both writing player movement.

## Scheduler lifecycle root — FROZEN requirement, old placement superseded
- runtime proved external owner must enter VS2 EntityDragger lifecycle; `f81507dd...`, run `35008163064` SUCCESS. This lifecycle requirement is FROZEN_GREEN.
- run `35025200849` later proved old scheduling order was `CREATE_COLLISION_HEAD -> CREATE_COLLISION_RETURN -> VS2_DRAG_BEFORE -> VS2_DRAG_AFTER` on all 14 complete same-owner ticks.
- therefore exact old postTick placement is not protected.
- production commit `0ce0dfd4f6f29685eb18b6e3a8c14ddc247bbb9b` moves only external-owner LocalPlayer drag immediately after `ClientLevel.tick(...)`, before Create client collision; native VS2 ship scheduling remains native.
- no setPos chase, synthetic velocity, gravity, collision clamp, camera mutation, fake ship, or Create geometry takeover is added.

## Active-owner Create contact-carry authority — FROZEN_GREEN
- production authority fix `652667e887720509f37618641e231f70e8e689c4`.
- proof `07dbd852712c3c3d81b4d405e253befd4b34ac65`, run `35017634522` SUCCESS.
- exact-owner suppressions `18`, sibling suppressions `3`, no collision-response writer overlap; conclusion `single_reference_body_writer_proven`.
- scope is narrow: LocalPlayer only + valid active external owner + Create ordinal-1 contact carry only. Create OBB, grounding, damage, floor/wall/ceiling geometry and first collision response remain authoritative.
- do not broaden without new direct runtime evidence.

## Authority-fixed real-train retest
Run `35020203661`:
- composition/compile/fixture/assets passed; runtime timed out waiting for jump.
- train moving, external owner acquisition, bounded forward walk, native backward and right strafe passed.
- jump was never requested because fresh floor/native-contact prerequisite disappeared; this is NOT jump-input evidence.
- turn seam showed carriage frame/support continuity collapse; no gravity/input/camera workaround is authorized.

## Same-point transform — FROZEN_GREEN
- commit `7bf93e0b8b9c8c9eac56f6f9a5aff2df9394a20d`, run `35023234306` SUCCESS.
- exact result `SAME_POINT_TRANSFORM_MATCHES_NATIVE_POINT_TIMING_DIFFERS`; same-point/current-point mismatches were `0.000000`.
- do NOT patch resolver previous/current transform math, yaw, partial-tick transform semantics, or point-vs-vector math without contrary evidence.

## Camera / free-look boundary — FROZEN_GREEN
- `08742d7e...`, run `35033671863` SUCCESS: `PLAYER_OWNER_RENDER_WIRED_CAMERA_OWNER_UNWIRED`; standing render follows external owner spatially while camera owner remains unwired.
- `127d85af...`, run `35034983734` SUCCESS: `EXTERNAL_OWNER_CAMERA_SPATIAL_FOLLOWS_PLAYER_LOOK_REMAINS_UNCOUPLED`; external packet/server yaw resolution exists, standing render has external position transform but no direct external rotation tokens; camera stays ship-mount-only.
- this is desired free-look architecture. Do NOT add camera counter-rotation/direct camera transform.

## Exact pre-collision owner / OBB runtime evidence
Source runtime run `35031106237`, artifact `reference-owner-v2-owner-obb-support-log`, digest `sha256:20182d039abb98dd4d52cef1d93d1f9f4899e1d5a824d0c7926d90167f1ea009`:
- exact owner/carriage 7 remains matched ticks 24–39.
- physical support is true through tick 33, false from tick 34 onward.
- owner-local Y remains essentially fixed around `2.0001` through ticks 34–39 despite `on_ground=false`.
- exact Create owner callback continues through ticks 34–39.
- Create active-owner ordinal-1 carry remains suppressed with collision response preserved.
- landing/turn/wall/ceiling are still unproven in this artifact.

## OBB support-loss proof chain — ZERO RESPONSE IS NOT ITSELF A FAILURE
- `0afa038e...`, run `35036337486` originally FAILED with `ACTIVE_OWNER_CREATE_OBB_RESPONSE_ZERO_ONLY`: ticks 34–39 had continuous external owner, stable owner-local Y, `surface=true`, but zero collision response. This failure criterion is now superseded as overstrict.
- `09e9cea...`, run `35037369180` SUCCESS: exact ticks 34–39 all have zero collision response but finite descriptors, positive temporal values `0.001275510..0.255244919`, and nonzero vector magnitude `0.0002`; classification `ACTIVE_OWNER_OBB_ZERO_RESPONSE_POSITIVE_TEMPORAL_VALID_NORMAL`.
- `2c8d765...`, run `35037534677` SUCCESS: exact Create bytecode exposes `CollisionResponse` fields and consumer-side normalization; the `0.0002` vector is not proof of a broken unit normal.
- `60dd46ca...`, run `35039049624` SUCCESS: `CREATE_OBB_ZERO_RESPONSE_HAS_EXPLICIT_PRODUCER_PATH_AND_NORMALIZED_CONSUMER`; producer has an explicit ZERO response path and consumer independently reads response/normal/temporal/surface.
- `c580e0ec...`, run `35040491258` SUCCESS: `CREATE_OBB_SUPPORTS_TEMPORAL_ONLY_SOLVED_RESPONSE`; Create has both a default no-collision path and a dynamic solved path, independently tests `collisionResponse != ZERO` and `temporalResponse != 1`, and computes temporal motion before transforming/consuming collision response.
- exact runtime ticks 34–39 satisfy `0 < temporal < 1`; therefore zero `collisionResponse` there is compatible with Create's legitimate temporal-only solved path and does NOT authorize a gameplay/collider patch.
- verifier-only commit `4c0a157...` updates `m1-reference-owner-v2-collision-frame-window-proof` to accept continuous temporal-only solved responses while still rejecting missing callback, missing airborne window, owner discontinuity, local-Y drift, missing surface, or unresolved zero-temporal descriptors.

## FROZEN_GREEN / protected
- bootstrap/Kotlin packaging repair `f3d1335c9fc89283d936af039eba34aa9778bd05`.
- Create train + VS2 coexistence.
- Steam 'n' Rails + Copycats preservation.
- V1 infrastructure run `34984299770`.
- V2 structural/core run `34994353308` except body-continuity assumptions disproved by runtime.
- external-owner EntityDragger lifecycle requirement from run `35008163064`.
- active-owner ordinal-1 authority boundary `652667e...` / run `35017634522`.
- same-point transform equivalence run `35023234306`.
- free-look/camera uncoupled boundary runs `35033671863` and `35034983734`.
- historical user-proven floor solidity and grounded walking remain protected behavioral criteria, not current completion proof.

## FAILED_HYPOTHESES / anti-loop
Do not reintroduce without new direct evidence:
- `EXACT_SHAPES_LOCALPLAYER_0fa4aa`;
- generic frame lease/replay/carry extension;
- synthetic carry velocity / inertia compensation;
- fake gravity;
- manual floor/wall clamps or floor-only collision workaround;
- per-tick teleport/setPos chase/reanchor architecture;
- direct camera forcing/rotation compensation;
- jump/input timing tuning without input-specific evidence;
- sprint/reverse/strafe tuning as a reference-frame fix;
- unscoped/global collider suppression, ownerless broad suppression, or suppression of Create's collision-response writer;
- duplicate Create/VS2 gameplay/collision authority;
- fake/proxy VS2 ship solely for lifecycle;
- harness mutation used to manufacture GREEN;
- resolver prev/current/yaw/point semantic changes after run `35023234306` absent contrary evidence;
- treating `surface=true + collisionResponse=ZERO` alone as a collision failure after runs `35039049624` and `35040491258`.

## next_safe_action
1. Inspect the Actions run triggered by verifier-only commit `4c0a15784fd004cf582bfe04617fb2aa411253fe`.
2. If queued/in_progress: HOLD; stack no gameplay patch.
3. If verifier/fixture mechanics fail: repair only the verifier/harness.
4. If the exact source artifact now classifies `ACTIVE_OWNER_CREATE_COLLISION_FRAME_CONTINUOUS_TEMPORAL_ONLY`, freeze this support-loss collision-frame slice as GREEN; do not patch OBB response.
5. Then advance to the smallest runtime proof that is still genuinely unproven: natural airborne landing continuity first, then wall/ceiling solidity, then turn/speed-change stability. Preserve free-look camera boundary.
6. Any production gameplay patch requires direct new failure evidence from the next unproven criterion; CI/verifier failure alone is insufficient.

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