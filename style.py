"""Qt stylesheets for TerraFish V2.

Design tokens (kept here as a comment so future tweaks stay consistent):

  Canvas       #10141a   window background
  Surface      #171d25   cards / panels
  Surface-2    #1c232c   inputs, chips, hovered surfaces
  Border       #262e38   default hairline border
  Border-hi    #333d49   hover/focus border
  Text         #e7ebf0   primary text
  Text-dim     #8b96a3   secondary text
  Text-faint   #525d6a   tertiary / eyebrow labels

  Accent (idle/waiting, "water")   #45d6c4  bg tint #173733
  Warn   (casting)                 #f0b268  bg tint #3a2f18
  Alert  (bite / reeling)          #ff8a72  bg tint #3a2420
  Danger (destructive)             #ef5f5f

Typography: a plain sans (Inter, falling back to system UI fonts) for
all interface text; a monospace face reserved specifically for numeric
read-outs (coordinates, thresholds, timers) so precise values are easy
to scan without turning the whole UI into a "terminal" look.
"""

FONT_UI = "'Inter', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
FONT_MONO = "'JetBrains Mono', 'Cascadia Mono', Consolas, monospace"

STYLE = f"""
QMainWindow, QWidget {{
    background-color: #10141a;
    color: #e7ebf0;
    font-family: {FONT_UI};
    font-size: 12px;
}}
QLabel {{ color: #8b96a3; }}

QLabel#brand {{
    color: #e7ebf0;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 0.2px;
}}
QLabel#brand_badge {{
    color: #45d6c4;
    background-color: #173733;
    border-radius: 8px;
    padding: 2px 7px;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1px;
}}
QLabel#eyebrow {{
    color: #525d6a;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 2px;
}}
QLabel#hint {{
    color: #525d6a;
    font-size: 10px;
    font-family: {FONT_MONO};
}}
QLabel#body_dim {{
    color: #8b96a3;
    font-size: 11px;
}}

QFrame#card {{
    background-color: #171d25;
    border: 1px solid #262e38;
    border-radius: 12px;
}}

/* Buttons -- default (secondary) style */
QPushButton {{
    background-color: #1c232c;
    color: #8b96a3;
    border: 1px solid #262e38;
    padding: 7px 12px;
    border-radius: 8px;
    font-family: {FONT_UI};
    font-size: 11px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: #222a34;
    border: 1px solid #333d49;
    color: #e7ebf0;
}}
QPushButton:pressed {{ background-color: #171d25; }}
QPushButton:disabled {{
    color: #3a4149;
    border-color: #1c232c;
    background-color: #14181f;
}}

/* Primary action -- the start/stop fishing button */
QPushButton#primary_btn {{
    background-color: #45d6c4;
    color: #0b1310;
    border: none;
    padding: 12px 14px;
    border-radius: 10px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.2px;
}}
QPushButton#primary_btn:hover {{ background-color: #63e0d1; }}
QPushButton#primary_btn:pressed {{ background-color: #37b8a8; }}
QPushButton#primary_btn[active="true"] {{
    background-color: #241417;
    color: #ff8a72;
    border: 1px solid #3a2420;
}}
QPushButton#primary_btn[active="true"]:hover {{ background-color: #2c1a1d; }}

/* Icon-only buttons */
QPushButton#icon_btn {{
    background-color: transparent;
    border: none;
    color: #525d6a;
    font-size: 13px;
    padding: 5px 8px;
    font-weight: 400;
}}
QPushButton#icon_btn:hover {{
    color: #e7ebf0;
    background-color: #1c232c;
    border-radius: 7px;
}}
QPushButton#icon_btn:disabled {{ color: #2a3038; background-color: transparent; }}

/* Inputs */
QSpinBox, QLineEdit {{
    background-color: #1c232c;
    color: #e7ebf0;
    border: 1px solid #262e38;
    border-radius: 7px;
    padding: 5px 8px;
    font-family: {FONT_MONO};
    font-size: 11px;
}}
QSpinBox:focus, QLineEdit:focus {{ border: 1px solid #45d6c4; }}
QSpinBox:disabled, QLineEdit:disabled {{ color: #4a5058; background-color: #171b21; }}

QCheckBox {{ color: #8b96a3; spacing: 8px; font-size: 11px; }}
QCheckBox::indicator {{
    width: 14px; height: 14px;
    border-radius: 4px;
    border: 1px solid #333d49;
    background: #1c232c;
}}
QCheckBox::indicator:checked {{ background: #45d6c4; border-color: #45d6c4; }}

/* Preset list */
QListWidget {{
    background-color: transparent;
    border: none;
    color: #8b96a3;
    outline: none;
    font-size: 11px;
}}
QListWidget::item {{
    padding: 7px 10px;
    border-radius: 7px;
    margin: 1px 0;
}}
QListWidget::item:selected {{
    background-color: #173733;
    color: #45d6c4;
}}
QListWidget::item:hover:!selected {{
    background-color: #1c232c;
    color: #e7ebf0;
}}

QProgressBar {{
    background-color: #1c232c;
    border: none;
    border-radius: 3px;
    height: 6px;
}}
QProgressBar::chunk {{
    background-color: #45d6c4;
    border-radius: 3px;
}}

QScrollArea {{ border: none; }}
QToolTip {{
    background-color: #1c232c;
    color: #e7ebf0;
    border: 1px solid #333d49;
    padding: 4px 6px;
    border-radius: 6px;
}}
"""

