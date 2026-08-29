#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Run 81 proved Create can establish a real local-player surface contact when the
# CI fixture approaches the simplified collider with normal downward motion.
# Measure the next thing directly: once contact is established, retain a client
# baseline and compare LocalPlayer displacement with carriage displacement after
# the automatic train starts moving. This is observation only.
field_anchor = '''    private static boolean fixtureColliderNormalized;\n'''
field_insert = '''    private static boolean fixtureColliderNormalized;\n    private static boolean carryBaselineCaptured;\n    private static boolean carryDeltaReported;\n    private static double carryPlayerX;\n    private static double carryPlayerY;\n    private static double carryPlayerZ;\n    private static double carryCarriageX;\n    private static double carryCarriageY;\n    private static double carryCarriageZ;\n'''
if "carryBaselineCaptured" not in source:
    if field_anchor not in source:
        raise SystemExit("Phase 71 could not find Gate E fixture field anchor")
    source = source.replace(field_anchor, field_insert, 1)

log_anchor = '''            LOGGER.info(\n                "GATE_E_CLIENT_STATE'''
telemetry = '''            if (!carryBaselineCaptured && createRegisteredContact && player.onGround()) {\n                carryBaselineCaptured = true;\n                carryPlayerX = player.getX();\n                carryPlayerY = player.getY();\n                carryPlayerZ = player.getZ();\n                carryCarriageX = carriage.getX();\n                carryCarriageY = carriage.getY();\n                carryCarriageZ = carriage.getZ();\n                LOGGER.info(\n                    "GATE_E_CLIENT_CARRY_BASELINE player={},{},{} carriage={},{},{} contact={} on_ground={}",\n                    carryPlayerX, carryPlayerY, carryPlayerZ,\n                    carryCarriageX, carryCarriageY, carryCarriageZ,\n                    createRegisteredContact, player.onGround());\n            } else if (carryBaselineCaptured && !carryDeltaReported) {\n                double carriageDx = carriage.getX() - carryCarriageX;\n                double carriageDy = carriage.getY() - carryCarriageY;\n                double carriageDz = carriage.getZ() - carryCarriageZ;\n                double carriageD2 = carriageDx * carriageDx + carriageDy * carriageDy + carriageDz * carriageDz;\n                if (carriageD2 > 0.01) {\n                    double playerDx = player.getX() - carryPlayerX;\n                    double playerDy = player.getY() - carryPlayerY;\n                    double playerDz = player.getZ() - carryPlayerZ;\n                    double driftX = playerDx - carriageDx;\n                    double driftY = playerDy - carriageDy;\n                    double driftZ = playerDz - carriageDz;\n                    double driftD2 = driftX * driftX + driftY * driftY + driftZ * driftZ;\n                    carryDeltaReported = true;\n                    LOGGER.info(\n                        "GATE_E_CLIENT_CARRY_DELTA player_delta={},{},{} carriage_delta={},{},{} relative_drift={},{},{} drift_sq={} contact_now={} on_ground_now={}",\n                        playerDx, playerDy, playerDz,\n                        carriageDx, carriageDy, carriageDz,\n                        driftX, driftY, driftZ, driftD2,\n                        createRegisteredContact, player.onGround());\n                }\n            }\n\n            LOGGER.info(\n                "GATE_E_CLIENT_STATE'''
if "GATE_E_CLIENT_CARRY_DELTA" not in source:
    if log_anchor not in source:
        raise SystemExit("Phase 71 could not find Gate E client state log anchor")
    source = source.replace(log_anchor, telemetry, 1)

client_probe.write_text(source, encoding="utf-8")
print("Phase 71: captured the first real Create LocalPlayer contact baseline and logged client player-vs-carriage displacement after train motion to directly verify carry; read-only telemetry only")
