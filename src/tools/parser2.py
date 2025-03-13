"""
smartedu教材等层级列表解析
"""

import json
import logging
from pathlib import Path

from .downloader import fetch_single_data
from .parser import RESOURCE_DICT
from .utils import get_headers
from .books import BookItem, BookPDF


def _traverse_tag_path(data):
    key1 = "hierarchies"
    key2 = "children"
    tags = []
    for child in data:
        if child[key1]:
            hier = child[key1][0]
            tags.extend(hier["ext"]["hidden_tags"])
            result = _traverse_tag_path(hier[key2])
            tags.extend(result)
    return tags


def _parse_tag_hiers(data, level):
    # 获得页面层及结构（电子教材（学段）->中、小学->学科->版本->年级/册次合并）
    key1 = "hierarchies"
    key2 = "children"
    key3 = "hierarchy_name"
    if data[key1] is None:
        return {}

    hier = data[key1][0]

    children = hier[key2]
    name = hier[key3]

    out = {}
    if name in ["年级", "册次"]:
        tags = _traverse_tag_path(children)
        if hier["ext"]["hidden_tags"]:
            tags = hier["ext"]["hidden_tags"] + tags
        return {"list": tags}
    else:
        next_paths = hier["ext"]["has_next_tag_path"]
        next_paths = [v for v in next_paths if v not in hier["ext"]["hidden_tags"]]
        out["level"] = level
        out["name"] = name
        out["children"] = next_paths
        for i, child in enumerate(children):
            tag_id, tag_name = child["tag_id"], child["tag_name"]
            result = _parse_tag_hiers(child, level + 1)
            result["tag"] = tag_name
            out[tag_id] = result
    return out


def _parse_tag_dict(data):
    key1 = "hierarchies"
    key2 = "children"

    out = {}
    key_id = data.get("tag_id", data.get("tag_path"))
    if key_id is None:
        return out
    tag = data.get("tag_name")
    out[key_id] = tag
    if data.get(key1):
        for hier in data[key1]:
            children = hier[key2]
            for e in children:
                res = _parse_tag_dict(e)
                out.update(res)
    return out


def _fetch_raw(name):
    resources = RESOURCE_DICT[name]["resources"]
    tag_url = resources["tag"]
    version_url = resources["version"]

    headers = get_headers()
    timeout = 5
    data_format = "json"
    parts_data = []

    tag_data = fetch_single_data(tag_url, headers, timeout, data_format)
    version_data = fetch_single_data(version_url, headers, timeout, data_format)
    if any([data is None for data in [tag_data, version_data]]):
        return None, parts_data

    more_urls = version_data.get("urls", [])
    if isinstance(more_urls, str):
        more_urls = more_urls.split(",")

    if more_urls:
        for url in more_urls:
            out = fetch_single_data(url, headers, timeout, data_format)
            if out:
                parts_data.extend(out)
    return tag_data, parts_data


def _fetch_raw_local(name, data_dir):
    logging.debug(f"Try load data from local {data_dir}")
    if not (data_dir and Path(data_dir).exists()):
        logging.warning(f"No data dir = {data_dir}")
        return None, None

    resources = RESOURCE_DICT[name]["resources"]
    tag_url = resources["tag"]
    version_url = resources["version"]
    tag_file = Path(data_dir, name.strip("/"), tag_url.split("/")[-1])
    version_file = Path(data_dir, name.strip("/"), version_url.split("/")[-1])
    parts_data = []
    if any([not file.exists() for file in [tag_file, version_file]]):
        return None, parts_data

    with open(tag_file, encoding="utf-8") as f:
        tag_data = json.load(f)
    with open(version_file, encoding="utf-8") as f:
        version_data = json.load(f)

    more_urls = version_data.get("urls", [])
    if isinstance(more_urls, str):
        more_urls = more_urls.split(",")

    if more_urls:
        for url in more_urls:
            file = Path(data_dir, name.strip("/"), url.split("/")[-1])
            with open(file, encoding="utf-8") as f:
                out = json.load(f)
            logging.debug(f"Read {file}, data={len(out)}")
            if out:
                parts_data.extend(out)
    return tag_data, parts_data


