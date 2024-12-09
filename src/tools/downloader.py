import logging
from concurrent.futures import as_completed, ThreadPoolExecutor
from pathlib import Path
from typing import Callable

from .utils import gen_filename, get_headers
from .utils_dl import download_file, fetch_single_data


def download_file2(url, name, save_dir, raw_url):
    headers = get_headers()
    timeout = 10
    chunk_size = 16 * 1024  # 16k
    file_path = gen_filename(url, name, save_dir)
    out = download_file(url, headers, timeout, chunk_size, file_path)
    out["raw"] = raw_url
    return out


def download_files(url_dict: dict, output_dir: str, max_workers: int = 5) -> list:
    """并发下载多个文件"""
    save_dir = Path(output_dir)
    if not save_dir.exists():
        save_dir.mkdir(parents=True)

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(download_file2, url, name, save_dir, raw_url): url
            for url, [name, raw_url] in url_dict.items()
        }
        for future in as_completed(future_to_url):
            # url = future_to_url[future]
            result = future.result()
            results.append(result)

    return results


def download_files_tk(
    app, url_dict: dict, output_dir: str, max_workers: int = 5, base_progress: int = 0
) -> list:
    """tk下载文件，更新进度条"""
    save_dir = Path(output_dir)
    if not save_dir.exists():
        save_dir.mkdir(parents=True)

    results = []
    total = len(url_dict)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(download_file2, url, name, save_dir, raw_url): url
            for url, [name, raw_url] in url_dict.items()
        }
        for future in as_completed(future_to_url):
            # url = future_to_url[future]
            result = future.result()
            results.append(result)

            finished = len(results)
            app.progress_label.config(text=f"已经下载 {finished} / {total} 项资源...")
            app.progress_var.set(base_progress + (finished / total) * (100 - base_progress))
            app.update()

    return results


def fetch_all_data(url_list: list, extract_func: Callable, max_workers: int = 5) -> dict:
    """
    获取配置信息
    """
    headers = get_headers()
    timeout = 5
    data_format = "json"

    results = {}
    total = len(url_list)

    # with tqdm(total=total, desc="获取资源链接") as pbar:
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(fetch_single_data, url, headers, timeout, data_format): url
            for url in url_list
        }

        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                if result:
                    resource = extract_func(result)
                    for title, resource_url in resource:
                        if resource_url:
                            logging.debug(f"title = {title}, resource_url={resource_url}")
                            results[resource_url] = [title, url]
                else:
                    logging.debug(f"None data URL = {url}")
            except Exception as e:
                logging.error(f"处理URL失败: {url}, 错误: {e}")
            # finally:
            #     pbar.update(1)
            #     # pbar.set_postfix({"找到": len(results)})

    return results
