"""Dependency-free checks for local Home Assistant brand assets."""

from __future__ import annotations

from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "custom_components" / "ypsilon_local" / "brand"


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert data[12:16] == b"IHDR"
    return struct.unpack(">II", data[16:24])


def test_icons_have_required_square_sizes() -> None:
    assert png_size(BRAND / "icon.png") == (256, 256)
    assert png_size(BRAND / "icon@2x.png") == (512, 512)
    assert png_size(BRAND / "dark_icon.png") == (256, 256)
    assert png_size(BRAND / "dark_icon@2x.png") == (512, 512)


def test_logos_are_landscape_and_have_exact_2x_variants() -> None:
    for prefix in ("", "dark_"):
        normal = png_size(BRAND / f"{prefix}logo.png")
        retina = png_size(BRAND / f"{prefix}logo@2x.png")
        assert normal[0] > normal[1]
        assert retina == (normal[0] * 2, normal[1] * 2)


def test_logo_is_not_square_icon_reused_as_logo() -> None:
    assert (BRAND / "logo.png").read_bytes() != (BRAND / "icon.png").read_bytes()
