"""Offline consistency, protocol and architecture regression audit."""
from __future__ import annotations

import ast
from collections import Counter
import importlib.util
import json
from pathlib import Path
import re
import sys
import types

ROOT = Path(__file__).resolve().parent.parent
HERE = ROOT / "custom_components" / "ypsilon_local"
AUDIT_PKG = "_ypsilon_audit"
PLATFORMS = {
    "sensor.py": "sensor", "binary_sensor.py": "binary_sensor",
    "number.py": "number", "switch.py": "switch",
    "button.py": "button", "time.py": "time",
}


def read(path: str) -> str:
    return (HERE / path).read_text()


def _ensure_package() -> None:
    if AUDIT_PKG not in sys.modules:
        root = types.ModuleType(AUDIT_PKG); root.__path__ = [str(HERE)]
        sys.modules[AUDIT_PKG] = root
    name = f"{AUDIT_PKG}.runxin"
    if name not in sys.modules:
        pkg = types.ModuleType(name); pkg.__path__ = [str(HERE / "runxin")]
        sys.modules[name] = pkg


def load_runxin(name: str):
    _ensure_package()
    full = f"{AUDIT_PKG}.runxin.{name}"
    if full in sys.modules:
        return sys.modules[full]
    spec = importlib.util.spec_from_file_location(full, HERE / "runxin" / f"{name}.py")
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load runxin/{name}.py")
    module = importlib.util.module_from_spec(spec); sys.modules[full] = module
    spec.loader.exec_module(module)
    return module


def _response(groups: list[tuple[int, int, int]], opcode: int) -> bytes:
    data: list[int] = []
    for field, low, high in groups:
        data += [field, low, high]
    header = [0x5A,0x5C,0,0,0,0,0,0,0,0,0,0,1,0,0x12,0,0]
    inner = [0xDF,0xFD,0,opcode,*data,0,0xDE]
    header[15] = len(inner); inner[2] = len(inner)
    inner[-2] = sum(inner[:-2]) & 0xFF
    frame = header + inner + [0,0xA5]; frame[2] = len(frame)
    frame[-2] = sum(frame[:-2]) & 0xFF
    return bytes(frame)


def protocol_checks() -> list[str]:
    errors: list[str] = []
    try:
        p = load_runxin("f79d"); framing = load_runxin("framing")
    except Exception as err:  # noqa: BLE001
        return [f"PROTOCOL load failed: {err}"]

    def check(name: str, fn) -> None:
        try: fn()
        except Exception as err: errors.append(f"PROTOCOL {name}: {err}")  # noqa: BLE001
    def req(ok: bool, msg: str) -> None:
        if not ok: raise AssertionError(msg)

    def frames() -> None:
        q = p.build_query([1,34,52]); p.validate_frame(q)
        req(q[:2] == b"\x5a\x5c", "query prefix")
        w = p.build_write_fields({43:50,49:1}); p.validate_frame(w)
        inner = p._inner_frame(w)
        req(inner[3] == 0x19, "write opcode")
        req(inner[4:-2] == bytes([43,50,0,49,1,0]), "multi-write payload")
        bad = bytearray(q); bad[-2] ^= 1
        try: p.validate_frame(bytes(bad))
        except p.F79DProtocolError: pass
        else: raise AssertionError("bad checksum accepted")

    def encodings() -> None:
        req(p.encode_field(43,50) == [43,50,0], "field43")
        req(p.encode_field(47,400) == [47,0x90,0x01], "field47")
        req(p.encode_field(7,200) == [7,0,0xC8], "field7")
        req(p.encode_field(10,(2,30)) == [10,2,30], "field10")
        req(p.WRITE_SIMPLE == {2,6,9,13,14,23,24,34,43,46,48,49}, "WRITE_SIMPLE")
        req(p.WRITE_U16 == {25,47,52}, "WRITE_U16")
        req(p.WRITE_U16_BE == {7}, "WRITE_U16_BE")
        req(p.WRITE_TIME == {4,5,10,15,17,19,21}, "WRITE_TIME")

    def decode() -> None:
        req(set(p.FIELD_NAMES) == set(range(1,53)), "field ids 1..52")
        req(len(set(p.FIELD_NAMES.values())) == 52, "duplicate field names")
        req(p.STATE_FIELDS == list(range(1,52)), "state query changed")
        d = p.decode_tlvs({47:(0x90,1),52:(0x68,1),7:(3,0xE8),11:(0,14)})
        req(d["rawWaterHardness"] == 400, "hardness")
        req(d["filterMaterialWorkingDay"] == 360, "field52")
        req(d["flowRateOff"] == 1000 and d["_raw_flowRate"] == 14, "flow endian")
        req(p.decode_tlvs({35:(0,1)})["residualWaterProduction"] is None, "volume continuation")
        req(p.decode_tlvs({35:(0,1),36:(59,0)})["residualWaterProduction"] == 159.0, "volume formula")
        req(p.decode_tlvs({4:(23,59)})["currentTime"] == "23:59:00", "time")
        req(p.decode_tlvs({4:(25,70)})["currentTime"] is None, "invalid time")
        flags = p.decode_tlvs({33:(1,0)})
        req(flags["saltShortageReminder"] and not flags["filterMaterialReminder"], "flags")

    def client() -> None:
        cmod = load_runxin("client")
        class Fake:
            def __init__(self): self.requests: list[bytes] = []
            def transact(self, frame: bytes) -> bytes:
                self.requests.append(frame); framing.validate_frame(frame)
                inner = framing.inner_frame(frame)
                if inner[3] == framing.QUERY_CODE:
                    groups = [(f,9,0) if f == 1 else (f,0,0) for f in inner[4:-2] if f in (1,34)]
                    return _response(groups, framing.QUERY_RESPONSE_CODE)
                return _response([], framing.WRITE_RESPONSE_CODE)
            def invalidate(self): pass
            def close(self): pass
        fake = Fake(); client = cmod.F79DClient(fake)
        req(client.read_identity() == {"deviceModel":9,"station":0}, "fake identity")
        client.write_fields({43:50}); req(len(fake.requests) == 2, "fake transaction count")

    for name, fn in (("frames",frames),("encodings",encodings),("decode",decode),("client",client)):
        check(name, fn)
    return errors


