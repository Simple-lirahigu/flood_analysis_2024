from __future__ import annotations

import sqlite3
from pathlib import Path


# 从 Zotero 数据库快照中导出筛选后的 CNKI 洪涝/洪水相关期刊文献。
# 不直接写 Zotero 数据库，避免破坏或制造重复题录。

DB_PATH = Path("outputs/zotero_current.sqlite.snapshot")
OUT_RIS = Path("outputs/cnki_honglao_15_journal_candidates.ris")
OUT_MD = Path("docs/cnki_honglao_15_journal_candidates.md")

# 这些 itemID 来自 Zotero 当前库的只读快照，均为 journalArticle。
SELECTED_ITEM_IDS = [
    31,   # 基于AutoML与可解释人工智能的洪涝易发性分析
    313,  # 基于逆频率比采样方法的洪水易发性评价
    319,  # 基于可解释性人工智能绘制空间洪水易发性图
    346,  # 基于机器学习的龙溪河流域山洪灾害风险评价
    344,  # 基于大数据挖掘的洪水灾害易发性评价系统设计
    228,  # 基于机器学习算法的洪涝灾害风险评估
    236,  # 鄱阳湖2020洪灾遥感评估
    217,  # 鄱阳湖洪涝灾害过程监测
    202,  # 洪涝灾害风险评估研究进展
    200,  # 洪涝灾害风险评估与分区研究进展
    77,   # 多源遥感蓄洪区洪涝监测
    25,   # 三种机器学习算法山洪灾害风险评价
    19,   # 洪涝灾害遥感监测评估研究综述
    17,   # 中国城市洪涝致灾机理与风险评估研究进展
    248,  # 中国城市洪涝问题及成因分析
]


def first(fields: dict[str, list[str]], name: str) -> str:
    values = fields.get(name) or []
    return values[0] if values else ""


def get_items(con: sqlite3.Connection) -> list[dict]:
    cur = con.cursor()
    placeholders = ",".join("?" for _ in SELECTED_ITEM_IDS)
    rows = cur.execute(
        f"""
        SELECT i.itemID, it.typeName, f.fieldName, v.value
        FROM items i
        JOIN itemTypes it ON it.itemTypeID = i.itemTypeID
        LEFT JOIN itemData d ON d.itemID = i.itemID
        LEFT JOIN fields f ON f.fieldID = d.fieldID
        LEFT JOIN itemDataValues v ON v.valueID = d.valueID
        WHERE i.itemID IN ({placeholders})
        """,
        SELECTED_ITEM_IDS,
    ).fetchall()

    creators = cur.execute(
        f"""
        SELECT ic.itemID, ct.creatorType, c.firstName, c.lastName
        FROM itemCreators ic
        JOIN creators c ON c.creatorID = ic.creatorID
        JOIN creatorTypes ct ON ct.creatorTypeID = ic.creatorTypeID
        WHERE ic.itemID IN ({placeholders})
        ORDER BY ic.itemID, ic.orderIndex
        """,
        SELECTED_ITEM_IDS,
    ).fetchall()

    attachments = cur.execute(
        f"""
        SELECT ia.parentItemID, v.value
        FROM itemAttachments ia
        JOIN itemData d ON d.itemID = ia.itemID
        JOIN fields f ON f.fieldID = d.fieldID
        JOIN itemDataValues v ON v.valueID = d.valueID
        WHERE ia.parentItemID IN ({placeholders})
          AND f.fieldName = 'title'
        """,
        SELECTED_ITEM_IDS,
    ).fetchall()

    data: dict[int, dict] = {}
    for item_id, item_type, field, value in rows:
        item = data.setdefault(
            item_id,
            {
                "itemID": item_id,
                "type": item_type,
                "fields": {},
                "creators": [],
                "attachments": [],
            },
        )
        if field and value:
            item["fields"].setdefault(field, []).append(value)

    for item_id, creator_type, first_name, last_name in creators:
        data.setdefault(item_id, {"fields": {}, "creators": [], "attachments": []})["creators"].append(
            {
                "creatorType": creator_type,
                "firstName": first_name or "",
                "lastName": last_name or "",
            }
        )

    for parent_id, title in attachments:
        if parent_id in data:
            data[parent_id]["attachments"].append(title)

    return [data[item_id] for item_id in SELECTED_ITEM_IDS if item_id in data]


