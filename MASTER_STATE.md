# MASTER_STATE — VS2 / Create Interactive

GitHub code is the implementation source of truth. This file is the durable project-state source of truth. Chat is temporary.

## Project
- Repository: `apm23/VS2-Create_Interactive`
- Milestone: `M1 — movement / collision`
- Goal: a moving Create train should feel like a stationary house that is actually moving.
- Architecture: Create owns train/carriage gameplay and collision geometry; VS2 supplies moving reference-space/transform foundation; this project is a thin adapter.

## Current state
- project_state: `ACTIVE_BLOCKER — fixture/harness: live jump floor-support publisher remains false after grounded collision repair`
- current_head: `AUTO_RECONCILE_GIT_HEAD` (state-only `[skip ci]` ledger commits may advance Git HEAD; compare implementation files before treating that as gameplay change)
- implementation_head: `aea87423ff9e1cd7943944822dbe6cbc21d327d5`
- previous_diagnostic_head: `a95cdf360313e84a4c154c2c0b4c7484bdfe4cdd`
- candidate_gameplay_commit: `aea87423ff9e1cd7943944822dbe6cbc21d327d5`
- last_good_implementation_commit: `e58adf3e9ac2baa24ea476bfeaaaf707cf35dd4e` (exact-shape regression removed; not M1 complete)
- active_blocker: `#727 and #728 show the grounded-negative-Y repair preserving sustained standing/carry and supported sprint/walk instead of the former progressive sink. #728 additionally proves native backward and native right-strafe are confirmed before jump, but the final jump admission remains false because vs2.productionFixtureJumpFloorSupportNow stays false even while the observed LocalPlayer repeatedly returns onGround=true. This is now a fixture/harness predicate-observability blocker, not evidence authorizing another gameplay collision or jump patch.`
- active_hypothesis: `the live jump floor-support publisher has an internal predicate mismatch among continuity cadence, same-carriage identity, local settled-step, broadphase, grounding, or carryBaselineCarriageId equality. Diagnostic a95cdf logs those exact read-only predicate components without changing input, jump admission, movement, collision, carry, gravity, train, or world state.`
- next_safe_action: `production-world-smoke #729 / run 34797427793 is in progress for diagnostic a95cdf. Do not duplicate-trigger and do not change jump admission/input timing. When #729 completes, inspect GATE_E_M1_JUMP_FLOOR_TRACE first and identify the first false component. If the mismatch is verifier/fixture bookkeeping, repair only that bookkeeping and rerun the smallest production-world proof. If runtime physical support itself regresses, return classification to collision and REVERT/repair only with direct evidence.`

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
- Create grounded-negative-Y consistency repair at `aea874`: #727/#728 retain grounded standing/carry and supported locomotion instead of the former progressive negative local-floor gap; do not broaden or replace it without direct regression evidence

Important: movement input dispatch is green. Missing jump proof is not permission to change jump/input timing or acceptance.

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
- Create `ContinuousOBBCollider.collideMany` can report surface/temporal contact while `collisionResponse=(0,0,0)`
- first observed Create response-site `setPos` is a no-op for zero response
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
- vanilla movement can consume downward Y before Create collision handling
- `GATE_E_CREATE_LOCALPLAYER_ZERO_COLLIDE_RESULT` logs `requested=0,0,0`, `allowed=0,0,0`; the first Create response-site `setPos` therefore performs no vertical correction
- Phase170 then identifies native carriage owner and later Create contact motion is horizontal
- this closed the question whether the zero `totalResponse` consumption call itself contributes vertical correction: it does not

### OBB/LocalPlayer correlation diagnostic `4479e094848b5ce75b0d3f4dc7aed55c9ac9ef47`
- changed only `scripts/prepare_vs2_26_2_phase65.py`
- extended the read-only `ContinuousOBBCollider.collideMany` trace window to 128 calls
- added current LocalPlayer tick, position, delta movement, and onGround state to each OBB result
- no gameplay mutation
- `port-build #893`, `client-smoke #810`, `production-carry-smoke #695`, and `runtime-smoke #852` completed SUCCESS
- `production-world-smoke #726` / run `34793031275` completed FAILURE and produced the decisive grounding/motion correlation below

