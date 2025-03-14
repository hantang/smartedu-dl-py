import base64
import random
import tempfile
from pathlib import Path

from ..configs.ua import UserAgents


def image_to_base64(filename, save_file):
    # Convert the image to base64 format
    with open(filename, "rb") as f:
        encoded_image = base64.b64encode(f.read())
    with open(save_file, "w", encoding="utf-8") as f:
        f.write(encoded_image.decode("utf-8"))


def base64_to_image(icon_str, name):
    temp_file = Path(tempfile.gettempdir(), name)
    icon_data = base64.b64decode(icon_str)
    with open(temp_file, "wb") as f:
        f.write(icon_data)
    return str(temp_file)


def format_bytes(size: float) -> str:  # 格式化字节
    # 返回以 KB、MB、GB、TB 为单位的数据大小
    for x in ["字节", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:3.1f} {x}"
        size /= 1024.0
    return f"{size:3.1f} PB"


def get_headers(auth=None):
    # ua = UserAgent(platforms=["pc", "desktop"])

    headers = {"User-Agent": random.choice(UserAgents)}
    # TODO 需要登录获取 'MAC id="0",nonce="0",mac="0"',
    if auth and "mac id=" in auth.lower():
        headers["X-ND-AUTH"] = auth
    return headers
