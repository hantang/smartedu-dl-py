"""
使用requests库下载文件
"""

import logging
from pathlib import Path


import requests


def fetch_single_data(
    url: str, headers: dict, timeout: int, data_format: str = "json"
) -> list | dict | str | None:
    # 获取json配置
    try:
        response = requests.get(url, timeout=timeout, headers=headers)
        # logging.debug(f"URL = {url}, status = {response.status_code}")
        if response.ok:
            return response.json() if data_format == "json" else response.text
        logging.debug(f"Failed url={url}, status={response.status_code}")
    except requests.exceptions.RequestException as res_err:
        logging.warning(f"URL: {url}; Request Error: {res_err}")
    except IOError as io_err:
        logging.warning(f"URL: {url}; IO Error: {io_err}")
    except Exception as err:
        logging.error(f"Download failed: {url}, 错误: {err}")

    return None


def download_file(url: str, headers: dict, timeout: int, chunk_size: int, file_path: str | Path):
    """下载单个文件"""

    out = {"url": url, "status": None, "code": -1, "file": str(file_path), "size": -1}
    try:
        with requests.get(url, headers=headers, stream=True, timeout=timeout) as response:
            # response.raise_for_status()
            logging.debug(f"download url = {url}, status = {response.status_code}")
            out["code"] = response.status_code
            if response.ok:
                total_size = int(response.headers.get("content-length", 0))

            with open(file_path, "wb") as file:
                for data in response.iter_content(chunk_size=chunk_size):
                    file.write(data)
                    file.flush()

            if total_size != 0 and Path(file_path).stat().st_size != total_size:
                raise RuntimeError("Could not download file")

            out["size"] = total_size
            out["status"] = "success"
            logging.debug(f"Download success: {url} -> {file_path}")
            return out

    except requests.exceptions.RequestException as res_err:
        logging.warning(f"URL: {url}; Request Error: {res_err}")
    except IOError as io_err:
        logging.warning(f"URL: {url}; IO Error: {io_err}")
    except Exception as err:
        logging.error(f"Download failed: {url}, 错误: {err}")

    out["status"] = "failed"
    return out


def download_ts_file(url: str, output_path: str, headers: dict, timeout: int):
    # 非stream下载
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        if response.ok:

            # 检查文件大小
            content_length = int(response.headers.get("content-length", 0))
            if content_length == 0:
                raise ValueError("Empty response")
            with open(output_path, "wb") as f:
                f.write(response.content)
            return True

    except requests.exceptions.RequestException as res_err:
        logging.warning(f"URL: {url}; Request Error: {res_err}")
    except IOError as io_err:
        logging.warning(f"URL: {url}; IO Error: {io_err}")
    except Exception as err:
        logging.error(f"Download failed: {url}, 错误: {err}")
    return False
