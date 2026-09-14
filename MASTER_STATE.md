# MASTER_STATE — VS2 / Create Interactive

GitHub code is the implementation source of truth. This file is the durable project-state source of truth. Chat is temporary.

## Project
- Repository: `apm23/VS2-Create_Interactive`
- Milestone: `M1 — movement / collision`
- Goal: a moving Create train should feel like a stationary house that is actually moving.
- Architecture: Create owns train/carriage gameplay and collision geometry; VS2 supplies moving reference-space/transform foundation; this project is a thin adapter.

## Current state
- project_state: `ACTIVE_BLOCKER — #730 native jump arc leaves intended carriage before natural landing; Create ground/final-motion ordering diagnostic in flight`
- current_head: `AUTO_RECONCILE_GIT_HEAD` (state-only `[skip ci]` ledger commits may advance Git HEAD; compare implementation files before treating that as gameplay change)
- implementation_head: `aea87423ff9e1cd7943944822dbe6cbc21d327d5`
- previous_diagnostic_head: `c7da75df793502f3fe4f61d0dd093190e00a06fa`
- candidate_gameplay_commit: `aea87423ff9e1cd7943944822dbe6cbc21d327d5`
- last_good_implementation_commit: `e58adf3e9ac2baa24ea476bfeaaaf707cf35dd4e` (exact-shape regression removed; not M1 complete)
- active_blocker: `#730 proves the #729 bookkeeping repair is valid and frozen locomotion remains green: production carry is physical_support_stable, walk/sprint passes, native backward/strafe remain confirmed, and the fixture issues a genuine native jump with positive vertical motion. The arc then fails natural landing on the intended baseline carriage: LocalPlayer remains reported onGround through most of the rising/falling arc, continuity later hands to a sibling carriage, becomes genuinely airborne for several ticks, and finally grounds on the sibling/lower frame rather than publishing GATE_E_M1_NATIVE_JUMP_LANDED for the intended carriage.`
- active_hypothesis: `Create's setOnGround decision and its final native setDeltaMovement write may observe different vertical state during the same jump collision pass. Diagnostic c7da75df preserves the existing behavior exactly and logs requested/applied grounding plus delta-Y at the setOnGround seam and current/incoming/applied Y at the final-motion seam. This will distinguish stale vertical state at the ground decision from a later native caller reasserting ground.`
- next_safe_action: `production-world-smoke #731 / run 34799207093 is in progress for c7da75df. Do not duplicate-trigger and do not patch jump admission/input, leases, replay, ownership, or collision while it runs. After compile/runtime validity is known, correlate GATE_E_CREATE_SET_ON_GROUND_SEAM with GATE_E_CREATE_FINAL_MOTION_SEAM during the jump ticks. If setOnGround sees non-rising/stale delta while final incoming motion is positive, inspect the native ordering boundary before any correction. If the redirect applies airborne=false correctly but observable state becomes grounded later, identify the later native ground writer. No gameplay mutation until that exact owner/order seam is proven.`

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
- native right-strafe input/motion proof
- Phase83 stale-baseline sibling-owner arbitration fixed at the exact #722 competing-owner seam by #724
- Create grounded-negative-Y consistency repair at `aea874`: #727/#728/#730 retain standing/carry and supported locomotion instead of the former progressive sink
- #729 floor-support bookkeeping correction at `94b920480f545845134d2e262791704489bb95d7`: ordinary horizontal native locomotion no longer invalidates fixture floor support merely because total local XYZ step is non-zero

Important: movement input dispatch and native jump request execution are green. Missing natural landing is not permission to change input timing or admission.

## Latest durable evidence
### exact-shape experiment `0fa4aa246021c6b7168b7212406d4f61fac59add`
- forced LocalPlayer to exact per-block shapes
- production-world #720 regressed protected locomotion/reference continuity
- reverted and locked failed; DO NOT REINTRODUCE without genuinely new evidence

### revert `e58adf3e9ac2baa24ea476bfeaaaf707cf35dd4e`
- removed exact-shape redirect and restored protected movement baseline

### production-world #721
- standing carry, forward/sprint, native backward, and right-strafe returned; support/frame loss remained

### production-world #722
- proved duplicate ownership: Create handed native ownership to a sibling while stale baseline Phase83 could still reanchor

### owner arbitration recovery `881f1a737c92efdd39b7e5fcda13efb6908b475f`
- composition fixed; #724 proved the stale post-handoff Phase83 reanchor no longer recurs
- this exact ownership seam is frozen green

### production-world #724
- frozen locomotion green
- exposed deeper native Create vertical-response consumption: floor support could be lost while X/Z remained over the train floor

### zero-response diagnostic `057d1b117960620f473eef1573821986f176ae76` / #725
- proved zero `totalResponse` gives no vertical positional correction at the first Create response-site setPos

### OBB correlation diagnostic `4479e094848b5ce75b0d3f4dc7aed55c9ac9ef47` / #726
- decisive invariant: Create could finish LocalPlayer surface/temporal handling with `onGround=true` while retaining negative Y delta
- next vanilla tick consumed exactly that retained negative Y and progressively sank the player
- transition could involve temporal side contact, so floor-normal-only correction is invalid

### grounded-motion candidate `aea87423ff9e1cd7943944822dbe6cbc21d327d5`
- changes only the final native-motion seam in `scripts/prepare_vs2_26_2_phase64.py`
- when Create itself finishes the actual LocalPlayer grounded, only negative final Y is clipped to zero
- X/Z and positive/upward Y untouched
- no setPos/teleport/manual floor height/shape change/lease/replay/synthetic carry
- marker: `GATE_E_CREATE_GROUNDED_Y_CLIP`

