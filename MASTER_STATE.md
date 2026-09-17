# MASTER_STATE — VS2 / Create Interactive

GitHub code is the implementation source of truth. This file is the durable project-state ledger; chat is temporary.

## Hard contract
- Repository: `apm23/VS2-Create_Interactive`; milestone: `M1 — movement/collision`.
- Create owns train/carriage gameplay and collision geometry.
- VS2 is the continuous moving reference-space foundation for player body/render/camera through grounded, airborne, turns and speed changes; mouse/look remains free.
- Create floor/walls/ceiling remain authoritative solid geometry in that moving frame.
- Forbidden: fake gravity; synthetic carry velocity/inertia; manual floor/wall clamps; floor-only fixes; per-tick teleport/setPos chase/reanchor architecture; duplicate authority/state; direct camera forcing/counter-rotation; fake/proxy VS2 ships; workaround chains hiding double ownership.

## Current reconciliation — 2026-09-17
- `current_head`: `82766397300abee3a71b2b2fab5e346ee6fd38fd` immediately before this ledger-only reconciliation commit.
- `82766397300abee3a71b2b2fab5e346ee6fd38fd`: `Make ceiling trace tick anchors idempotent` — proof-infra only, no gameplay change.
- Previous ceiling instrumentation HEAD: `61122b80e8e07416af01232e6ac290109f5bf9b2`.
- Latest gameplay implementation remains `9aea12a6114198c33c70d52897eb9d3c29342425` (`Refresh jump owner from exact Create grounded carry contact`).
- Active blocker: `CEILING`.
- Project state: `CAMERA_DATA_PROVEN_VISUAL_INCONCLUSIVE_MEDIA_PENDING_USER_AUDIT; CEILING_READ_ONLY_RUNTIME_PROOF_RETRY_IN_PROGRESS`.
- final_ready: `false`.
- Historical failed user JAR SHA256 `96053e314891495fbb4bf16c446023568fed542497e083083dad7ed420dcd7ef`: grounded floor/walk good, walls soft, jump dragged 2–4 carriages, turns swept player/camera, wall penetration/throw; never retest this SHA.

## Camera
- Exact source proof HEAD `8ed60f1de4c75810073dbb7ed10bee2a89c325e9`; run `35135734132` SUCCESS; artifact `10461944899`, digest `sha256:69494207606455f0f6ee2f50927d397bbf49300f482ba37d4d28e85d10282fbf`.
- Classifier `CAMERA_EXTERNAL_REFERENCE_POSITIONAL_ALIGNED_WITHIN_0_05`; owner7; ticks32/42; 180° heading span; max/p95/median horizontal error 0; basis `previous_owner_to_current_owner`; look/player/collision/gameplay unmutated.
- Visual audit preserved but non-blocking: run `35138243767` black; run `35163349899` visible and contained ~54.26° turn with ~0 error but framing aimed mostly floor/lower wall; run `35166011444` nonblack direct-framebuffer capture but no active-owner turn in capture interval, artifact `10474552888` digest `sha256:04cb6bb574625f1836ef341d3ddc1a53498fae79dbefb64efca7ed6df6355e12`.
- Status: `DATA_PROVEN_VISUAL_INCONCLUSIVE_MEDIA_PENDING_USER_AUDIT`. Do not reopen camera gameplay from media timing/framing failure. User prioritizes mod progress; framing cleanup may occur later.

## Autonomous video policy
- Video only after a blocker is data/runtime closure-ready; never during debugging/instrumentation/correction.
- Assistant reviews actual MP4 frames; user presence is not required. Preserve every video/review for later audit.
- PASS => `AUTO_FROZEN_GREEN_PENDING_USER_AUDIT` and continue.
- Visible FAIL => reopen only affected subsystem and diagnose automatically.
- Black/unreadable/missed observation after narrow media repair budget => `VISUAL_INCONCLUSIVE_MEDIA_PENDING_USER_AUDIT`; preserve data proof and continue independent engineering.
- Final exact JAR still requires real-user Minecraft acceptance; CI/video cannot produce `FINAL_READY`.

