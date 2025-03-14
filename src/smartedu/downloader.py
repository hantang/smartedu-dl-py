import logging
from concurrent.futures import as_completed, ThreadPoolExecutor
from pathlib import Path
from typing import Callable

from .utils.dl import download_file, fetch_file
from .utils.file import gen_filename
from .utils.misc import get_headers


def _download_file(url, name, save_dir, raw_url, auth=None) -> dict:
    headers = get_headers()
    timeout = 10
    chunk_size = 16 * 1024  # 16k
    file_path = gen_filename(url, name, save_dir)
    out = download_file(
        file_path, url, headers, timeout=timeout, stream=True, chunk_size=chunk_size
    )
    out["raw"] = raw_url
    return out


def download_files(url_dict: dict, output_dir: str, max_workers: int = 5, auth: str = None) -> list:
    """并发下载多个文件"""
    save_dir = Path(output_dir)
    if not save_dir.exists():
        save_dir.mkdir(parents=True)

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(_download_file, url, name, save_dir, raw_url, auth): url
            for url, [name, raw_url] in url_dict.items()
        }
        for future in as_completed(future_to_url):
            # url = future_to_url[future]
            result = future.result()
            results.append(result)

    return results


def fetch_resources(url_list: list, extract_func: Callable, max_workers: int = 5) -> dict:
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
            executor.submit(fetch_file, url, headers, timeout, data_format): url for url in url_list
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
