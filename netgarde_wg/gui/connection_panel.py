from __future__ import annotations

import sys
from typing import Callable

if sys.platform != "darwin":
    raise ImportError("connection_panel module is macOS only")

from AppKit import (  # noqa: E402
    NSBackingStoreBuffered,
    NSBezelStyleRounded,
    NSButton,
    NSColor,
    NSFont,
    NSMakeRect,
    NSTextField,
    NSView,
    NSWindow,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskTitled,
)

from netgarde_wg.gui.connection_view import ConnectionSnapshot

_WIDTH = 380.0
_MARGIN = 20.0
_ROW_HEIGHT = 22.0
_SECTION_TITLE_HEIGHT = 18.0
_SECTION_GAP = 12.0
_BUTTON_HEIGHT = 28.0
_LABEL_WIDTH = 130.0
_VALUE_WIDTH = 220.0

_CONNECTION_ROWS = [
    ("Service", "server_display"),
    ("Gateway", "gateway_display"),
    ("VPN address", "vpn_address"),
    ("DNS", "dns"),
    ("Device", "hostname"),
    ("Public IP", "public_ip"),
    ("Connected for", "connected_for"),
]

_TRAFFIC_ROWS = [
    ("Download", "down_rate"),
    ("Upload", "up_rate"),
    ("Total down", "down_total"),
    ("Total up", "up_total"),
]