def _parse_hierarchies(level, tag_item, tag_dict):
    hierarchies = tag_item.get("hierarchies")
    tag_id = tag_item["tag_id"]
    tag_name = tag_item["tag_name"]
    # assert tag_name == tag_dict[tag_id], (tag_name, tag_dict[tag_id])

    if hierarchies is None:
        bookItem = BookItem(level, "-", tag_id, tag_name)
        return bookItem

    hierarchy = hierarchies[0]
    children = hierarchy["children"]
    bookItem = BookItem(level, hierarchy["hierarchy_name"], tag_id, tag_name)

    if len(children) > 0:
        for child in children:
            childBook = _parse_hierarchies(level + 1, child, tag_dict)
            bookItem.add_child(childBook)

    return bookItem


def _update_hierarchies(book_base: BookItem, tag_dict: dict, doc_list: list[BookPDF]):
    for bookPDF in doc_list:
        # logging.info(f"bookPDF = {bookPDF.tag_path} {bookPDF.book_name}")
        tag_paths = bookPDF.tag_path.split("/")

        prev_item = book_base
        current_item = book_base
        if tag_paths[0] != book_base.tag_id:
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
            # logging.info(f"{i}, current_tag_id = {current_tag_id} / current_item={current_item.level}/{current_item.tag_name}")
            if flag:
                continue

            name = tag_dict[current_tag_id]
            new_book_item = BookItem(prev_item.level + 1, name, current_tag_id, name)
            new_book_item.set_book(bookPDF.book_id, bookPDF.book_name)
            prev_item.add_child(new_book_item)
    return book_base


def fetch_metadata(data_dir=None, local=False):
    # 生成教材层级结构以及对应书名、ID等
    name = "/tchMaterial"  # TODO 目前仅教材，待支持课件

    tag_data, parts_data = None, None
    if not local:
        logging.debug(f"Fetch online data")
        tag_data, parts_data = _fetch_raw(name)

    if not tag_data and data_dir:
        logging.debug("Fetch local data")
        tag_data, parts_data = _fetch_raw_local(name, data_dir)

    if not tag_data:
        return None

    tag_dict = {}
    doc_list = []
    for e in parts_data:
        for tag in e["tag_list"]:
            tag_id = tag["tag_id"]
            if tag_id not in tag_dict:
                tag_dict[tag_id] = tag["tag_name"]

        for tag_path in e["tag_paths"]:
            tag_id = tag_path.split("/")[-1]
            bookPDF = BookPDF(e["id"], e["title"], tag_path, tag_id)
            doc_list.append(bookPDF)

    tag_base = tag_data["hierarchies"][0]
    tag_items = tag_base["children"][0]

    # 专题*/电子教材
    book_item = _parse_hierarchies(1, tag_items, tag_dict)
    book_base = BookItem(
        0, tag_base["hierarchy_name"], tag_data["tag_path"], tag_base["hierarchy_name"]
    )
    book_base.add_child(book_item)
    book_base = _update_hierarchies(book_base, tag_dict, doc_list)
    return book_base


def query_metadata(book_item: BookItem, max_level: int = 5):
    # 获得下一级列表
    title = book_item.name
    children = book_item.children
    is_book = False
    book_options = []
    if len(children) > 0 and children[0].is_book:
        for child in children:
            tag_name = "《{}》".format(child.book_name.replace("•", "·"))
            book_options.append((child.book_id, tag_name))
        children = []
        is_book = True
    else:
        for child in children:
            tag_name = child.tag_name.replace("•", "·")
            tag_name = tag_name.replace(" ", "")
            book_options.append((child.tag_id, tag_name))

    # if book_item.is_book or book_item.level >= max_level:
    option_names = [opt[1] for opt in book_options]
    logging.info(f"{book_item.level}, {is_book}, options = {option_names}")

    return title, book_options, children, is_book


def gen_url_from_tags(content_id_list):
    # 转化成URL
    name = "/tchMaterial"
    resources = RESOURCE_DICT[name]["resources"]
    example_url = resources["detail"]
    urls = [example_url.format(contentId=cid) for cid in content_id_list]
    return urls
