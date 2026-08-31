#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "upstream"
client_probe = ROOT / "fabric/src/main/java/org/valkyrienskies/mod/fabric/client/GateEClientProbe.java"
source = client_probe.read_text(encoding="utf-8")

# Production-world #418 proved carry/support/placement are stable through the bounded walk window,
# but the fixture's keyUp=true pulse never produces horizontal LocalPlayer velocity or carriage-local
# displacement. Phase192 only printed primitive Input fields; Minecraft 26.2 KeyboardInput now keeps
# sampled movement state in object-valued inherited fields, so that diagnostic was incomplete.
# Expand the existing read-only input snapshot to include every non-static field value/type across the
# input class hierarchy. This diagnoses the harness sampling boundary only; it does not synthesize input,
# move the player, alter Create carry/collision, or mutate train/world/VS2 state.
old = '''                                                        phase192InputBuilder.append(';')
                                                            .append(phase192InputClass.getSimpleName()).append('.')
                                                            .append(phase192Field.getName()).append('=')
                                                            .append(String.valueOf(phase192Field.get(phase192Input)));'''
new = '''                                                        phase192InputBuilder.append(';')
                                                            .append(phase192InputClass.getSimpleName()).append('.')
                                                            .append(phase192Field.getName()).append('=')
                                                            .append(String.valueOf(phase192Field.get(phase192Input)));
                                                    } else if (!java.lang.reflect.Modifier.isStatic(phase192Field.getModifiers())) {
                                                        phase192Field.setAccessible(true);
                                                        Object phase195Value = phase192Field.get(phase192Input);
                                                        phase192InputBuilder.append(';')
                                                            .append(phase192InputClass.getSimpleName()).append('.')
                                                            .append(phase192Field.getName()).append('[')
                                                            .append(phase192Type.getName()).append("]=")
                                                            .append(String.valueOf(phase195Value));'''
if "phase195Value" not in source:
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"Phase 195 expected one Phase192 primitive input field append, found {count}")
    source = source.replace(old, new, 1)

required = [
    "GATE_E_PHASE192_LOCAL_INPUT",
    "phase195Value",
    "java.lang.reflect.Modifier.isStatic",
    "phase192Type.getName()",
    "phase192InputClass.getSuperclass()",
    "client.options.keyUp.isDown()",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("Phase 195 lost input-payload diagnostic anchors: " + ", ".join(missing))

inserted = new
for forbidden in [
    "player.setPos(", "player.setDeltaMovement(", "player.move(", ".teleport(",
    "setBlock(", "setSchedule(", "setTrain(", "setVelocity(", "syncCarriage(",
    "cir.setReturnValue(", "setDown(",
]:
    if forbidden in inserted:
        raise SystemExit("Phase 195 introduced forbidden mutation token: " + forbidden)

client_probe.write_text(source, encoding="utf-8")
print("Phase 195: traces object-valued sampled KeyboardInput payload during bounded walk; read-only only")
