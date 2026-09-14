# MASTER_STATE — VS2 / Create Interactive

GitHub code is the implementation source of truth. This file is the durable project-state source of truth. Chat is temporary.

## Project
- Repository: `apm23/VS2-Create_Interactive`
- Milestone: `M1 — movement / collision`
- Goal: a moving Create train should feel like a stationary house that is actually moving.
- Architecture: Create owns train/carriage gameplay and collision geometry; VS2 supplies moving reference-space/transform foundation; this project is a thin adapter.

## Current state
- project_state: `ACTIVE_BLOCKER — native Create LocalPlayer vertical collision-response consumption boundary`
- current_head: `AUTO_RECONCILE_GIT_HEAD` (state-only `[skip ci]` ledger commits may advance Git HEAD; compare implementation files before treating that as gameplay change)
- implementation_head: `057d1b117960620f473eef1573821986f176ae76` (read-only diagnostic delta over the validated native-owner candidate)
- candidate_gameplay_commit: `881f1a737c92efdd39b7e5fcda13efb6908b475f`
- last_good_implementation_commit: `e58adf3e9ac2baa24ea476bfeaaaf707cf35dd4e` (exact-shape regression removed; not M1 complete)
- active_blocker: `#724 proves Create detects an upward floor contact after LocalPlayer has moved downward, but the native Create response-consumption path applies no vertical position correction before support is lost; the exact internal zero-response branch is now being traced read-only`
- active_hypothesis: `the remaining sink begins inside the native Create LocalPlayer collision-response consumption path: ContinuousOBBCollider reports surface contact/upward normal while collisionResponse is zero, so the first ContraptionCollider.collide(totalResponse, entity) may authorize zero displacement and the later contact-point carry moves only horizontally`
- next_safe_action: `wait for the automatically-triggered proofs for diagnostic head 057d1b. Do not mutate gameplay while any relevant run is queued/in_progress. Once compile is green, inspect production-world logs for GATE_E_CREATE_LOCALPLAYER_ZERO_COLLIDE_RESULT adjacent to Phase65 collideMany and Phase76 setPos. If the zero-response path is proven, choose the smallest native Create collision-consumption fix; do not add clamps, leases, replay, synthetic carry, or jump/input changes.`

## Architecture contract
Forbidden unless new direct evidence proves unavoidable:
- fake gravity
- synthetic carry velocity
- inertia compensation
- manual wall clamp
- floor-only collision
- per-tick teleport/setPos carry workaround
- duplicate authority / duplicate world state
- workaround chains hiding Create+VS2 double ownership

Preferred order:
1. native Create/Minecraft collision mechanism
2. reuse existing authoritative VS2/Create transform
3. simplify/remove duplicate ownership
4. thin adapter
5. new workaround only with direct evidence and explicit justification

## Frozen / protected green
Do not modify without direct regression evidence:
- boot/no-crash baseline
- Create train + VS2 baseline coexistence
- Steam 'n' Rails and Copycats preservation
- standing carry continuity
- forward/sprint input and supported walking proof
- native backward input/motion proof
- native right-strafe input/motion dispatch proof
- Phase83 stale-baseline sibling-owner arbitration at the exact #722 competing-owner seam: #724 hands Create native ownership to carriage `5` without the former unsupported Phase83 reanchor from stale carriage `4`

Important: movement input dispatch is green. Missing jump proof is downstream of support loss and is not permission to change jump/input timing.

## Latest durable evidence
### exact-shape experiment `0fa4aa246021c6b7168b7212406d4f61fac59add`
- forced LocalPlayer to exact per-block shapes
- production-world #720 regressed protected locomotion/reference continuity
- locked failed and reverted; DO NOT REINTRODUCE without genuinely new evidence

### revert `e58adf3e9ac2baa24ea476bfeaaaf707cf35dd4e`
- removed exact-shape redirect
- restored protected movement baseline

### production-world #721 / run `34769096716`
- standing carry, supported forward/sprint, native backward, and native right-strafe dispatch returned
- support/frame loss remained before jump proof

### production-world #722 / run `34788419359`
- read-only ownership proof isolated duplicate ownership
- Create handed native LocalPlayer ownership to sibling carriage `5`
- stale exact-baseline carriage `7` could still perform Phase83 `EntityDragger#reanchorEntityWithExternalFrame` afterward with physical support false
- this justified owner-identity arbitration instead of another lease/replay workaround

### native-owner candidate `6a4d960e65d79a6f4a4c5973a83b2e6debd5aa2e`
- Phase83 grounded exact-baseline lease must still match Phase170's most recent Create-native owner
- no collision/input/gravity/velocity/train/world mutation

### production-world #723 / run `34789741282`
- invalid as runtime evidence: generated Java failed compilation because `phase83ActiveNativeOwner` was referenced before declaration
- classification was `prepare/composition`

### composition recovery `881f1a737c92efdd39b7e5fcda13efb6908b475f`
- moved the existing native-owner local declaration to first use; gameplay predicate unchanged
- `port-build #891` completed SUCCESS, closing the prepare/composition blocker
- `production-carry-smoke #693` completed SUCCESS
- `production-world-smoke #724` reached real runtime and completed FAILURE at the later jump gate

