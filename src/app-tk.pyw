"""
图形界面版本（tkinter实现）：智慧教育平台资源下载工具
"""

import argparse
import logging

from smartedu.ui.theme import set_dpi_scale, set_theme
from smartedu.ui.tk import BasicDownloadApp


def main(theme=None):
    scale, os_name = set_dpi_scale()
    app = BasicDownloadApp(scale, os_name)
    set_theme(theme=theme, font_scale=scale)
    app.eval("tk::PlaceWindow . center")
    app.mainloop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument(
        "--theme", "-t", default="auto", type=str, choices=["light", "dark", "auto", "raw"]
    )
    args = parser.parse_args()

    # 配置日志
    fmt = "%(asctime)s %(filename)s %(levelname)s %(message)s"
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level, format=fmt)
    logging.debug("调试模式已启用")

    main(args.theme)