### production-world #727
- former immediate sink path no longer reproduces
- `PRODUCTION_CARRY physical_support_stable`; supported walk/sprint passes
- failure moved downstream to jump proof

### production-world #728
- carry remains stable; walk/sprint, native backward, native right-strafe all confirm
- jump admission remains false because live fixture floor-support publisher is false
- establishes that missing jump was not an input timing bug

### floor-predicate diagnostic `a95cdf360313e84a4c154c2c0b4c7484bdfe4cdd` / #729
- read-only predicate trace isolates the false component to the obsolete near-zero total local-step requirement
- tick cadence, same carriage, broadphase, onGround, and baseline identity remain valid during native locomotion
- ordinary backward/strafe correctly makes total local XYZ step non-zero

### fixture bookkeeping repair `94b920480f545845134d2e262791704489bb95d7`
- changes only M1 fixture support bookkeeping
- replaces near-zero XYZ-step requirement with fixed fixture-floor local-Y alignment while preserving cadence/carriage/broadphase/onGround/baseline checks
- no player/collision/train/world/input mutation
- `port-build #897`, `client-smoke #814`, `runtime-smoke #856`, and `production-carry-smoke #699` pass

### production-world #730 / run `34798398059`
- frozen baseline preserved: `PRODUCTION_CARRY physical_support_stable`; supported walk/sprint succeeds
- native jump is genuinely requested at tick 53
- native vertical arc is observed immediately with `delta_y=+0.3331999936`
- no natural-landing marker follows
- continuity remains `onGround=true` through much of the visible rising/falling arc despite physical support having left the original floor
- later continuity changes from baseline carriage `4` to sibling carriage `5`
- ticks around 63–65 are genuinely airborne on carriage 5; tick 66 becomes grounded around sibling local Y `-1.0` while baseline remains carriage 4
- therefore the failure is not merely a missing verifier marker; the jump leaves the intended carriage/reference target before natural landing

### ground/final-motion ordering diagnostic `c7da75df793502f3fe4f61d0dd093190e00a06fa`
- modifies only `scripts/prepare_vs2_26_2_m1_jump_arm_trace.py`
- Phase64 behavior is preserved; existing native `setOnGround` and final `setDeltaMovement` writes remain one-for-one
- adds `GATE_E_CREATE_SET_ON_GROUND_SEAM`: requested ground flag, prior ground state, delta-Y observed at call, rising guard, applied ground flag
- adds `GATE_E_CREATE_FINAL_MOTION_SEAM`: ground state before final write, current delta-Y, incoming motion Y, applied motion Y, grounded-clip flag
- both traces are bounded to the relevant fixture jump window and read-only
- `production-world-smoke #731` / run `34799207093` is in progress; do not duplicate-trigger

## Native Create-Fly source finding locked
Pinned Create Fly runtime is `26.2-rc-2-6.0.9-1`.
In native `ContraptionColliderClient.collideEntities`:
- `entityMotion` starts from LocalPlayer delta movement
- temporal collision can compute `idealVerticalMotion`
- zero response can produce zero positional allowance
- walkable surface collision can call `entity.setOnGround(true)`
- contact carry applies X/Z position movement
- method later writes retained `entityMotion` through final `entity.setDeltaMovement(entityMotion)`

#726 proves final grounded state and final vertical motion were inconsistent for downward motion; `aea874` repairs that exact invariant. #730 now exposes an airborne-side ordering/ownership boundary, not renewed evidence to broaden the grounded negative-Y repair.

## Failed hypotheses — DO NOT REPEAT WITHOUT NEW EVIDENCE
- `EXACT_SHAPES_LOCALPLAYER_0fa4aa`
- generic accumulation/extension of frame leases, replay, or carry corrections
- synthetic carry velocity / fake inertia compensation
- manual floor/wall clamps
- harness mutation that manufactures success
- treating missing jump as a jump-input bug
- treating right-strafe timing as cause of support loss
- broad sibling/global suppression instead of direct native-owner identity
- floor-normal-only correction for #726
- near-zero total local XYZ movement as a prerequisite for supported locomotion; #729 disproved it for the fixture bookkeeping path

## Root-cause classification
Current: `collision / airborne ground-state and reference-owner ordering`.

The #722 double-owner seam is closed/frozen. The #726 grounded-negative-Y mismatch is repaired/frozen strongly enough for #727/#728/#730. #729 repaired only fixture bookkeeping and #730 then proved a real native jump arc. The remaining first broken invariant is during that arc: grounding/reference ownership does not stay consistent with the intended baseline carriage through natural landing. #731 is measuring Create's exact ground-decision versus final-motion ordering before any new behavior is authorized.

## Anti-loop lock
- Do not change sprint/reverse/strafe input windows.
- Do not patch jump admission/acceptance.
- Do not extend native contact leases.
- Do not add replay/recovery branches.
- Do not re-enable exact-shape LocalPlayer redirect.
- Do not add synthetic carry, fake gravity, inertia compensation, or manual floor/wall clamps.
- Do not retune Phase83 native-owner arbitration unless direct regression reproduces its exact closed seam.
- Do not broaden `aea874` unless renewed direct sink/regression evidence requires it.
- Do not treat #730 missing landing as verifier-only: artifact evidence shows real sibling-carriage handoff/lower grounding.
- While #731 is active, do not duplicate-trigger or make gameplay changes. First classify the exact Create setOnGround/final-motion ordering from the new read-only markers.

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
