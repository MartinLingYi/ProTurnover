import xml.etree.ElementTree as ET
from typing import List, Optional


class ClipItem:
    def __init__(self, element: ET.Element):
        self._el = element

    # -------- name --------
    @property
    def name(self) -> Optional[str]:
        return self._el.findtext("name")

    @name.setter
    def name(self, value: str):
        node = self._el.find("name")
        if node is None:
            node = ET.SubElement(self._el, "name")
        node.text = value

    # -------- pathurl --------
    @property
    def pathurl(self) -> Optional[str]:
        node = self._el.find(".//file/pathurl")
        return node.text if node is not None else None

    @pathurl.setter
    def pathurl(self, value: str):
        file_node = self._el.find("file")
        if file_node is None:
            file_node = ET.SubElement(self._el, "file")

        path_node = file_node.find("pathurl")
        if path_node is None:
            path_node = ET.SubElement(file_node, "pathurl")

        path_node.text = value

    # -------- 原始元素（备用）--------
    @property
    def element(self) -> ET.Element:
        return self._el


class XMLTimeline:
    def __init__(self, path: str):
        self.tree = ET.parse(path)
        self.root = self.tree.getroot()

        self.clipitems: List[ClipItem] = [
            ClipItem(el) for el in self.root.iter("clipitem")
        ]

    def save(self, path: str):
        self.tree.write(path, encoding="utf-8", xml_declaration=True)

    # 按名称查找
    def find_by_name(self, name: str) -> List[ClipItem]:
        return [c for c in self.clipitems if c.name == name]

    # 迭代支持
    def __iter__(self):
        return iter(self.clipitems)