## Ceiling proof — active retry
- Read-only files: `scripts/prepare_vs2_26_2_ceiling_contact_trace.py`, `.github/workflows/m1-ceiling-contact-runtime-proof.yml`.
- First run `35167469407` on HEAD `61122b80e8e07416af01232e6ac290109f5bf9b2` FAILED in compose only: `ceiling trace could not find LocalPlayer setPos marker`.
- Root cause proven: existing Phase186 already changes the Phase76 setPos record to `GATE_E_LOCALPLAYER_SET_POS index={} player_tick={}`. The ceiling script incorrectly required the pre-Phase186 anchor and attempted to add the same tick field twice.
- Repair commit `82766397300abee3a71b2b2fab5e346ee6fd38fd` makes GateE/collide/setPos tick anchors idempotent. This is proof infrastructure only; movement/collision/input/camera/world/train/physics values remain untouched.
- Relevant retry workflow: `m1-ceiling-contact-runtime-proof`, run `35167683911`, exact HEAD `82766397300abee3a71b2b2fab5e346ee6fd38fd`; `in_progress` at this reconciliation.
- Ignore unrelated generic workflow noise while this targeted proof runs.
- Pristine r0v3 save SHA256 `e78bfb854a0f3ad0bfb87ded836ef322335812d303e51223825f3741f7232556`; existing natural-landing native-input harness reused without geometry/route/timing/gameplay mutation.
- Required timeline: tick; exact Create `worldToLocalPos` local position/overhead geometry; OBB normal; collisionResponse; surfaceCollision; temporalResponse; requested/allowed collide; tick-bearing final Create setPos writer.
- Classifiers:
  - `CEILING_NOT_EXERCISED` => no gameplay patch; observation/selection only.
  - `CEILING_CONTACT_OBSERVED_CORRELATION_INCOMPLETE` => read-only correlation follow-up only.
  - `CEILING_CONTACT_CORRELATED` => inspect exact timeline before any gameplay conclusion.
- Compose/compile/harness/verifier failures authorize proof-infra repair only.
- No ceiling video until data/runtime closure-ready.

## Preserved evidence / FROZEN boundaries
- bootstrap/Kotlin `f3d1335...`; Create+VS2 coexistence; Steam 'n' Rails + Copycats.
- V1 infra `34984299770`; external-owner lifecycle `35008163064`; same-point transform `35023234306`; free-look boundary `35034983734`; OBB temporal support-loss `35041914462`; native drag gate `35045444238`; existing VS2 body writer `35048234680`; descent support-miss `35051781646`; owner-cap lag `35071088843`; fixture arbitration `35084762923`, `35085286003`.
- Current Create collision-frame continuity run `35100081357`: candidate-vs-Phase131 residual 0; max frame step `0.048467738`; external owner continuous; existing EntityDragger writer runs.
- Wall/ceiling source map run `35101691613`, artifact `10448192299`: current Create `worldToLocalPos` OBB path; X/Z wall clipping; Y vertical clipping; response setPos; surface contact-motion writer; duplicate authority removed.
- Pinned contacts run `35104224078`, artifact `10450080515`: seven horizontal wall rows, no ceiling row.
- Wall semantics run `35104523803`, artifact `10449412710`: all seven wall rows valid temporal-only; `unresolved_zero=0`.
- Valid OBB rule: `surface=true + collisionResponse=ZERO + 0<temporal<1` can be solved Create behavior; zero response alone is not failure.
- Historical native jump run `35089177675`, HEAD `012d92dabb86cac5571d5d320eea9fa77ea539d6`, artifact `10444135201`: native airborne tick46, rise `+0.33319999363422365`, owner7 continuous ticks46..83. Do not reuse its old post-arc lifecycle failure as current ceiling failure.
- Camera external-owner gate reachability `35113644070`; camera active-turn data proof `35135734132`; historical user floor solidity + grounded walking.

## FAILED_HYPOTHESES / anti-loop
Do not reintroduce absent new direct evidence: `EXACT_SHAPES_LOCALPLAYER_0fa4aa`; generic frame lease/replay/carry extension; lifecycle extension beyond proven jump/landing seam; synthetic carry velocity/inertia; fake gravity; manual floor/wall clamp; floor-only workaround; per-tick teleport/setPos chase; direct camera forcing/counter-rotation; jump/input timing production tuning; sprint/reverse/strafe tuning as reference-frame fix; global collider suppression; suppressing Create collision-response writer; duplicate Create/VS2 authority; fake/proxy VS2 ship; harness mutation to manufacture green; blind resolver prev/current/yaw/point changes; old `toLocalVector(...,0)` mismatch as current failure; temporal-only zero response as failure; patching `isDraggable`/`vs$shouldDrag`; adding/replacing body-position writer; Phase64 Y/grounding clip from code location; hardcoded carriage id/block/span/geometry; changing server `firstOrNull` fixture selector; post-release hypothetical camera rows as active mismatch; camera counter-rotation after exact active-turn proof.

## next_safe_action
1. Inspect only targeted run `35167683911` first. While queued/in_progress, HOLD and do not stack another patch.
2. If compose/compile/harness/verifier fails, diagnose exact proof-infra fault and repair proof infra only.
3. If runtime SUCCESS, classify exactly: `CEILING_NOT_EXERCISED` => observation only; `CEILING_CONTACT_OBSERVED_CORRELATION_INCOMPLETE` => read-only correlation only; `CEILING_CONTACT_CORRELATED` => inspect exact tick timeline before deciding whether any measured failure exists.
4. No gameplay patch without direct complete runtime failure evidence. Never patch walls from temporal-only rows.
5. No ceiling video before closure-ready data proof.
6. Protected/FROZEN regression => REVERT before workaround.
7. `FINAL_READY` forbidden until exact final JAR passes real-user actual Minecraft: no sinking, stable standing, forward/back/strafe/sprint, jump+natural landing, floor/wall/ceiling solidity, stable train movement/speed changes.
