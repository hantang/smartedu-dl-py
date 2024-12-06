"""
命令行版本：智慧教育平台资源下载工具
"""

import logging
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

import click
from rich.console import Console
from rich.progress import BarColumn, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.progress import Progress
from rich.table import Table

from tools.downloader import download_files, fetch_all_data
from tools.logo import DESCRIBES, LOGO_TEXT2
from tools.parser import extract_resource_url, parse_urls
from tools.parser2 import fetch_metadata, gen_url_from_tags, query_metadata

DEFAULT_URLS = []
DEFAULT_PATH = "./downloads"

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(filename)s [line:%(lineno)d] %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def display_welcome():
    """显示欢迎信息"""
    click.clear()
    click.echo(LOGO_TEXT2)
    click.secho(f"=== {DESCRIBES[0]} ===", fg="blue", bold=True)
    click.echo(f"> {DESCRIBES[1]}")
    click.echo(f"> {DESCRIBES[2]}\n")


def parse_range(range_str: str, max_num: int, min_num: int = 1) -> list:
    """解析范围表达式，如 "1-3,5,7-9" """
    range_str = range_str.strip().lower()
    if range_str in ["a", "all"]:
        return list(range(min_num, max_num + 1))

    result = set()
    for part in range_str.split(","):
        if "-" in part:
            start, end = map(str.strip, part.split("-"))
            start, end = int(start), int(end)
            start = max(start, min_num)
            end = min(end, max_num)
            if min_num <= start <= end <= max_num:
                result.update(range(start, end + 1))
        else:
            num = int(part.strip())
            if min_num <= num <= max_num:
                result.add(num)
    return sorted(list(result))


def validate_save_path(path_str: str) -> Tuple[bool, str]:
    """验证保存路径"""
    try:
        path = Path(path_str).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return True, str(path)
    except Exception as e:
        return False, str(e)


def display_urls(urls: list, title: str = "URL列表"):
    """显示URL列表"""
    click.secho(f"\n{title}:", fg="yellow")
    for i, url in enumerate(urls, 1):
        click.echo(f"{i:>2d}. {url}")


def display_results(console: Console, results: list, elapsed_time: float):
    """展示下载结果统计"""
    # 创建总体统计表格
    summary_table = Table(title="下载统计", show_header=False, title_style="bold magenta")
    success_count = sum(1 for r in results if r["status"] == "success")
    failed_count = len(results) - success_count

    summary_table.add_row("总计文件", str(len(results)))
    summary_table.add_row("成功下载", f"[green]{success_count}[/green]")
    summary_table.add_row("下载失败", f"[red]{failed_count}[/red]")
    summary_table.add_row("总用时", f"{elapsed_time:.1f}秒")

    console.print("\n")
    console.print(summary_table)

    # 创建详细结果表格
    if results:
        result_table = Table(title="\n下载详情", title_style="bold magenta")
        result_table.add_column("序号", justify="right")
        result_table.add_column("URL", justify="left", no_wrap=False)
        result_table.add_column("状态", justify="center")
        result_table.add_column("保存路径", justify="left", no_wrap=False)

        for i, res in enumerate(results, 1):
            # status_style = "green" if res["status"] == "success" else "red"
            status = (
                f"[green]成功（{res['code']}）[/green]"
                if res["status"] == "success"
                else f"[red]失败（{res['code']}）[/red]"
            )
            file_path = res.get("file", "---")
            url = res.get("raw", res["url"])
            result_table.add_row(str(i), url, status, file_path)
        console.print(result_table)


