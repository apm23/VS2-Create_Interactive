#!/usr/bin/env python3
from pathlib import Path

SOURCE = Path(__file__).with_name("prepare_vs2_26_2_reference_owner_v2.py")
text = SOURCE.read_text(encoding="utf-8")

old = '''    replay_start = probe.find('            if (false && carryBaselineCaptured', phase83_marker)\n    if gate_start < 0 or replay_start < 0:\n        raise SystemExit("reference-owner v2 could not bound historical Phase83 bridge")\n    probe = probe[:gate_start] + ''' + "'''            // REFERENCE_OWNER_V2: historical Phase83 lease/reanchor authority removed.\n            // Native Create contact acquires the generalized owner above; VS2 EntityDragger owns continuity.\n\n'''" + ''' + probe[replay_start:]\n'''

new = r'''    if gate_start < 0:
        raise SystemExit("reference-owner v2 could not bound historical Phase83 bridge")

    def find_java_block_end(source: str, statement_start: int) -> int:
        open_brace = source.find('{', statement_start)
        if open_brace < 0:
            raise SystemExit("reference-owner v2 historical Phase83 gate has no opening brace")
        depth = 0
        i = open_brace
        state = "normal"
        while i < len(source):
            c = source[i]
            n = source[i + 1] if i + 1 < len(source) else ""
            if state == "normal":
                if c == '"':
                    state = "string"
                elif c == "'":
                    state = "char"
                elif c == '/' and n == '/':
                    state = "line_comment"
                    i += 1
                elif c == '/' and n == '*':
                    state = "block_comment"
                    i += 1
                elif c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0:
                        return i + 1
            elif state == "string":
                if c == '\\':
                    i += 1
                elif c == '"':
                    state = "normal"
            elif state == "char":
                if c == '\\':
                    i += 1
                elif c == "'":
                    state = "normal"
            elif state == "line_comment":
                if c == '\n':
                    state = "normal"
            elif state == "block_comment":
                if c == '*' and n == '/':
                    state = "normal"
                    i += 1
            i += 1
        raise SystemExit("reference-owner v2 historical Phase83 gate has no matching closing brace")

    gate_end = find_java_block_end(probe, gate_start)
    if not (gate_start < phase83_marker < gate_end):
        raise SystemExit("reference-owner v2 Phase83 marker escaped selected historical gate")
    probe = probe[:gate_start] + ''' + "'''            // REFERENCE_OWNER_V2: historical Phase83 lease/reanchor authority removed.\n            // Native Create contact acquires the generalized owner above; VS2 EntityDragger owns continuity.\n\n'''" + ''' + probe[gate_end:]
'''

if old not in text:
    raise SystemExit("composefix could not find the exact V2 Phase83 boundary block")
patched = text.replace(old, new, 1)

# Exact source-failure proof run 35062047086 over runtime artifact 35057564114 proves the first
# jump-lifecycle seam: false vanilla grounding can clear a valid external owner before Create has
# genuinely reacquired the carriage. Attempt3 owner-cap proof run 35071088843 proves the second seam:
# the ordinary 25-tick owner cap expires at tick68 while the same carriage's native Create landing is
# only reached at tick70, producing exactly 0.330086470 blocks of missed carriage-frame motion.
# Keep the ordinary external-owner cap unchanged, but give an already-armed native jump a bounded
# 40-tick safety window. As soon as the existing owner receives same-owner grounded native Create
# contact, refresh it back into the ordinary lifecycle. No movement vector, gravity, reanchor,
# collision override, transform change, camera mutation, or additional body writer is introduced.
old_state = '''    var ticksSinceExternalReferenceOwner: Int = 0
    var serverRelativeExternalPosition: Vector3dc? = null
'''
new_state = '''    var ticksSinceExternalReferenceOwner: Int = 0
    var externalReferenceOwnerJumpActive: Boolean = false
    var serverRelativeExternalPosition: Vector3dc? = null
'''
if patched.count(old_state) != 1:
    raise SystemExit(f"composefix expected one external-owner age state anchor, found {patched.count(old_state)}")
