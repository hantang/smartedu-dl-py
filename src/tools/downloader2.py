"""
m3u8视频下载，转换成mp4，仍有问题
# TODO: 合并失败需要处理
# 依赖：brew install ffmpeg
# 现成工具：
# - https://github.com/nilaoda/N_m3u8DL-RE
# - https://github.com/nilaoda/N_m3u8DL-CLI (only windows)
"""

import logging
import shutil
import tempfile
import time
from concurrent.futures import as_completed, ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from tqdm import tqdm

from .utils import clean_dir, gen_filename2, get_headers


def download_ts_file(url: str, output_path: str, headers: dict, timeout: int):
    response = requests.get(url, headers=headers, timeout=timeout)
    if response.ok:

        # 检查文件大小
        content_length = int(response.headers.get("content-length", 0))
        if content_length == 0:
            raise ValueError("Empty response")
        with open(output_path, "wb") as f:
            f.write(response.content)
        return True
    return False


def download_ts_file2(
    url: str,
    output_path: str,
    headers: dict,
    timeout: int,
    max_retries: int = 3,
    retry_delay: float = 1.0,
) -> str:
    """
    下载单个ts文件，支持重试机制

    Args:
        url: 文件URL
        output_path: 保存路径
        index: 文件序号
        total: 总文件数
        headers: 请求头
        timeout: 超时时间
        max_retries: 最大重试次数
        retry_delay: 重试延迟时间(秒)
    """
    for retry in range(max_retries):
        try:
            res = download_ts_file(url, output_path, headers, timeout)
            if res:
                logging.debug(f"下载成功: {url}")
                return output_path
        except Exception as e:
            if retry < max_retries - 1:
                delay = retry_delay * (retry + 1)  # 递增延迟
                logging.warning(
                    f"下载失败 {url}, 重试 {retry + 1}/{max_retries}, " f"延迟 {delay}秒: {str(e)}"
                )
                time.sleep(delay)
            else:
                logging.error(f"下载失败 {url}, 已重试{max_retries}次: {str(e)}")
    return None


def download_ts_files(base_url, segments, temp_dir: str, max_workers: int):
    """
    并发下载所有ts文件，带重试和进度显示
    """
    headers = get_headers()
    timeout = 30

    downloaded_files = []
    failed_segments = []
    total_segments = len(segments)
    logging.info(f"找到 {total_segments} 个视频片段")

    # # 降低并发数重试
    # retry_workers = max(1, max_workers // 2)
    # retry_delay = 2.0  # 增加重试延迟

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for index, segment in enumerate(segments):
            ts_url = urljoin(base_url, segment.uri)
            output_ts = Path(temp_dir, f"segment_{index:05d}.ts")
            futures.append(executor.submit(download_ts_file2, ts_url, output_ts, headers, timeout))

        # 等待所有下载完成并显示进度
        with tqdm(total=total_segments, desc="下载进度") as pbar:
            for index, future in enumerate(as_completed(futures)):
                ts_file = future.result()
                if ts_file:
                    downloaded_files.append(ts_file)
                else:
                    failed_segments.append((index, segments[index]))
                pbar.update(1)
                # 适当休眠，避免请求过快
                if index % max_workers == 0:
                    time.sleep(0.5)

    # 检查是否所有文件都下载成功
    if len(downloaded_files) != total_segments:
        missing = total_segments - len(downloaded_files)
        logging.error(f"下载不完整: 缺少 {missing} 个片段")
        # if missing / total_segments > 0.1:  # 如果缺失超过10%，则报错
        raise ValueError(
            f"下载失败: 预期 {total_segments} 个片段，实际下载 {len(downloaded_files)} 个"
        )

    # 按序号排序ts文件
    downloaded_files.sort()
    return downloaded_files