### production-world #726 / run `34793031275`
The correlation changes the root hypothesis from an unproven floor-response guess to a concrete native state mismatch:
- while still healthy, repeated Create OBB results can be `surface=true`, temporal `<1`, zero discrete response, and Create keeps the LocalPlayer grounded
- tick `24` remains physically supported at local floor top `2.0` with local vertical gap about `+0.0001001`
- the same tick's temporal Create handling leaves final LocalPlayer Y delta about `-0.0529708647` while `onGround=true`
- on tick `25`, LocalPlayer world Y has dropped by exactly that retained downward amount, and local physical support becomes false with vertical gap about `-0.0528707647`
- later ticks retain the same pattern: Create surface/contact handling may keep `onGround=true` while a negative Y delta survives to the next vanilla movement, producing progressively deeper gaps (`-0.1569`, `-0.3019`, `-0.4747`, then no valid floor-top support)
- the exact sink transition does not require a stale Phase83 owner and occurs after the #722 duplicate-owner seam is already fixed
- some OBB temporal contacts at the transition are horizontal/side normals rather than an upward floor normal; therefore a floor-normal-only position correction would be the wrong patch

Direct classification from #726 remains `collision`, specifically `Create grounded state versus final vertical motion consistency`.

### grounded-motion candidate `aea87423ff9e1cd7943944822dbe6cbc21d327d5`
- changes only `scripts/prepare_vs2_26_2_phase64.py`
- keeps the existing upward-jump/onGround protection
- adds one redirect at Create's final `Entity.setDeltaMovement(Vec3)` call in `ContraptionColliderClient.collideEntities`
- only for the actual LocalPlayer with `vs2.createCarryCompat=true`, and only after Create has already marked it `onGround`, a negative final Y component is clipped to zero
- X/Z and positive/upward Y are untouched
- no setPos/teleport/manual floor height/collision-shape change/reference-frame mutation/lease/replay/synthetic carriage velocity is introduced
- marker `GATE_E_CREATE_GROUNDED_Y_CLIP` proves exactly when the native-grounding consistency repair fires

### production-world #727 / run `34794456616`
The grounded-motion candidate closes the former immediate sink path without regressing the protected standing/walk baseline:
- `port-build #894`, `client-smoke #811`, `runtime-smoke #853`, and `production-carry-smoke #696` completed SUCCESS
- production proof reports `PRODUCTION_CARRY physical_support_stable carriage_id=10 ticks=24-29 samples=6 span=0.000000000`
- supported sprint/walk confirms at player tick `30` with `on_ground=true`, `broadphase=true`, and `support_healthy=true`
- the run then fails later because no native jump landing marker appears
- this is positive evidence for the grounded-negative-Y repair, not a regression signal and not permission to stack another collision workaround

### jump-arm diagnostic `61cac5cebb119393d8adce581dfa0c5d1009ce67` + composition `2f0de46c8037835fbd06e7d6a39b917984d8daef`
- adds `GATE_E_M1_JUMP_ARM_TRACE` at the final native jump admission boundary
- telemetry only reads backward/strafe confirmation, onGround, jumpArmReady, live floor-support state/tick, native-contact tick, and delta Y
- no player/train/world/input/collision/gravity mutation

### production-world #728 / run `34796986066`
The artifact resolves the post-#727 ambiguity without changing gameplay:
- production carry remains stable (`carry_delta_plus_local_stable`, carriage `10`, ticks `29-31`, zero local span)
- supported sprint/walk again confirms, this time at tick `35`
- native backward is requested and confirmed at tick `39`
- native right-strafe is requested and confirmed at tick `40`
- `GATE_E_CREATE_GROUNDED_Y_CLIP` fires during the same grounded locomotion window and continuity returns `on_ground=true`
- despite backward/strafe already confirmed, `GATE_E_M1_JUMP_ARM_TRACE` remains `jump_arm_ready=false`
- the live floor publisher is already `floor_support_now=false` during the grounded locomotion window and remains false afterward; therefore missing jump is not evidence of missing reverse/strafe dispatch or a reason to change input timing
- later trace shows the floor-support publication stops advancing at tick `140` and native-contact publication at tick `48`, but the floor-support predicate was false before those stale values, so the first false predicate component must be isolated before any acceptance change

