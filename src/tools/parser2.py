"""
smartedu教材等层级列表解析
"""

import json
import logging
from pathlib import Path

from .downloader import fetch_single_data
from .parser import RESOURCE_DICT
from .utils import get_headers


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
        out["next"] = next_paths
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


def _fetch_raw_local(name):
    base = "../data"
    logging.debug(f"Try load data from local {base}")
    resources = RESOURCE_DICT[name]["resources"]
    tag_url = resources["tag"]
    version_url = resources["version"]
    tag_file = Path(base, name.strip("/"), tag_url.split("/")[-1])
    version_file = Path(base, name.strip("/"), version_url.split("/")[-1])
    parts_data = []
    if any([not file.exists() for file in [tag_file, version_file]]):
        return None, parts_data

    tag_data = json.load(open(tag_file))
    version_data = json.load(open(version_file))

    more_urls = version_data.get("urls", [])
    if isinstance(more_urls, str):
        more_urls = more_urls.split(",")

    if more_urls:
        for url in more_urls:
            file = Path(base, name.strip("/"), url.split("/")[-1])
            out = json.load(open(file))
            logging.debug(f"Read {file}, data={len(out)}")
            if out:
                parts_data.extend(out)
    return tag_data, parts_data


def fetch_metadata():
    # 生成教材层级结构以及对应书名、ID等
    name = "/tchMaterial"  # TODO 目前仅教材，待支持课件
    tag_data, parts_data = _fetch_raw(name)
    if not tag_data:
        tag_data, parts_data = _fetch_raw_local(name)
    if not tag_data:
        return None, None, None

    # 专题*/电子教材
    hier_dict = _parse_tag_hiers(tag_data, level=1)
    tag_dict = _parse_tag_dict(tag_data)
    hier_tags_title = {}
    hier_tags_id = {}
    for e in parts_data:
        for tp in e["tag_paths"]:
            tp_list = tp.strip().split("/")
            k2 = tp_list[-1].strip()
            tmp_hier_dict = hier_dict
            for k in tp_list[1:]:
                if k not in tmp_hier_dict:
                    break
                tmp_hier_dict = tmp_hier_dict[k]
            if "list" in tmp_hier_dict and k2 not in tmp_hier_dict["list"]:
                tmp_hier_dict["list"].append(k2)
            if k2:
                hier_tags_title[k2] = e["title"]
                hier_tags_id[k2] = e["id"]  # contentId

    logging.debug(f"hier_tags_title = {len(hier_tags_title)}")
    logging.debug(f"tag_dict = {len(tag_dict)}")
    logging.debug(f"hier_tags_id = {len(hier_tags_id)}")
    tag_dict.update(hier_tags_title)

    return hier_dict, tag_dict, hier_tags_id


def query_metadata(key, hier_dict, tag_dict, id_dict):
    # 获得下一级列表
    data = hier_dict[key]

    options = []
    if "next" in data:
        level = data["level"]
        name = data["name"]
        for k in data["next"]:
            if k and k in data:
                options.append([k, data[k]["tag"]])
    else:
        level = -1
        name = "课本分册"
        for k in data["list"]:
            if k and k in tag_dict and k in id_dict:
                options.append([id_dict[k], tag_dict[k]])
    return level, name, options


def gen_url_from_tags(content_id_list):
    # 转化成URL
    name = "/tchMaterial"
    resources = RESOURCE_DICT[name]["resources"]
    example_url = resources["detail"]
    urls = [example_url.format(contentId=cid) for cid in content_id_list]
    return urls
