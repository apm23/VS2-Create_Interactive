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
- project_state: `ROOT_REDESIGN — NATIVE DRAG GATE AND VS2 BODY WRITER ARE GREEN; ACTIVE BLOCKER IS EXTERNAL-OWNER LIFECYCLE CLEAR / ARTICULATED CARRIAGE HANDOFF DURING NATIVE JUMP`.
- ledger_basis_head: `cbda22c1b7caa63f32fec6a21dafb920467f35da` (`Dispatch lifecycle expiry proof`).
- final_ready: `false`.
- exact historical failed user JAR SHA256: `96053e314891495fbb4bf16c446023568fed542497e083083dad7ed420dcd7ef`; never ask user to retest it.
- production scheduler patch: `0ce0dfd4f6f29685eb18b6e3a8c14ddc247bbb9b`.
- production active-owner Create carry authority patch: `652667e887720509f37618641e231f70e8e689c4`.
- current diagnostic: verifier-only `m1-reference-owner-v2-lifecycle-expiry-proof`, created at `67090464871845e8a25e14a1a38267ac6a4c03ca`; dispatcher `35048420489` was queued/in_progress when this ledger was written.
- diagnostic reuses exact runtime artifact from run `35044312977`; production gameplay/physics is unchanged.

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

## Natural airborne proof — DIRECT GAMEPLAY FAILURE
Run `35042299917` reached a real vanilla jump and FAILED `owner-relative airborne drift too large: 21.599091`.
Artifact id `10425533703`, digest `sha256:9b3a9596b03e31625e7aeadc194b7e2faf21e2d6e9fef45a1329ddd370c07e39`.
- jump REQUESTED/AIRBORNE tick30 with vertical delta `+0.3331999936`.
- carriage7 owner-local continuity is reasonable through tick33 then catastrophically jumps at tick34 from local X `-1.282011` to `23.707201`.
- selected Create candidate switches 7 -> 5 at the seam while the reference-owner lifecycle is under investigation.
- apparent LANDED tick37 is not accepted carriage landing because support/broadphase was already lost.
This authorizes root-boundary diagnosis, not OBB/gravity/camera/input tuning.

## Native drag gate — FROZEN_GREEN
Run `35045444238` workflow conclusion was failure only because verifier expected gate rejection. Useful runtime classification:
`EXTERNAL_OWNER_NATIVE_GATE_NOT_REJECTING` with `rejected=0`, `airborne_rejected=0`; rows show `shipyard=false provider=true should_drag=true result=true` across grounded and airborne ticks.
Do not patch `isDraggable` / `vs$shouldDrag`.

## Exact VS2 body writer — FROZEN_GREEN
Proof runtime run `35046701119` produced 15 PRE/POST writer pairs but its original verifier falsely required `on_ground=false`, while native jump markers already showed a real vertical arc with `on_ground=true`.
Verifier-only v2 run `35048234680` SUCCESS reclassified the exact same runtime artifact:
`REFERENCE_OWNER_V2_DRAG_APPLY_RECHECK classification=EXTERNAL_OWNER_BODY_WRITER_APPLIES_CALCULATED_STEP source_run=35046701119 request_tick=22 airborne_tick=22 landing_marker_tick=24 vertical_delta=0.33319999363422365 jump_material_pairs=3 missed_jump_material=0 max_jump_movement=3.6026309728622437 max_writer_residual=0.0 verifier_only=true production_unchanged=true final_ready=false`.
Pairs ticks22–24 all have residual exactly `0.0`.
Conclusion: when external-owner movement reaches the existing VS2 apply guard, boundingBox/setPos applies the calculated step exactly. Do not patch/add another body writer.

## Active lifecycle question
Current V2 lifetime source does, before the drag branch on non-preTick calls:
- increment `ticksSinceExternalReferenceOwner`;
- compute `groundedContactExpired = entity.onGround() && ticksSinceExternalReferenceOwner > 2`;
- call `clearExternalReferenceOwner()` if resolver fails, groundedContactExpired, or native max lifetime expires.
Acquisition/refresh requires selected exact Create carriage + physical support + `player.onGround()` + recent native Create contact.

