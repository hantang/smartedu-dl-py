from typing import List


class BookItem:
    def __init__(self, level: str, name: str, tag_id: str, tag_name: str):
        self.level: int = level
        self.name: str = name
        self.tag_id: str = tag_id
        self.tag_name: str = tag_name
        self.book_id: str = ""
        self.book_name: str = ""
        self.is_book: bool = False
        self.children: List[BookItem] = []

    def set_book(self, book_id: str, book_name: str) -> None:
        self.book_id = book_id
        self.book_name = book_name
        self.is_book = True

    def add_child(self, child) -> None:
        self.children.append(child)


class BookPDF:
    def __init__(self, book_id: str, book_name: str, tag_path: str, tag_id: str):
        self.book_id = book_id
        self.book_name = book_name
        self.tag_path = tag_path
        self.tag_id = tag_id
