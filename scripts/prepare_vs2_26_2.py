#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / "upstream"

# The 1.21.11 fork carries CRLF in its Gradle launcher. Normalize scripts first so
# Linux CI executes the exact pinned checkout reliably.
for relative in ("gradlew", "gradle/wrapper/gradle-wrapper.properties"):
    p = ROOT / relative
    p.write_bytes(p.read_bytes().replace(b"\r\n", b"\n"))


def replace(path: str, old: str, new: str):
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"Expected text not found in {path}: {old!r}")
    p.write_text(text.replace(old, new), encoding="utf-8")


def regex(path: str, pattern: str, replacement: str, flags=0):
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    new, count = re.subn(pattern, replacement, text, flags=flags)
    if count == 0:
        raise SystemExit(f"Pattern not found in {path}: {pattern!r}")
    p.write_text(new, encoding="utf-8")

# Loom 1.17.x projects targeting MC 26.2 use modern Gradle 9.x. 9.7.0 is pinned
# from a known-good 26.2 Architectury Loom project and supports Java 25.
replace("gradle/wrapper/gradle-wrapper.properties", "gradle-8.11-all.zip", "gradle-9.7.0-all.zip")

# Core target/toolchain.
replace("gradle.properties", "minecraft_version=1.21.11", "minecraft_version=26.2")
replace("gradle.properties", "archives_base_name=valkyrienskies-1-21-11", "archives_base_name=valkyrienskies-26-2")
replace("gradle.properties", "architectury_version=19.0.1", "architectury_version=21.0.7")
replace("gradle.properties", "fabric_loader_version=0.18.6", "fabric_loader_version=0.19.3")
replace("gradle.properties", "fabric_api_version=0.141.4+1.21.11", "fabric_api_version=0.158.0+26.2")
replace("gradle.properties", "fcap_version = 21.11.1", "fcap_version = 26.2.1")

# Architectury tooling compatible with the 26.x unobfuscated era.
replace("build.gradle", 'id "architectury-plugin" version "3.4.161"', 'id "architectury-plugin" version "3.5.169"')
replace("build.gradle", 'id "dev.architectury.loom" version "1.14.473" apply false', 'id "dev.architectury.loom" version "1.17.483" apply false')
replace("build.gradle", 'id "org.jetbrains.kotlin.jvm" version "2.0.0" apply false', 'id "org.jetbrains.kotlin.jvm" version "2.4.10" apply false')

# Minecraft 26.2 runs on Java 25. Ensure both Java and Kotlin target it.
insert_marker = 'allprojects {\n    apply plugin: "java"'
p = ROOT / "build.gradle"
text = p.read_text(encoding="utf-8")
if insert_marker not in text:
    raise SystemExit("allprojects marker not found")
text = text.replace(insert_marker, 'allprojects {\n    apply plugin: "java"\n\n    java {\n        sourceCompatibility = JavaVersion.VERSION_25\n        targetCompatibility = JavaVersion.VERSION_25\n    }\n\n    tasks.withType(JavaCompile).configureEach {\n        options.release = 25\n    }')
p.write_text(text, encoding="utf-8")

# Fabric Language Kotlin compatible with current loader/toolchain.
replace("fabric/gradle.properties", "kotlin_fabric_version=1.13.1+kotlin.2.1.10", "kotlin_fabric_version=1.13.13+kotlin.2.4.10")

# Remove stale manual Sodium compile jar and old optional mod compile deps from the first core-physics port.
for file in ("common/build.gradle", "fabric/build.gradle"):
    p = ROOT / file
    text = p.read_text(encoding="utf-8")
    text = re.sub(r'^\s*modCompileOnly\(files\("\$rootDir/libs/sodium-fabric-0\.8\.11-loompatched\.jar"\)\)\s*$', '    // 26.2 core-port: Sodium compat disabled until core physics builds cleanly.', text, flags=re.M)
    p.write_text(text, encoding="utf-8")

