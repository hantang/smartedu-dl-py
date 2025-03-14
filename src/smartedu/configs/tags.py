from __future__ import annotations
from typing import Optional, Any, Dict, List, Tuple
import re


def strip(x):
    x = x.replace("•", "·")
    return re.sub(r"\s+", "", x)


class BookItem:
    def __init__(self, book_id: str, book_name: str, tag_path: str, tag_id: str):
        self.book_id = book_id
        self.book_name = book_name
        self.tag_path = tag_path
        self.tag_id = tag_id

    def __repr__(self):
        return f"BookItem: {self.book_id}/{self.book_name}"


class TagHierarchy:
    """
    convert and flatten tch_material_tag.json
    """

    def __init__(
        self,
        level: int = 0,
        name: Optional[str] = None,
        tag_id: Optional[str] = None,
        tag_name: Optional[str] = None,
        children: Optional[List[TagHierarchy]] = None,
        hierarchies_ext: Optional[Dict[str, Any]] = None,
    ):
        self.level = level
        self.name = name

        self.tag_id = tag_id
        self.tag_name = tag_name
        self.children = (
            [TagHierarchy.from_dict(level + 1, child) for child in children] if children else []
        )
        self.tag_list = hierarchies_ext.get("hidden_tags") if hierarchies_ext else []
        self.tag_path = hierarchies_ext.get("tag_path") if hierarchies_ext else []
        self._is_book = False
        self.book_item: BookItem = None

    @classmethod
    def from_dict(cls, level, data: Dict[str, Any]) -> TagHierarchy:
        tag_id = data.get("tag_id") if level > 0 else data.get("tag_path")
        hierarchy = data["hierarchies"][0] if data["hierarchies"] else {}
        return cls(
            level=level,
            name=hierarchy.get("hierarchy_name"),
            tag_id=tag_id,
            tag_name=data.get("tag_name"),
            children=hierarchy.get("children"),
            hierarchies_ext=hierarchy.get("ext"),
        )

    @property
    def is_book(self) -> bool:
        return self._is_book

    def set_book(self, book_item: BookItem) -> None:
        # assert book_item.tag_id == self.tag_id  # TODO
        self.book_item = book_item
        self._is_book = True

    def add_child(self, child: TagHierarchy) -> None:
        self.children.append(child)

    def _get_books(self) -> List[Tuple[str, str]]:
        options = []
        for child in self.children:
            item = child.book_item
            options.append((item.book_id, "《{}》".format(strip(item.book_name))))
        return options

    def get_options(self):
        if self.children and self.children[0]._is_book:
            return True, self._get_books()
        else:
            return False, [(child.tag_id, strip(child.tag_name)) for child in self.children]

    def __repr__(self):
        return f"TagHierarchy: level={self.level}, name={self.name}\n\ttag={self.tag_id}/{self.tag_name}\n\tchild={len(self.children)}, book={self.book_item}"