SETTINGS_PANEL_STYLE = f"""
SettingsPanel {{
    background-color: #10141a;
    border-left: 1px solid #262e38;
}}
SettingsPanel QLabel {{
    color: #8b96a3;
    background-color: transparent;
    font-size: 11px;
}}
SettingsPanel QLabel#sp_title {{
    color: #e7ebf0;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.2px;
    background-color: transparent;
}}
SettingsPanel QLabel#sp_section {{
    color: #525d6a;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 2px;
    background-color: transparent;
}}
SettingsPanel QLabel#sp_version {{
    color: #3a4149;
    font-size: 10px;
    background-color: transparent;
}}
SettingsPanel QPushButton {{
    background-color: #1c232c;
    color: #8b96a3;
    border: 1px solid #262e38;
    padding: 6px 12px;
    border-radius: 8px;
    font-family: {FONT_UI};
    font-size: 11px;
    font-weight: 600;
    text-align: left;
}}
SettingsPanel QPushButton:hover {{
    background-color: #222a34;
    border: 1px solid #333d49;
    color: #e7ebf0;
}}
SettingsPanel QPushButton#sp_icon_btn {{
    background-color: transparent;
    border: none;
    color: #525d6a;
    font-size: 13px;
    padding: 5px 8px;
}}
SettingsPanel QPushButton#sp_icon_btn:hover {{
    color: #e7ebf0;
    background-color: #1c232c;
    border-radius: 7px;
}}
SettingsPanel QPushButton#sp_hk_btn {{
    background-color: #173733;
    border: 1px solid #234943;
    color: #45d6c4;
    font-size: 11px;
    font-weight: 700;
    padding: 4px 12px;
    border-radius: 7px;
    min-width: 22px;
    text-align: center;
}}
SettingsPanel QPushButton#sp_hk_btn:hover {{ border-color: #45d6c4; }}
SettingsPanel QPushButton#sp_hk_btn_blue {{
    background-color: #16232f;
    border: 1px solid #1f3548;
    color: #6fb8e6;
    font-size: 11px;
    font-weight: 700;
    padding: 4px 12px;
    border-radius: 7px;
    min-width: 22px;
    text-align: center;
}}
SettingsPanel QPushButton#sp_hk_btn_blue:hover {{ border-color: #6fb8e6; }}
SettingsPanel QPushButton#sp_aot_on {{
    background-color: #173733;
    color: #45d6c4;
    border: 1px solid #234943;
    padding: 4px 12px;
    border-radius: 7px;
    font-size: 11px;
    font-weight: 700;
    text-align: center;
}}
SettingsPanel QPushButton#sp_aot_off {{
    background-color: #1c232c;
    color: #525d6a;
    border: 1px solid #262e38;
    padding: 4px 12px;
    border-radius: 7px;
    font-size: 11px;
    font-weight: 600;
    text-align: center;
}}
SettingsPanel QPushButton#sp_aot_off:hover {{ color: #8b96a3; border-color: #333d49; }}
SettingsPanel QSpinBox, SettingsPanel QLineEdit {{
    background-color: #1c232c;
    color: #e7ebf0;
    border: 1px solid #262e38;
    border-radius: 7px;
    padding: 5px 8px;
    font-family: {FONT_MONO};
    font-size: 11px;
}}
SettingsPanel QSpinBox:focus, SettingsPanel QLineEdit:focus {{ border: 1px solid #45d6c4; }}
SettingsPanel QCheckBox {{
    color: #8b96a3;
    spacing: 8px;
    background-color: transparent;
    font-size: 11px;
}}
SettingsPanel QCheckBox::indicator {{
    width: 14px; height: 14px;
    border-radius: 4px;
    border: 1px solid #333d49;
    background: #1c232c;
}}
SettingsPanel QCheckBox::indicator:checked {{ background: #45d6c4; border-color: #45d6c4; }}
"""
