# MASTER_STATE — VS2 / Create Interactive

GitHub code is the implementation source of truth. This file is the durable project-state ledger; chat is temporary.

## Hard contract
- Repository: `apm23/VS2-Create_Interactive`; milestone: `M1 — movement/collision`.
- Create owns train/carriage gameplay and collision geometry.
- VS2 is the continuous moving reference-space foundation for player body/render/camera through grounded, airborne, turns and speed changes; mouse/look remains free.
- Create floor/walls/ceiling remain authoritative solid geometry in that moving frame.
- Forbidden: fake gravity; synthetic carry velocity/inertia; manual floor/wall clamps; floor-only fixes; per-tick teleport/setPos chase/reanchor architecture; duplicate authority/state; direct camera forcing/counter-rotation; fake/proxy VS2 ships; workaround chains hiding double ownership.

## Current reconciliation — 2026-09-17
- `current_head`: `a2d9dfdbd2b363bc0443e2e69639e1cc2a1133fe` immediately before this ledger-only reconciliation commit.
- `a2d9dfdbd2b363bc0443e2e69639e1cc2a1133fe`: `Select and correlate natural ceiling overlap` — proof selection/correlation only. A pristine attempt becomes the winner only after unchanged native jump naturally reaches `ceiling_head_gap <= 0`; overlap ticks now report collide/setPos correlation even if no ceiling OBB normal is emitted. No gameplay, input, save, fixture, train, collision, camera, ownership, geometry, or physics mutation.
- Previous natural-overhead selector HEAD: `8b989700f99af99a160992d8801711d8cad4b853`.
- Latest gameplay implementation remains `9aea12a6114198c33c70d52897eb9d3c29342425` (`Refresh jump owner from exact Create grounded carry contact`).
- Active blocker: `CEILING`.
- Project state: `CAMERA_DATA_PROVEN_VISUAL_INCONCLUSIVE_MEDIA_PENDING_USER_AUDIT; CEILING_NATURAL_OVERLAP_CORRELATION_PROOF_IN_PROGRESS`.
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

