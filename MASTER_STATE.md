# MASTER_STATE — VS2 / Create Interactive

GitHub code is the implementation source of truth. This file is the durable project-state source of truth. Chat is temporary.

## Project
- Repository: `apm23/VS2-Create_Interactive`
- Milestone: `M1 — movement / collision`
- Goal: a moving Create train should feel like a stationary house that is actually moving.
- Architecture: Create owns train/carriage gameplay and collision geometry; VS2 supplies moving reference-space/transform foundation; this project is a thin adapter.

## Current state
- project_state: `ROOT_REDESIGN — read-only ownership micro-proof in flight`
- current_head: `AUTO_RECONCILE_GIT_HEAD` (state-only `[skip ci]` ledger commits may advance Git HEAD; compare implementation files before treating that as a gameplay change)
- implementation_head: `e58adf3e9ac2baa24ea476bfeaaaf707cf35dd4e`
- diagnostic_head: `69044c59a804e8b473038258d2d7c7ec2a843372`
- last_good_implementation_commit: `e58adf3e9ac2baa24ea476bfeaaaf707cf35dd4e` (exact-shape regression removed; not M1 complete)
- active_blocker: `Create carriage-contact ownership and the VS2 external-frame bridge disagree before/through lateral locomotion; physical support can be false while the bridge still reanchors LocalPlayer from a leased carriage frame, followed by native ownership handoff to sibling carriages and eventual floor/envelope loss`
- active_hypothesis: `the remaining failure is unstable/double moving-frame ownership at the Create-contact ↔ VS2-EntityDragger boundary; the support disagreement begins before the right-strafe request, so strafe input itself is not the root cause`
- next_safe_action: `wait for the production-world-smoke triggered by diagnostic_head 69044c59 and inspect the downstream carry-gap-diagnostics ownership micro-proof. Use its ordered timeline to identify the one authoritative carriage/reference frame and transform order. Do not mutate gameplay until that proof completes.`

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

Important: strafe INPUT/MOTION dispatch is green; post-input carriage support/collision stability is NOT green. New #721 log inspection also shows the first Phase81 physical-support disagreement already occurs before the strafe request, so do not treat strafe timing as causal.

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
- deeper ordered-log inspection changes the causal boundary: the first `GATE_E_PHASE81_SUPPORT_CONTINUITY` physical-support failure occurs at tick 29, with saved carriage 7 and current carriage 5, six ticks BEFORE the right-strafe request at tick 35
- support remains false on carriage 7 at ticks 31-34 even though Create still publishes native applications on carriage 7 through tick 33
- tick 34: native application age is 1, physical support is false, LocalPlayer is airborne, and Phase83 invokes VS2 `EntityDragger#reanchorEntityWithExternalFrame` from the leased carriage-7 frame
- tick 35: native Create contact application changes to carriage 5 while the saved baseline remains carriage 7; subsequent support/current-carriage identity continues to disagree
- later unsupported Phase83 reanchors occur on carriage 5 (including stale native-application ages), after which LocalPlayer leaves the carriage floor/envelope
- no native jump request occurs because healthy supported/native-contact prerequisites are already lost; this is NOT evidence to change jump timing
- conclusion: the ownership/support seam is already broken before strafe; strafe exposes/continues it but does not create it

### diagnostic commit `69044c59a804e8b473038258d2d7c7ec2a843372`
- gameplay/generated source unchanged
- updates only the workflow-run diagnostic and a non-executed CI trigger note
- production-world-smoke is triggered through the existing `scripts/prepare_vs2_26_2*.py` path filter
- downstream `carry-gap-diagnostics` now produces a deterministic ordered ownership micro-proof from existing read-only markers: first support loss, relation to strafe, Create native owner handoff, unsupported Phase83 external-frame reanchor, and LocalPlayer setPos owner

## Failed hypotheses — DO NOT REPEAT WITHOUT NEW EVIDENCE
- `EXACT_SHAPES_LOCALPLAYER_0fa4aa`: forcing `ContraptionColliderClient` LocalPlayer to use exact per-block shapes. Run #720 regressed protected locomotion/reference-frame continuity. Do not reintroduce as-is.
- generic accumulation of frame leases/replays/carry corrections
- synthetic carry velocity / fake inertia compensation
- manual floor/wall clamps
- harness mutation that manufactures gameplay success
- treating missing jump marker as a jump-input bug; support/frame ownership is already broken before jump admission
- treating right-strafe timing as the cause of support loss; #721 Phase81 telemetry loses physical support before the strafe request

## Root-cause classification
Current: `native Create/VS2 integration — reference-frame ownership + collision boundary`.

The ownership micro-proof must answer exactly:
`Which single carriage/reference frame is authoritative for LocalPlayer collision and transform when Phase81 physical support first disagrees, and in what order do Create native collision/setPos and the VS2 external-frame bridge apply?`

## Anti-loop lock
- Do not change sprint/reverse/strafe input windows.
- Do not extend native contact leases.
- Do not add another replay/recovery branch.
- Do not re-enable exact-shape LocalPlayer redirect.
- Do not patch jump acceptance.
- Do not add another gameplay mutation while diagnostic_head proof is active.
- Prefer removal/simplification of duplicate ownership after proof over another compensation layer.
- If evidence proves Create native collision and the Phase83/EntityDragger bridge independently move/reanchor LocalPlayer from competing/stale carriage frames, redesign to one authoritative transform path.

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
3. If `current_head` is `AUTO_RECONCILE_GIT_HEAD`, compare commits since `implementation_head`; state-only `[skip ci]` ledger commits and diagnostic-only commits do not count as gameplay changes.
4. Inspect only latest relevant Actions needed for the active blocker.
5. Respect protected/frozen green and failed-hypothesis locks.
6. Continue only from `next_safe_action`.
7. FINAL_READY is terminal and only the user may reopen development after it.