### jump floor-predicate diagnostic `a95cdf360313e84a4c154c2c0b4c7484bdfe4cdd`
- extends the existing final jump diagnostic with `GATE_E_M1_JUMP_FLOOR_TRACE`
- logs continuity tick adjacency, same-carriage identity, local step squared / settled threshold, broadphase, onGround, carry-baseline identity, and final support predicate
- read-only only; no jump/input/admission, player motion, collision, carry, gravity, train, world, lease, replay, or reference-frame mutation
- `production-world-smoke #729` / run `34797427793` is in progress; do not duplicate-trigger while active

## Native Create-Fly source finding locked for this candidate
Pinned Create Fly runtime is `26.2-rc-2-6.0.9-1`.
In its native `ContraptionColliderClient.collideEntities`:
- `entityMotion` is copied from the LocalPlayer delta movement
- temporal collision computes `idealVerticalMotion` and may write that Y back into entity delta movement
- zero `totalResponse` produces zero positional allowance at the first `ContraptionCollider.collide` call
- a `surfaceCollision` later calls `entity.setOnGround(true)` for the walkable case
- contact-point carry then applies only X/Z to position
- at the end of the method Create writes the retained local `entityMotion` back with `entity.setDeltaMovement(entityMotion)`

#726 proves that this final write can combine `onGround=true` with negative Y. Candidate `aea874` changes only that final inconsistency for LocalPlayer; it does not invent floor geometry or carriage motion. #727/#728 then show the candidate preventing the former immediate progressive sink through sustained standing/supported locomotion windows.

## Failed hypotheses — DO NOT REPEAT WITHOUT NEW EVIDENCE
- `EXACT_SHAPES_LOCALPLAYER_0fa4aa`
- generic accumulation/extension of frame leases, replay, or carry corrections
- synthetic carry velocity / fake inertia compensation
- manual floor/wall clamps
- harness mutation that manufactures success
- treating missing jump marker as a jump-input bug
- treating right-strafe timing as cause of support loss
- broad sibling/global suppression instead of direct native-owner identity
- floor-normal-only correction as the explanation for #726 support loss; #726 shows the decisive transition can be a temporal side contact while grounded negative Y is retained

## Root-cause classification
Current active blocker: `fixture/harness — live jump floor-support publisher predicate`.

The exact #722 reference-frame double-owner seam is closed/frozen by #724. The native grounded-negative-Y collision mismatch isolated by #726 is repaired by candidate `aea874` strongly enough for #727/#728 to retain sustained grounded standing and supported locomotion. The first unproven boundary is now the read-only fixture publisher feeding jump admission: #728 shows its final value false while native reverse/strafe and grounded continuity are already present. This classification does not authorize changing jump admission; #729 must identify the exact false component first.

## Anti-loop lock
- Do not change sprint/reverse/strafe input windows.
- Do not patch jump admission/acceptance.
- Do not extend native contact leases.
- Do not add replay/recovery branches.
- Do not re-enable exact-shape LocalPlayer redirect.
- Do not add synthetic carry, fake gravity, or manual floor/wall clamps.
- Do not retune the proven Phase83 native-owner predicate unless direct regression reproduces that exact seam.
- Do not broaden or stack another vertical/collision workaround on top of `aea874` without direct renewed sink/regression evidence.
- Do not reinterpret #728's missing jump as an input bug: native backward and right-strafe are already confirmed before the failed admission.
- While #729 is active, do not duplicate-trigger or mutate the floor-support/jump predicate. Inspect `GATE_E_M1_JUMP_FLOOR_TRACE` first.
- If `aea874` regresses any frozen-green subsystem, REVERT it before adding compensation.

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
