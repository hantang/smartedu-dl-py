"""
smartedu配置信息和解析
"""

import logging
import random
from urllib.parse import parse_qs, urlparse

SERVER_LIST = [
    "s-file-1",
    "s-file-2",
    "s-file-3",
]

SERVER_LIST2 = [
    "pretest-s-file-1",
    "pretest-s-file-2",
    "pretest-s-file-3",
]

# resource_type_code/resource_type_code_name
RESOURCE_TYPE_DICT = {
    "assets_document": ["文档", ["pdf", "jpg", "superboard"]],
    "assets_audio": ["音频", ["mp3", "ogg"]],
    "assets_video": ["视频", ["m3u8"]],
}

TI_FORMATS = [
    ["folder", "image/jpg"],
    ["jpg", "image/jpg"],
    ["m3u8", "video/m3u8"],
    ["mp3", "audio/mp3"],
    ["ogg", "audio/ogg"],
    ["pdf", "application/pdf"],
    ["superboard", "superboard"],
]

DOMAIN_REMAP_DICT = {
    "web-bd.ykt.eduyun.cn": "basic.smartedu.cn",
    "xue-test.ykt.eduyun.cn": "basic.smartedu.cn",
    "jpk-test.ykt.eduyun.cn": "jpk.basic.smartedu.cn",  # 基础教育精品课
}

