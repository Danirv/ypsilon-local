"""Load the pure protocol packages without importing Home Assistant."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "ypsilon_local"
TEST_PKG = "_ypsilon_testpkg"


def _ensure_namespace() -> None:
    if TEST_PKG not in sys.modules:
        root = types.ModuleType(TEST_PKG)
        root.__path__ = [str(INTEGRATION)]
        sys.modules[TEST_PKG] = root
    for child in ("runxin", "transport"):
        name = f"{TEST_PKG}.{child}"
        if name not in sys.modules:
            pkg = types.ModuleType(name)
            pkg.__path__ = [str(INTEGRATION / child)]
            sys.modules[name] = pkg


def load(relative: str):
    """Load e.g. `runxin.f79d` or `transport.broadlink_bl3372`."""
    _ensure_namespace()
    full = f"{TEST_PKG}.{relative}"
    if full in sys.modules:
        return sys.modules[full]
    path = INTEGRATION.joinpath(*relative.split(".")).with_suffix(".py")
    spec = importlib.util.spec_from_file_location(full, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {relative} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[full] = module
    spec.loader.exec_module(module)
    return module
