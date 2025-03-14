import json
import logging
from pathlib import Path

from .configs.resources import RESOURCE_DICT
from .configs.tags import BookItem, TagHierarchy
from .utils.dl import fetch_file
from .utils.misc import get_headers


def fetch_version_data_online(version_name: str) -> list:
    """读取data_version.json等"""
    resources = RESOURCE_DICT[version_name]["resources"]
    tag_url = resources["tag"]
    version_url = resources["version"]

    headers = get_headers()
    timeout = 5
    data_format = "json"

    output = []
    for url in [tag_url, version_url]:
        name = url.split("/")[-1]
        logging.debug(f"fetch data = {url}")
        data = fetch_file(url, headers, timeout, data_format)
        output.append((name, data))

    version_data = output[-1][1]
    detail_list = []
    if version_data:
        detail_urls = version_data.get("urls", [])
        if isinstance(detail_urls, str):
            detail_urls = detail_urls.split(",")
        if detail_urls:
            for detail_url in detail_urls:
                logging.debug(f"fetch data = {detail_url}")
                detail_name = detail_url.split("/")[-1]
                out = fetch_file(detail_url, headers, timeout, data_format)
                detail_list.append((detail_name, out))
    output.append(("details", detail_list))
    return output


def load_version_data_local(version_name: str, data_dir: str) -> list:
    """从本地读取data_version.json等"""
    resources = RESOURCE_DICT[version_name]["resources"]
    tag_url = resources["tag"]
    version_url = resources["version"]

    base_dir = Path(data_dir, version_name.strip("/"))

    output = []
    for url in [tag_url, version_url]:
        name = url.split("/")[-1]
        data_file = Path(base_dir, name)
        logging.debug(f"fetch data = {data_file}")
        with open(data_file, encoding="utf-8") as f:
            data = json.load(f)
        output.append((name, data))

    version_data = output[-1][1]
    detail_list = []
    if version_data:
        detail_urls = version_data.get("urls", [])
        if isinstance(detail_urls, str):
            detail_urls = detail_urls.split(",")
        if detail_urls:
            for detail_url in detail_urls:
                detail_name = detail_url.split("/")[-1]
                data_file = Path(base_dir, detail_name)
                with open(data_file, encoding="utf-8") as f:
                    out = json.load(f)
                logging.debug(f"fetch data = {data_file}, data={len(out)}")
                detail_list.append((detail_name, out))

    output.append(("details", detail_list))

    return output


def save_version_data(name, save_dir):
    """获取在线data_version.json等并保存"""
    output = fetch_version_data_online(name)

    save_dir = Path(save_dir, name.strip("/"))
    if not save_dir.exists():
        logging.info(f"Create dir {save_dir}")
        save_dir.mkdir(parents=True)

    for name, data in output[:2] + output[2][1]:
        save_file = Path(save_dir, name)
        logging.info(f"save data {save_file}")
        with open(save_file, "w") as f:
            json.dump(data, f, indent=None, ensure_ascii=False)


def update_hierarchies(tag_hier: TagHierarchy, tag_dict: dict, book_list: list[BookItem]):
    for book_item in book_list:
        tag_paths = book_item.tag_path.split("/")

        prev_item = tag_hier
        current_item = tag_hier
        if tag_paths[0] != tag_hier.tag_id:
            continue

        for i in range(1, len(tag_paths)):
            current_tag_id = tag_paths[i]
            prev_item = current_item

            # current_item = None
            flag = False
            if prev_item is not None:
                for j, item in enumerate(prev_item.children):
                    if item.tag_id == current_tag_id:
                        current_item = prev_item.children[j]
                        flag = True
                        break

            if flag:
                continue

            name = tag_dict[current_tag_id]
            new_tag = TagHierarchy(prev_item.level + 1, name, current_tag_id, name)
            new_tag.set_book(book_item)
            prev_item.add_child(new_tag)

    return tag_hier


def fetch_metadata(data_dir=None, local=False):
    # 生成教材层级结构以及对应书名、ID等
    name = "/tchMaterial"  # TODO 目前仅教材，待支持课件

    version_data = None
    if not local:
        logging.debug(f"Fetch online data")
        version_data = fetch_version_data_online(name)

    if (version_data is None or version_data[0][1] is None) and data_dir:
        logging.debug("Fetch local data")
        version_data = load_version_data_local(name, data_dir)
    tag_data = version_data[0][1]

    if not tag_data:
        return None

    parts_data = [line for _, entry in version_data[2][1] for line in entry]
    logging.debug(f"parts_data = {len(parts_data)}")

    tag_dict = {}
    book_list = []
    for e in parts_data:
        for tag in e["tag_list"]:
            tag_id = tag["tag_id"]
            if tag_id not in tag_dict:
                tag_dict[tag_id] = tag["tag_name"]

        for tag_path in e["tag_paths"]:
            tag_id = tag_path.split("/")[-1]
            book_item = BookItem(e["id"], e["title"], tag_path, tag_id)
            book_list.append(book_item)

    # 专题*/电子教材
    meta_data = TagHierarchy.from_dict(0, tag_data)
    meta_data = update_hierarchies(meta_data, tag_dict, book_list)
    return meta_data


def query_metadata(tag_hier: TagHierarchy, max_level: int = 5):
    # 获得下一级列表
    title = tag_hier.name
    children = tag_hier.children
    is_book, book_options = tag_hier.get_options()

    logging.debug(f"{tag_hier.level}, {is_book}, options = {[opt[1] for opt in book_options]}")
    return title, book_options, children, is_book


if __name__ == "__main__":
    fmt = "%(asctime)s %(filename)s [line:%(lineno)d] %(levelname)s %(message)s"
    logging.basicConfig(level=logging.INFO, format=fmt)

    names = ["/tchMaterial", "/syncClassroom"]
    save_dir = "../data2"
    for name in names:
        save_version_data(name, save_dir)