RESOURCE_DICT = {
    "/tchMaterial": {
        # 电子教材层级和列表数据等
        "name": "教材",
        "example": ["https://basic.smartedu.cn/tchMaterial"],
        "resources": {
            "version": "https://s-file-1.ykt.cbern.com.cn/zxx/ndrs/resources/tch_material/version/data_version.json",
            "tag": "https://s-file-1.ykt.cbern.com.cn/zxx/ndrs/tags/tch_material_tag.json",
            "detail": "https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId={contentId}",
        },
    },
    "/syncClassroom": {
        # 电子课件层级和列表数据等
        "name": "课程教学",
        "example": ["https://basic.smartedu.cn/syncClassroom"],
        "resources": {
            "version": "https://s-file-1.ykt.cbern.com.cn/zxx/ndrs/national_lesson/teachingmaterials/version/data_version.json",
            "tag": "https://s-file-1.ykt.cbern.com.cn/zxx/ndrs/tags/national_lesson_tag.json",
            "national_type": "https://s-file-1.ykt.cbern.com.cn/zxx/ndrs/tags/national_type.json",
            "prepare_type": "https://s-file-1.ykt.cbern.com.cn/zxx/ndrs/tags/prepare_type.json",
            "k12": "https://s-file-1.ykt.cbern.com.cn/zxx/ndrs/tags/k12.json",
            "detail": "https://basic.smartedu.cn/syncClassroom/classActivity?activityId={activityId}",
            "detail2": "https://basic.smartedu.cn/syncClassroom/prepare/detail?resourceId={resourceId}",
        },
    },
    "/tchMaterial/detail": {
        "name": "教材",
        "params": ["contentId"],
        "examples": [
            "https://basic.smartedu.cn/tchMaterial/detail?contentType=assets_document&contentId=1c73b348-e8b6-47d6-84b0-6dbacbe28268&catalogType=tchMaterial&subCatalog=tchMaterial"
        ],
        "resources": {
            # server 取自SERVER_LIST中的一个
            # 课本PDF
            "default": "https://{server}.ykt.cbern.com.cn/zxx/ndrv2/resources/tch_material/details/{contentId}.json",
            # 备用 旧版本
            "backup": "https://{server}.ykt.cbern.com.cn/zxx/ndrs/resources/tch_material/details/{contentId}.json",
            # 配套音频
            "audio": "https://{server}.ykt.cbern.com.cn/zxx/ndrs/resources/{contentId}/relation_audios.json",
        },
    },
    "/syncClassroom/experimentLesson": {
        "name": "课程教学>教师备课授课>实验教学",
        "params": ["courseId"],
        "examples": [
            "https://basic.smartedu.cn/syncClassroom/experimentLesson?courseId=72556642-a27e-911a-addb-16ad13036d06&classHourId=lesson_1"
        ],
        "resources": {
            "default": "https://{server}.ykt.cbern.com.cn/zxx/ndrs/experiment/resources/details/{courseId}.json",
        },
    },
    "/syncClassroom/prepare/detail": {
        "name": "课程教学>教师授课备课",
        "params": ["resourceId"],
        "examples": [
            "https://basic.smartedu.cn/syncClassroom/prepare/detail?resourceId=3e37109b-3720-30b6-ec41-2e6f82289d0d&classHourId=lesson_1",
            "https://web-bd.ykt.eduyun.cn/syncClassroom/prepare/detail?resourceId=3e37109b-3720-30b6-ec41-2e6f82289d0d&classHourId=lesson_1",
        ],
        "resources": {
            # 课本、课件、视频等
            "default": "https://{server}.ykt.cbern.com.cn/zxx/ndrv2/prepare_sub_type/resources/details/{resourceId}.json",
        },
    },
    "/syncClassroom/classActivity": {
        "name": "课程教学>学生自主学习, 课程教学>教师备课资源",
        "params": ["activityId"],
        "examples": [
            "https://basic.smartedu.cn/syncClassroom/classActivity?activityId=f3154132-92c9-4ba2-b528-dc9b929694a0&chapterId=e664f90c-8bf6-37e9-b572-22cfe23c2b48&teachingmaterialId=2fbcdb5d-0682-4cca-b979-076d0119e3d3&fromPrepare=0"
        ],
        "resources": {
            "default": "https://{server}.ykt.cbern.com.cn/zxx/ndrv2/national_lesson/resources/details/{activityId}.json",
        },
    },
    "/syncClassroom/examinationpapers": {
        "name": "课程教学>教师备课授课>习题资源",
        "params": ["resourceId"],
        "examples": [
            "https://basic.smartedu.cn/syncClassroom/examinationpapers?resourceId=f374fc22-71e5-429f-be3d-e3ddc21aeab2&chapterId=a1a96830-f6aa-3e67-91d0-6cdc597fa1d6&teachingmaterialId=d92ca54e-2cdc-4921-95f3-769eafd0c814&fromPrepare=1"
        ],
        "resources": {
            "default": "https://{server}.ykt.cbern.com.cn/zxx/ndrs/examinationpapers/resources/details/{resourceId}.json",
        },
    },
    "/syncClassroom/basicWork/detail": {
        "name": "课程教学>教师备课授课>基础性作业",
        "params": ["contentId"],
        "examples": [
            "https://basic.smartedu.cn/syncClassroom/basicWork/detail?contentType=assets_document&contentId=62044dd6-2ee9-454e-9db5-66693a302b70&catalogType=basicWork"
        ],
        "resources": {
            "default": "https://{server}.ykt.cbern.com.cn/zxx/ndrs/special_edu/resources/details/{contentId}.json",
        },
    },
    "/schoolService/detail": {
        "name": "课后服务",
        "params": ["contentId"],
        "examples": [
            "https://basic.smartedu.cn/schoolService/detail?contentType=assets_document&contentId=64fe6c2c-dd2f-432d-b844-319517da49f8&catalogType=schoolService&subCatalog=jdyd",
            "https://basic.smartedu.cn/schoolService/detail?contentType=assets_video&contentId=714f2940-5a2a-4c99-90bd-5eab4b50a171&catalogType=schoolService&subCatalog=ysjy",
            "https://basic.smartedu.cn/schoolService/detail?contentType=thematic_course&contentId=9c7b6c05-b452-4a7e-9397-288d70f749bc&catalogType=schoolService&subCatalog=kpjy",
        ],
        "resources": {
            "default": "https://{server}.ykt.cbern.com.cn/zxx/ndrs/special_edu/resources/details/{contentId}.json",
            # 限制contentType=thematic_course 课后服务>科普教育
            "thematic_course": "https://{server}.ykt.cbern.com.cn/zxx/ndrs/special_edu/thematic_course/{contentId}/resources/list.json",
        },
    },
    "/sedu/detail": {
        "name": "德育",
        "params": ["contentId"],
        "examples": [
            "https://basic.smartedu.cn/sedu/detail?contentType=assets_video&contentId=bd636b98-03e4-4f6d-a0a2-7fe8e5019770&catalogType=sedu&subCatalog=xffz",
            "https://x-api.ykt.eduyun.cn/proxy/assessment/v1/assessments/bd636b98-03e4-4f6d-a0a2-7fe8e5019770?assessment_type=assets_video",
        ],
        "resources": {
            "default": "https://{server}.ykt.cbern.com.cn/zxx/ndrs/special_edu/resources/details/{contentId}.json",
        },
    },
    "/specialEdu/detail": {
        "name": "特殊教育",
        "params": ["contentId"],
        "examples": [
            "https://basic.smartedu.cn/specialEdu/detail?contentType=assets_video&contentId=8e0f627c-97ba-72cd-7cc6-c369fe2b24f9&catalogType=specialEdu&subCatalog=rhjy&libraryId=220aaecd-6eb9-4ed3-b529-84f4e385ddca"
        ],
        "resources": {
            "default": "https://{server}.ykt.cbern.com.cn/zxx/ndrs/special_edu/resources/details/{contentId}.json",
        },
    },
    "/family/detail": {
        "name": "家庭教育",
        "params": ["contentId"],
        "examples": [
            "https://basic.smartedu.cn/family/detail?contentType=assets_video&contentId=419ff2e0-8f7d-4627-8348-6bb3bb3e2592&catalogType=family&subCatalog=jyff"
        ],
        "resources": {
            "default": "https://{server}.ykt.cbern.com.cn/zxx/ndrs/special_edu/resources/details/{contentId}.json",
        },
    },
    "/eduReform/detail": {
        "name": "教改经验",
        "params": ["contentId"],
        "examples": [
            "https://basic.smartedu.cn/eduReform/detail?contentType=assets_video&contentId=58f3bdf5-28e1-442b-8102-8ccbb6e21399&catalogType=eduReform&subCatalog=ywjy"
        ],
        "resources": {
            "default": "https://{server}.ykt.cbern.com.cn/zxx/ndrs/special_edu/resources/details/{contentId}.json",
        },
    },
    "/wisdom/detail": {
        "name": "劳动教育>劳动智慧",
        "params": ["contentId"],
        "examples": [
            "https://basic.smartedu.cn/wisdom/detail?contentType=assets_video&contentId=30f4ed2d-598a-4976-9072-d8d6960e40fe&catalogType=wisdom&subCatalog=aljj"
        ],
        "resources": {
            "default": "https://{server}.ykt.cbern.com.cn/ldjy/ndrs/special_edu/resources/details/{contentId}.json"
        },
    },
    "/yearQualityCourse": {
        "name": "基础教育精品课：微课展示",
        "params": ["courseId"],
        "examples": [
            "https://jpk.basic.smartedu.cn/yearQualityCourse?courseId=0860683c-e824-646b-68bf-1d6052c6f496&courseType=elite_lesson&classHourId=lesson_1"
        ],
        "resources": {
            "default": "https://{server}.ykt.cbern.com.cn/competitive/elite_lesson/resources/{courseId}.json",
        },
    },
    "/sport/courseDetail": {
        "name": "体育",
        "params": ["courseId"],
        "examples": [
            "https://basic.smartedu.cn/sport/courseDetail?courseId=9170b99a-f442-46d8-80b1-60bb82ee5174&tag=篮球&channelId=40bca6ef-ee76-40c8-b059-89e5baf01134&libraryId=3cdefab6-f36b-4bf7-ae44-033577ba93af&breadcrumb=运动技能&firstLevel=64868ec4-935b-4904-b39c-d56c6841301e&secondLevel=ed81a602-d760-4b55-9403-ba9725593e70&resourceId=673c4906-4194-4f3c-b49e-652e3641ee5f"
        ],
        "resources": {
            "first": "https://{server}.ykt.cbern.com.cn/twy/s_course/v2/business_courses/{courseId}/course_relative_infos/zh-CN.json",
            "second": "https://{server}.ykt.cbern.com.cn/twy/s_course/v2/activity_sets/{activity_set_id}/fulls.json",
            # activity_set_id 来自zh-CN.json
        },
    },
    "/art/courseDetail": {
        "name": "美育",
        "params": ["courseId"],
        "examples": [
            "https://basic.smartedu.cn/art/courseDetail?courseId=c94d7dba-d764-4fba-b9a1-db40cb2035cd&tag=声乐类&channelId=31741f87-5444-42f9-ac3f-795d7dc7ef7a&libraryId=7612f2f2-98f1-46e1-b889-36bdecdbe63e&breadcrumb=音乐&firstLevel=c9b9ccdc-6c24-43f3-842a-edd55333a0df&secondLevel=d942b76a-88ca-4939-aa58-e8747a9cff64&thirdLevel=5afd4d11-10e5-44e7-9c2e-0b798f487f79&resourceId=6987b582-a003-49fa-9159-c457379834aa"
        ],
        "resources": {
            "first": "https://{server}.ykt.cbern.com.cn/twy/s_course/v2/business_courses/{courseId}/course_relative_infos/zh-CN.json",
            "second": "https://{server}.ykt.cbern.com.cn/twy/s_course/v2/activity_sets/{activity_set_id}/fulls.json",
            # activity_set_id 来自zh-CN.json
        },
    },
}


def _clean_url(resource_url):
    # https://r1-ndr-private.ykt.cbern.com.cn -> https://r1-ndr.ykt.cbern.com.cn
    return resource_url.replace("ndr-private.", "ndr.")


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


def parse_urls(urls: list, audio: bool = False) -> list:
    # 根据URL路径判断资源类型，获得临时的配置信息URL(config, 返回json数据)，再解析得到最终资源URL
    config_urls = []
    config_key = "default"
    config_key2 = "audio"
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
            if item["ti_format"] == suffix and item["ti_storages"]:
                resource_url = random.choice(item["ti_storages"])
                resource_url = _clean_url(resource_url)
                break

        # jpg: entry["custom_properties"]["preview"]
        output.append([f"{title}.{suffix}", resource_url])
    return output


def extract_resource_url(data: dict | list, suffix_list: list) -> list:
    # TODO "pdf", "mp3", "ogg", "m3u8"
    logging.debug(f"extract suffix = {suffix_list}")
    out = []
    for suffix in suffix_list:
        result = _extract_resource(data, suffix)
        out.extend(result)
        logging.debug(f"result = {result}")
    return out
