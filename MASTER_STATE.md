# MASTER_STATE — VS2 / Create Interactive

GitHub code is the implementation source of truth. This file is the durable project-state ledger. Chat is temporary.

## Project
- Repository: `apm23/VS2-Create_Interactive`
- Milestone: `M1 — movement / collision`
- HARD architecture: Create owns train/carriage gameplay and collision geometry. VS2 must be the actual continuous moving reference-space/transform foundation for player body/render/camera. Compatibility remains a thin adapter.
- Forbidden: fake gravity, synthetic carry velocity/inertia, manual floor/wall clamp, floor-only collision workaround, per-tick teleport/setPos chase/reanchor architecture, duplicate Create/VS2 gameplay/collision authority, direct camera forcing, fake/proxy VS2 ship, or workaround chains hiding double ownership.

## Current reconciled state — 2026-09-16
- project_state: `ROOT_REDESIGN — V2 ACTIVE-OWNER CONTACT-CARRY AUTHORITY PROVEN; REAL-TRAIN BODY CONTINUITY RETEST REQUIRED`
- ledger_basis_head: `07dbd852712c3c3d81b4d405e253befd4b34ac65`
- final_ready: `false`
- user_runtime_validation: `FAILED` for historical exact JAR SHA256 `96053e314891495fbb4bf16c446023568fed542497e083083dad7ed420dcd7ef`; no V2 authority-fixed user candidate has been built/tested yet.

### Architecture/root proofs
- architecture diagnostic commit `6e079d62d0d30e8508ad825ef80791088fa28e5c`, run `34963733838` SUCCESS: previous adapter was contact/lease reanchor, not continuous VS2 reference space.
- native owner seam commit `c364910f3c9419a5b37b41a3c59fa77124a10b02`, run `34969572212` SUCCESS: pinned VS2 native owner lifecycle requires registered `ShipId`; no native public non-Ship owner seam. Fake/proxy ship is forbidden.
- redesign map commit `abb57fff0d3635f09c9f85aa699df9f88d57abcf`, run `34972926851` SUCCESS.
- bounded core-slice commit `2eeac3f8222931a56e760f05ec62bbe2131e2c43`, run `34975161200` SUCCESS: standing-player M1 reference-owner path is bounded to owner state, body drag, LocalPlayer relative packet, server resolve, standing render interpolation, and yaw transform; Create collision mutation and ship-mounted camera mode are not required.
- Create bilateral seam commit `ebf4aaf73a0fb401cfeb77e9017f43af3b6f11c9`, run `34977644889` SUCCESS: Create `6.0.9-1`, resolved JAR SHA256 `d9c6cb6116d5caa1174a289ecd7d3cdd463ccef6e8db1249ab0bcfcd8c935870`, common carriage Entity id usable as owner key, previous world->local and current local->world transforms available.

### V1/V2 reference-owner implementation
- V1 initial `6ef53dabf799bb62e8b2d6a2d239b33917f751e4`; hardened `655fd1daa67f232a2add7b2d663786759031d02a`; composition fix `59e75959d8a38f94a637aa1a8120280c2bf2df0a`; trigger `4aeaf9f5ba66dedb6a7ac3b14fc81bab371be8f7`.
- V1 proof run `34984299770` SUCCESS: generalized non-Ship owner state + bilateral Entity-id resolver + native EntityDragger application lifecycle compile; acquisition intentionally disabled; old Phase83/205 reanchor mutually excluded when external owner active.
- V2 implementation `5f687aca0af43ca4783fb915c3aea1651da74dc1`; initial workflow `40b68fd3c71857f3ab125b9bd5211f4973897996`; composefix `ea546f83f3549736aa4ac0dfad23b82005a63cd0`; proof commit `a3f37d8e8c896dc05eca1e4b74759a25100a34bc`.
- V2 structural proof run `34994353308` SUCCESS: selected Create carriage acquires one external owner; bounded lifetime; dedicated `PacketPlayerReferenceMotion`; same-owner client/server/render/yaw resolution; old Phase83/205 reanchor authority removed; no fake ship; Fabric compile GREEN.

## Historical exact-JAR user runtime gate
The user directly tested SHA256 `96053e314891495fbb4bf16c446023568fed542497e083083dad7ed420dcd7ef` after historical final-build `34953958207` and final-verify `34955884046` had passed CI.
- floor hard/solid: PASS
- grounded walking: PASS
- walls soft: FAIL
- jump/airborne dragged player backward about 2–4 carriages: FAIL
- turns swept player/camera and could throw player outside: FAIL
- behavior did not feel like standing in a stable VS2 moving reference frame: FAIL
Direct user runtime overrides historical CI GREEN. Never ask the user to retest this SHA.

## V2 real-train failure that opened the authority investigation
- runtime gate commit `b1464506b6e0f3635c4d50ecb7615913a87d5ba9`, run `34997330399` FAILURE.
- real carriage/train PASS; external owner acquisition PASS; grounded walk PASS; vanilla jump requested->airborne->natural landing PASS; legacy Phase83/205 reanchor markers absent.
- body continuity failed catastrophically: about `93.48251` blocks total airborne carriage-local horizontal drift and about `51.82845` blocks max one-tick local step.
- artifact showed `ContraptionColliderClient.collideEntities:330` applying material horizontal `setPos` while the external VS2 owner was active.
- body diagnostic commit `b06466a1a7e2a17009a79bd131bdea6366a0619c`, run `35001323376` failed before runtime due an indentation-specific instrumentation anchor; no gameplay evidence from that failed diagnostic.

## Authority root evidence and fix — CURRENT GREEN BOUNDARY
The authority investigation established that Create's second `Entity.setPos` inside `ContraptionColliderClient.collideEntities` is the contact-point carry writer, while Create's first setPos remains collision-response/OBB authority.

