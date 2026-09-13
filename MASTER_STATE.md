# MASTER_STATE — VS2 / Create Interactive

GitHub code is the implementation source of truth. This file is the durable project-state source of truth. Chat is temporary.

## Project
- Repository: `apm23/VS2-Create_Interactive`
- Milestone: `M1 — movement / collision`
- Goal: a moving Create train should feel like a stationary house that is actually moving.
- Architecture: Create owns train/carriage gameplay and collision geometry; VS2 supplies moving reference-space/transform foundation; this project is a thin adapter.

## Current state
- project_state: `REGRESSED -> REVERTING_EXACT_SHAPE_EXPERIMENT`
- current_head_before_this_commit: `0fa4aa246021c6b7168b7212406d4f61fac59add`
- last_good_commit: `26e2f82f981bb332a3cdc0fea69e8dc12543250d`
- active_blocker: `production-world-smoke #720 regressed bounded supported walking after exact-shape experiment`
- active_hypothesis: `forcing LocalPlayer onto Create exact per-block shape path changes the native collision/reference-frame interaction and is not safe as the wall fix`
- next_safe_action: `verify the revert with the push-triggered production proof; if locomotion returns, keep exact-shape hypothesis locked failed and redesign wall collision at the ownership/reference-frame boundary rather than stacking a workaround`

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
- forward/sprint/reverse/strafe path proven before the exact-shape experiment

## Latest durable evidence
### production-world-smoke #719 (pre-exact-shape)
- forward/sprint, reverse and right-strafe input paths reached proof
- jump became airborne but final natural landing proof was not completed
- lateral wall collision remained broken: player crossed occupied wall geometry
- this isolated wall collision as the blocker without invalidating locomotion

### commit `0fa4aa246021c6b7168b7212406d4f61fac59add`
- experiment: for LocalPlayer, bypass simplified colliders and force Create's exact per-block VoxelShape fallback
- also added Create compileOnly dependency for typed mixin signatures

### production-world-smoke #720 / run 33596712459
- build/startup succeeded
- sustained standing carry passed: `PRODUCTION_CARRY physical_support_stable carriage_id=5 ticks=51-56 samples=6 span=0.000889604`
- bounded supported walking FAILED before wall/jump acceptance
- walk starts on carriage 7 at tick 32
- tick 34 local X discontinuity from about `-7.43` to `18.05` (step ~25.48)
- subsequent samples repeatedly switch carriage identity between 7 and 5
- tick 36 loses grounded/support health
- final walk marker has `confirmed=false`, `sprinting=false`
- this is a direct regression versus the pre-experiment locomotion proof, so the exact-shape experiment must be reverted rather than patched around

## Failed hypotheses — DO NOT REPEAT WITHOUT NEW EVIDENCE
- `EXACT_SHAPES_LOCALPLAYER_0fa4aa`: forcing `ContraptionColliderClient` LocalPlayer to return null simplified colliders and use exact per-block shapes. Run #720 regressed protected locomotion/reference-frame continuity. Do not reintroduce as-is.
- generic accumulation of frame leases/replays/carry corrections
- synthetic carry velocity / fake inertia compensation
- manual floor/wall clamps
- harness mutation that manufactures gameplay success

## Root-cause classification
Current: `native Create/VS2 integration / reference-frame ownership`, exposed by collision-path change.
The #720 discontinuities are not evidence for changing input/harness acceptance first.

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
2. Inspect actual GitHub HEAD and reconcile it here.
3. Inspect only latest relevant Actions needed for the active blocker.
4. Respect protected/frozen green and failed-hypothesis locks.
5. Continue only from `next_safe_action`.
6. FINAL_READY is terminal and only the user may reopen development after it.