def preprocess(list_file, urls):
    # 获取预定义URL
    predefined_urls = []
    if list_file:
        try:
            with open(list_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        more_urls = [url.strip() for url in line.split(",") if url.strip()]
                        predefined_urls.extend(more_urls)
        except Exception as e:
            logger.error(f"读取文件失败: {list_file}, error={e}", exc_info=True)

    if urls:
        predefined_urls.extend(url.strip() for url in urls.split(",") if url.strip())
    return predefined_urls


def simple_download(urls, save_path, audio):
    def _extract_resource_url(data):
        suffix_list = ["pdf"]
        if audio:
            suffix_list.extend(["mp3"])
        return extract_resource_url(data, suffix_list)

    click.echo(
        f"\n共选择 {click.style(str(len(urls)), fg='yellow')} 项目，"
        f"将保存到 {click.style(str(save_path), fg='yellow')} 目录，"
    )
    config_urls = parse_urls(urls, audio)
    resource_dict = fetch_all_data(config_urls, _extract_resource_url)
    total = len(resource_dict)

    click.echo(
        f"\n共输入URL {click.style(str(len(urls)), fg='yellow')} 个，"
        f"解析得到配置 {click.style(str(len(config_urls)), fg='yellow')} 个，"
        f"有效的资源文件共 {click.style(str(total), fg='yellow')} 个"
    )
    if total == 0:
        click.echo("\n没有找到资源文件（PDF/MP3等）。结束下载")
        return

    # 开始下载
    start_time = time.time()
    click.echo("\n开始下载文件...")
    console = Console()

    # 下载文件
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        download_task = progress.add_task("正在下载文件...", total=total)
        results = download_files(resource_dict, save_path)
        progress.update(download_task, completed=total)

    # 显示统计信息
    elapsed_time = time.time() - start_time
    display_results(console, results, elapsed_time)


def _interactive_mode1():
    hier_dict, tag_dict, id_dict = None, None, None
    if hier_dict is None:
        click.echo("\n联网查询科目数据中……")
        hier_dict, tag_dict, id_dict = fetch_metadata()
    if hier_dict is None:
        click.secho("获取数据失败，稍后再试", fg="red")
        return None

    # while True:
    current_opt_id = hier_dict["next"][0]
    current_hider_dict = hier_dict
    last_name = ""
    last_hider_dict = hier_dict
    last_opt_id = current_opt_id
    while True:
        level, name, options = query_metadata(current_opt_id, current_hider_dict, tag_dict, id_dict)
        option_names = [op for _, op in options]
        if len(options) == 0:
            click.secho(f"当前{last_name}没有候选，请重新选择其他{last_name}", fg="red")
            current_hider_dict = last_hider_dict
            current_opt_id = last_opt_id
            continue
        elif level == -1:
            break

        display_urls(option_names, f"请选择以下某项{last_name}【{name}】（共{len(options)}项）")
        new_key_index = click.prompt("请输入", default="1", show_default=True).strip()
        if new_key_index.isdigit() and 1 <= int(new_key_index) <= len(options):
            last_hider_dict = current_hider_dict
            last_opt_id = current_opt_id
            current_hider_dict = current_hider_dict[current_opt_id]
            current_opt_id, last_name = options[int(new_key_index) - 1]
        else:
            click.secho("输入不合法，请重新输入", fg="red")

    display_urls(option_names, f"目前有{last_name}书册如下（共{len(options)}项）")
    urls_to_process = gen_url_from_tags([cid for cid, _ in options])
    return urls_to_process


def _interactive_mode2():
    while True:
        click.echo("\n请输入URL（用逗号分隔）:")
        input_urls = click.prompt("").strip()
        urls_to_process = [url.strip() for url in input_urls.split(",") if url.strip()]
        if urls_to_process:
            display_urls(urls_to_process, "输入的URL列表")
            break
        click.secho("未输入有效URL，请重新输入", fg="red")
    return urls_to_process


def _interactive_filter(urls_to_process):
    selected_urls = []
    while True:
        note = "输入序号或者序号范围，如: 1-3,5,7-9"
        click.echo(f"\n请选择要下载的URL（{note}）:")
        range_input = click.prompt("请输入（默认全部）", default="A", show_default=True)

        selected_indices = parse_range(range_input, len(urls_to_process))
        if selected_indices:
            selected_urls = [urls_to_process[i - 1] for i in selected_indices]
            break
        click.secho("无效的选择，请重新输入", fg="red")

    resource_urls = []
    for url in selected_urls:
        if url.startswith("http"):
            resource_urls.append(url)
    return selected_urls


def _interactive_path(save_path):
    while True:
        click.echo(f"\n设置保存路径: （默认路径={save_path}）")
        if click.confirm("是否使用默认路径?", default=True):
            break

        save_path = click.prompt("请输入新的保存路径")
        is_valid, validated_path = validate_save_path(save_path)
        if is_valid:
            save_path = validated_path
            break
        click.secho(f"无效的路径: {save_path}，请重新输入", fg="red")
    return save_path


def interactive_download(default_output: str, audio: bool):
    """交互式下载流程"""

    while True:
        click.echo("\n请选择下载模式:")
        click.echo("1. 查询教材列表")
        click.echo("2. 手动输入URL")
        click.echo("0. 退出")

        choice = click.prompt("请选择", type=click.Choice(["1", "2", "0"]), show_choices=False)

        if choice == "0":
            click.echo("\n退出程序")
            sys.exit(0)

        # 获取URL列表
        urls_to_process = []
        if choice == "1":
            urls_to_process = _interactive_mode1()

        elif choice == "2":
            urls_to_process = _interactive_mode1()
        if urls_to_process is None:
            continue

        # 确认下载URL
        resource_urls = _interactive_filter(urls_to_process)
        if not resource_urls:
            click.secho("没有找到可下载的合法URL", fg="red")
            continue
        # 确认保存路径
        save_path = _interactive_path(default_output)

        # 开始下载
        simple_download(resource_urls, save_path, audio)

        # 询问是否继续
        if not click.confirm("\n是否继续下载?", default=True):
            click.echo("\n结束下载")
            break


@click.command()
@click.help_option("-h", "--help")
@click.option("--debug", "-d", is_flag=True, help="启用调试模式")
@click.option("--interactive", "-i", is_flag=True, help="交互模式")
@click.option("--audio", "-a", is_flag=True, help="下载音频文件（如果有）")
@click.option("--urls", "-u", help="URL路径列表，用逗号分隔")
@click.option("--list_file", "-f", type=click.Path(exists=True), help="包含URL的文件")
@click.option("--output", "-o", type=click.Path(), default=DEFAULT_PATH, help="下载文件保存目录")
def main(
    debug: bool,
    interactive: bool,
    audio: bool,
    urls: Optional[str],
    list_file: Optional[str],
    output: str,
):
    # 如果是请求帮助信息，不需要显示欢迎信息
    if any(arg in sys.argv[1:] for arg in ["-h", "--help"]):
        return

    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("调试模式已启用")

    display_welcome()
    try:
        if interactive and (not urls and not list_file):
            interactive_download(output, audio)
        elif urls or list_file:
            # 非交互模式，直接下载预定义URL
            predefined_urls = preprocess(list_file, urls)
            if not predefined_urls:
                logger.error("没有提供有效的URL")
                sys.exit(1)
            simple_download(predefined_urls, output, audio)
        else:
            logger.warning("请使用-u/-f提供URL列表，或使用-i进行交互")

    except Exception as e:
        logger.error(f"程序执行出错, error={e}", exc_info=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n程序已终止")
        sys.exit(0)


if __name__ == "__main__":
    main()
