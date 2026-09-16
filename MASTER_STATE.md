# MASTER_STATE — VS2 / Create Interactive

GitHub code is the implementation source of truth. This file is the durable project-state ledger. Chat is temporary.

## Project / hard contract
- Repository: `apm23/VS2-Create_Interactive`
- Milestone: `M1 — movement / collision`
- Create owns train/carriage gameplay and collision geometry.
- VS2 must be the actual continuous moving reference-space/transform foundation for player body/render/camera.
- Standing/walking/jumping must remain carriage-relative through grounded, airborne, turns, acceleration/deceleration and speed changes while mouse/look remains free.
- Create floor/walls/ceiling remain authoritative solid geometry in that same moving frame.
- Forbidden: fake gravity, synthetic carry velocity/inertia, manual floor/wall clamps, floor-only workarounds, per-tick teleport/setPos chase/reanchor architecture, duplicate Create/VS2 authority, direct camera forcing/rotation compensation, fake/proxy VS2 ships, or workaround chains hiding double ownership.

## Current reconciled state — 2026-09-16
- project_state: `ROOT_REDESIGN — UPWARD-JUMP OWNER CLEAR FIXED; OWNER-RELATIVE JUMP CONTINUITY MATERIALLY IMPROVED; OWNER REMAINS ACTIVE THROUGH DESCENT; HEADLESS FALSE-LANDING AISTEP CUTOFF PROVEN; HARNESS-ONLY REAL-SUPPORT NATURAL-LANDING REPROOF ACTIVE`.
- ledger_basis_head: `618da46f8cffe9ed34a3502e4e4080bb0fc4f4b1` (`Repair headless natural landing proof boundary`).
- final_ready: `false`.
- exact historical failed user JAR SHA256: `96053e314891495fbb4bf16c446023568fed542497e083083dad7ed420dcd7ef`; never ask user to retest it.
- production scheduler patch: `0ce0dfd4f6f29685eb18b6e3a8c14ddc247bbb9b`.
- production active-owner Create carry authority patch: `652667e887720509f37618641e231f70e8e689c4`.
- production upward-jump lifecycle correction: `a14260cc76b61e5c6be0de38e634abe9ee7f0800`.
- active proof workflow: `m1-reference-owner-v2-natural-landing-proof-v2`.
- active proof run: `35052376394`, exact proof head `618da46f...`; in progress when this ledger was written.
- proof-only harness commit changes fixture/native-aiStep scheduling and verification only; production physics/gameplay source is unchanged relative to `a14260c...`.

## Historical direct-user runtime gate — authoritative regression evidence
Exact JAR SHA256 `96053e314891495fbb4bf16c446023568fed542497e083083dad7ed420dcd7ef` FAILED:
- floor hard/solid PASS and grounded walking PASS;
- walls soft FAIL;
- jump/airborne dragged player backward ~2–4 carriages FAIL;
- turns swept player/camera, wall could be penetrated, player could be thrown outside FAIL;
- behavior did not feel like a stable VS2 moving base FAIL.
This blocks `FINAL_READY` regardless of automated GREEN.

## Root architecture / implementation proofs
- `6e079d62...`, run `34963733838` SUCCESS: old implementation was contact/lease reanchor, not continuous VS2 reference space.
- `c364910f...`, run `34969572212` SUCCESS: pinned VS2 native owner requires registered ShipId; fake/proxy ship forbidden.
- `abb57fff...`, run `34972926851` SUCCESS: reference-owner redesign boundary mapped.
- `2eeac3f...`, run `34975161200` SUCCESS: core slice bounded to owner state/body drag/relative packet/server resolution/render/yaw; Create collision separate.
- `ebf4aaf...`, run `34977644889` SUCCESS: Create carriage Entity id + bilateral transforms available; pinned Create JAR SHA256 `d9c6cb6116d5caa1174a289ecd7d3cdd463ccef6e8db1249ab0bcfcd8c935870`.
- V1 run `34984299770` SUCCESS: generalized external owner state + Entity-id resolver + VS2 EntityDragger lifecycle.
- V2 run `34994353308` SUCCESS structurally; first real-train run `34997330399` later disproved body-continuity assumptions with ~93.48-block airborne drift.

## Scheduler / authority — FROZEN_GREEN
- External-owner EntityDragger lifecycle requirement: run `35008163064` SUCCESS.
- Runtime order run `35025200849` showed Create collision before VS2 drag in old order.
- Production scheduler `0ce0dfd4...` moves only external-owner LocalPlayer drag after `ClientLevel.tick` and before Create collision; native VS2 ship scheduling unchanged.
- Active-owner Create ordinal-1 carry authority `652667e...`; run `35017634522` SUCCESS `single_reference_body_writer_proven`.
- Create OBB/grounding/floor/walls/ceiling remain authoritative.

