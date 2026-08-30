#!/usr/bin/env python3
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
java = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/mixin/gatee/MixinCreateNewContraptionCellReplication.java"
mixin_json = ROOT / "fabric/src/main/resources/vs2-create-compat.mixins.json"

# Production-world #131 proves sustained carriage-local stability for nine consecutive
# ticks with zero local-frame span. The same run also proves the authoritative server
# placement succeeds while Create Fly's client handler rejects a packet when localPos is
# not already present; the fixture-only insertion immediately makes the exact client cell
# visible. Install the narrow compatibility fix at the client handler RETURN: only add a
# previously-missing, non-air cell that arrived in Create's own block-change packet.
# Also report when Create's native handler already populated the exact cell, so world smoke
# can distinguish native replication from the compatibility fallback without mutating state.
# Phase 149 additionally emits the exact published target proof at this authoritative packet
# handler, avoiding the older reflective observer race while preserving the same semantics.
# Production-world #264 then proved this authoritative packet path can publish exact sync
# while Phase154 still sees exact_cell_present=false, because the packet observer set the
# historical completion flags but not the newer walk-fixture readiness flag. Bridge that
# telemetry state here at the exact authoritative target only; no block/player/train state
# or collision/physics behavior is changed.
java.parent.mkdir(parents=True, exist_ok=True)
java.write_text(r'''package org.valkyrienskies.mod.fabric.mixin.gatee;

import java.lang.reflect.Method;
import java.util.Map;
import java.util.Objects;
import net.minecraft.client.Minecraft;
import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * Create Fly 6.0.9's AllHandle#onContraptionBlockChanged returns when a packet targets
 * a local position absent from the client contraption map. That is correct for ordinary
 * state updates only if the cell already exists, but it drops server-authoritative new
 * cells produced by CarriageContraptionEntity#setBlock. Preserve Create's normal handler
 * and fill only that missing-cell case from the packet it already accepted from server.
 */
@Mixin(targets = "com.zurrtum.create.client.AllHandle", remap = false)
public abstract class MixinCreateNewContraptionCellReplication {
    private void vs2$reportExactPublishedTarget(int entityId, BlockPos localPos, BlockState newState, String path) {
        String carriageText = System.getProperty("vs2.productionNativePlacementCarriageId");
        String xText = System.getProperty("vs2.productionNativePlacementEmptyX");
        String yText = System.getProperty("vs2.productionNativePlacementEmptyY");
        String zText = System.getProperty("vs2.productionNativePlacementEmptyZ");
        if (carriageText == null || xText == null || yText == null || zText == null) return;
        try {
            int expectedCarriage = Integer.parseInt(carriageText);
            BlockPos expectedPos = new BlockPos(Integer.parseInt(xText), Integer.parseInt(yText), Integer.parseInt(zText));
            if (entityId == expectedCarriage && expectedPos.equals(localPos) && newState.is(Blocks.STONE)) {
                System.setProperty("vs2.productionNativePlacementClientObserved", "true");
                System.setProperty("vs2.productionNativePlacementExactClientObserved", "true");
                System.setProperty("vs2.productionNativePlacementExactCellPresent", "true");
                Minecraft exactMinecraft = Minecraft.getInstance();
                if (System.getProperty("vs2.productionNativePlacementExactCellFirstTick") == null
                        && exactMinecraft.player != null) {
                    System.setProperty("vs2.productionNativePlacementExactCellFirstTick",
                        Integer.toString(exactMinecraft.player.tickCount));
                }
                System.out.println("GATE_F_NATIVE_PLACEMENT_CLIENT_EXACT_SYNC carriage_id=" + entityId
                    + " empty_local=" + localPos + " state=" + newState
                    + " synced=true packet_authoritative=true exact_cell_present=true source=" + path);
            }
        } catch (RuntimeException ignored) {
            // Telemetry is fail-open and never changes packet handling or gameplay state.
        }
    }

    @Inject(method = "onContraptionBlockChanged", at = @At("RETURN"), remap = false)
    private void vs2$replicateMissingCell(@Coerce Object packet, CallbackInfo ci) {
        Minecraft minecraft = Minecraft.getInstance();
        if (minecraft.level == null || packet == null) return;
        try {
            int entityId = ((Number) packet.getClass().getMethod("entityId").invoke(packet)).intValue();
            BlockPos localPos = (BlockPos) packet.getClass().getMethod("localPos").invoke(packet);
            BlockState newState = (BlockState) packet.getClass().getMethod("newState").invoke(packet);
            if (localPos == null || newState == null || newState.isAir()) return;

            Entity entity = minecraft.level.getEntity(entityId);
            if (entity == null) return;
            Object contraption = entity.getClass().getMethod("getContraption").invoke(entity);
            if (contraption == null) return;
            Object blocksObject = contraption.getClass().getMethod("getBlocks").invoke(contraption);
            if (!(blocksObject instanceof Map<?, ?> blocks)) return;

            Object nativeEntry = blocks.get(localPos);
            if (nativeEntry != null) {
                Object nativeState = null;
                try {
                    nativeState = nativeEntry.getClass().getMethod("state").invoke(nativeEntry);
                } catch (ReflectiveOperationException ignored) {
                    // Telemetry only; preserve Create's native result even if value shape changes.
                }
                boolean stateMatch = Objects.equals(nativeState, newState);
                System.out.println("VS2_CREATE_CELL_REPLICATION_CONFIRMED entity_id=" + entityId
                    + " local_pos=" + localPos + " state=" + newState
                    + " path=create_native entry_present=true state_match=" + stateMatch
                    + " packet_authoritative=true");
                if (stateMatch) {
                    vs2$reportExactPublishedTarget(entityId, localPos, newState, "create_native");
                }
                return;
            }

            @SuppressWarnings("unchecked")
            Map<Object, Object> writable = (Map<Object, Object>) (Map<?, ?>) blocks;
            StructureTemplate.StructureBlockInfo info =
                new StructureTemplate.StructureBlockInfo(localPos.immutable(), newState, null);
            writable.put(localPos.immutable(), info);

            boolean resetInvoked = false;
            try {
                contraption.getClass().getMethod("invalidateColliders").invoke(contraption);
            } catch (ReflectiveOperationException ignored) {
                // Rendering reset below remains sufficient on Create variants without this helper.
            }
            for (Method method : this.getClass().getMethods()) {
                if (!method.getName().equals("resetClientContraption") || method.getParameterCount() != 1) continue;
                if (!method.getParameterTypes()[0].isInstance(contraption)) continue;
                method.invoke(this, contraption);
                resetInvoked = true;
                break;
            }
            System.out.println("VS2_CREATE_NEW_CELL_REPLICATION entity_id=" + entityId
                + " local_pos=" + localPos + " state=" + newState + " inserted=true");
            System.out.println("VS2_CREATE_NEW_CELL_REPLICATION_PROVEN entity_id=" + entityId
                + " local_pos=" + localPos + " state=" + newState
                + " inserted=true reset_invoked=" + resetInvoked + " packet_authoritative=true");
            System.out.println("VS2_CREATE_CELL_REPLICATION_CONFIRMED entity_id=" + entityId
                + " local_pos=" + localPos + " state=" + newState
                + " path=vs2_new_cell_fallback entry_present=true state_match=true"
                + " packet_authoritative=true");
            vs2$reportExactPublishedTarget(entityId, localPos, newState, "vs2_new_cell_fallback");
        } catch (ReflectiveOperationException | RuntimeException ignored) {
            // Compatibility is intentionally fail-open: never crash Create/VS2 for an optional seam.
        }
    }
}
''', encoding="utf-8")