def _imports(text: str) -> set[str]:
    result: set[str] = set()
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Import): result |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module: result.add(node.module)
    return result


def architecture_checks() -> list[str]:
    errors: list[str] = []
    required = [
        "runxin/__init__.py","runxin/errors.py","runxin/fields.py","runxin/framing.py","runxin/f79d.py","runxin/client.py",
        "transport/__init__.py","transport/base.py","transport/broadlink_bl3372.py",
    ]
    for rel in required:
        if not (HERE / rel).exists(): errors.append(f"missing architecture module: {rel}")
    for path in (HERE / "runxin").glob("*.py"):
        imports = _imports(path.read_text())
        bad = sorted(x for x in imports if x == "homeassistant" or x.startswith("homeassistant.") or x == "broadlink" or x.startswith("broadlink."))
        if bad: errors.append(f"{path.relative_to(HERE)} imports {bad}")
        for marker in ("send_packet(",".decrypt(","pack_tfb(","unpack_tfb("):
            if marker in path.read_text(): errors.append(f"{path.relative_to(HERE)} leaks transport detail {marker}")
    base = read("transport/base.py")
    if "F79D" in base or "broadlink" in _imports(base): errors.append("transport/base.py is not generic")
    broadlink = read("transport/broadlink_bl3372.py")
    if "send_packet(0x6A" not in broadlink: errors.append("BL3372 0x6A path lost")
    if any(x in broadlink for x in ("FIELD_NAMES","decode_tlvs","F79D_FIELD_SPECS")): errors.append("BL3372 transport leaks field codec")
    api = read("api.py")
    if any(x in api for x in ("send_packet(",".decrypt(","0x22:0x24","0x38:")): errors.append("api.py leaks BroadLink wire details")
    if "BroadlinkBL3372Transport" not in api or "F79DClient" not in api: errors.append("api.py composition missing")
    shim = read("protocol.py")
    if "Compatibility facade" not in shim or "runxin.f79d" not in shim: errors.append("protocol.py compatibility facade missing")
    return errors