patched = patched.replace(old_state, new_state, 1)

old_drag_gate = '''    fun isEntityBeingDraggedByExternalReference(): Boolean {
        return externalReferenceOwnerEntityId != null &&
            ticksSinceExternalReferenceOwner < TICKS_TO_DRAG_ENTITIES && !mountedToEntity
    }
'''
new_drag_gate = '''    fun externalReferenceOwnerLifetimeLimit(): Int {
        return if (externalReferenceOwnerJumpActive) 40 else TICKS_TO_DRAG_ENTITIES
    }

    fun isEntityBeingDraggedByExternalReference(): Boolean {
        return externalReferenceOwnerEntityId != null &&
            ticksSinceExternalReferenceOwner < externalReferenceOwnerLifetimeLimit() && !mountedToEntity
    }
'''
if patched.count(old_drag_gate) != 1:
    raise SystemExit(f"composefix expected one external-owner drag gate, found {patched.count(old_drag_gate)}")
patched = patched.replace(old_drag_gate, new_drag_gate, 1)

old_refresh = '''    fun refreshExternalReferenceOwner(ownerEntityId: Int) {
        if (externalReferenceOwnerEntityId != ownerEntityId) {
            externalReferenceOwnerEntityId = ownerEntityId
        }
        ticksSinceExternalReferenceOwner = 0
    }
'''
new_refresh = '''    fun refreshExternalReferenceOwner(ownerEntityId: Int) {
        if (externalReferenceOwnerEntityId != ownerEntityId) {
            externalReferenceOwnerEntityId = ownerEntityId
        }
        ticksSinceExternalReferenceOwner = 0
        externalReferenceOwnerJumpActive = false
    }
'''
if patched.count(old_refresh) != 1:
    raise SystemExit(f"composefix expected one owner refresh function, found {patched.count(old_refresh)}")
patched = patched.replace(old_refresh, new_refresh, 1)

old_clear = '''    fun clearExternalReferenceOwner() {
        externalReferenceOwnerEntityId = null
        ticksSinceExternalReferenceOwner = 0
        serverRelativeExternalPosition = null
'''
new_clear = '''    fun clearExternalReferenceOwner() {
        externalReferenceOwnerEntityId = null
        ticksSinceExternalReferenceOwner = 0
        externalReferenceOwnerJumpActive = false
        serverRelativeExternalPosition = null
'''
if patched.count(old_clear) != 1:
    raise SystemExit(f"composefix expected one owner clear function, found {patched.count(old_clear)}")
patched = patched.replace(old_clear, new_clear, 1)

old_lifetime = '''                val groundedContactExpired = entity.onGround() && entityDraggingInformation.ticksSinceExternalReferenceOwner > 2
'''
new_lifetime = '''                val nativeUpwardMotion = entity.deltaMovement.y > 1.0E-5
                if (nativeUpwardMotion) {
                    entityDraggingInformation.externalReferenceOwnerJumpActive = true
                }
                val groundedContactExpired = entity.onGround() &&
                    !entityDraggingInformation.externalReferenceOwnerJumpActive &&
                    entityDraggingInformation.ticksSinceExternalReferenceOwner > 2
'''
if patched.count(old_lifetime) != 1:
    raise SystemExit(f"composefix expected one grounded lifecycle expiry predicate, found {patched.count(old_lifetime)}")
patched = patched.replace(old_lifetime, new_lifetime, 1)

old_owner_expiry = '''                val ownerExpired = entityDraggingInformation.ticksSinceExternalReferenceOwner >= EntityDraggingInformation.TICKS_TO_DRAG_ENTITIES
'''
new_owner_expiry = '''                val ownerExpired = entityDraggingInformation.ticksSinceExternalReferenceOwner >= entityDraggingInformation.externalReferenceOwnerLifetimeLimit()
'''
if patched.count(old_owner_expiry) != 1:
    raise SystemExit(f"composefix expected one owner-cap predicate, found {patched.count(old_owner_expiry)}")
