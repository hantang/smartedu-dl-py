import ctypes
import platform
import tkinter.font as tkFont

import sv_ttk
import darkdetect


def set_dpi_scale():
    scale = 1.0
    os_name = platform.system()
    if os_name == "Windows":
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        ScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0)
        scale = ScaleFactor / 100.0
    return scale, os_name


def set_theme(theme="auto", font_family=None, font_scale=1.0):
    if theme == "raw":
        return
    if theme == "auto":
        theme = darkdetect.theme()
    sv_ttk.set_theme(theme)

    default_font = tkFont.nametofont("TkDefaultFont")
    # windows: {'family': 'Microsoft YaHei UI', 'size': 9, 'weight': 'normal', 'slant': 'roman', 'underline': 0, 'overstrike': 0}
    # macos: {'family': '.AppleSystemUIFont', 'size': 13, 'weight': 'normal', 'slant': 'roman', 'underline': 0, 'overstrike': 0}

    family = font_family if font_family else default_font.actual("family")
    # Update font: SunValley*Font: 12/14/.../68
    parts = [
        "Caption",
        "Body",
        "BodyStrong",
        "BodyLarge",
        "Subtitle",
        "Title",
        "TitleLarge",
        "Display",
    ]
    for font_name in parts:
        font = tkFont.nametofont(f"SunValley{font_name}Font")
        # size = font.actual("size")
        size = font.cget("size")
        font.configure(size=int(size * font_scale))
        font.configure(family=family)
