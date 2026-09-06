"""Static consistency audit. Not shipped; run manually before releasing."""

from __future__ import annotations

import ast
import builtins
import importlib.util
import json
import pathlib
import re
from collections import Counter

HERE = pathlib.Path(__file__).resolve().parent.parent / "custom_components" / "ypsilon_local"
PLATFORMS = {
    "sensor.py": "sensor",
    "binary_sensor.py": "binary_sensor",
    "number.py": "number",
    "switch.py": "switch",
    "button.py": "button",
    "time.py": "time",
}


def read(name: str) -> str:
    return (HERE / name).read_text()


def undefined_names(tree: ast.AST) -> set[str]:
    """Names loaded but never bound in the module.

    Deliberately simple: it only needs to catch a missing import, which is the
    failure mode that silently ships and then raises at runtime.
    """
    defined: set[str] = set(dir(builtins)) | {"__name__", "__file__", "self", "cls"}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                defined.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(node.name)
        elif isinstance(node, ast.TypeAlias) and isinstance(node.name, ast.Name):
            defined.add(node.name.id)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                defined |= {n.id for n in ast.walk(target) if isinstance(n, ast.Name)}
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            defined.add(node.target.id)
        elif isinstance(node, ast.arg):
            defined.add(node.arg)
        elif isinstance(node, (ast.For, ast.AsyncFor, ast.comprehension)):
            defined |= {n.id for n in ast.walk(node.target) if isinstance(n, ast.Name)}
        elif isinstance(node, ast.ExceptHandler) and node.name:
            defined.add(node.name)
        elif isinstance(node, ast.withitem) and node.optional_vars:
            defined |= {
                n.id for n in ast.walk(node.optional_vars) if isinstance(n, ast.Name)
            }
        elif isinstance(node, ast.Global):
            defined |= set(node.names)
    used = {
        n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
    }
    return used - defined


def protocol_src() -> str:
    return read("protocol.py")


