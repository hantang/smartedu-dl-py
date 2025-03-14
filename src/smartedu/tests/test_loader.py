from ..loader import fetch_metadata


def test_fetch_metadata():
    data_dir = "../data/v2/"
    meta_data = fetch_metadata(data_dir, True)
    data = [
        (0, "专题*", ""),
        (0, "电子教材", ""),
        (0, "学科", ""),
        (0, "版本", ""),
        (0, "年级", ""),
        (0, "册次", ""),
        (0, "上册", "（根据2022年版课程标准修订）义务教育教科书·道德与法治一年级上册"),
    ]
    current = meta_data
    for index, name, book in data:
        # print(current)
        assert current.name == name, (current.name, name)
        if index >= len(current.children):
            # print(current.book_item)
            assert current.book_item.book_name == book
            break
        current = current.children[index]