## Ceiling proof — natural overlap correlation in progress
- Read-only files: `scripts/prepare_vs2_26_2_ceiling_contact_trace.py`, `.github/workflows/m1-ceiling-contact-runtime-proof.yml`.
- First run `35167469407` on HEAD `61122b80e8e07416af01232e6ac290109f5bf9b2` FAILED in compose only: `ceiling trace could not find LocalPlayer setPos marker`.
- Repair `82766397300abee3a71b2b2fab5e346ee6fd38fd` made GateE/collide/setPos tick anchors idempotent; proof infra only.
- Run `35167683911` then failed because the unchanged native-input sequence did not reach native jump on that launch; this was observation/harness availability, not ceiling gameplay failure.
- Commit `36ef9a4e12908fb9c384cfc9724a66838aa10675` retried identical pristine launches without changing input sequence, fixture geometry, train route/timing, or gameplay. Targeted run `35168785447` SUCCESS and reached native jump.
- Commit `5cec40cc0f417b834209a9a5940cf6086de67790` added read-only inventory of EXISTING simplified-collider floor/ceiling clearances; no player relocation, geometry mutation, fixture selection, input timing, collision, or physics change.
- Targeted run `35169937364` on exact HEAD `5cec40cc0f417b834209a9a5940cf6086de67790` SUCCESS. Exact classifier: `CEILING_NOT_EXERCISED`; native airborne tick `62`; rise `+0.333199994`; `obb_rows=128`; `ceiling_normal_rows=0`; `finite_overhead_rows=29`; nearest observed overhead tick `58`, local feet `(-6.6981282294422755,2.0630680924316422,2.193405150489639)`, ceiling bottom `4.0`, head gap `0.136931955`. No gameplay patch authorized.
- Commit `f5640f368734b7b3eed017dc47db42f72d5dcee1` moved inventory sampling to the first ready player/carriage observation; telemetry only.
- Targeted run `35172916766` on exact HEAD `f5640f368734b7b3eed017dc47db42f72d5dcee1` SUCCESS; artifact `10476979722`, digest `sha256:b04716cf0cdd488761426b08d0ae47768d27a3cb6e39f3ffd27d1b7409b24957`.
- That run naturally reached native jump on pristine attempt 3: airborne tick `69`, rise `+0.333199994`. Existing-geometry inventory observed a 2.0-block floor/ceiling clearance without moving player or changing fixture geometry.
- On that naturally successful attempt, exact Create-frame overhead geometry showed head overlap at apex: tick73 `ceiling_head_gap=-0.049287131060964384`; tick74 `ceiling_head_gap=-0.05230339257001049`. Geometric overlap alone is not gameplay failure evidence.
- Commit `a56feb3c8498dc73fd96275de4aa833887834aa1` extended only CI OBB observation from 128 to 256 calls.
- Targeted run `35174843637` on exact HEAD `a56feb3c8498dc73fd96275de4aa833887834aa1` SUCCESS; artifact `10478157982`, digest `sha256:184bd7717e2e54d9cd694c496b8fc3199a5944e1376190800a092a28fd9f5f1e`. Its winning pristine launch reached native jump (`airborne_tick=49`) but had `finite_overhead_rows=0`, so classifier remained `CEILING_NOT_EXERCISED`. No gameplay patch authorized.
- Commit `8b989700f99af99a160992d8801711d8cad4b853` changed proof selection so a pristine attempt won only after unchanged native jump plus finite Create-frame overhead were naturally observed. This remained proof-only.
- Run `35175493622` on exact HEAD `8b989700f99af99a160992d8801711d8cad4b853` was rerun four times because observation is stochastic. Attempt 2 reached native jump with finite overhead but nearest gap remained about `+1.199899948`; no contact. Attempt 3 did not reach native jump. Attempt 4 SUCCESS artifact `10479646032`, digest `sha256:7fc389c3cd1aad4c903b39da44fade54649b7ac21774875d071e20acb02a39ac`: airborne tick `49`, rise `+0.333199994`, `obb_rows=188`, `ceiling_normal_rows=0`, `finite_overhead_rows=28`, nearest tick `52`, ceiling bottom `5.0`, head gap `+0.113351687`; classifier `CEILING_NOT_EXERCISED`. These runs do not authorize gameplay changes.
- The finite-overhead selector was still too permissive because it stopped on ceilings that were merely nearby. Commit `a2d9dfdbd2b363bc0443e2e69639e1cc2a1133fe` now selects only a naturally reached geometric overlap (`ceiling_head_gap <= 0`) and prints exact overlap tick collide/Create-setPos correlation even when no downward ceiling normal is emitted.
- Relevant targeted workflow now: `m1-ceiling-contact-runtime-proof`, run `35178003561`, exact proof HEAD `a2d9dfdbd2b363bc0443e2e69639e1cc2a1133fe`; `in_progress` at this reconciliation.
- Ignore unrelated generic workflow noise while this targeted proof runs.
- Pristine r0v3 save SHA256 `e78bfb854a0f3ad0bfb87ded836ef322335812d303e51223825f3741f7232556`.
- Required timeline: tick; exact Create `worldToLocalPos` local position/overhead geometry; OBB normal; collisionResponse; surfaceCollision; temporalResponse; requested/allowed collide; tick-bearing final Create setPos writer.
- Classifiers:
  - `CEILING_NOT_EXERCISED` => no gameplay patch; observation/selection only.
  - `CEILING_CONTACT_OBSERVED_CORRELATION_INCOMPLETE` => read-only correlation follow-up only.
  - `CEILING_CONTACT_CORRELATED` => inspect exact timeline before any gameplay conclusion.
- Compile/harness/verifier/telemetry-window/selection failures authorize proof-infra repair only.
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
1. Inspect only targeted run `35178003561` first. While queued/in_progress, HOLD and do not stack another patch.
2. If it naturally reaches `ceiling_head_gap <= 0`, inspect the exact overlap ticks for OBB normal, surfaceCollision, temporalResponse, collisionResponse, requested/allowed collide, and final Create setPos writer. The overlap correlation emitted by `a2d9dfdb...` is the authoritative next evidence.
3. If all pristine launches lack native jump plus geometric overlap, keep `CEILING_NOT_EXERCISED`; do not patch gameplay. Any follow-up remains observation/selection only.
4. Geometric head overlap by itself does not authorize a gameplay patch. Only complete current-frame runtime evidence proving missing/incorrect Create ceiling response authorizes the smallest gameplay/root correction.
5. Never patch walls from temporal-only rows. No ceiling video before closure-ready data proof.
6. Protected/FROZEN regression => REVERT before workaround.
7. `FINAL_READY` forbidden until exact final JAR passes real-user actual Minecraft: no sinking, stable standing, forward/back/strafe/sprint, jump+natural landing, floor/wall/ceiling solidity, stable train movement/speed changes.