# Exclude all third-party mod compatibility in the first 26.2 compile pass, including Sodium/Voxy/Iris.
p = ROOT / "common/build.gradle"
text = p.read_text(encoding="utf-8")
text = re.sub(
    r'exclude \{\s*it\.path\.contains\("/mixin/mod_compat/"\).*?\n\s*\}',
    'exclude { it.path.contains("/mixin/mod_compat/") }',
    text,
    flags=re.S,
)
# Disable compile-only third-party deps known to target older MC versions. Core VS2 does not need these.
patterns = [
    r'^\s*modCompileOnly\("maven\.modrinth:alexs-caves:.*$',
    r'^\s*modCompileOnly\("curse\.maven:weather-storms-tornadoes-.*$',
    r'^\s*modCompileOnly\("maven\.modrinth:tis3d:.*$',
    r'^\s*modCompileOnly\("maven\.modrinth:dynmap:.*$',
    r'^\s*modCompileOnly\("curse\.maven:entity-model-features-.*$',
    r'^\s*modCompileOnly\("curse\.maven:entity-texture-features-fabric-.*$',
    r'^\s*modCompileOnly\("com\.simibubi\.create:create-fabric:.*$',
    r'^\s*\{ exclude group:.*fakeconfigtoml.*$',
    r'^\s*modCompileOnly\("curse\.maven:vanillin-.*$',
    r'^\s*modCompileOnly\("maven\.modrinth:create-utilities:.*$',
    r'^\s*modCompileOnly\("curse\.maven:vmp-fabric-.*$',
    r'^\s*modCompileOnly\("curse\.maven:bluemap-.*$',
    r'^\s*modCompileOnly\("com\.github\.iPortalTeam:ImmersivePortalsMod:.*$',
]
for pattern in patterns:
    text = re.sub(pattern, lambda m: '    // 26.2 core-port disabled: ' + m.group(0).strip(), text, flags=re.M)
p.write_text(text, encoding="utf-8")

# Fabric-side optional compatibility deps.
p = ROOT / "fabric/build.gradle"
text = p.read_text(encoding="utf-8")
for pattern in [
    r'^\s*modCompileOnly\("maven\.modrinth:create-utilities:.*$',
    r'^\s*modCompileOnly\("maven\.modrinth:cc-tweaked:.*$',
    r'^\s*modCompileOnly\("maven\.modrinth:entity-model-features:.*$',
    r'^\s*modCompileOnly\("maven\.modrinth:entitytexturefeatures:.*$',
    r'^\s*modCompileOnly\("curse\.maven:forge-config-api-port-fabric-.*$',
    r'^\s*modCompileOnly\("com\.jamieswhiteshirt:reach-entity-attributes:.*$',
    r'^\s*modCompileOnly\("dev\.cafeteria:fake-player-api:.*$',
    r'^\s*modCompileOnly\("com\.github\.iPortalTeam:ImmersivePortalsMod:.*$',
    r'^\s*modCompileOnly\("maven\.modrinth:dynmap:.*$',
    r'^\s*modCompileOnly\("curse\.maven:connectiblechains-.*$',
]:
    text = re.sub(pattern, lambda m: '    // 26.2 core-port disabled: ' + m.group(0).strip(), text, flags=re.M)
p.write_text(text, encoding="utf-8")

# Disable Sodium/Voxy/Iris compatibility source on Fabric as well.
p = ROOT / "fabric/build.gradle"
text = p.read_text(encoding="utf-8")
needle = 'java {\n            exclude "org/valkyrienskies/mod/fabric/mixin/compat/hexcasting/**"'
if needle not in text:
    raise SystemExit("fabric sourceSets marker not found")
text = text.replace(needle, 'java {\n            exclude "org/valkyrienskies/mod/fabric/mixin/compat/**"')
p.write_text(text, encoding="utf-8")

# Keep Kotlin compiler aligned with Java 25.
p = ROOT / "build.gradle"
text = p.read_text(encoding="utf-8")
marker = '    kotlin {\n        compilerOptions {'
if marker in text:
    text = text.replace(marker, '    kotlin {\n        jvmToolchain(25)\n        compilerOptions {')
p.write_text(text, encoding="utf-8")

print("Prepared pinned VS2 1.21.11 source for first Minecraft 26.2 core compile pass")
