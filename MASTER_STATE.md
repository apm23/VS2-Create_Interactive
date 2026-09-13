# MASTER_STATE — VS2 / Create Interactive

GitHub code is the implementation source of truth. This file is the durable project-state source of truth. Chat is temporary.

## Project
- Repository: `apm23/VS2-Create_Interactive`
- Milestone: `M1 — movement / collision`
- Goal: a moving Create train should feel like a stationary house that is actually moving.
- Architecture: Create owns train/carriage gameplay and collision geometry; VS2 supplies moving reference-space/transform foundation; this project is a thin adapter.

## Current state
- project_state: `WORKING — native-owner arbitration test in flight`
- current_head: `AUTO_RECONCILE_GIT_HEAD` (state-only `[skip ci]` ledger commits may advance Git HEAD; compare implementation files before treating that as a gameplay change)
- implementation_head: `6a4d960e65d79a6f4a4c5973a83b2e6debd5aa2e`
- diagnostic_head: `69044c59a804e8b473038258d2d7c7ec2a843372`
- last_good_implementation_commit: `e58adf3e9ac2baa24ea476bfeaaaf707cf35dd4e` (exact-shape regression removed; not M1 complete)
- candidate_implementation_commit: `6a4d960e65d79a6f4a4c5973a83b2e6debd5aa2e` (unproven until its real-train production smoke completes)
- active_blocker: `Create can hand native LocalPlayer ownership to a sibling carriage while Phase83 still treats the old exact-baseline carriage's registered-contact/native-age lease as authoritative; this creates same-tick Create setPos followed by VS2 EntityDragger reanchor from a stale carriage frame`
- active_hypothesis: `a grounded exact-baseline Phase83 lease is valid only while that baseline remains Phase170's most recent Create-native owner; owner identity should arbitrate the bridge without changing Create collision, input, gravity, or carry velocity`
- next_safe_action: `inspect the production-world-smoke triggered by implementation_head 6a4d960e. If it is queued/in_progress, HOLD. When complete, verify frozen locomotion remains green and specifically whether unsupported Phase83 external reanchors after a different Create-native owner disappear. Only then classify any remaining floor/support failure.`

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

## Frozen / protected green
Do not modify without direct regression evidence:
- boot/no-crash baseline
- Create train + VS2 baseline coexistence
- Steam 'n' Rails and Copycats preservation
- standing carry continuity
- forward/sprint input and supported walking proof
- native backward input/motion proof
- native right-strafe input/motion dispatch proof

Important: strafe INPUT/MOTION dispatch is green; post-input carriage support/collision stability is NOT green. #721/#722 show the first Phase81 physical-support disagreement occurs before the strafe request, so do not treat strafe timing as causal.

## Latest durable evidence
### production-world-smoke #719 (pre-exact-shape)
- forward/sprint, reverse and right-strafe input paths reached proof
- jump became airborne but final natural landing proof was not completed
- lateral wall collision remained broken: player crossed occupied wall geometry
- this isolated wall/collision ownership as the blocker without invalidating basic locomotion

### exact-shape experiment `0fa4aa246021c6b7168b7212406d4f61fac59add`
- experiment forced LocalPlayer from Create simplified colliders onto exact per-block VoxelShapes
- production-world-smoke #720 regressed protected walking/reference continuity before wall/jump proof
- experiment is locked failed and was reverted

### revert implementation `e58adf3e9ac2baa24ea476bfeaaaf707cf35dd4e`
- restores Phase39 runtime-only Create dependency and the previously proven LocalPlayer PlayerType.CLIENT bridge
- removes the exact-shape redirect entirely

### production-world-smoke #721 / run `34769096716`
- revert validation build/startup succeeded
- standing carry returned: `PRODUCTION_CARRY carry_delta_plus_local_stable carriage_id=7 ticks=25-28 samples=4 span=0.000000000`
- supported walk/sprint returned: `GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED ... player_tick=30 ... confirmed=true sprinting=true`
- backward request + native motion confirmed at tick 34
- right-strafe request + native motion confirmed at tick 35
- therefore the exact-shape-specific locomotion regression is gone
- deeper ordered-log inspection changes the causal boundary: the first Phase81 physical-support failure occurs before right-strafe

### diagnostic commit `69044c59a804e8b473038258d2d7c7ec2a843372`
- gameplay/generated source unchanged
- adds a deterministic read-only Create/VS2 ownership micro-proof to downstream diagnostics