patched = patched.replace(old_owner_expiry, new_owner_expiry, 1)

old_acquisition_tail = '''                LOGGER.info("REFERENCE_OWNER_V2_ACQUIRE player_tick={} carriage_id={} physical_support=true recent_native_contact=true owner_key=entity_id",
                    player.tickCount, carriage.getId());
            }

'''
new_acquisition_tail = '''                LOGGER.info("REFERENCE_OWNER_V2_ACQUIRE player_tick={} carriage_id={} physical_support=true recent_native_contact=true owner_key=entity_id",
                    player.tickCount, carriage.getId());
            }

            if (phase83ExactBaselineCarriage
                && !phase81PhysicalSupport
                && player.onGround()
                && phase83RecentNativeApplication) {
                org.valkyrienskies.mod.common.util.IEntityDraggingInformationProvider referenceProvider =
                    (org.valkyrienskies.mod.common.util.IEntityDraggingInformationProvider) (Object) player;
                Integer activeOwnerId = referenceProvider.getDraggingInformation().getExternalReferenceOwnerEntityId();
                boolean sameOwner = activeOwnerId != null && activeOwnerId == carriage.getId();
                boolean jumpLandingAfterOrdinaryCap = sameOwner
                    && referenceProvider.getDraggingInformation().getExternalReferenceOwnerJumpActive()
                    && referenceProvider.getDraggingInformation().getTicksSinceExternalReferenceOwner()
                        >= org.valkyrienskies.mod.common.util.EntityDraggingInformation.TICKS_TO_DRAG_ENTITIES;
                boolean settledSameOwnerNativeContact = sameOwner
                    && !referenceProvider.getDraggingInformation().getExternalReferenceOwnerJumpActive();
                if (jumpLandingAfterOrdinaryCap || settledSameOwnerNativeContact) {
                    referenceProvider.getDraggingInformation().refreshExternalReferenceOwner(carriage.getId());
                    LOGGER.info("REFERENCE_OWNER_V2_NATIVE_GROUNDED_REFRESH player_tick={} carriage_id={} jump_landing_after_ordinary_cap={} settled_same_owner_contact={} physical_support=false recent_native_contact=true owner_key=entity_id",
                        player.tickCount, carriage.getId(), jumpLandingAfterOrdinaryCap, settledSameOwnerNativeContact);
                }
            }

'''
if patched.count(old_acquisition_tail) != 1:
    raise SystemExit(f"composefix expected one strict acquisition tail, found {patched.count(old_acquisition_tail)}")
patched = patched.replace(old_acquisition_tail, new_acquisition_tail, 1)

for required in [
    "externalReferenceOwnerJumpActive: Boolean = false",
    "externalReferenceOwnerJumpActive = true",
    "externalReferenceOwnerLifetimeLimit(): Int",
    "if (externalReferenceOwnerJumpActive) 40 else TICKS_TO_DRAG_ENTITIES",
    "!entityDraggingInformation.externalReferenceOwnerJumpActive",
    "entityDraggingInformation.ticksSinceExternalReferenceOwner > 2",
    "entityDraggingInformation.externalReferenceOwnerLifetimeLimit()",
    "REFERENCE_OWNER_V2_NATIVE_GROUNDED_REFRESH",
    "jumpLandingAfterOrdinaryCap",
    "settledSameOwnerNativeContact",
]:
    if required not in patched:
        raise SystemExit("composefix lost jump-landing lifecycle anchor: " + required)

compile(patched, str(SOURCE), "exec")
exec(compile(patched, str(SOURCE), "exec"), {"__name__": "__main__", "__file__": str(SOURCE)})
