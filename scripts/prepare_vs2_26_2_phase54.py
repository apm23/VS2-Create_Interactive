#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"

source = client_probe.read_text(encoding="utf-8")
old = '''                        StringBuilder frameApi = new StringBuilder();
                        for (java.lang.reflect.Method method : contraption.getClass().getMethods()) {'''
new = '''                        String anchorState = "unresolved";
                        try {
                            java.lang.reflect.Field anchorField = null;
                            Class<?> anchorOwner = contraption.getClass();
                            while (anchorOwner != null && anchorField == null) {
                                try {
                                    anchorField = anchorOwner.getDeclaredField("anchor");
                                } catch (NoSuchFieldException ignored) {
                                    anchorOwner = anchorOwner.getSuperclass();
                                }
                            }
                            if (anchorField != null) {
                                anchorField.setAccessible(true);
                                Object anchorValue = anchorField.get(contraption);
                                anchorState = String.valueOf(anchorValue);
                                if (anchorValue instanceof net.minecraft.core.BlockPos anchorPos) {
                                    double anchoredX = localFeet.x - anchorPos.getX();
                                    double anchoredY = localFeet.y - anchorPos.getY();
                                    double anchoredZ = localFeet.z - anchorPos.getZ();
                                    net.minecraft.core.BlockPos anchoredSupportPos = net.minecraft.core.BlockPos.containing(
                                        anchoredX, anchoredY - 0.05, anchoredZ);
                                    Object anchoredSupport = blocks.get(anchoredSupportPos);
                                    anchorState += ";local_minus_anchor=" + anchoredX + "," + anchoredY + "," + anchoredZ
                                        + ";anchored_support_pos=" + anchoredSupportPos.toShortString()
                                        + ";anchored_support_present=" + (anchoredSupport != null);
                                }
                            } else {
                                anchorState = "field_missing";
                            }
                        } catch (ReflectiveOperationException | RuntimeException exception) {
                            anchorState = "error=" + exception.getClass().getSimpleName();
                        }
                        StringBuilder frameApi = new StringBuilder();
                        for (java.lang.reflect.Method method : contraption.getClass().getMethods()) {'''
if old not in source:
    raise SystemExit("Phase 54 could not find frame API anchor")
source = source.replace(old, new, 1)

old2 = '''                            + ";block_bounds=" + minBlockX + "," + minBlockY + "," + minBlockZ + "->" + maxBlockX + "," + maxBlockY + "," + maxBlockZ
                            + ";frame_api=" + frameApi'''
new2 = '''                            + ";block_bounds=" + minBlockX + "," + minBlockY + "," + minBlockZ + "->" + maxBlockX + "," + maxBlockY + "," + maxBlockZ
                            + ";anchor_state=" + anchorState
                            + ";frame_api=" + frameApi'''
if old2 not in source:
    raise SystemExit("Phase 54 could not find frame state log anchor")
source = source.replace(old2, new2, 1)

client_probe.write_text(source, encoding="utf-8")
print("Phase 54: resolved Create Contraption.anchor and tested anchor-adjusted local support lookup; read-only telemetry only")

runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase55.py")), run_name="__main__")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase88.py")), run_name="__main__")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase99.py")), run_name="__main__")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase101.py")), run_name="__main__")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase102.py")), run_name="__main__")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase103.py")), run_name="__main__")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase133.py")), run_name="__main__")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase134.py")), run_name="__main__")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase135.py")), run_name="__main__")
runpy.run_path(str(Path(__file__).with_name("prepare_vs2_26_2_phase136.py")), run_name="__main__")
