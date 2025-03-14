import json
import pytest

from ..configs.tags import TagHierarchy


def test_tag_hierarchy():
    data_file = "../data/v2/tchMaterial/tch_material_tag.json"

    with open(data_file) as f:
        data = json.load(f)

    tag_hier = TagHierarchy.from_dict(0, data)
    # tag_hier.tag_id
    tag_hier.name == "专题*"
    len(tag_hier.children) == 1

    child_hier = tag_hier.children[0]

    assert child_hier.name == "电子教材"
    assert len(child_hier.children) == 6

    options = child_hier.get_options()
    option_titles = [opt[1] for opt in options]
    assert option_titles == [
        "小学",
        "初中",
        "小学（五·四学制）",
        "初中（五·四学制）",
        "高中",
        "特殊教育",
    ]


if __name__ == "__main__":
    pytest.main("-s test_tags.py")
