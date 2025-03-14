"""
使用requests库下载文件
"""

import logging
from pathlib import Path
from typing import Any

import requests


def fetch_file(url: str, headers: dict, timeout: int = 5, data_format: str = "json") -> Any:
    # 获取json配置
    try:
        response = requests.get(url, timeout=timeout, headers=headers)
        logging.debug(f"URL = {url}, status = {response.status_code}")
        if response.ok:
            return response.json() if data_format == "json" else response.text

    except requests.exceptions.RequestException as res_err:
        logging.warning(f"URL: {url}; Request Error: {res_err}")
    except IOError as io_err:
        logging.warning(f"URL: {url}; IO Error: {io_err}")
    except Exception as err:
        logging.error(f"Download failed: {url}, 错误: {err}")

    return None


def download_file(
    file_path: str | Path,
    url: str,
    headers: dict,
    timeout: int = 5,
    stream: bool = True,
    chunk_size: int = 8192,
):
    """下载单个文件"""
    out = {"url": url, "status": "failed", "code": -1, "file": str(file_path), "size": -1}
    try:
        with requests.get(url, headers=headers, stream=True, timeout=timeout) as response:
            # response.raise_for_status()
            logging.debug(f"download url = {url}, status = {response.status_code}")
            status_code, total_size = stream_download(
                url, file_path, headers, stream, timeout, chunk_size
            )
            out["code"] = status_code
            out["size"] = total_size
            if status_code == 200 and total_size > 0:
                out["status"] = "success"
            logging.debug(f"Download success: {url} -> {file_path}")
            return out

    except requests.exceptions.RequestException as res_err:
        logging.warning(f"URL: {url}; Request Error: {res_err}")
    except IOError as io_err:
        logging.warning(f"URL: {url}; IO Error: {io_err}")
    except Exception as err:
        logging.error(f"Download failed: {url}, 错误: {err}")
    return out


def stream_download(
    url: str, file_path: str | Path, headers: dict, stream: bool, timeout: int, chunk_size: int
):
    """下载单个文件"""
    with requests.get(url, headers=headers, stream=stream, timeout=timeout) as response:
        status_code = response.status_code
        total_size = int(response.headers.get("content-length", 0))
        logging.debug(f"download url = {url}, status = {status_code}, size= {total_size}")

        if response.ok and total_size > 0:
            with open(file_path, "wb") as fw:
                if stream:
                    for data in response.iter_content(chunk_size=chunk_size):
                        fw.write(data)
                        fw.flush()
                else:
                    fw.write(response.content)

        if total_size == 0 or Path(file_path).stat().st_size != total_size:
            raise RuntimeError("Could not download file")
        return status_code, total_size


# def normal_download(url: str, file_path: str | Path, headers: dict, timeout: int=5):


# def download_ts_file(url: str, output_path: str, headers: dict, timeout: int):
#     # 非stream下载
#     try:


#     except requests.exceptions.RequestException as res_err:
#         logging.warning(f"URL: {url}; Request Error: {res_err}")
#     except IOError as io_err:
#         logging.warning(f"URL: {url}; IO Error: {io_err}")
#     except Exception as err:
#         logging.error(f"Download failed: {url}, 错误: {err}")
#     return False
