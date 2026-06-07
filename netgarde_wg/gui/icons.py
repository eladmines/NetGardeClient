from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

if sys.platform != "darwin":
    raise ImportError("icons module is macOS only")

from AppKit import NSBezierPath, NSBitmapImageRep, NSImage, NSMakeSize  # noqa: E402

from netgarde_wg.paths import user_data_dir


def _bundled_asset_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "netgarde_wg" / "gui" / "assets"
    return Path(__file__).resolve().parent / "assets"


def _cache_asset_dir() -> Path:
    return user_data_dir() / "icons"


def _shield_path(*, connected: bool) -> NSBezierPath:
    path = NSBezierPath.bezierPath()
    if connected:
        path.moveToPoint_((11.0, 20.5))
        path.lineToPoint_((18.8, 17.0))
        path.lineToPoint_((18.8, 9.2))
        path.curveToPoint_controlPoint1_controlPoint2_((11.0, 2.0), (16.0, 4.0), (18.8, 6.5))
        path.curveToPoint_controlPoint1_controlPoint2_((3.2, 9.2), (6.0, 4.0), (3.2, 6.5))
        path.lineToPoint_((3.2, 17.0))
        path.closePath()
    else:
        path.moveToPoint_((11.0, 19.8))
        path.lineToPoint_((18.2, 16.6))
        path.lineToPoint_((18.2, 9.4))
        path.curveToPoint_controlPoint1_controlPoint2_((11.0, 3.0), (15.6, 4.8), (18.2, 7.0))
        path.curveToPoint_controlPoint1_controlPoint2_((3.8, 9.4), (6.4, 4.8), (3.8, 7.0))
        path.lineToPoint_((3.8, 16.6))
        path.closePath()
    return path


def _draw_icon(*, connected: bool) -> NSImage:
    size = 22.0
    image = NSImage.alloc().initWithSize_(NSMakeSize(size, size))
    image.lockFocus()
    try:
        from AppKit import NSColor

        NSColor.blackColor().set()
        shield = _shield_path(connected=connected)
        if connected:
            shield.fill()
            check = NSBezierPath.bezierPath()
            check.moveToPoint_((7.4, 10.8))
            check.lineToPoint_((10.0, 8.2))
            check.lineToPoint_((14.8, 13.2))
            check.setLineWidth_(1.8)
            NSColor.whiteColor().set()
            check.stroke()
        else:
            shield.setLineWidth_(1.5)
            shield.stroke()
            slash = NSBezierPath.bezierPath()
            slash.moveToPoint_((6.5, 6.5))
            slash.lineToPoint_((15.5, 15.5))
            slash.setLineWidth_(1.5)
            slash.stroke()
    finally:
        image.unlockFocus()
    image.setTemplate_(True)
    return image


def _write_png(image: NSImage, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tiff = image.TIFFRepresentation()
    if tiff is None:
        raise RuntimeError(f"failed to render icon {path}")
    rep = NSBitmapImageRep.imageRepWithData_(tiff)
    png = rep.representationUsingType_properties_(4, {})
    if png is None:
        raise RuntimeError(f"failed to encode icon {path}")
    path.write_bytes(bytes(png))


@lru_cache(maxsize=2)
def status_icon_path(*, connected: bool) -> str:
    """Return a cached PNG path for the menu bar status icon."""
    name = "menubar-connected.png" if connected else "menubar-disconnected.png"
    bundled = _bundled_asset_dir() / name
    if bundled.is_file():
        return str(bundled)
    cached = _cache_asset_dir() / name
    if not cached.is_file():
        _write_png(_draw_icon(connected=connected), cached)
    return str(cached)