class ConnectionPanel:
    def __init__(self) -> None:
        self._window: NSWindow | None = None
        self._content: NSView | None = None
        self._status_value: NSTextField | None = None
        self._title_field: NSTextField | None = None
        self._value_fields: dict[str, NSTextField] = {}
        self._section_widgets: dict[str, list[object]] = {}
        self._connect_button: NSButton | None = None
        self._disconnect_button: NSButton | None = None
        self._on_connect: Callable[[], None] | None = None
        self._on_disconnect: Callable[[], None] | None = None

    def _ensure_window(self) -> NSWindow:
        if self._window is not None:
            return self._window

        window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, _WIDTH, 420),
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable,
            NSBackingStoreBuffered,
            False,
        )
        window.setTitle_("NetGarde")
        window.setLevel_(3)
        window.setReleasedWhenClosed_(False)

        content = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, _WIDTH, 420))
        self._content = content

        self._title_field = self._make_label("NetGarde", bold=True, size=18)
        content.addSubview_(self._title_field)

        self._status_value = self._make_value("")
        content.addSubview_(self._status_value)

        self._add_section_widgets(content, "connection", "Connection", _CONNECTION_ROWS)
        self._add_section_widgets(content, "traffic", "Traffic", _TRAFFIC_ROWS)

        self._connect_button = NSButton.alloc().init()
        self._connect_button.setTitle_("Connect")
        self._connect_button.setBezelStyle_(NSBezelStyleRounded)
        self._connect_button.setTarget_(self)
        self._connect_button.setAction_("connectClicked:")
        content.addSubview_(self._connect_button)

        self._disconnect_button = NSButton.alloc().init()
        self._disconnect_button.setTitle_("Disconnect")
        self._disconnect_button.setBezelStyle_(NSBezelStyleRounded)
        self._disconnect_button.setTarget_(self)
        self._disconnect_button.setAction_("disconnectClicked:")
        content.addSubview_(self._disconnect_button)

        window.setContentView_(content)
        self._window = window
        self._layout()
        return window

    def _add_section_widgets(
        self,
        content: NSView,
        section_key: str,
        title: str,
        rows: list[tuple[str, str]],
    ) -> None:
        widgets: list[object] = []
        heading = self._make_label(title, bold=True, size=13)
        content.addSubview_(heading)
        widgets.append(heading)

        for label, key in rows:
            label_field = self._make_label(label, bold=False, size=12)
            content.addSubview_(label_field)
            widgets.append(label_field)

            value_field = self._make_value("")
            content.addSubview_(value_field)
            widgets.append(value_field)
            self._value_fields[key] = value_field

        self._section_widgets[section_key] = widgets

    def _layout(self) -> None:
        if self._content is None or self._window is None:
            return

        y = _MARGIN

        if self._connect_button is not None:
            self._connect_button.setFrame_(
                NSMakeRect(_MARGIN, y, 150, _BUTTON_HEIGHT)
            )
        if self._disconnect_button is not None:
            self._disconnect_button.setFrame_(
                NSMakeRect(_WIDTH - _MARGIN - 150, y, 150, _BUTTON_HEIGHT)
            )
        y += _BUTTON_HEIGHT + _SECTION_GAP

        y = self._layout_section("traffic", _TRAFFIC_ROWS, y)
        y = self._layout_section("connection", _CONNECTION_ROWS, y)

        if self._status_value is not None:
            self._status_value.setFrame_(
                NSMakeRect(_MARGIN, y, _WIDTH - 2 * _MARGIN, _ROW_HEIGHT)
            )
        y += _ROW_HEIGHT + 8

        if self._title_field is not None:
            self._title_field.setFrame_(NSMakeRect(_MARGIN, y, 200, 24))
        y += 28 + _MARGIN

        height = y
        self._content.setFrame_(NSMakeRect(0, 0, _WIDTH, height))
        self._window.setContentSize_((_WIDTH, height))

    def _layout_section(self, section_key: str, rows: list[tuple[str, str]], y: float) -> float:
        widgets = self._section_widgets.get(section_key, [])
        if not widgets:
            return y

        y += _SECTION_GAP
        for index, (_label, _key) in enumerate(rows):
            widget_index = 1 + index * 2
            label_field = widgets[widget_index]
            value_field = widgets[widget_index + 1]
            label_field.setFrame_(
                NSMakeRect(_MARGIN, y, _LABEL_WIDTH, _ROW_HEIGHT)
            )
            value_field.setFrame_(
                NSMakeRect(_MARGIN + _LABEL_WIDTH, y, _VALUE_WIDTH, _ROW_HEIGHT)
            )
            y += _ROW_HEIGHT

        heading = widgets[0]
        heading.setFrame_(NSMakeRect(_MARGIN, y, 300, _SECTION_TITLE_HEIGHT))
        y += _SECTION_TITLE_HEIGHT
        return y

    @staticmethod
    def _make_label(text: str, *, bold: bool, size: float) -> NSTextField:
        field = NSTextField.alloc().init()
        field.setStringValue_(text)
        field.setBezeled_(False)
        field.setDrawsBackground_(False)
        field.setEditable_(False)
        field.setSelectable_(False)
        weight = 0.4 if bold else 0.0
        field.setFont_(NSFont.systemFontOfSize_weight_(size, weight))
        if bold:
            field.setTextColor_(NSColor.labelColor())
        else:
            field.setTextColor_(NSColor.secondaryLabelColor())
        return field

    @staticmethod
    def _make_value(text: str) -> NSTextField:
        field = NSTextField.alloc().init()
        field.setStringValue_(text)
        field.setBezeled_(False)
        field.setDrawsBackground_(False)
        field.setEditable_(False)
        field.setSelectable_(True)
        field.setFont_(NSFont.monospacedSystemFontOfSize_weight_(12.0, 0.0))
        field.setTextColor_(NSColor.labelColor())
        field.setLineBreakMode_(4)
        return field

    def show(
        self,
        snapshot: ConnectionSnapshot,
        *,
        on_connect: Callable[[], None],
        on_disconnect: Callable[[], None],
    ) -> None:
        self._on_connect = on_connect
        self._on_disconnect = on_disconnect
        window = self._ensure_window()
        self._apply_snapshot(snapshot)
        window.center()
        window.makeKeyAndOrderFront_(None)

    def refresh(self, snapshot: ConnectionSnapshot) -> None:
        if self._window is None or not self._window.isVisible():
            return
        self._apply_snapshot(snapshot)

    def _apply_snapshot(self, snapshot: ConnectionSnapshot) -> None:
        if self._status_value is not None:
            color = "Connected" if snapshot.connected else "Disconnected"
            self._status_value.setStringValue_(f"● {color}")
            self._status_value.setTextColor_(
                NSColor.systemGreenColor() if snapshot.connected else NSColor.systemRedColor()
            )

        values = {
            "server_display": snapshot.server_display,
            "gateway_display": snapshot.gateway_display,
            "vpn_address": snapshot.vpn_address,
            "dns": snapshot.dns,
            "hostname": snapshot.hostname,
            "public_ip": snapshot.public_ip,
            "connected_for": snapshot.connected_for,
            "down_rate": snapshot.down_rate,
            "up_rate": snapshot.up_rate,
            "down_total": snapshot.down_total,
            "up_total": snapshot.up_total,
        }
        for key, field in self._value_fields.items():
            field.setStringValue_(values.get(key, "—"))

        if self._connect_button is not None:
            self._connect_button.setEnabled_(not snapshot.connected)
        if self._disconnect_button is not None:
            self._disconnect_button.setEnabled_(snapshot.connected)

    def connectClicked_(self, _sender) -> None:
        if self._on_connect is not None:
            self._on_connect()

    def disconnectClicked_(self, _sender) -> None:
        if self._on_disconnect is not None:
            self._on_disconnect()


_panel = ConnectionPanel()


def show_connection_panel(
    snapshot: ConnectionSnapshot,
    *,
    on_connect: Callable[[], None],
    on_disconnect: Callable[[], None],
) -> None:
    _panel.show(snapshot, on_connect=on_connect, on_disconnect=on_disconnect)


def refresh_connection_panel(snapshot: ConnectionSnapshot) -> None:
    _panel.refresh(snapshot)
