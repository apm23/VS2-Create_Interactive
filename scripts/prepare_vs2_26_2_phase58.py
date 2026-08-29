#!/usr/bin/env python3
import json
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
# Earlier 26.2 port phases isolate legacy Create compat Java sources. Keep this
# tiny new mixin in its own non-isolated package so Loom actually compiles it.
legacy_java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/compat/create/MixinContraptionColliderLocalPlayer.java"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinContraptionColliderLocalPlayer.java"
resources = ROOT / "fabric/src/main/resources"
fabric_mod = resources / "fabric.mod.json"
mixin_json = resources / "vs2-create-compat.mixins.json"

if legacy_java.exists():
    legacy_java.unlink()
java.parent.mkdir(parents=True, exist_ok=True)
java.write_text(r'''package org.valkyrienskies.mod.fabric.mixin.gatee;

import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Create Fly 26.2 currently classifies every Player as SERVER inside
 * ContraptionCollider#getPlayerType, so the local client player is skipped before
 * collision resolution. Override only the actual LocalPlayer on the client.
 */
@Mixin(targets = "com.zurrtum.create.content.contraptions.ContraptionCollider", remap = false)
public abstract class MixinContraptionColliderLocalPlayer {
    @Inject(method = "getPlayerType", at = @At("HEAD"), cancellable = true, remap = false)
    private static void vs2$createLocalPlayerType(Entity entity, CallbackInfoReturnable<Object> cir) {
        if (!"net.minecraft.client.player.LocalPlayer".equals(entity.getClass().getName())) return;
        try {
            Class<?> playerType = Class.forName(
                "com.zurrtum.create.content.contraptions.ContraptionCollider$PlayerType",
                false,
                entity.getClass().getClassLoader());
            Object[] constants = playerType.getEnumConstants();
            if (constants == null) return;
            for (Object constant : constants) {
                if ("CLIENT".equals(String.valueOf(constant))) {
                    cir.setReturnValue(constant);
                    return;
                }
            }
        } catch (ClassNotFoundException ignored) {
            // Create absent: target mixin is client-gated and this path is never used.
        }
    }
}
''', encoding="utf-8")

mixin_json.write_text(json.dumps({
    "required": False,
    "minVersion": "0.8",
    "package": "org.valkyrienskies.mod.fabric.mixin.gatee",
    "compatibilityLevel": "JAVA_25",
    "client": ["MixinContraptionColliderLocalPlayer"],
    "injectors": {"defaultRequire": 1}
}, indent=2) + "\n", encoding="utf-8")

metadata = json.loads(fabric_mod.read_text(encoding="utf-8"))
mixins = metadata.setdefault("mixins", [])
entry = {"config": "vs2-create-compat.mixins.json", "environment": "client"}
if entry not in mixins:
    mixins.append(entry)
fabric_mod.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

print("Phase 58: compat fix maps Create Fly LocalPlayer to PlayerType.CLIENT from non-isolated gatee mixin package; no forced movement/teleport/carry logic")

# The player-type fix is now runtime-proven. Continue with read-only geometry proof
# so we can distinguish a real collision failure from a smoke fixture whose saved
# player is not physically standing on any carriage block.
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase59.py")), run_name="__main__")
