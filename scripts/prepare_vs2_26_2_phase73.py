#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinEntityLocalPlayerMoveTrace.java"
resources = ROOT / "fabric/src/main/resources"
mixin_json = resources / "vs2-create-compat.mixins.json"

java.parent.mkdir(parents=True, exist_ok=True)
java.write_text(r'''package org.valkyrienskies.mod.fabric.mixin.gatee;

import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.phys.Vec3;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Run 84 showed no marker from a LocalPlayer-targeted move mixin even though the
 * player remained fixed while the carriage moved 5.66 blocks. Entity owns the
 * actual inherited move implementation, so instrument that exact method and
 * filter to the real LocalPlayer instance. Read-only telemetry only. */
@Mixin(Entity.class)
public abstract class MixinEntityLocalPlayerMoveTrace {
    @Unique private static final Logger VS2_GATE_E_ENTITY_MOVE_LOGGER = LogManager.getLogger("VS2-GateE-EntityMove");
    @Unique private static int vs2$localMoveCalls;
    @Unique private double vs2$beforeX;
    @Unique private double vs2$beforeY;
    @Unique private double vs2$beforeZ;
    @Unique private int vs2$currentIndex;

    @Inject(method = "move", at = @At("HEAD"), require = 0)
    private void vs2$beforeEntityMove(MoverType type, Vec3 requested, CallbackInfo ci) {
        Entity self = (Entity) (Object) this;
        if (!(self instanceof LocalPlayer)) return;
        String thread = Thread.currentThread().getName();
        if (!(thread.contains("Render") || thread.contains("Client"))) return;
        int index = ++vs2$localMoveCalls;
        vs2$currentIndex = index;
        if (index > 220) return;
        vs2$beforeX = self.getX();
        vs2$beforeY = self.getY();
        vs2$beforeZ = self.getZ();
        VS2_GATE_E_ENTITY_MOVE_LOGGER.info(
            "GATE_E_LOCALPLAYER_ENTITY_MOVE_HEAD index={} mover={} requested={},{},{} pos={},{},{} velocity={},{},{} on_ground={}",
            index, String.valueOf(type), requested.x, requested.y, requested.z,
            vs2$beforeX, vs2$beforeY, vs2$beforeZ,
            self.getDeltaMovement().x, self.getDeltaMovement().y, self.getDeltaMovement().z,
            self.onGround());
    }

    @Inject(method = "move", at = @At("RETURN"), require = 0)
    private void vs2$afterEntityMove(MoverType type, Vec3 requested, CallbackInfo ci) {
        Entity self = (Entity) (Object) this;
        if (!(self instanceof LocalPlayer)) return;
        int index = vs2$currentIndex;
        if (index <= 0 || index > 220) return;
        String thread = Thread.currentThread().getName();
        if (!(thread.contains("Render") || thread.contains("Client"))) return;
        VS2_GATE_E_ENTITY_MOVE_LOGGER.info(
            "GATE_E_LOCALPLAYER_ENTITY_MOVE_RETURN index={} mover={} requested={},{},{} actual={},{},{} pos={},{},{} velocity={},{},{} on_ground={}",
            index, String.valueOf(type), requested.x, requested.y, requested.z,
            self.getX() - vs2$beforeX, self.getY() - vs2$beforeY, self.getZ() - vs2$beforeZ,
            self.getX(), self.getY(), self.getZ(),
            self.getDeltaMovement().x, self.getDeltaMovement().y, self.getDeltaMovement().z,
            self.onGround());
    }
}
''', encoding="utf-8")

metadata = json.loads(mixin_json.read_text(encoding="utf-8"))
client = metadata.setdefault("client", [])
if "MixinEntityLocalPlayerMoveTrace" not in client:
    client.append("MixinEntityLocalPlayerMoveTrace")
mixin_json.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

print("Phase 73: traced the actual inherited Entity.move path for LocalPlayer so carriage-motion application can be observed directly after the confirmed Run 84 carry drift; read-only telemetry only")