def merge_mp4(temp_dir, downloaded_files, output_path):
    """使用ffmpeg合并为mp4"""
    logging.info("使用ffmpeg合并视频片段...")
    concat_file = Path(temp_dir, "concat.txt")
    with open(concat_file, "w", encoding="utf-8") as f:
        for ts_file in downloaded_files:
            f.write(f"file '{ts_file}'\n")

    try:
        import ffmpeg

        # 计算总大小
        total_size = sum(Path(f).stat().st_size for f in downloaded_files)

        # 使用ffmpeg合并视频
        process = (
            ffmpeg.input(concat_file, format="concat", safe=0)
            .output(str(output_path), c="copy")
            .overwrite_output()
            .run_async(pipe_stdout=True, pipe_stderr=True)
        )

        # 显示进度
        last_size = 0
        with tqdm(total=total_size, unit="B", unit_scale=True, desc="合并进度") as pbar:
            while process.poll() is None:
                if output_path.exists():
                    current_size = output_path.stat().st_size
                    if current_size > last_size:
                        pbar.update(current_size - last_size)
                        last_size = current_size
                time.sleep(0.1)

            # 确保进度条到达100%
            if output_path.exists():
                final_size = output_path.stat().st_size
                if final_size > last_size:
                    pbar.update(final_size - last_size)

        stdout, stderr = process.communicate()
        # if process.returncode != 0:
        #     raise ffmpeg.Error("FFmpeg failed", stderr.decode())

        # 验证输出文件大小
        if output_path.stat().st_size == 0:
            raise ValueError("Output file is empty")

        return True

    except Exception as e:
        logging.error(f"FFmpeg合并失败: {e}")
        return False


def _merge_ts(downloaded_files, output_path):
    logging.info("直接合并ts文件...")
    total_size = sum(Path(f).stat().st_size for f in downloaded_files)

    with open(output_path, "wb") as outfile:
        with tqdm(total=total_size, unit="B", unit_scale=True, desc="合并进度") as pbar:
            for ts_file in downloaded_files:
                with open(ts_file, "rb") as infile:
                    while True:
                        chunk = infile.read(8192)  # 8KB chunks
                        if not chunk:
                            break
                        outfile.write(chunk)
                        pbar.update(len(chunk))


def m3u8_to_mp4(temp_dir: str, downloaded_files: list, output_path: Path) -> dict:
    """
    将下载的ts文件合并为mp4或ts文件
    """
    result = {"status": "failed", "file": None, "size": 0}

    try:
        # 检查是否安装了ffmpeg
        has_ffmpeg = shutil.which("ffmpeg") is not None
        logging.debug(f"FFmpeg available: {has_ffmpeg}")

        if has_ffmpeg:
            mp4_output_path = gen_filename2(output_path)
            has_ffmpeg = merge_mp4(temp_dir, downloaded_files, mp4_output_path)
            # 如果失败降级到ts合并
            if has_ffmpeg:
                output_path = mp4_output_path

        if not has_ffmpeg:
            # 直接合并ts文件
            if output_path.suffix.lower() == ".mp4":
                output_path = output_path.with_suffix(".ts")
            ts_output_path = gen_filename2(output_path)
            _merge_ts(downloaded_files, ts_output_path)
            output_path = ts_output_path

        # 检查结果
        if output_path.exists() and output_path.stat().st_size > 0:
            out = {
                "status": "success",
                "file": str(output_path),
                "size": output_path.stat().st_size,
            }
            result.update(out)
            logging.info(f"视频合并完成: {output_path}")
        else:
            raise RuntimeError("合并后的文件无效")

    except Exception as e:
        logging.error(f"合并失败: {str(e)}", exc_info=True)
        result["error"] = str(e)

    return result


def download_m3u8(url: str, output_path: str = None, max_workers: int = 10) -> dict:
    """
    下载m3u8视频并转换为mp4格式
    """
    result = {"url": url}

    # 创建临时目录存放ts文件
    temp_dir = tempfile.mkdtemp()
    logging.info(f"创建临时目录: {temp_dir}")

    # 生成输出文件路径
    if output_path is None:
        output_path = Path(temp_dir) / "output.mp4"
    else:
        output_path = Path(output_path)

    try:
        # 使用urlparse解析base_url
        parsed_url = urlparse(url)
        url_path = parsed_url.path.rsplit("/", 1)[0]
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{url_path}/"

        # 解析m3u8文件
        import m3u8
        m3u8_obj = m3u8.load(url)
        if not m3u8_obj.segments:
            raise ValueError("No segments found in m3u8 file")

        downloaded_files = download_ts_files(base_url, m3u8_obj.segments, temp_dir, max_workers)

        out = m3u8_to_mp4(temp_dir, downloaded_files, output_path)
        result.update(out)

    except Exception as e:
        logging.error(f"处理失败: {str(e)}", exc_info=True)
        result["error"] = str(e)

    finally:
        clean_dir(temp_dir)

    return result
