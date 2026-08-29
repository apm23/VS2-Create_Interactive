#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Run 81 proved Create can establish a real local-player surface contact when the
# CI fixture approaches the simplified collider with normal downward motion.
# Measure the next thing directly: once contact is established, retain a client
# baseline and compare LocalPlayer displacement with carriage displacement after
# the automatic train starts moving. This is observation only.
#
# Production-world #59 exposed a telemetry flaw rather than a gameplay result:
# the baseline was captured on carriage id 8, then support legitimately handed off
# to sibling carriage id 10. Comparing id 10's entity position against id 8's
# baseline produced a meaningless 13.69-block "drift" even while contact and
# on-ground remained true and Create-filtered carry replays were succeeding.
# Track the baseline carriage id and rebase observation whenever physical support
# hands off to another carriage entity. No player/train/physics state is changed.
field_anchor = '''    private static boolean fixtureColliderNormalized;\n'''
field_insert = '''    private static boolean fixtureColliderNormalized;\n    private static boolean carryBaselineCaptured;\n    private static boolean carryDeltaReported;\n    private static int carryBaselineCarriageId = Integer.MIN_VALUE;\n    private static double carryPlayerX;\n    private static double carryPlayerY;\n    private static double carryPlayerZ;\n    private static double carryCarriageX;\n    private static double carryCarriageY;\n    private static double carryCarriageZ;\n'''
if "carryBaselineCaptured" not in source:
    if field_anchor not in source:
        raise SystemExit("Phase 71 could not find Gate E fixture field anchor")
    source = source.replace(field_anchor, field_insert, 1)
elif "carryBaselineCarriageId" not in source:
    old_fields = '''    private static boolean carryBaselineCaptured;\n    private static boolean carryDeltaReported;\n'''
    new_fields = '''    private static boolean carryBaselineCaptured;\n    private static boolean carryDeltaReported;\n    private static int carryBaselineCarriageId = Integer.MIN_VALUE;\n'''
    if old_fields not in source:
        raise SystemExit("Phase 71 could not find existing carry telemetry fields")
    source = source.replace(old_fields, new_fields, 1)

log_anchor = '''            LOGGER.info(\n                "GATE_E_CLIENT_STATE'''
telemetry = '''            if (!carryBaselineCaptured && createRegisteredContact && player.onGround()) {\n                carryBaselineCaptured = true;\n                carryBaselineCarriageId = carriage.getId();\n                carryPlayerX = player.getX();\n                carryPlayerY = player.getY();\n                carryPlayerZ = player.getZ();\n                carryCarriageX = carriage.getX();\n                carryCarriageY = carriage.getY();\n                carryCarriageZ = carriage.getZ();\n                LOGGER.info(\n                    "GATE_E_CLIENT_CARRY_BASELINE carriage_id={} player={},{},{} carriage={},{},{} contact={} on_ground={}",\n                    carryBaselineCarriageId, carryPlayerX, carryPlayerY, carryPlayerZ,\n                    carryCarriageX, carryCarriageY, carryCarriageZ,\n                    createRegisteredContact, player.onGround());\n            } else if (carryBaselineCaptured && !carryDeltaReported) {\n                if (carriage.getId() != carryBaselineCarriageId) {\n                    if (createRegisteredContact && player.onGround()) {\n                        LOGGER.info(\n                            "GATE_E_CLIENT_CARRY_REBASE previous_carriage_id={} current_carriage_id={} player_tick={} contact={} on_ground={}",\n                            carryBaselineCarriageId, carriage.getId(), player.tickCount,\n                            createRegisteredContact, player.onGround());\n                        carryBaselineCarriageId = carriage.getId();\n                        carryPlayerX = player.getX();\n                        carryPlayerY = player.getY();\n                        carryPlayerZ = player.getZ();\n                        carryCarriageX = carriage.getX();\n                        carryCarriageY = carriage.getY();\n                        carryCarriageZ = carriage.getZ();\n                    }\n                } else {\n                    double carriageDx = carriage.getX() - carryCarriageX;\n                    double carriageDy = carriage.getY() - carryCarriageY;\n                    double carriageDz = carriage.getZ() - carryCarriageZ;\n                    double carriageD2 = carriageDx * carriageDx + carriageDy * carriageDy + carriageDz * carriageDz;\n                    if (carriageD2 > 0.01) {\n                        double playerDx = player.getX() - carryPlayerX;\n                        double playerDy = player.getY() - carryPlayerY;\n                        double playerDz = player.getZ() - carryPlayerZ;\n                        double driftX = playerDx - carriageDx;\n                        double driftY = playerDy - carriageDy;\n                        double driftZ = playerDz - carriageDz;\n                        double driftD2 = driftX * driftX + driftY * driftY + driftZ * driftZ;\n                        carryDeltaReported = true;\n                        LOGGER.info(\n                            "GATE_E_CLIENT_CARRY_DELTA carriage_id={} player_delta={},{},{} carriage_delta={},{},{} relative_drift={},{},{} drift_sq={} contact_now={} on_ground_now={}",\n                            carryBaselineCarriageId, playerDx, playerDy, playerDz,\n                            carriageDx, carriageDy, carriageDz,\n                            driftX, driftY, driftZ, driftD2,\n                            createRegisteredContact, player.onGround());\n                    }\n                }\n            }\n\n            LOGGER.info(\n                "GATE_E_CLIENT_STATE'''
if "GATE_E_CLIENT_CARRY_DELTA" not in source:
    if log_anchor not in source:
        raise SystemExit("Phase 71 could not find Gate E client state log anchor")
    source = source.replace(log_anchor, telemetry, 1)
elif "GATE_E_CLIENT_CARRY_REBASE" not in source:
    old_start = source.index('            if (!carryBaselineCaptured && createRegisteredContact && player.onGround()) {')
    old_end = source.index('            LOGGER.info(\n                "GATE_E_CLIENT_STATE', old_start)
    source = source[:old_start] + telemetry[:-len('            LOGGER.info(\n                "GATE_E_CLIENT_STATE')] + source[old_end:]

required = [
    'carryBaselineCarriageId',
    'GATE_E_CLIENT_CARRY_REBASE',
    'carriage.getId() != carryBaselineCarriageId',
    'GATE_E_CLIENT_CARRY_DELTA carriage_id={}',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 71 lost carriage-aware telemetry anchors: " + ", ".join(missing))

client_probe.write_text(source, encoding="utf-8")
print("Phase 71: rebased read-only carry delta telemetry across sibling carriage handoff so drift is only measured within one carriage frame; no gameplay or physics mutation")

runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase72.py")), run_name="__main__")