## Transform / camera / look — FROZEN_GREEN
- Same-point transform run `35023234306` SUCCESS: exact same-point mismatch `0`; do not change resolver prev/current/yaw/point semantics absent contrary evidence.
- Camera run `35033671863` SUCCESS: external owner spatial render wired, camera owner unwired.
- Look run `35034983734` SUCCESS: external-owner spatial follow with look uncoupled.
- Free look is desired; no camera counter-rotation/direct camera transform.

## OBB support-loss — FROZEN_GREEN
- Source runtime `35031106237`: owner/carriage 7 matched through support loss and Create callbacks continued.
- Semantics runs `35037369180`, `35037534677`, `35039049624`, `35040491258` established valid temporal-only solved response.
- verifier-only run `35041914462` SUCCESS: `ACTIVE_OWNER_CREATE_COLLISION_FRAME_CONTINUOUS_TEMPORAL_ONLY`.
- `surface=true + collisionResponse=ZERO + 0<temporal<1` is valid Create behavior. OBB is not the active blocker.

## Natural airborne root chain
### Original direct gameplay failure
Run `35042299917` reached a real vanilla jump and FAILED `owner-relative airborne drift too large: 21.599091`.
Artifact id `10425533703`, digest `sha256:9b3a9596b03e31625e7aeadc194b7e2faf21e2d6e9fef45a1329ddd370c07e39`.
- jump REQUESTED/AIRBORNE tick30, delta Y `+0.3331999936`.
- carriage7 owner-local continuity reasonable through tick33, catastrophic jump at tick34.
- selected Create candidate switched 7 -> 5 at seam.

### Native drag gate — FROZEN_GREEN
Run `35045444238`: `EXTERNAL_OWNER_NATIVE_GATE_NOT_REJECTING`; rejected=0, airborne_rejected=0, `should_drag=true result=true` through airborne ticks. Do not patch native gate.

### Exact VS2 body writer — FROZEN_GREEN
Verifier-only v2 run `35048234680` over source run `35046701119`:
`EXTERNAL_OWNER_BODY_WRITER_APPLIES_CALCULATED_STEP`, jump material pairs=3, missed=0, max writer residual=0.0.
Conclusion: existing boundingBox/setPos writer applies the calculated step exactly when reached. Do not add/replace a body writer.

### Lifecycle false clear — PROVEN + FIXED
Verifier-only run `35048427002` SUCCESS:
`EXTERNAL_OWNER_CLEARED_BY_GROUNDED_CONTACT_EXPIRY_ON_NATIVE_JUMP_TICK`.
Exact evidence from source run `35044312977`: jump tick23, owner7 age3 -> 4, deltaY `+0.33319999363422365`, vertical arc true while `onGround=true`, then next tick owner null.
Production commit `a14260c...` changes only grounded expiry policy:
- derives `nativeUpwardMotion = entity.deltaMovement.y > 1.0E-5`;
- grounded stale-contact expiry cannot clear owner while genuine upward native movement is active.
No movement vector, reanchor, writer, gravity, collision or camera authority was added.

### Post-fix natural run — materially improved but not accepted landing
Run `35049968486`, job `104647999042`, exact head `d74f32b...`, runtime/compile succeeded; verifier failed before valid landing acceptance.
Artifact id `10428701383`, digest `sha256:8d14cea93417daaf5ea0940a69bc9870f9e889609de097fb9a92c881a189bdfe`.
- owner5 acquired tick20; jump REQUESTED/AIRBORNE tick23.
- horizontal owner-relative continuity through early jump improved to about `0.783534` total drift and `0.205107` max one-tick step instead of the prior multi-carriage failure.
- generic fixture `LANDED` marker tick31 was false: Create physical support had not returned.
- owner5 descent reached a stable support-miss plateau around local Y `2.218572`, gap `~0.218572`, while X/Z remained inside.
- no natural-landing GREEN may be inferred from the generic `onGround` marker.

### Descent lifecycle — FROZEN_GREEN for this boundary
Read-only workflow commit `55d9033...`, run `35051781646` SUCCESS:
`EXTERNAL_OWNER_ACTIVE_THROUGH_DESCENT_SUPPORT_MISS_MAX_AGE_EXPIRES_AFTERWARD`.
- owner5 acquire tick20; pinned drag cap 25; predicted expiry tick45.
- EntityDragger writer continuous ticks21..44.
- support-miss plateau begins tick36 and owner remains actively dragged through tick44.
Conclusion: lifecycle does NOT cause the initial hover/support miss; do not extend lifecycle generically.

## Headless fixture false-landing boundary — PROVEN HARNESS ISSUE
Static composed-source workflow `m1-headless-native-airstep-boundary-proof`, run `35051955516` SUCCESS, mapped the exact fixture method `vs2$runNativeAiStepWhenHeadlessTickSkippedIt`.
Its old jump fallback was gated by `!vs2$jumpLandedLogged`, so a false generic `onGround` landing marker could disarm headless native `aiStep` before Create support actually returned.

