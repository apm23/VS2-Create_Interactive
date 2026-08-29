#!/usr/bin/env python3
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinLocalPlayerMoveTrace.java"
resources = ROOT / "fabric/src/main/resources"
mixin_json = resources / "vs2-create-compat.mixins.json"

java.parent.mkdir(parents=True, exist_ok=True)
java.write_text(r'''package org.valkyrienskies.mod.fabric.mixin.gatee;

import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.phys.Vec3;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Read-only client movement-path telemetry. Run 84 proved that Create establishes
 * contact, then the carriage moves while LocalPlayer remains fixed. Trace whether
 * any horizontal carriage-like move is ever applied to LocalPlayer. */
@Mixin(LocalPlayer.class)
public abstract class MixinLocalPlayerMoveTrace {
    @Unique private static final Logger VS2_GATE_E_MOVE_LOGGER = LogManager.getLogger("VS2-GateE-Move");
    @Unique private static int vs2$moveCalls;
    @Unique private double vs2$beforeX;
    @Unique private double vs2$beforeY;
    @Unique private double vs2$beforeZ;
    @Unique private int vs2$currentIndex;

    @Inject(method = "move", at = @At("HEAD"), require = 0)
    private void vs2$beforeMove(MoverType type, Vec3 requested, CallbackInfo ci) {
        String thread = Thread.currentThread().getName();
        if (!(thread.contains("Render") || thread.contains("Client"))) return;
        int index = ++vs2$moveCalls;
        vs2$currentIndex = index;
        if (index > 160) return;
        LocalPlayer self = (LocalPlayer) (Object) this;
        vs2$beforeX = self.getX();
        vs2$beforeY = self.getY();
        vs2$beforeZ = self.getZ();
        VS2_GATE_E_MOVE_LOGGER.info(
            "GATE_E_LOCALPLAYER_MOVE_HEAD index={} mover={} requested={},{},{} pos={},{},{} on_ground={}",
            index, String.valueOf(type), requested.x, requested.y, requested.z,
            vs2$beforeX, vs2$beforeY, vs2$beforeZ, self.onGround());
    }

    @Inject(method = "move", at = @At("RETURN"), require = 0)
    private void vs2$afterMove(MoverType type, Vec3 requested, CallbackInfo ci) {
        int index = vs2$currentIndex;
        if (index <= 0 || index > 160) return;
        String thread = Thread.currentThread().getName();
        if (!(thread.contains("Render") || thread.contains("Client"))) return;
        LocalPlayer self = (LocalPlayer) (Object) this;
        double dx = self.getX() - vs2$beforeX;
        double dy = self.getY() - vs2$beforeY;
        double dz = self.getZ() - vs2$beforeZ;
        VS2_GATE_E_MOVE_LOGGER.info(
            "GATE_E_LOCALPLAYER_MOVE_RETURN index={} mover={} requested={},{},{} actual={},{},{} pos={},{},{} on_ground={}",
            index, String.valueOf(type), requested.x, requested.y, requested.z,
            dx, dy, dz, self.getX(), self.getY(), self.getZ(), self.onGround());
    }
}
''', encoding="utf-8")

metadata = json.loads(mixin_json.read_text(encoding="utf-8"))
client = metadata.setdefault("client", [])
if "MixinLocalPlayerMoveTrace" not in client:
    client.append("MixinLocalPlayerMoveTrace")
mixin_json.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

print("Phase 72: attempted LocalPlayer-local move tracing with require=0; Phase 73 now instruments Entity.move, which owns the inherited implementation")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase73.py")), run_name="__main__")