def repository_checks() -> list[str]:
    errors: list[str] = []
    required = [
        "LICENSE","NOTICE","README.md","CHANGELOG.md","CONTRIBUTING.md","SECURITY.md","LEGAL.md","THIRD_PARTY.md","hacs.json",
        ".github/workflows/validate.yml",".github/workflows/hassfest.yml",".github/workflows/audit.yml",".github/workflows/release.yml",
        "scripts/publication_check.py","docs/architecture.md","docs/protocol.md","docs/f79d.md","docs/broadlink-bl3372.md",
        "docs/adding-a-transport.md","docs/adding-a-device-profile.md",
    ]
    for rel in required:
        if not (ROOT / rel).exists(): errors.append(f"missing publication file: {rel}")
    for path in HERE.rglob("*.py"):
        try: ast.parse(path.read_text())
        except SyntaxError as err: errors.append(f"SYNTAX {path.relative_to(HERE)}: {err}")
    for path in HERE.rglob("*.json"):
        try: json.loads(path.read_text())
        except Exception as err: errors.append(f"JSON {path.relative_to(HERE)}: {err}")  # noqa: BLE001
    manifest = json.loads(read("manifest.json"))
    if manifest.get("version") != "2.4.0": errors.append("manifest version != 2.4.0")
    if manifest.get("name") != "Ypsilon": errors.append("manifest name != Ypsilon")
    hacs = json.loads((ROOT / "hacs.json").read_text())
    if hacs != {"name":"Ypsilon"}: errors.append(f"unexpected hacs.json: {hacs}")
    if (HERE / "strings.json").exists(): errors.append("custom integration must not ship strings.json")
    if not (HERE / "brand" / "icon.png").exists(): errors.append("brand/icon.png missing")

    sensors, binaries = read("sensor.py"), read("binary_sensor.py")
    diagnostic = {
        "operation_day","remaining_day","maximum_regeneration_interval","backwash_time","backwash_remaining",
        "slow_wash_time","slow_wash_remaining","refill_time","refill_remaining","wash_time","wash_remaining",
        "resin_volume","filter_work_days","device_model","polling_mode",
    }
    for key in diagnostic:
        m = re.search(rf'YpsilonSensorDescription\((?:(?!YpsilonSensorDescription).)*?key="{key}"(?P<body>.*?)\n    \),', sensors, re.S)
        if not m or "entity_category=EntityCategory.DIAGNOSTIC" not in m.group("body"): errors.append(f"{key}: diagnostic sensor regression")
    for key in ("valve_closed_alarm","salt_shortage_alarm","resin_replacement","salt_shortage_reminder","filter_reminder"):
        m = re.search(rf'YpsilonBinaryDescription\((?:(?!YpsilonBinaryDescription).)*?key="{key}"(?P<body>.*?)\n    \),', binaries, re.S)
        if not m or "entity_category=EntityCategory.DIAGNOSTIC" not in m.group("body"): errors.append(f"{key}: diagnostic binary regression")

    keys: dict[str,set[str]] = {}
    exception_keys: set[str] = set()
    for file, domain in PLATFORMS.items():
        text = read(file)
        exceptions = set(re.findall(r'translation_key="(\w+)",\s*\n\s*translation_placeholders', text))
        exception_keys |= exceptions
        found = set(re.findall(r'translation_key="(\w+)"', text)) | set(re.findall(r'_attr_translation_key = "(\w+)"', text))
        found -= exceptions
        if found: keys[domain] = found
    for lang in ("ca","en","es"):
        translation = json.loads(read(f"translations/{lang}.json"))
        data = translation.get("entity",{})
        for domain, expected in keys.items():
            missing = sorted(expected - set(data.get(domain,{})))
            if missing: errors.append(f"translations/{lang}.json {domain}: missing {missing}")
        missing_exceptions = sorted(exception_keys - set(translation.get("exceptions",{})))
        if missing_exceptions: errors.append(f"translations/{lang}.json exceptions: missing {missing_exceptions}")
    names = []
    for domain, group in json.loads(read("translations/en.json"))["entity"].items():
        for key, val in group.items():
            if isinstance(val,dict) and "name" in val: names.append((val["name"],domain,key))
    for name,count in Counter(x[0] for x in names).items():
        if count > 1: errors.append(f"duplicate English entity name {name!r}")
    return errors


def main() -> int:
    errors = protocol_checks() + architecture_checks() + repository_checks()
    print("\n".join(errors) if errors else "AUDIT CLEAN")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
