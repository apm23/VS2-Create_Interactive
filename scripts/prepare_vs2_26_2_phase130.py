#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Run #142 proved the carry gate is correctly failing because Phase81 physical support
# turns false while broadphase/onGround remain true. The Phase81 vertical gap becomes NaN,
# which only tells us its simplified-collider state stopped exposing xz_inside_any/gap.
# Expose that already-computed source string beside the existing support telemetry,
# read-only, before changing any carry/collision behavior. Later cumulative phases can
# rewrite the enclosing guard, so locate the support log structurally rather than pinning
# its exact if-condition text.
if "GATE_E_PHASE131_SUPPORT_SOURCE" not in source:
    marker = '"GATE_E_PHASE81_SUPPORT_CONTINUITY'
    marker_pos = source.find(marker)
    if marker_pos < 0:
        raise SystemExit("Phase 130 could not find Phase81 support log marker")

    search_start = max(0, marker_pos - 4000)
    prefix = source[search_start:marker_pos]
    candidates = list(re.finditer(r'(?m)^(?P<indent>[ \t]*)if \(', prefix))
    support_if_pos = None
    support_indent = None
    for candidate in reversed(candidates):
        absolute = search_start + candidate.start()
        segment = source[absolute:marker_pos]
        if "carryReplayGuardSamples" in segment and "LOGGER.info" in segment:
            support_if_pos = absolute
            support_indent = candidate.group("indent")
            break
    if support_if_pos is None or support_indent is None:
        raise SystemExit("Phase 130 could not locate structural Phase81 support log guard")

    probe = (
        f'{support_indent}if (productionSmokeFixture && fixtureContactAcquireTicks >= 12\n'
        f'{support_indent}        && player.tickCount >= 14 && player.tickCount <= 40) {{\n'
        f'{support_indent}    LOGGER.info(\n'
        f'{support_indent}        "GATE_E_PHASE131_SUPPORT_SOURCE player_tick={{}} carriage_id={{}} physical_support={{}} vertical_gap={{}} simplified_state={{}} read_only=true",\n'
        f'{support_indent}        player.tickCount, carriage.getId(), phase81PhysicalSupport, phase81VerticalGap, simplifiedColliderState);\n'
        f'{support_indent}    int productionSmokeSupportLossTicks;\n'
        f'{support_indent}    try {{\n'
        f'{support_indent}        productionSmokeSupportLossTicks = Integer.parseInt(System.getProperty("vs2.productionSmokeSupportLossTicks", "0"));\n'
        f'{support_indent}    }} catch (NumberFormatException ignored) {{\n'
        f'{support_indent}        productionSmokeSupportLossTicks = 0;\n'
        f'{support_indent}    }}\n'
        f'{support_indent}    productionSmokeSupportLossTicks = phase81PhysicalSupport ? 0 : productionSmokeSupportLossTicks + 1;\n'
        f'{support_indent}    System.setProperty("vs2.productionSmokeSupportLossTicks", Integer.toString(productionSmokeSupportLossTicks));\n'
        f'{support_indent}    LOGGER.info(\n'
        f'{support_indent}        "GATE_E_PHASE131_SUPPORT_STREAK player_tick={{}} carriage_id={{}} physical_support={{}} consecutive_loss_ticks={{}} broadphase={{}} on_ground={{}} fixture_only=true",\n'
        f'{support_indent}        player.tickCount, carriage.getId(), phase81PhysicalSupport, productionSmokeSupportLossTicks, broadphaseOverlap, player.onGround());\n'
        f'{support_indent}    if (productionSmokeSupportLossTicks >= 3 && broadphaseOverlap && player.onGround()) {{\n'
        f'{support_indent}        throw new IllegalStateException("Production smoke rejected unsupported carriage-local carry continuity after "\n'
        f'{support_indent}            + productionSmokeSupportLossTicks + " consecutive ticks");\n'
        f'{support_indent}    }}\n'
        f'{support_indent}}}\n\n'
    )
    source = source[:support_if_pos] + probe + source[support_if_pos:]

