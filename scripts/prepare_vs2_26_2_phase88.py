#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #162 proved the interaction pipeline may receive only one successful
# production carry callback. If the fixture first sets pitch inside that callback,
# Phase 89 sees the old pre-aim pitch and waits forever for a second carry callback.
# Pre-aim the test-only LocalPlayer at the start of the Gate E client tick instead, so
# any later carry callback in that tick already has deterministic downward orientation.
# This changes only productionSmokeFixture view orientation; no player position,
# velocity, collision, train, inventory, world state, or interaction dispatch changes.
preaim_anchor = '''            var player = client.player;\n'''
preaim = '''            if (productionSmokeFixture && client.player != null) {
                client.player.setXRot(90.0F);
                if (!java.lang.Boolean.getBoolean("vs2.productionInteractionPreAimApplied")) {
                    System.setProperty("vs2.productionInteractionPreAimApplied", "true");
                    LOGGER.info(
                        "GATE_F_INTERACTION_PREAIM_FIXTURE player_tick={} pitch={} view_only=true",
                        client.player.tickCount, client.player.getXRot());
                }
            }
            var player = client.player;
'''
if "GATE_F_INTERACTION_PREAIM_FIXTURE" not in source:
    if preaim_anchor not in source:
        raise SystemExit("Phase 88 could not find Gate E player tick anchor for fixture pre-aim")
    source = source.replace(preaim_anchor, preaim, 1)

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
    'GATE_F_INTERACTION_PREAIM_FIXTURE',
    'vs2.productionInteractionPreAimApplied',
    'GATE_F_INTERACTION_AIM_FIXTURE',
    'player.setXRot(90.0F)',
    'productionSmokeFixture',
    'GATE_F_INTERACTION_TARGET',
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 88 lost deterministic interaction-aim anchors: " + ", ".join(missing))

for forbidden in [
    'setPos(', 'setDeltaMovement(', 'setBlock(', '.useItemOn(', '.useItem(', '.attack(',
]:
    if forbidden in preaim:
        raise SystemExit("Phase 88 pre-aim fixture found forbidden gameplay mutation: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 88: pre-aims the production smoke view fixture before carry telemetry, then preserves the carry-time downward aim; no gameplay/physics mutation")

# Phase 89 runs after Phase 88 and can now treat even the first available carry callback
# as settled because its pre-aim pitch was established earlier in the client tick.
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase89.py")), run_name="__main__")
