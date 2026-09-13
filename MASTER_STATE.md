# MASTER_STATE — VS2 / Create Interactive

GitHub code is the implementation source of truth. This file is the durable project-state source of truth. Chat is temporary.

## Project
- Repository: `apm23/VS2-Create_Interactive`
- Milestone: `M1 — movement / collision`
- Goal: a moving Create train should feel like a stationary house that is actually moving.
- Architecture: Create owns train/carriage gameplay and collision geometry; VS2 supplies moving reference-space/transform foundation; this project is a thin adapter.

## Current state
- project_state: `ROOT_REDESIGN — reference-frame / collision ownership boundary`
- current_head: `e58adf3e9ac2baa24ea476bfeaaaf707cf35dd4e`
- last_good_commit: `e58adf3e9ac2baa24ea476bfeaaaf707cf35dd4e` (exact-shape regression removed; not M1 complete)
- active_blocker: `native right-strafe leaves the supported carriage frame: Create contact ownership hands off across carriages while physical support disappears, VS2 EntityDragger continues external-frame reanchoring, and the player falls through/away before jump can arm`
- active_hypothesis: `the remaining failure is unstable/double moving-frame ownership at the Create-contact ↔ VS2-EntityDragger boundary, not missing fixture input or a need for another collision workaround`
- next_safe_action: `freeze gameplay mutation and build/inspect the smallest read-only ownership/collision micro-proof around the strafe-loss ticks: one active carriage, Create collision owner, VS2 external frame, transform order, physical-support state, and final allowed movement. Do not add leases/replays/clamps or change jump timing.`

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

Important: strafe INPUT/MOTION dispatch is green; post-strafe carriage support/collision stability is NOT green.

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

### revert commit `e58adf3e9ac2baa24ea476bfeaaaf707cf35dd4e`
- restores Phase39 runtime-only Create dependency and the previously proven LocalPlayer PlayerType.CLIENT bridge
- removes the exact-shape redirect entirely

### production-world-smoke #721 / run 34769096716
- revert validation build/startup succeeded
- standing carry returned: `PRODUCTION_CARRY carry_delta_plus_local_stable carriage_id=7 ticks=25-28 samples=4 span=0.000000000`
- supported walk/sprint returned: `GATE_E_PHASE154_FIXTURE_WALK_CONFIRMED ... player_tick=30 ... confirmed=true sprinting=true`
- backward request + native motion confirmed at tick 34
- right-strafe request + native motion confirmed at tick 35
- therefore the exact-shape-specific locomotion regression is gone
- after strafe, the actual gameplay state still collapses at the ownership/collision boundary:
  - by tick 43 LocalPlayer is airborne at world Y about `-59.67`; saved baseline carriage is 7 while current contact/rebase work is on carriage 5
  - `GATE_E_PHASE81_SUPPORT_CONTINUITY` reports `same_carriage=false physical_support=false`
  - VS2 `EntityDragger#reanchorEntityWithExternalFrame` still applies the carriage-frame translation while physical support is false
  - carriage-local feet for carriage 5 are already below the carriage support plane (`local_feet ... y=-0.674...` at tick 43)
  - by tick 47 local feet are about `y=-1.0`, broadphase becomes false, and the player has left the real carriage envelope
- no native jump request occurs because the healthy supported/native-contact prerequisites are already lost downstream of strafe; this is NOT evidence to change jump timing
- conclusion: revert is validated, but M1 remains blocked by Create/VS2 frame/collision ownership during lateral locomotion

## Failed hypotheses — DO NOT REPEAT WITHOUT NEW EVIDENCE
- `EXACT_SHAPES_LOCALPLAYER_0fa4aa`: forcing `ContraptionColliderClient` LocalPlayer to use exact per-block shapes. Run #720 regressed protected locomotion/reference-frame continuity. Do not reintroduce as-is.
- generic accumulation of frame leases/replays/carry corrections
- synthetic carry velocity / fake inertia compensation
- manual floor/wall clamps
- harness mutation that manufactures gameplay success
- treating missing jump marker in #721 as a jump-input bug; support/frame ownership is already broken before jump admission

## Root-cause classification
Current: `native Create/VS2 integration — reference-frame ownership + collision boundary`.
Evidence now shows this sequence directly: valid native locomotion -> strafe -> carriage identity/support disagreement -> external-frame reanchor while physical support is false -> player below carriage -> broadphase loss.

The next investigation must answer exactly one ownership question before gameplay mutation:
`Which single carriage/reference frame is authoritative for LocalPlayer collision and transform on the first tick where strafe causes support loss, and in what order do Create collision resolution and VS2 EntityDragger apply?`

## Anti-loop lock for next cycle
- Do not change sprint/reverse/strafe input windows.
- Do not extend native contact leases.
- Do not add another replay/recovery branch.
- Do not re-enable exact-shape LocalPlayer redirect.
- Do not patch jump acceptance.
- Prefer read-only instrumentation or a minimal isolated ownership experiment.
- If evidence proves both Create and VS2 independently move/reanchor the LocalPlayer in the same boundary, redesign to one authoritative transform path instead of compensating afterward.

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
