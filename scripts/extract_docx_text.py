from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZipFile

from lxml import etree


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="从 docx 文档中抽取纯文本段落。")
    parser.add_argument("--input", required=True, help="输入 docx 文件路径。")
    parser.add_argument("--output", required=True, help="输出 txt 文件路径。")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

    if not input_path.exists():
        raise FileNotFoundError(f"输入文件不存在：{input_path}")

    with ZipFile(input_path) as archive:
        xml = archive.read("word/document.xml")

    root = etree.fromstring(xml)
    paragraphs: list[str] = []
    for para in root.xpath(".//w:p", namespaces=ns):
        texts: list[str] = []
        for node in para.xpath(".//w:t | .//w:tab | .//w:br", namespaces=ns):
            if node.tag.endswith("}t"):
                texts.append(node.text or "")
            elif node.tag.endswith("}tab"):
                texts.append("\t")
            elif node.tag.endswith("}br"):
                texts.append("\n")
        text = "".join(texts).strip()
        if text:
            paragraphs.append(text)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(paragraphs), encoding="utf-8")
    print(f"段落数：{len(paragraphs)}")
    print(f"字符数：{sum(len(item) for item in paragraphs)}")
    print(f"输出文件：{output_path}")


if __name__ == "__main__":
    main()
