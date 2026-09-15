#!/usr/bin/env python3
from pathlib import Path

SOURCE = Path(__file__).with_name("prepare_vs2_26_2_reference_owner_v2.py")
text = SOURCE.read_text(encoding="utf-8")

old = '''    replay_start = probe.find('            if (false && carryBaselineCaptured', phase83_marker)\n    if gate_start < 0 or replay_start < 0:\n        raise SystemExit("reference-owner v2 could not bound historical Phase83 bridge")\n    probe = probe[:gate_start] + ''' + "'''            // REFERENCE_OWNER_V2: historical Phase83 lease/reanchor authority removed.\n            // Native Create contact acquires the generalized owner above; VS2 EntityDragger owns continuity.\n\n'''" + ''' + probe[replay_start:]\n'''

new = r'''    if gate_start < 0:
        raise SystemExit("reference-owner v2 could not bound historical Phase83 bridge")

    def find_java_block_end(source: str, statement_start: int) -> int:
        open_brace = source.find('{', statement_start)
        if open_brace < 0:
            raise SystemExit("reference-owner v2 historical Phase83 gate has no opening brace")
        depth = 0
        i = open_brace
        state = "normal"
        while i < len(source):
            c = source[i]
            n = source[i + 1] if i + 1 < len(source) else ""
            if state == "normal":
                if c == '"':
                    state = "string"
                elif c == "'":
                    state = "char"
                elif c == '/' and n == '/':
                    state = "line_comment"
                    i += 1
                elif c == '/' and n == '*':
                    state = "block_comment"
                    i += 1
                elif c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0:
                        return i + 1
            elif state == "string":
                if c == '\\':
                    i += 1
                elif c == '"':
                    state = "normal"
            elif state == "char":
                if c == '\\':
                    i += 1
                elif c == "'":
                    state = "normal"
            elif state == "line_comment":
                if c == '\n':
                    state = "normal"
            elif state == "block_comment":
                if c == '*' and n == '/':
                    state = "normal"
                    i += 1
            i += 1
        raise SystemExit("reference-owner v2 historical Phase83 gate has no matching closing brace")

    gate_end = find_java_block_end(probe, gate_start)
    if not (gate_start < phase83_marker < gate_end):
        raise SystemExit("reference-owner v2 Phase83 marker escaped selected historical gate")
    probe = probe[:gate_start] + ''' + "'''            // REFERENCE_OWNER_V2: historical Phase83 lease/reanchor authority removed.\n            // Native Create contact acquires the generalized owner above; VS2 EntityDragger owns continuity.\n\n'''" + ''' + probe[gate_end:]
'''

if old not in text:
    raise SystemExit("composefix could not find the exact V2 Phase83 boundary block")
patched = text.replace(old, new, 1)
compile(patched, str(SOURCE), "exec")
exec(compile(patched, str(SOURCE), "exec"), {"__name__": "__main__", "__file__": str(SOURCE)})
