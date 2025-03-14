"""
命令行版本：智慧教育平台资源下载工具
"""

import logging
import sys
from typing import Optional

import click

from smartedu.configs.conf import DEFAULT_PATH, DATA_PATH
from smartedu.ui.cli import display_welcome, display_info, preprocess
from smartedu.ui.cli import simple_download, interactive_download
from smartedu.parser import get_formats


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(filename)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


@click.command()
@click.help_option("--help", "-h")
@click.option("--debug", "-d", is_flag=True, help="启用调试模式")
@click.option("--interactive", "-i", is_flag=True, help="交互模式（默认）")
@click.option("--formats", "-t", help="下载资源类型，逗号分隔")
@click.option("--auth", "-a", help="用户登录信息X-ND-AUTH字段；当下载失败或非最新版教材时配置")
@click.option("--backup", "-b", is_flag=True, help="尝试用备用链接下载")
@click.option("--urls", "-u", help="URL路径列表，逗号分隔")
@click.option("--file", "-f", type=click.Path(exists=True), help="包含URL的文件")
@click.option("--output", "-o", type=click.Path(), default=DEFAULT_PATH, help="下载文件保存目录")
def main(
    debug: bool,
    interactive: bool,
    formats: Optional[str],
    auth: Optional[str],
    backup: bool,
    urls: Optional[str],
    file: Optional[str],
    output: str,
):
    # 如果是请求帮助信息，不需要显示欢迎信息
    if any(arg in sys.argv[1:] for arg in ["-h", "--help"]):
        return

    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("调试模式已启用")

    mode = (urls or file) and (not interactive)
    display_welcome(not mode)
    formats = get_formats(formats)
    if auth:
        auth = auth.strip()

    info = {
        "下载资源类型": formats,
        "登录参数（X-ND-AUTH）": auth,
        "启用备用链接": backup,
        "默认保存路径": output,
    }
    display_info(info)

    if urls or file:
        info = {"下载链接": urls, "链接文件": file}
        display_info(info, title="手动指定链接：")

    try:
        if mode:
            # 非交互模式，直接下载预定义URL
            predefined_urls = preprocess(file, urls)
            if not predefined_urls:
                logger.error("没有提供有效的URL")
                sys.exit(1)
            simple_download(predefined_urls, output, formats, auth)
        else:
            # 默认改成交互模式
            interactive_download(output, formats, auth, backup, data_dir=DATA_PATH)
            # logger.warning("请使用-u/-f提供URL列表，或使用-i进行交互")

    except Exception as e:
        logger.error(f"程序执行出错, error={e}", exc_info=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n程序已终止")
        sys.exit(0)


if __name__ == "__main__":
    main()
