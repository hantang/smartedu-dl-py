
import sv_ttk
import darkdetect
import tkinter.font as tkFont


def set_theme(theme=None, font_family=None, font_scale=1.0):
    if not theme or theme not in ["dark", "light"]:
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

