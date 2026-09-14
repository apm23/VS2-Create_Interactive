#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
contact_trace = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinAbstractContraptionEntityContactTrace.java"
source = contact_trace.read_text(encoding="utf-8")

# Direct user runtime evidence reopened M1 floor/support despite automated GREEN. Phase170 only
# publishes its native-application marker when Create's returned contact motion is > 1e-8, which
# means a real ContraptionColliderClient invocation with zero/near-zero motion is invisible at the
# exact stable-standing/support boundary we now need to distinguish. Add read-only per-carriage,
# per-player-tick telemetry before that non-zero filter. Do not publish/modify Phase170 ownership
# properties and do not alter motion, position, velocity, collision, lease, gravity, or train state.
anchor = '''        net.minecraft.client.player.LocalPlayer phase170Player = net.minecraft.client.Minecraft.getInstance().player;
        if (phase170NativeClientColliderCall && phase170Player != null && motion.lengthSqr() > 1.0E-8) {'''
replacement = '''        net.minecraft.client.player.LocalPlayer phase170Player = net.minecraft.client.Minecraft.getInstance().player;
        if (phase170NativeClientColliderCall && phase170Player != null) {
            String phase204TraceTickKey = "vs2.phase204NativeSupportTraceTick." + self.getId();
            String phase204PlayerTick = Integer.toString(phase170Player.tickCount);
            if (!phase204PlayerTick.equals(System.getProperty(phase204TraceTickKey))) {
                System.setProperty(phase204TraceTickKey, phase204PlayerTick);
                net.minecraft.world.phys.AABB phase204PlayerBox = phase170Player.getBoundingBox();
                boolean phase204CarriageOverlap = self.getBoundingBox().inflate(0.5).intersects(phase204PlayerBox);
                LOGGER.info(
                    "GATE_E_PHASE204_NATIVE_SUPPORT_BOUNDARY player_tick={} carriage_id={} native_create_call=true motion={} motion_sq={} zero_or_near_zero={} on_ground={} player_y={} bb_min_y={} delta={} carriage_overlap={} read_only=true",
                    phase170Player.tickCount, self.getId(), motion, motion.lengthSqr(), motion.lengthSqr() <= 1.0E-8,
                    phase170Player.onGround(), phase170Player.getY(), phase204PlayerBox.minY,
                    phase170Player.getDeltaMovement(), phase204CarriageOverlap);
            }
        }
        if (phase170NativeClientColliderCall && phase170Player != null && motion.lengthSqr() > 1.0E-8) {'''

if "GATE_E_PHASE204_NATIVE_SUPPORT_BOUNDARY" not in source:
    if source.count(anchor) != 1:
        raise SystemExit("Phase 204 expected exactly one Phase170 native-contact application boundary")
    source = source.replace(anchor, replacement, 1)

required = [
    "GATE_E_PHASE204_NATIVE_SUPPORT_BOUNDARY",
    "native_create_call=true",
    "zero_or_near_zero={}",
    "motion.lengthSqr() <= 1.0E-8",
    "phase170Player.onGround()",
    "phase204PlayerBox.minY",
    "phase170Player.getDeltaMovement()",
    "phase204CarriageOverlap",
    "read_only=true",
    "phase170NativeClientColliderCall && phase170Player != null && motion.lengthSqr() > 1.0E-8",
    "vs2.phase170NativeContactApplicationTick",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 204 lost native support-boundary telemetry anchors: " + ", ".join(missing))

inserted = replacement
for forbidden in [
    "player.setPos(", "phase170Player.setPos(", "setDeltaMovement(", ".move(", ".teleport(",
    "setBlock(", "setVelocity(", "syncCarriage(", "cir.setReturnValue(", "method.invoke(lease",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 204 introduced forbidden gameplay mutation: " + forbidden)

contact_trace.write_text(source, encoding="utf-8")
print("Phase 204: traces zero/non-zero native Create support-boundary calls read-only; Phase170 ownership publication remains unchanged")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase205.py")), run_name="__main__")