# Production-world #164 now proves a real Create-native empty-hand right-click dispatch
# (handled=true) and authoritative new-cell placement replication in the same run. Keep
# the next step observational: remember only the entity id used by that confirmed native
# dispatch, then compare it with the exact carriage id whose new STONE cell reached the
# client. This prevents future smoke success from combining interaction on one sibling
# carriage with placement replication on another. No item, block, player, train, or
# physics state is changed by this correlation telemetry.
if "vs2.productionNativeRightClickCarriageId" not in source:
    confirmed_anchor = '''                                                    if (Boolean.TRUE.equals(handled)) {\n                                                        LOGGER.info(\n                                                            "GATE_F_NATIVE_RIGHT_CLICK_CONFIRMED carriage_id={} player_tick={} handled=true target_source=create_native_ray_settled",'''
    confirmed_replacement = '''                                                    if (Boolean.TRUE.equals(handled)) {\n                                                        System.setProperty("vs2.productionNativeRightClickCarriageId", Integer.toString(carriage.getId()));\n                                                        LOGGER.info(\n                                                            "GATE_F_NATIVE_RIGHT_CLICK_CONFIRMED carriage_id={} player_tick={} handled=true target_source=create_native_ray_settled",'''
    if confirmed_anchor not in source:
        raise SystemExit("Phase 130 could not find confirmed native right-click anchor")
    source = source.replace(confirmed_anchor, confirmed_replacement, 1)

if "GATE_F_INTERACTION_PLACEMENT_CARRIAGE_CORRELATION" not in source:
    exact_sync_anchor = '''                            System.setProperty("vs2.productionNativePlacementClientObserved", "true");\n                            System.setProperty("vs2.productionNativePlacementExactClientObserved", "true");\n                            LOGGER.info(\n                                "GATE_F_NATIVE_PLACEMENT_CLIENT_EXACT_SYNC carriage_id={} player_tick={} empty_local={} entity_present={} entry_present={} state={} synced=true read_only=true",'''
    exact_sync_replacement = '''                            System.setProperty("vs2.productionNativePlacementClientObserved", "true");\n                            System.setProperty("vs2.productionNativePlacementExactClientObserved", "true");\n                            String nativeRightClickCarriageIdText = System.getProperty("vs2.productionNativeRightClickCarriageId");\n                            boolean interactionPlacementSameCarriage = nativeRightClickCarriageIdText != null\n                                && nativeRightClickCarriageIdText.equals(Integer.toString(exactCarriageId));\n                            LOGGER.info(\n                                "GATE_F_INTERACTION_PLACEMENT_CARRIAGE_CORRELATION interaction_carriage_id={} placement_carriage_id={} same_carriage={} read_only=true",\n                                nativeRightClickCarriageIdText, exactCarriageId, interactionPlacementSameCarriage);\n                            if (productionSmokeFixture && nativeRightClickCarriageIdText != null && !interactionPlacementSameCarriage) {\n                                throw new IllegalStateException("Production smoke interaction/placement carriage mismatch: interaction="\n                                    + nativeRightClickCarriageIdText + " placement=" + exactCarriageId);\n                            }\n                            LOGGER.info(\n                                "GATE_F_NATIVE_PLACEMENT_CLIENT_EXACT_SYNC carriage_id={} player_tick={} empty_local={} entity_present={} entry_present={} state={} synced=true read_only=true",'''
    if exact_sync_anchor not in source:
        raise SystemExit("Phase 130 could not find exact placement sync anchor")
    source = source.replace(exact_sync_anchor, exact_sync_replacement, 1)

required = [
    'GATE_E_PHASE131_SUPPORT_SOURCE',
    'GATE_E_PHASE131_SUPPORT_STREAK',
    'vs2.productionSmokeSupportLossTicks',
    'Production smoke rejected unsupported carriage-local carry continuity',
    'simplified_state={}',
    'phase81PhysicalSupport',
    'phase81VerticalGap',
    'simplifiedColliderState',
    'vs2.productionNativeRightClickCarriageId',
    'GATE_F_INTERACTION_PLACEMENT_CARRIAGE_CORRELATION',
    'interactionPlacementSameCarriage',
    'Production smoke interaction/placement carriage mismatch',
    'read_only=true',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 130 lost support/correlation telemetry: " + ", ".join(missing))

for forbidden in ['setBlock(', 'setPos(', 'setDeltaMovement(', '.useItemOn(', '.useItem(', '.attack(']:
    if forbidden in exact_sync_replacement if 'exact_sync_replacement' in locals() else False:
        raise SystemExit("Phase 130 correlation telemetry found forbidden mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 130: rejects unsupported production-smoke carry false positives and enforces same-carriage confirmed native interaction/placement correlation; production carry unchanged")