### production-world #724 / run `34790108716`
Frozen/protected locomotion remains available:
- supported forward/sprint confirmed at LocalPlayer tick `19`
- native backward requested/confirmed at tick `23`
- native right-strafe dispatch still reached later

Native-owner arbitration result:
- Create establishes sibling carriage `5` as native owner at tick `34`
- the former #722 stale-baseline Phase83 reanchor after that handoff does not recur
- therefore the exact duplicate-owner seam targeted by `881f1a` is considered proven fixed/frozen; do not widen or retune it merely because M1 still fails

Deeper collision boundary exposed on carriage `4` before the sibling handoff:
- tick `20`: strict physical support is true; local floor top is `2.0`
- tick `21`: inherited vanilla `Entity.move` requests about `Y=-0.03632`; actual move also consumes about `-0.03632 Y` because the moving Create floor is not vanilla world collision geometry
- immediately afterward Create `ContinuousOBBCollider.collideMany` reports `surface=true`, upward collision normal about `+0.062 Y`, and `response=(0,0,0)`
- Create's first observed `setPos` at the collision response site is a no-op in position
- Phase170 then applies native carriage-4 contact motion; the observed Create collision allowance/contact carry is horizontal only
- Create's later `setPos` moves X only, leaving Y at the sunk value
- Phase131 then changes to `physical_support=false` while the player remains inside X/Z floor footprint
- tick `22` support deteriorates further; the legacy Phase83 age-1 same-owner lease reanchor is downstream of the already-lost floor support and is not the root fix
- shell eventually reports missing native jump/landing, but jump never had a healthy support boundary to start from

Direct classification from #724: `collision — native Create LocalPlayer vertical response consumption`, not input, jump verifier, fixture, or prepare/composition.

### read-only collision-consumption diagnostic `057d1b117960620f473eef1573821986f176ae76`
- changes only `scripts/prepare_vs2_26_2_phase75.py`
- retains existing horizontal requested-vs-allowed `ContraptionCollider.collide` trace
- adds `GATE_E_CREATE_LOCALPLAYER_ZERO_COLLIDE_RESULT` for zero-vector LocalPlayer collide requests, including player tick, returned allowance, current delta movement, position, onGround, and thread
- purpose: correlate Phase65 `ContinuousOBBCollider.collideMany` surface/up-normal/zero-response result with the first Create `ContraptionCollider.collide(totalResponse, entity)` consumption call and Phase76 `setPos`, before the later horizontal contact-point carry
- strictly read-only: no position, velocity, onGround, collision, input, gravity, train/world, lease, replay, or reference-frame mutation
- push automatically triggered the normal proof set; no duplicate manual workflow trigger is allowed while those runs are active

## Failed hypotheses — DO NOT REPEAT WITHOUT NEW EVIDENCE
- `EXACT_SHAPES_LOCALPLAYER_0fa4aa`
- generic accumulation/extension of frame leases, replay, or carry corrections
- synthetic carry velocity / fake inertia compensation
- manual floor/wall clamps
- harness mutation that manufactures success
- treating missing jump marker as a jump-input bug
- treating right-strafe timing as cause of support loss
- broad sibling/global suppression instead of direct native-owner identity

## Root-cause classification
Current: `collision`.

Prepare/composition is closed by successful `port-build #891`. The #722 reference-frame double-owner seam is closed at its exact target by #724. The first still-broken boundary is now the native Create LocalPlayer vertical collision-response consumption path after `ContinuousOBBCollider` reports a floor surface/upward normal but zero collision response.

## Anti-loop lock
- Do not change sprint/reverse/strafe input windows.
- Do not patch jump admission/acceptance.
- Do not extend native contact leases.
- Do not add replay/recovery branches.
- Do not re-enable exact-shape LocalPlayer redirect.
- Do not add synthetic carry, velocity, fake gravity, or manual floor/wall clamps.
- Do not retune the now-proven Phase83 native-owner predicate unless a direct regression reproduces that exact stale-owner seam.
- First prove how Create consumes the zero collision response; then patch only that native collision boundary if evidence warrants it.
- If a future collision patch regresses any frozen-green subsystem, REVERT before adding compensation.

## M1 acceptance — all required in one real moving-train proof
- [ ] stable standing
- [ ] forward/backward/strafe
- [ ] sprint
- [ ] jump + airborne + natural landing
- [ ] solid floor/walls/ceiling
- [ ] no sink/throw/drift/lag-behind
- [ ] stable through movement/turn/speed changes as fixture permits

No box may be checked from separate runs; M1 requires one complete proof.

## Final artifact state
- m1_complete: `false`
- final_build_started: `false`
- final_commit: `NONE`
- final_jar: `NONE`
- final_verification: `NOT_STARTED`
- final_ready: `false`

## Fresh-chat protocol
1. Read this file completely.
2. Inspect actual GitHub HEAD.
3. If `current_head=AUTO_RECONCILE_GIT_HEAD`, compare commits since `implementation_head`; state-only `[skip ci]` ledger commits are not gameplay changes.
4. Inspect only latest relevant Actions needed for the active blocker.
5. Respect Frozen Green, Failed Hypotheses, and Anti-loop locks.
6. Continue only from `next_safe_action`.
7. If relevant run is queued/in_progress, HOLD; do not create a duplicate run.
8. FINAL_READY is terminal and only the user may reopen development after it.