### production-world-smoke #722 / run `34788419359` + carry-gap-diagnostics #221 / run `34788726817`
- real-train blocker reproduced while protected locomotion markers remained available
- downstream ownership micro-proof completed successfully and is read-only
- baseline carriage `7`; walk confirmed tick `30`; right-strafe request tick `35`
- first physical-support loss is tick `31`, current carriage `7`, same-carriage `true`: support loss begins BEFORE strafe
- Create continues native carriage-7 applications on ticks 31-33 while support is false
- tick 35: Create publishes native owner carriage `5`, applies motion about `-8.58936 X`, and `ContraptionColliderClient#collideEntities` calls LocalPlayer `setPos`
- after that same tick, Phase81 returns to saved/current carriage `7` with physical support false
- Phase83 then calls `EntityDragger#reanchorEntityWithExternalFrame` from carriage `7`, moving LocalPlayer another about `-2.19505 X`
- Phase83 reports `physical_support=false`, `on_ground=true`, `native_application_age=2`, `grounded_gap_bridge=false`, but `native_frame_eligible=true`
- tick 36 repeats Create-native carriage `5` setPos followed by unsupported Phase83 carriage-7 external reanchor
- direct conclusion: registered contact / bounded native-age alone can keep a stale baseline bridge alive after Create has handed native ownership to another carriage, producing duplicate moving-frame ownership

### candidate ownership-arbitration implementation `6a4d960e65d79a6f4a4c5973a83b2e6debd5aa2e`
- changes only `scripts/prepare_vs2_26_2_m1_wall_fixture_window.py`
- existing Phase83 grounded exact-baseline registered-contact/native-age lease now additionally requires that baseline carriage id equals Phase170's most recent native Create owner id
- does NOT alter Create collision solver, exact-shape policy, input windows, jump, gravity, velocity, train state, world state, or add new carry state
- preserves the prior one-to-two-tick / registered-contact lease only while ownership identity still agrees
- purpose: prevent stale carriage-7 VS2 reanchor after Create has already handed native ownership to carriage 5, while preserving prior bounded same-owner gap behavior
- validation pending real-train production smoke

## Failed hypotheses — DO NOT REPEAT WITHOUT NEW EVIDENCE
- `EXACT_SHAPES_LOCALPLAYER_0fa4aa`: forcing `ContraptionColliderClient` LocalPlayer to use exact per-block shapes. Run #720 regressed protected locomotion/reference-frame continuity. Do not reintroduce as-is.
- generic accumulation of frame leases/replays/carry corrections
- synthetic carry velocity / fake inertia compensation
- manual floor/wall clamps
- harness mutation that manufactures gameplay success
- treating missing jump marker as a jump-input bug; support/frame ownership is already broken before jump admission
- treating right-strafe timing as the cause of support loss; #721/#722 lose physical support before the strafe request
- broad unqualified sibling/global suppression as a substitute for owner identity; arbitration must be tied to direct Create-native ownership evidence

## Root-cause classification
Current: `native Create/VS2 integration — reference-frame ownership + collision boundary`.

Ownership proof answered the immediate ambiguity:
- Create native collision/setPos can establish carriage `5` as current native owner.
- Phase83 can subsequently move the same LocalPlayer again from stale baseline carriage `7` while physical support is false.
- the candidate fix therefore makes Phase170 native-owner identity an explicit prerequisite for retaining the grounded exact-baseline external-frame lease.

## Anti-loop lock
- Do not change sprint/reverse/strafe input windows.
- Do not extend native contact leases.
- Do not add another replay/recovery branch.
- Do not re-enable exact-shape LocalPlayer redirect.
- Do not patch jump acceptance.
- Do not add synthetic carry, velocity, gravity, or manual collision clamps.
- Do not mutate the candidate ownership predicate again until its real-train proof completes.
- If candidate regresses frozen-green, REVERT before any compensating workaround.
- If candidate removes duplicate Phase83 ownership but floor/support still fails, classify the remaining vertical/collision boundary separately rather than extending the bridge again.

## M1 acceptance — all required in one real moving-train proof
- [ ] stable standing
- [ ] forward/backward/strafe
- [ ] sprint
- [ ] jump + airborne + natural landing
- [ ] solid floor/walls/ceiling
- [ ] no sink/throw/drift/lag-behind
- [ ] stable through movement/turn/speed changes as fixture permits

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
3. If `current_head` is `AUTO_RECONCILE_GIT_HEAD`, compare commits since `implementation_head`; state-only `[skip ci]` ledger commits do not count as gameplay changes.
4. Inspect only latest relevant Actions needed for the active blocker.
5. Respect protected/frozen green and failed-hypothesis locks.
6. Continue only from `next_safe_action`.
7. FINAL_READY is terminal and only the user may reopen development after it.