- authority precursor evidence showed same-tick duplicate movement: VS2 external owner body delta plus Create ordinal-1 contact carry.
- sibling diagnostic run `35014460439` is **not gameplay evidence** because that fixture never acquired the external owner (`phase81PhysicalSupport=false`); do not infer absence/presence of sibling authority from that failed run.
- independent authority artifact proved a material sibling carriage callback can write contact carry on the same active-owner tick after the exact-owner callback was suppressed. This justified arbitration at the active external-owner boundary, not global Create suppression.
- authority fix commit: `652667e887720509f37618641e231f70e8e689c4` (`Scope Create contact carry to active VS2 reference owner`).
- authority proof workflow commit / reconciled HEAD: `07dbd852712c3c3d81b4d405e253befd4b34ac65` (`Prove active V2 owner has sole contact-carry authority`).
- authority proof run `35017634522`, job `104544985035`: **SUCCESS**.
- compile: `BUILD SUCCESSFUL`.
- runtime proof result:
  - body ticks: `[18,19,20,21,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41]`
  - exact-owner suppression count: `18`
  - sibling suppression count: `3`
  - observed sibling pairs: `[(8,10),(10,8)]`
  - `material_line330_overlap=[]`
  - `collision_response_writer_untouched=true`
  - conclusion: `single_reference_body_writer_proven`
- implementation scope is deliberately narrow: LocalPlayer only, only while a valid external VS2 reference owner is active, only Create `collideEntities` ordinal-1 contact-point carry translation is suppressed. Create's collision-response writer, OBB, floor/wall/ceiling geometry, grounding, and damage paths remain untouched. No synthetic motion is added.

This authority boundary is now FROZEN_GREEN unless later direct runtime evidence contradicts it. Do not broaden or retune it without new evidence.

## FROZEN_GREEN / protected
- Kotlin/bootstrap packaging repair `f3d1335c9fc89283d936af039eba34aa9778bd05`.
- Create train + VS2 coexistence.
- Steam 'n' Rails and Copycats preservation.
- V1 infrastructure proof `34984299770`.
- V2 structural/core proof `34994353308` except its old body-continuity assumption, which runtime `34997330399` disproved before authority arbitration.
- active-owner contact-carry authority boundary from `652667e...` / `35017634522`.
- historical user-proven grounded floor solidity and grounded walking remain behavioral criteria, not proof of current V2 completion.

## FAILED_HYPOTHESES / anti-loop
Do not reintroduce without new direct evidence:
- `EXACT_SHAPES_LOCALPLAYER_0fa4aa`;
- generic frame lease/replay/carry extension;
- synthetic carry velocity / inertia compensation;
- fake gravity;
- manual floor/wall clamps or floor-only collision workaround;
- per-tick teleport/setPos chase/reanchor as architecture;
- direct camera forcing/rotation compensation;
- jump/input timing tuning without input-specific evidence;
- sprint/reverse/strafe tuning as a reference-frame fix;
- unscoped/global collider suppression, ownerless sibling suppression, or suppression of Create's collision-response writer;
- duplicate Create/VS2 gameplay or collision authority;
- fake/proxy VS2 ship solely to obtain native lifecycle;
- harness mutation used to manufacture GREEN.

Clarification: the proven `652667e...` arbitration is **not** the forbidden broad/global suppression above. It is active-reference-owner scoped, LocalPlayer-only, and ordinal-1 contact-carry-only while Create collision response remains authoritative.

## next_safe_action
Rerun the exact real-train V2 body-continuity gate with the **current** composition:
1. base + Phase98 + Phase205 + V1 + V2 composefix;
2. `prepare_vs2_26_2_reference_owner_v2_schedule_fix.py`;
3. `prepare_vs2_26_2_reference_owner_v2_authority_fix.py`;
4. verified `r0v3` real moving-train fixture;
5. fix only the known WALK verifier ERE so it can recognize the already-emitted `confirmed=true` marker.

The retest must require real carriage + moving train + external owner acquisition + grounded walk + vanilla jump/airborne/natural landing, historical Phase83/205 reanchor absence, and carriage-local airborne continuity thresholds (`max_horizontal_drift <= 1.5`, `max_one_tick_step <= 0.75`). It must not change gameplay physics merely to satisfy the verifier.

If this retest fails, inspect exact runtime evidence and patch only the proven remaining boundary. If it passes, body continuity may be frozen GREEN, but M1 is still not FINAL_READY: wall/ceiling/turns/speed changes/free camera and an exact new JAR still require downstream proof and direct user runtime validation.

## Finalization policy — HARD USER RUNTIME GATE
CI/automated proof can produce candidates but can never alone restore `FINAL_READY`. `FINAL_READY` requires a new exact final JAR that passes real-user runtime for standing, forward/backward/strafe/sprint, jump+airborne+natural landing, floor/walls/ceiling, turns, acceleration/deceleration/speed changes, no sink/throw/drift/lag-behind, and free/stable camera/look, plus watchdog local runtime-gate SHA match.

## Fresh-chat/watchdog protocol
1. Inspect actual HEAD.
2. Read this file completely and reconcile `ledger_basis_head` with actual HEAD; ledger-only commits may advance HEAD without gameplay change.
3. Inspect only latest relevant Actions evidence for the active blocker.
4. Respect FROZEN_GREEN and FAILED_HYPOTHESES.
5. Execute `next_safe_action`; do not stop at narration.
6. HOLD only for genuinely queued/in-progress relevant workflow/evidence.
7. No failure evidence = no symptom gameplay patch.
8. One commit = one hypothesis.
9. Never `FINAL_READY` from CI alone.
