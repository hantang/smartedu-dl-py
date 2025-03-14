import logging
import shutil
import tempfile
from pathlib import Path
from urllib.parse import urlparse


def gen_filename(url, name, save_path, default="output.txt"):
    """确保文件名唯一，如果存在则添加添加(1), (2)等后缀"""
    save_path = Path(save_path)
    filename = name if name else (Path(urlparse(url).path).name if url else default)
    new_filename = save_path / filename
    stem = new_filename.stem

    counter = 0
    while new_filename.exists():
        counter += 1
        new_filename = save_path / f"{stem}({counter}){new_filename.suffix}"

    logging.debug(f"new file = {new_filename}, counter={counter}")
    return new_filename


def gen_filename2(save_file):
    save_file = Path(save_file)
    name = save_file.name
    return gen_filename(None, name, save_file.parent)


def clean_dir(temp_dir):
    # 清理临时文件
    try:
        logging.debug(f"清理临时目录: {temp_dir}")
        shutil.rmtree(temp_dir)
    except Exception as e:
        logging.warning(f"清理临时文件失败: {e}")


def get_file_path(base_file, filename):
    if filename is None:
        return None

    current_dir = Path(base_file).parent
    logging.debug(f"base = {base_file}\ncurrent_dir={current_dir}")

    out_path = Path(current_dir, filename).resolve()
    logging.debug(f"file = {filename}\nout={out_path}")
    return out_path

