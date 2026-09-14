# MASTER_STATE — VS2 / Create Interactive

GitHub code is the implementation source of truth. This file is the durable project-state source of truth. Chat is temporary.

## Project
- Repository: `apm23/VS2-Create_Interactive`
- Milestone: `M1 — movement / collision`
- Goal: a moving Create train should feel like a stationary house that is actually moving.
- Architecture: Create owns train/carriage gameplay and collision geometry; VS2 supplies moving reference-space/transform foundation; this project is a thin adapter.

## Current state
- project_state: `ACTIVE_BLOCKER — collision: native Create LocalPlayer vertical response-consumption seam`
- current_head: `AUTO_RECONCILE_GIT_HEAD` (state-only `[skip ci]` ledger commits may advance Git HEAD; compare implementation files before treating that as gameplay change)
- implementation_head: `4479e094848b5ce75b0d3f4dc7aed55c9ac9ef47` (read-only OBB/LocalPlayer correlation diagnostic)
- previous_diagnostic_head: `057d1b117960620f473eef1573821986f176ae76`
- candidate_gameplay_commit: `881f1a737c92efdd39b7e5fcda13efb6908b475f`
- last_good_implementation_commit: `e58adf3e9ac2baa24ea476bfeaaaf707cf35dd4e` (exact-shape regression removed; not M1 complete)
- active_blocker: `#725 proves the first Create collision-consumption call receives totalResponse=(0,0,0) and returns allowed=(0,0,0) after vanilla LocalPlayer movement has already consumed downward Y. The later native contact-point carry applies X/Z only, so the already-consumed vertical sink is not repaired.`
- active_hypothesis: `the remaining sink is inside native Create LocalPlayer collision-response consumption. The next proof must correlate the same LocalPlayer tick with ContinuousOBBCollider surface/temporal/normal/zero-response output so a correction can be derived from Create-native collision data rather than a manual floor clamp.`
- next_safe_action: `Do not mutate gameplay while the proof set for 4479e094 is queued/in_progress. When production-world-smoke #726 completes, inspect the extended GATE_E_CREATE_COLLIDE_MANY_RESULT records immediately adjacent to GATE_E_CREATE_LOCALPLAYER_ZERO_COLLIDE_RESULT. If the same-tick OBB result proves surface/temporal/up-normal/zero-response, design the smallest native Create collision-consumption fix. Do not add clamps, leases, replay, synthetic carry, fake gravity, or jump/input changes.`

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
- `port-build #891` SUCCESS, closing prepare/composition blocker
- `production-carry-smoke #693` SUCCESS
- `production-world-smoke #724` reached runtime and failed later at jump gate

### production-world #724 / run `34790108716`
Frozen locomotion remained available:
- supported forward/sprint confirmed
- native backward confirmed
- native right-strafe dispatch reached

Native-owner arbitration result:
- Create establishes sibling carriage `5` as native owner
- the former #722 stale-baseline Phase83 reanchor after handoff does not recur
- exact duplicate-owner seam targeted by `881f1a` is proven fixed/frozen

Deeper collision boundary exposed:
- strict physical support is initially true, floor top local Y `2.0`
- vanilla `Entity.move` consumes downward Y because moving Create floor is not vanilla world collision geometry
- Create `ContinuousOBBCollider.collideMany` reports surface contact/upward normal while `collisionResponse=(0,0,0)`
- first observed Create response-site `setPos` is a no-op
- later Create contact carry is horizontal only
- physical support is then lost while X/Z remain over the train floor
- missing jump is downstream, not an input/verifier bug

Direct classification from #724: `collision — native Create LocalPlayer vertical response consumption`.

### read-only collision-consumption diagnostic `057d1b117960620f473eef1573821986f176ae76`
- changed only `scripts/prepare_vs2_26_2_phase75.py`
- added `GATE_E_CREATE_LOCALPLAYER_ZERO_COLLIDE_RESULT` for zero-vector LocalPlayer `ContraptionCollider.collide` requests
- no position, velocity, onGround, collision, input, gravity, train/world, lease, replay, or reference-frame mutation
- `port-build #892`, `client-smoke #809`, `production-carry-smoke #694`, and `runtime-smoke #851` completed SUCCESS
- `world-smoke #812` and `production-world-smoke #725` completed FAILURE at later acceptance/runtime gates, giving real diagnostic evidence rather than compile failure

### production-world #725 / run `34791239228`
The zero-response path is directly proven:
- LocalPlayer tick `21`: vanilla `Entity.move` consumes downward Y before Create collision handling
- immediately afterward `GATE_E_CREATE_LOCALPLAYER_ZERO_COLLIDE_RESULT` logs `requested=0,0,0`, `allowed=0,0,0`; the first Create response-site `setPos` therefore performs no vertical correction
- Phase170 then identifies native carriage owner and Create contact motion is horizontal
- the later Create contact-point `setPos` changes X/Z but leaves Y unchanged
- support is still only barely within tolerance at tick 21, then progressively sinks below the local floor on following ticks
- this closes the question whether the zero `totalResponse` consumption call itself contributes vertical correction: it does not

### OBB/LocalPlayer correlation diagnostic `4479e094848b5ce75b0d3f4dc7aed55c9ac9ef47`
- changes only `scripts/prepare_vs2_26_2_phase65.py`
- extends the read-only `ContinuousOBBCollider.collideMany` trace window from 64 to 128 calls because #725 reached the LocalPlayer zero-response seam just after the old cap
- adds current LocalPlayer tick, position, delta movement, and onGround state to each OBB result log
- does not mutate collision, movement, position, velocity, train/world, input, leases, or reference frames
- purpose: correlate the OBB surface/temporal/normal/zero-response result with the exact same LocalPlayer tick as the zero `ContraptionCollider.collide` call, so the next gameplay patch can use native Create collision information rather than inventing a floor clamp
- push automatically triggered the normal proof set; as of this ledger update the relevant runs, including `production-world-smoke #726` / run `34793031275`, are in progress. Do not duplicate-trigger while active.

## Native Create-Fly source finding locked for next design step
Pinned Create Fly runtime is `26.2-rc-2-6.0.9-1`.
In native `ContraptionColliderClient.collideEntities`:
- `hardCollision` is false when `totalResponse == Vec3.ZERO`
- `surfaceCollision` may still be true
- Create then calls `ContraptionCollider.collide(totalResponse, entity)` and applies the returned vector to XYZ
- for zero `totalResponse`, #725 proves this returns zero and does not repair already-consumed Y
- inside the later `surfaceCollision` contact carry, Create computes `contactPointMotion`, calls `ContraptionCollider.collide(contactPointMotion, entity)`, then applies only X and Z while explicitly retaining the existing Y
- temporal collision handling adjusts delta movement, not the already-consumed current position

This is source evidence for the collision-consumption seam, not permission for a manual floor-height correction. The next patch must stay native-data-driven.

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

Prepare/composition is closed. The exact #722 reference-frame double-owner seam is closed and frozen by #724. The first still-broken boundary is native Create LocalPlayer vertical collision-response consumption after moving-floor contact is detected.

## Anti-loop lock
- Do not change sprint/reverse/strafe input windows.
- Do not patch jump admission/acceptance.
- Do not extend native contact leases.
- Do not add replay/recovery branches.
- Do not re-enable exact-shape LocalPlayer redirect.
- Do not add synthetic carry, velocity, fake gravity, or manual floor/wall clamps.
- Do not retune the proven Phase83 native-owner predicate unless direct regression reproduces that exact seam.
- First correlate same-tick OBB result to zero-response consumption; then patch only that native collision boundary if evidence warrants it.
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