def load_protocol_module():
    """Load protocol.py without importing Home Assistant."""
    path = HERE / "protocol.py"
    spec = importlib.util.spec_from_file_location("ypsilon_protocol_audit", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load protocol module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit_protocol_regressions() -> list[str]:
    """Run protocol regression checks offline, without Home Assistant installed."""
    issues: list[str] = []

    try:
        protocol = load_protocol_module()
    except Exception as err:  # noqa: BLE001
        return [f"PROTOCOL load failed: {err}"]

    def check(name: str, fn) -> None:
        try:
            fn()
        except Exception as err:  # noqa: BLE001
            issues.append(f"PROTOCOL {name}: {err}")

    def require(condition: bool, message: str) -> None:
        if not condition:
            raise AssertionError(message)

    def query_frame_is_valid() -> None:
        frame = protocol.build_query([1, 34, 52])
        protocol.validate_frame(frame)
        require(frame[:2] == b"\x5a\x5c", f"unexpected prefix {frame[:2].hex()}")

    def write_encodings_match_legacy_codec() -> None:
        require(protocol.encode_field(43, 50) == [43, 50, 0], "field 43 encoding")
        require(protocol.encode_field(47, 400) == [47, 0x90, 0x01], "field 47 encoding")
        require(protocol.encode_field(7, 200) == [7, 0x00, 0xC8], "field 7 encoding")
        require(protocol.encode_field(10, (2, 30)) == [10, 2, 30], "field 10 encoding")

    def multi_field_write_uses_one_control_frame() -> None:
        frame = protocol.build_write_fields({43: 50, 49: 1})
        protocol.validate_frame(frame)
        inner = protocol._inner_frame(frame)
        require(inner[3] == protocol.WRITE_CODE, f"unexpected opcode {inner[3]}")
        require(inner[4:-2] == bytes([43, 50, 0, 49, 1, 0]), f"unexpected payload {inner[4:-2].hex()}")

    def u16_and_field52_decode_little_endian() -> None:
        decoded = protocol.decode_tlvs({47: (0x90, 0x01), 52: (0x68, 0x01)})
        require(decoded["rawWaterHardness"] == 400, "rawWaterHardness != 400")
        require(decoded["filterMaterialWorkingDay"] == 360, "filterMaterialWorkingDay != 360")

    def flow_family_decode_is_big_endian_raw() -> None:
        decoded = protocol.decode_tlvs({7: (0x03, 0xE8), 11: (0x00, 0x0E)})
        require(decoded["flowRateOff"] == 1000, "flowRateOff != 1000")
        require(decoded["flowRate"] == 14, "flowRate != 14")
        require(decoded["_raw_flowRate"] == 14, "_raw_flowRate != 14")

    def volume_requires_continuation() -> None:
        decoded = protocol.decode_tlvs({35: (0, 1)})
        require(decoded["residualWaterProduction"] is None, "volume decoded without continuation")

    def volume_pair_reconstruction() -> None:
        # Production formula: next_high + next_low*100 + high*10000.
        decoded = protocol.decode_tlvs({35: (0, 1), 36: (59, 0)})
        require(decoded["residualWaterProduction"] == 159.0, "volume reconstruction != 159.0")

    def time_validation() -> None:
        good = protocol.decode_tlvs({4: (23, 59)})
        bad = protocol.decode_tlvs({4: (25, 70)})
        require(good["currentTime"] == "23:59:00", "valid time decoded incorrectly")
        require(bad["currentTime"] is None, "invalid time was accepted")

    def reminder_flags_split_low_and_high_bytes() -> None:
        decoded = protocol.decode_tlvs({33: (1, 0)})
        require(decoded["saltShortageReminder"] is True, "salt reminder low byte not decoded")
        require(decoded["filterMaterialReminder"] is False, "filter reminder high byte not decoded")

    def invalid_checksum_is_rejected() -> None:
        frame = bytearray(protocol.build_query([1]))
        frame[-2] ^= 0x01
        try:
            protocol.validate_frame(bytes(frame))
        except protocol.F79DProtocolError:
            return
        raise AssertionError("invalid checksum was accepted")

    checks = (
        ("query frame", query_frame_is_valid),
        ("write encodings", write_encodings_match_legacy_codec),
        ("multi-field write", multi_field_write_uses_one_control_frame),
        ("u16/field52 decode", u16_and_field52_decode_little_endian),
        ("flow-family decode", flow_family_decode_is_big_endian_raw),
        ("volume continuation", volume_requires_continuation),
        ("volume reconstruction", volume_pair_reconstruction),
        ("time validation", time_validation),
        ("reminder flags", reminder_flags_split_low_and_high_bytes),
        ("checksum rejection", invalid_checksum_is_rejected),
    )
    for name, fn in checks:
        check(name, fn)

    return issues


def audit() -> list[str]:
    issues: list[str] = []
    issues.extend(audit_protocol_regressions())

    # Public repository/HACS packaging invariants. Account-specific placeholders
    # are checked separately by publication_check.py so the source template can
    # still be audited before the maintainer configures their GitHub username.
    repo_root = HERE.parent.parent
    required_repo_files = (
        "LICENSE", "NOTICE", "README.md", "CHANGELOG.md", "CONTRIBUTING.md",
        "SECURITY.md", "LEGAL.md", "THIRD_PARTY.md", "hacs.json",
        ".github/workflows/validate.yml", ".github/workflows/hassfest.yml",
        ".github/workflows/audit.yml", ".github/workflows/release.yml",
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        "scripts/configure_repository.py", "scripts/publication_check.py",
    )
    for relative in required_repo_files:
        if not (repo_root / relative).exists():
            issues.append(f"missing publication file: {relative}")
    brand_icon = HERE / "brand" / "icon.png"
    if not brand_icon.exists():
        issues.append("missing custom integration brand/icon.png")
    hacs_data = json.loads((repo_root / "hacs.json").read_text())
    if set(hacs_data) != {"name"}:
        issues.append(f"hacs.json should be minimal; found keys {sorted(hacs_data)}")
    if hacs_data.get("name") != "Ypsilon":
        issues.append("hacs.json name must be Ypsilon")
    manifest_data = json.loads((HERE / "manifest.json").read_text())
    if manifest_data.get("version") != "2.3.0":
        issues.append(f"manifest version is {manifest_data.get('version')}, expected 2.3.0")
    if manifest_data.get("name") != "Ypsilon":
        issues.append("manifest display name must be Ypsilon")

    for path in HERE.rglob("*.py"):
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError as err:
            issues.append(f"SYNTAX {path.name}: {err}")
            continue
        missing = sorted(undefined_names(tree))
        if missing:
            issues.append(f"{path.name}: undefined names {missing}")
    for path in HERE.rglob("*.json"):
        try:
            json.loads(path.read_text())
        except Exception as err:  # noqa: BLE001
            issues.append(f"JSON {path.name}: {err}")

    sensors = read("sensor.py")
    binaries = read("binary_sensor.py")

    # Custom components load translations/<lang>.json directly in current HA;
    # strings.json is a Core build-time input and would be misleading here.
    if (HERE / "strings.json").exists():
        issues.append("custom component must not ship strings.json")

    # Keep the generated device page intentional: maintenance/configuration
    # telemetry belongs under Diagnostics rather than crowding primary sensors.
    required_diagnostic_sensors = {
        "operation_day",
        "remaining_day",
        "maximum_regeneration_interval",
        "backwash_time",
        "backwash_remaining",
        "slow_wash_time",
        "slow_wash_remaining",
        "refill_time",
        "refill_remaining",
        "wash_time",
        "wash_remaining",
        "resin_volume",
        "filter_work_days",
        "device_model",
        "polling_mode",
    }
    required_diagnostic_binaries = {
        "valve_closed_alarm",
        "salt_shortage_alarm",
        "resin_replacement",
        "salt_shortage_reminder",
        "filter_reminder",
    }
    for text, constructor, required in (
        (sensors, "YpsilonSensorDescription", required_diagnostic_sensors),
        (binaries, "YpsilonBinaryDescription", required_diagnostic_binaries),
    ):
        blocks_by_key: dict[str, str] = {}
        for block in re.findall(rf"{constructor}\((.*?)\n    \),", text, re.S):
            match = re.search(r'key="(\w+)"', block)
            if match:
                blocks_by_key[match.group(1)] = block
        for key in sorted(required):
            block = blocks_by_key.get(key)
            if block is None:
                issues.append(f"missing required diagnostic entity {key}")
            elif "entity_category=EntityCategory.DIAGNOSTIC" not in block:
                issues.append(f"{key}: expected EntityCategory.DIAGNOSTIC")

    # Every diagnostic field the coordinator publishes must reach an entity,
    # otherwise the data is collected and silently thrown away.
    coord = set(re.findall(r"\b(_[a-zA-Z]\w+)=", read("coordinator.py")))
    coord -= {"_interval", "_update", "_field52_cache", "_consecutive_failures",
              "_failed_polls", "_active_until", "_is_active", "_apply_interval",
              "_device_is_busy", "_async_update_data"}
    exposed = set(re.findall(r'field="(_\w+)"', sensors + binaries))
    # Surfaced as an attribute of the communication-problem binary sensor
    # rather than as an entity of its own.
    exposed |= set(re.findall(r'get\("(_\w+)"\)', sensors + binaries))
    orphans = sorted(coord - exposed)
    if orphans:
        issues.append(f"coordinator fields with no entity: {orphans}")

    # A constant defined but never used usually means a block was lost.
    for name in ("SOURCE_INTEGRATION", "SOURCE_DEVICE"):
        if sensors.count(name) < 2:
            issues.append(f"{name} defined but unused - lost sensor block?")

    blocks = re.findall(r"YpsilonSensorDescription\((.*?)\n    \),", sensors, re.S)
    for block in blocks:
        key = re.search(r'key="(\w+)"', block)
        key = key.group(1) if key else "?"
        device_class = re.search(r"device_class=SensorDeviceClass\.(\w+)", block)
        state_class = re.search(r"state_class=SensorStateClass\.(\w+)", block)
        if device_class and device_class.group(1) == "ENUM":
            if "options=" not in block:
                issues.append(f"{key}: ENUM without options")
            if state_class:
                issues.append(f"{key}: ENUM must not carry a state_class")
        if (
            device_class
            and state_class
            and device_class.group(1) in {"VOLUME", "WATER", "ENERGY", "GAS"}
            and state_class.group(1) == "MEASUREMENT"
        ):
            issues.append(f"{key}: {device_class.group(1)} + MEASUREMENT is invalid")

    # Entity translation keys only: exception keys live under "exceptions" and
    # are matched separately, so they must not be looked up as entity names.
    keys: dict[str, set[str]] = {}
    exception_keys: set[str] = set()
    for filename, domain in PLATFORMS.items():
        text = read(filename)
        exception_keys |= set(
            re.findall(r'translation_key="(\w+)",\s*\n\s*translation_placeholders', text)
        )
        found = re.findall(r'translation_key="(\w+)"', text)
        found += re.findall(r'_attr_translation_key = "(\w+)"', text)
        if found:
            keys.setdefault(domain, set()).update(found)
    for domain in keys:
        keys[domain] -= exception_keys

    for filename in ("translations/ca.json", "translations/en.json", "translations/es.json"):
        data = json.loads(read(filename)).get("entity", {})
        for domain, expected in keys.items():
            missing = sorted(expected - set(data.get(domain, {})))
            if missing:
                issues.append(f"{filename} {domain}: missing {missing}")

    for filename in ("translations/ca.json", "translations/en.json", "translations/es.json"):
        declared = set(json.loads(read(filename)).get("exceptions", {}))
        missing = sorted(exception_keys - declared)
        if missing:
            issues.append(f"{filename} exceptions: missing {missing}")

    entities = json.loads(read("translations/en.json"))["entity"]
    names = [
        (value["name"], domain, key)
        for domain, group in entities.items()
        for key, value in group.items()
        if isinstance(value, dict) and "name" in value
    ]
    for name, count in Counter(n for n, _, _ in names).items():
        if count > 1:
            where = [f"{d}.{k}" for n, d, k in names if n == name]
            issues.append(f"duplicate entity name {name!r}: {where}")

    # A control must never be able to ask for a value the encoder cannot
    # represent: the frame would be built from a truncated number.
    numbers = read("number.py")
    write_u16 = set(re.findall(r"WRITE_U16(?:_BE)? = \{([^}]*)\}", protocol_src()))
    u16_fields: set[int] = set()
    for group in re.findall(r"WRITE_U16(?:_BE)? = \{([^}]*)\}", protocol_src()):
        u16_fields |= {int(n) for n in re.findall(r"\d+", group)}
    for block in re.findall(r"YpsilonNumberDescription\((.*?)\n    \),", numbers, re.S):
        key = re.search(r'key="(\w+)"', block).group(1)
        field_id = int(re.search(r"field_id=(\d+)", block).group(1))
        maximum = float(re.search(r"native_max_value=([\d.]+)", block).group(1))
        raw = maximum * 100 if "hundredths=True" in block else maximum
        limit = 0xFFFF if field_id in u16_fields else 0xFF
        if raw > limit:
            issues.append(f"{key}: max {maximum} exceeds field {field_id} capacity")

    # Every alert field must exist in the protocol decoder, otherwise it is
    # silently always false and the alert can never fire.
    protocol = read("protocol.py")
    known = set(re.findall(r'\d+: "(\w+)"', protocol))
    known |= set(re.findall(r'decoded\["(\w+)"\]', protocol))
    alerts = re.findall(r'\("(\w+)", "\w+"\)', read("const.py"))
    unknown = sorted(set(alerts) - known)
    if unknown:
        issues.append(f"const.py ALERT_FIELDS not produced by the decoder: {unknown}")

    # User-facing strings belong in the translation files, not in f-strings.
    catalan = ("No s'ha pogut", "és per sota", "supera el màxim", "no documentat")
    for filename in PLATFORMS:
        text = read(filename)
        for marker in catalan:
            if marker in text:
                issues.append(f"{filename}: hardcoded Catalan string {marker!r}")

    return issues


if __name__ == "__main__":
    problems = audit()
    print("\n".join(problems) if problems else "AUDIT CLEAN")
    raise SystemExit(1 if problems else 0)