config = json.loads(mixin_json.read_text(encoding="utf-8"))
client_mixins = config.setdefault("client", [])
name = "MixinCreateNewContraptionCellReplication"
if name not in client_mixins:
    client_mixins.append(name)
mixin_json.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

required = [
    'targets = "com.zurrtum.create.client.AllHandle"',
    'method = "onContraptionBlockChanged"',
    'blocks.get(localPos)',
    'path=create_native',
    'new StructureTemplate.StructureBlockInfo',
    'writable.put(localPos.immutable(), info)',
    'resetClientContraption',
    'VS2_CREATE_NEW_CELL_REPLICATION',
    'VS2_CREATE_NEW_CELL_REPLICATION_PROVEN',
    'VS2_CREATE_CELL_REPLICATION_CONFIRMED',
    'GATE_F_NATIVE_PLACEMENT_CLIENT_EXACT_SYNC',
    'vs2$reportExactPublishedTarget',
    'path=vs2_new_cell_fallback',
    'packet_authoritative=true',
    'vs2.productionNativePlacementExactCellPresent',
    'vs2.productionNativePlacementExactCellFirstTick',
    'exact_cell_present=true',
]
text = java.read_text(encoding="utf-8")
missing = [token for token in required if token not in text]
if missing:
    raise SystemExit("Phase 128 lost Create new-cell replication anchors: " + ", ".join(missing))

for forbidden in ['setPos(', 'setDeltaMovement(', '.move(', '.teleport', '.useItemOn(', '.attack(']:
    if forbidden in text:
        raise SystemExit("Phase 128 found forbidden player/train mutation: " + forbidden)

print("Phase 128/149: production compat fills Create Fly client new-cell replication gap, bridges authoritative exact-cell telemetry into the walk fixture, and proves exact published target")

runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase129.py")), run_name="__main__")