Exact older read-only boundary artifact run `35044312977` gives the relevant seam:
- genuine native jump at player tick23 with `delta_y=+0.33319999363422365`, `vertical_arc=true`, while the marker still reports `on_ground=true`;
- scheduler entry tick23 still has owner7 active with owner_age=3 and expected owner-frame step ~`+5.088284254` X;
- owner is null/inactive on the next tick;
- selected Create candidate is already sibling carriage5 around the jump seam.
This strongly suggests the grounded-contact expiry policy can falsely clear the owner on the first native jump tick because Minecraft has not yet flipped `onGround` even though upward motion is real. The active verifier-only proof must confirm this exact code-path implication before any production patch.

## FROZEN_GREEN / protected
- bootstrap/Kotlin packaging `f3d1335...`;
- Create train + VS2 coexistence;
- Steam 'n' Rails + Copycats preservation;
- V1 infrastructure run `34984299770`;
- V2 structural/core run `34994353308` except disproved body-continuity assumptions;
- external-owner lifecycle requirement run `35008163064`;
- active-owner ordinal-1 authority run `35017634522`;
- same-point transform run `35023234306`;
- camera/free-look runs `35033671863`, `35034983734`;
- OBB temporal-only support-loss run `35041914462`;
- native drag gate open run `35045444238`;
- exact existing VS2 body writer application run `35048234680` over source run `35046701119`;
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
- fake/proxy VS2 ship;
- harness mutation used to manufacture GREEN;
- resolver prev/current/yaw/point semantic changes after run `35023234306` absent contrary evidence;
- treating temporal-only zero collisionResponse as failure;
- patching `isDraggable`/`vs$shouldDrag` after run `35045444238`;
- adding/replacing a body-position writer after run `35048234680` proved the existing writer exact when reached.

## next_safe_action
1. Inspect dispatcher `35048420489`, then the dispatched `m1-reference-owner-v2-lifecycle-expiry-proof` run.
2. If queued/in_progress: HOLD; no gameplay patch.
3. If proof resolves `EXTERNAL_OWNER_CLEARED_BY_GROUNDED_CONTACT_EXPIRY_ON_NATIVE_JUMP_TICK`, one production hypothesis is authorized: make grounded expiry distinguish a genuine upward native jump from grounded support staleness without synthetic velocity/reanchor/extra authority, then rerun the smallest natural-jump continuity proof.
4. If unresolved, instrument the exact lifecycle clear reason at runtime; do not patch transform math or writer.
5. Only after natural airborne landing continuity is GREEN advance to wall/ceiling solidity, then turn/speed-change stability.
6. Any production patch must preserve every FROZEN_GREEN boundary above.

## Finalization policy — HARD USER RUNTIME GATE
Automated proof can never alone set `FINAL_READY`. A new exact JAR must pass direct user runtime for stable standing, forward/back/strafe/sprint, jump+airborne+natural landing, floor/walls/ceiling, turns, acceleration/deceleration/speed changes, no sink/throw/drift/lag-behind, and free/stable camera/look. Watchdog local SHA gate must match that exact accepted JAR.

## Fresh-chat/watchdog protocol
1. Inspect actual HEAD.
2. Read this file completely and reconcile ledger basis with actual HEAD; ledger-only/diagnostic commits may advance HEAD without gameplay mutation.
3. Inspect only latest relevant Actions evidence for active blocker.
4. Respect FROZEN_GREEN and FAILED_HYPOTHESES.
5. Execute next_safe_action; do not stop at narration.
6. HOLD only for genuinely queued/in-progress relevant proof/evidence.
7. No failure evidence = no symptom gameplay patch.
8. One gameplay commit = one evidence-backed hypothesis.
9. Never `FINAL_READY` from CI alone.
