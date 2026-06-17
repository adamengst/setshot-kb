#!/usr/bin/env python3
"""
Validate settings-kb.json against the KBEntry schema expected by the Swift app.

Required non-optional fields (Swift Decodable will fail the entire array decode
if ANY entry is missing one of these):
  id, domain, key, source, value_type, noise, ai_generated

Run: python3 validate_kb.py
Exit code 0 = valid, 1 = errors found.
"""

import json
import sys

REQUIRED = {
    "id": str,
    "domain": str,
    "key": str,
    "source": str,
    "value_type": str,
    "noise": bool,
    "ai_generated": bool,
}

OPTIONAL_STRING = {"description", "ui_location", "settings_url", "noise_reason",
                   "min_macos", "notes", "key_prefix", "icon_bundle_id",
                   "implicit_default"}
OPTIONAL_INT = {"contributed_by_issue"}
OPTIONAL_DICT = {"value_map"}       # [String: String]
OPTIONAL_LIST = {"ui_location_overrides", "requires_hardware"}
ALL_KNOWN = set(REQUIRED) | OPTIONAL_STRING | OPTIONAL_INT | OPTIONAL_DICT | OPTIONAL_LIST

def validate():
    with open("settings-kb.json") as f:
        kb = json.load(f)

    if not isinstance(kb, list):
        print("ERROR: settings-kb.json is not a JSON array")
        return False

    errors = []
    seen_ids = {}

    for i, entry in enumerate(kb):
        loc = f"entry[{i}] domain={entry.get('domain','?')} key={entry.get('key','?')!r}"

        # Required fields
        for field, expected_type in REQUIRED.items():
            if field not in entry:
                errors.append(f"{loc}: missing required field '{field}'")
            elif not isinstance(entry[field], expected_type):
                errors.append(f"{loc}: '{field}' must be {expected_type.__name__}, got {type(entry[field]).__name__}")

        # Duplicate IDs
        eid = entry.get("id")
        if eid is not None:
            if eid in seen_ids:
                errors.append(f"{loc}: duplicate id '{eid}' (first seen at entry[{seen_ids[eid]}])")
            else:
                seen_ids[eid] = i

        # value_map must be dict[str, str]
        if "value_map" in entry and entry["value_map"] is not None:
            vm = entry["value_map"]
            if not isinstance(vm, dict):
                errors.append(f"{loc}: 'value_map' must be a dict")
            else:
                for k, v in vm.items():
                    if not isinstance(k, str) or not isinstance(v, str):
                        errors.append(f"{loc}: value_map keys and values must be strings, got {k!r}:{v!r}")

        # ui_location_overrides must be list of dicts with before_macos_major (int) and ui_location (str)
        if "ui_location_overrides" in entry and entry["ui_location_overrides"] is not None:
            overrides = entry["ui_location_overrides"]
            if not isinstance(overrides, list):
                errors.append(f"{loc}: 'ui_location_overrides' must be an array")
            else:
                for j, ov in enumerate(overrides):
                    if not isinstance(ov.get("before_macos_major"), int):
                        errors.append(f"{loc}: override[{j}] 'before_macos_major' must be an int")
                    if not isinstance(ov.get("ui_location"), str):
                        errors.append(f"{loc}: override[{j}] 'ui_location' must be a string")

        # Unknown fields (warn, not error)
        unknown = set(entry) - ALL_KNOWN
        if unknown:
            errors.append(f"{loc}: unknown fields {sorted(unknown)} (will be ignored by decoder but check for typos)")

    if errors:
        print(f"VALIDATION FAILED: {len(errors)} error(s) in {len(kb)} entries\n")
        for e in errors:
            print(f"  {e}")
        return False

    print(f"OK: {len(kb)} entries validated")
    return True

if __name__ == "__main__":
    sys.exit(0 if validate() else 1)
