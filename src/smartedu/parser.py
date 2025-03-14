"""
smartedu配置信息和解析
"""

import logging
import random
import re

from urllib.parse import parse_qs, urlparse

from .configs.resources import DOMAIN_REMAP_DICT, RESOURCE_TYPE_DICT, RESOURCE_DICT
from .configs.resources import FORMATS_REMAP, ACCEPTED_FORMATS, SERVER_LIST


def _convert_url(resource_url):
    # https://r1-ndr-private.ykt.cbern.com.cn -> https://r1-ndr.ykt.cbern.com.cn
    logging.debug(f"Raw URL = {resource_url}")

    new_url = resource_url
    new_url = re.sub(r"[^/]+\.pdf$", "pdf.pdf", new_url)
    new_url = re.sub("ndr-(doc-)?private", "ndr", new_url)
    logging.debug(f"New URL = {new_url}")

    return new_url


def validate_url(url: str):
    url = url.strip()
    if not url.startswith("http"):
        return None

    parse_result = urlparse(url)
    host = parse_result.netloc
    if not (host in DOMAIN_REMAP_DICT.keys() or host in DOMAIN_REMAP_DICT.values()):
        logging.debug(f"Not valid host = {host}")
        return None

    path = parse_result.path
    if path not in RESOURCE_DICT or path in ["/tchMaterial", "/syncClassroom"]:
        logging.debug(f"Not valid path = {path}")
        return None
    return parse_result


def parse_urls(urls: list, formats: list, activate_backup: bool) -> list:
    # 根据URL路径判断资源类型，获得临时的配置信息URL(config, 返回json数据)，再解析得到最终资源URL
    config_urls = []
    config_key = "default"
    config_key2 = "audio"
    config_key3 = "backup"
    audio = False
    for v in formats:
        if v.strip().lower() in RESOURCE_TYPE_DICT["assets_audio"][1]:
            audio = True
            break

    for url in set(urls):
        parse_result = validate_url(url)
        if parse_result is None:
            continue
        config_info = RESOURCE_DICT[parse_result.path]
        queries = parse_qs(parse_result.query)

        params = config_info["params"]
        params += ["contentType"]
        params_out = {}
        for key in params:
            params_out[key] = queries[key][0] if queries.get(key) else None
        params_out["server"] = random.choice(SERVER_LIST)

        contentType = params_out["contentType"]
        if contentType == "thematic_course":
            config_key = "thematic_course"

        config_url = config_info["resources"][config_key].format(**params_out)
        config_urls.append(config_url)
        if activate_backup:
            backup_urls = config_info["resources"][config_key3]
            backup_urls = [backup_url.format(**params_out) for backup_url in backup_urls]
            logging.debug(f"backup links = {backup_urls}")
            config_urls.extend(backup_urls)

        if audio and config_key2 in config_info["resources"]:
            audio_url = config_info["resources"][config_key2].format(**params_out)
            config_urls.append(audio_url)
            logging.debug(f"Add audio: {audio_url}")

    logging.debug(f"config urls = {len(config_urls)}")
    logging.debug(str(config_urls))
    return config_urls


def _extract_resource(data, suffix="pdf"):
    # suffix: pdf, jpg, mp3, ogg, ...
    data2 = data
    if isinstance(data, dict):
        if data.get("relations"):
            data2 = data["relations"].get("national_course_resource")
        else:
            data2 = [data]

    output = []
    if not data2:
        return output

    for i, entry in enumerate(data2):
        # entry_id = entry['id']
        title = entry.get("title", f"{suffix.upper()}-{i:02d}")
        resource_url = None
        for item in entry["ti_items"]:
            if item["ti_format"].lower().strip() == suffix and item["ti_storages"]:
                resource_url = random.choice(item["ti_storages"])
                break

        # jpg: entry["custom_properties"]["preview"]
        if resource_url:
            output.append([f"{title}.{suffix}", _convert_url(resource_url), resource_url])
    return output


def extract_resource_url(data: dict | list, suffix_list: list) -> list:
    logging.debug(f"extract suffix = {suffix_list}")
    out = []
    for suffix in suffix_list:
        suffix = suffix.strip().lower()
        suffix = FORMATS_REMAP.get(suffix, suffix)
        if suffix not in ACCEPTED_FORMATS:
            continue
        result = _extract_resource(data, suffix)
        out.extend(result)
        logging.debug(f"result = {result}")
    return out


def gen_url_from_tags(content_id_list):
    # 转化成URL
    name = "/tchMaterial"
    resources = RESOURCE_DICT[name]["resources"]
    example_url = resources["detail"]
    urls = [example_url.format(contentId=cid) for cid in content_id_list]
    return urls


def get_formats(formats):
    out = []
    if formats:
        out = [v.strip() for v in formats.strip(",") if v.strip() in ACCEPTED_FORMATS]
    if len(out) == 0:
        out = ["pdf"]
    return out