def ris_escape(text: str) -> str:
    return (text or "").replace("\r", " ").replace("\n", " ").strip()


def write_ris(items: list[dict]) -> None:
    lines: list[str] = []
    for item in items:
        fields = item["fields"]
        lines.append("TY  - JOUR")
        lines.append(f"T1  - {ris_escape(first(fields, 'title'))}")
        for creator in item["creators"]:
            name = "".join([creator.get("lastName", ""), creator.get("firstName", "")]).strip()
            if name:
                lines.append(f"AU  - {ris_escape(name)}")
        if first(fields, "publicationTitle"):
            lines.append(f"JO  - {ris_escape(first(fields, 'publicationTitle'))}")
        if first(fields, "date"):
            lines.append(f"PY  - {ris_escape(first(fields, 'date'))[:4]}")
            lines.append(f"DA  - {ris_escape(first(fields, 'date'))}")
        if first(fields, "volume"):
            lines.append(f"VL  - {ris_escape(first(fields, 'volume'))}")
        if first(fields, "issue"):
            lines.append(f"IS  - {ris_escape(first(fields, 'issue'))}")
        if first(fields, "pages"):
            lines.append(f"SP  - {ris_escape(first(fields, 'pages'))}")
        if first(fields, "DOI"):
            lines.append(f"DO  - {ris_escape(first(fields, 'DOI'))}")
        if first(fields, "url"):
            lines.append(f"UR  - {ris_escape(first(fields, 'url'))}")
        if first(fields, "abstractNote"):
            lines.append(f"AB  - {ris_escape(first(fields, 'abstractNote'))}")
        lines.append("KW  - 洪涝")
        lines.append("KW  - 洪涝易发性")
        lines.append("KW  - CNKI")
        attachment_status = "已有附件：" + "；".join(item["attachments"]) if item["attachments"] else "原文PDF/CAJ待从CNKI补充。"
        lines.append(f"N1  - {attachment_status}")
        lines.append("ER  -")
        lines.append("")
    OUT_RIS.parent.mkdir(parents=True, exist_ok=True)
    OUT_RIS.write_text("\n".join(lines), encoding="utf-8")


def write_md(items: list[dict]) -> None:
    lines = [
        "# CNKI 洪涝/洪涝易发性期刊论文候选 15 篇",
        "",
        "来源：Zotero 当前库只读快照 + 已有 CNKI 题录。",
        "",
        "筛选条件：",
        "",
        "- 文献类型：期刊论文",
        "- 主题：洪涝、洪涝易发性、洪水易发性、洪涝风险评估、洪涝遥感监测",
        "- 优先：核心期刊、CSCD、北大核心、EI相关来源；具体收录状态仍需在 CNKI 详情页最终核验",
        "- PDF/CAJ：仅记录附件状态，不假装已下载",
        "",
        "| 序号 | 题名 | 作者 | 年份 | 期刊 | DOI/链接 | 附件状态 |",
        "|---:|---|---|---|---|---|---|",
    ]
    for index, item in enumerate(items, start=1):
        fields = item["fields"]
        title = first(fields, "title")
        authors = "；".join("".join([c.get("lastName", ""), c.get("firstName", "")]).strip() for c in item["creators"])
        year = first(fields, "date")[:4]
        journal = first(fields, "publicationTitle")
        doi_or_url = first(fields, "DOI") or first(fields, "url")
        attachment_status = "已有附件" if item["attachments"] else "待补PDF/CAJ"
        lines.append(
            f"| {index} | {title} | {authors} | {year} | {journal} | {doi_or_url} | {attachment_status} |"
        )

    lines.extend(
        [
            "",
            "## 使用说明",
            "",
            f"- Zotero 可导入 RIS 文件：`{OUT_RIS}`",
            "- 如果导入 Zotero 后发现重复题录，优先保留已有带 PDF/CAJ 附件或字段更完整的条目。",
            "- DOI、分类号、单位、关键词和摘要并非每条都完整，需要通过 CNKI 详情页或全文继续补齐。",
        ]
    )
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"缺少 Zotero 快照：{DB_PATH}")
    con = sqlite3.connect(DB_PATH)
    try:
        items = get_items(con)
    finally:
        con.close()
    write_ris(items)
    write_md(items)
    print(f"exported {len(items)} items")
    print(OUT_RIS)
    print(OUT_MD)


if __name__ == "__main__":
    main()
