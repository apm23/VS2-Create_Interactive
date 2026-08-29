#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Runs 13-14 proved sustained production carry, but every sampled client.hitResult
# remained a BlockHitResult MISS whose miss point simply advanced with the carried
# player. Before attempting any right-click or placement mutation, make the smoke
# camera deterministic: while the independently named productionSmokeFixture is
# enabled, point the LocalPlayer straight down during successful carry ticks. This
# changes only smoke-test view orientation; it does not alter position, velocity,
# train state, collision response, inventory, or perform an interaction.
anchor = '''                                if (productionSmoke && explicitCarryCompat && client.hitResult != null) {
                                    net.minecraft.world.phys.HitResult interactionHit = client.hitResult;'''
replacement = '''                                if (productionSmoke && explicitCarryCompat && client.hitResult != null) {
                                    if (productionSmokeFixture) {
                                        player.setXRot(90.0F);
                                        LOGGER.info(
                                            "GATE_F_INTERACTION_AIM_FIXTURE carriage_id={} player_tick={} pitch={}",
                                            carriage.getId(), player.tickCount, player.getXRot());
                                    }
                                    net.minecraft.world.phys.HitResult interactionHit = client.hitResult;'''

if "GATE_F_INTERACTION_AIM_FIXTURE" not in source:
    if anchor not in source:
        raise SystemExit("Phase 88 could not find Phase 87 interaction-target anchor")
    source = source.replace(anchor, replacement, 1)

required = [
    'GATE_F_INTERACTION_AIM_FIXTURE',
    'player.setXRot(90.0F)',
    'productionSmokeFixture',
    'GATE_F_INTERACTION_TARGET',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 88 lost deterministic interaction-aim anchors: " + ", ".join(missing))

client_probe.write_text(source, encoding="utf-8")
print("Phase 88: aimed production smoke camera straight down during sustained carry; view-fixture telemetry only, no interaction mutation")

# Phase 89 must run after Phase 88 because it distinguishes the same-callback view
# assignment from a later carry callback where Minecraft has had a frame to refresh
# client.hitResult. Keep this chained from the production smoke's existing script
# sequence without widening any gameplay behavior.
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase89.py")), run_name="__main__")