Correlation verifier repaired at commit `3f31a629...`; run `35052085653` SUCCESS:
`HEADLESS_FALSE_LANDING_DISARMS_JUMP_FALLBACK_AT_STRAFE_END_BEFORE_REAL_SUPPORT`.
Exact source run `35049968486`:
- false landed marker tick31;
- fallback ticks continue 32..36 only because strafe window remains true;
- jump_window=false after false marker;
- fallback last tick36;
- LocalPlayer move last tick36;
- stable support-miss plateau starts tick36.
Conclusion: the post-tick36 stall in that CI run is a headless fixture scheduling artifact, not production physics evidence.

## Active real-support landing repro
Commit `618da46f8cffe9ed34a3502e4e4080bb0fc4f4b1` is one harness-only hypothesis:
- adds `scripts/prepare_vs2_26_2_natural_landing_harness_v2.py`;
- adds `.github/workflows/m1-reference-owner-v2-natural-landing-proof-v2.yml`;
- keeps existing native `aiStep` fallback alive for a bounded 40-tick jump arc despite a false generic landing marker;
- adds no direct `setPos`, `setDeltaMovement`, move, gravity, teleport or `setOnGround` mutation;
- landing verifier no longer trusts generic `onGround` marker; it requires genuine same-owner Phase131 `physical_support=true` reacquisition;
- preserves exact verified r0v3 world SHA `e78bfb854a0f3ad0bfb87ded836ef322335812d303e51223825f3741f7232556`.
Active run: `35052376394`.

## FROZEN_GREEN / protected
- bootstrap/Kotlin packaging `f3d1335...`;
- Create train + VS2 coexistence;
- Steam 'n' Rails + Copycats preservation;
- V1 infrastructure run `34984299770`;
- V2 structural/core run `34994353308` except disproved runtime body-continuity assumptions;
- external-owner lifecycle requirement run `35008163064`;
- active-owner ordinal-1 authority run `35017634522`;
- same-point transform run `35023234306`;
- camera/free-look runs `35033671863`, `35034983734`;
- OBB temporal-only support-loss run `35041914462`;
- native drag gate open run `35045444238`;
- exact existing VS2 body writer run `35048234680` over source run `35046701119`;
- owner lifecycle active through descent support miss run `35051781646`;
- historical user-proven floor solidity and grounded walking as protected behavioral criteria.

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
- unscoped/global collider suppression or suppression of Create collision-response writer;
- duplicate Create/VS2 gameplay/collision authority;
- fake/proxy VS2 ship;
- harness mutation used to manufacture physics GREEN;
- resolver prev/current/yaw/point semantic changes after run `35023234306` absent contrary evidence;
- treating temporal-only zero collisionResponse as failure;
- patching `isDraggable`/`vs$shouldDrag` after run `35045444238`;
- adding/replacing a body-position writer after run `35048234680`.

## next_safe_action
1. Inspect only active natural-landing-v2 run `35052376394` first.
2. If queued/in_progress: HOLD; stack no production or harness hypothesis.
3. If compile/workflow/harness mechanics fail before useful runtime evidence: repair only this proof harness.
4. If runtime reaches genuine same-owner Phase131 support reacquisition and verifier prints `natural_landing_real_support_green`: freeze natural landing criterion for automated M1 proof and advance to wall/ceiling solidity; do not claim FINAL_READY.
5. If runtime still has no genuine Create support reacquisition while bounded native aiStep continues: inspect the exact Create grounding/collision boundary from that new artifact before any gameplay patch. Do not extend lifecycle, alter transform math, or add movement writers.
6. Only after natural landing is GREEN advance to wall/ceiling, then turn/speed-change stability.
7. Any production patch must be one evidence-backed hypothesis and preserve every FROZEN_GREEN boundary.

## Finalization policy — HARD USER RUNTIME GATE
Automated proof can never alone set `FINAL_READY`. A new exact JAR must pass direct user runtime for stable standing, forward/back/strafe/sprint, jump+airborne+natural landing, floor/walls/ceiling, turns, acceleration/deceleration/speed changes, no sink/throw/drift/lag-behind, and free/stable camera/look. Watchdog local SHA gate must match that exact accepted JAR.

## Fresh-chat/watchdog protocol
1. Inspect actual HEAD.
2. Read this file completely and reconcile ledger basis with actual HEAD; ledger-only/diagnostic commits may advance HEAD without gameplay mutation.
3. Inspect only latest relevant Actions evidence for active blocker.
4. Respect FROZEN_GREEN and FAILED_HYPOTHESES.
5. Execute `next_safe_action`; do not stop at narration.
6. HOLD only for genuinely queued/in-progress relevant proof/evidence.
7. No failure evidence = no symptom gameplay patch.
8. One gameplay commit = one evidence-backed hypothesis.
9. Never `FINAL_READY` from CI alone.
