import argparse
import re
import sys
from datetime import datetime
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import get_connection  # noqa: E402


KEYWORDS = [
    "B+树",
    "B树",
    "KMP",
    "哈希表",
    "最短路径",
    "Dijkstra",
    "Floyd",
    "拓扑排序",
    "图算法",
    "排序",
    "线索二叉树",
    "二叉树",
    "栈",
    "队列",
]


def ensure_material_chunks_table(connection):
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS material_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_id INTEGER,
            subject TEXT,
            title TEXT,
            keyword TEXT,
            content TEXT,
            source_type TEXT,
            use_count INTEGER DEFAULT 0,
            last_accessed TEXT,
            pinned INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.commit()


def is_heading(line):
    text = line.strip()

    if not text:
        return False

    if text.startswith("#"):
        return True

    if len(text) <= 40 and (text.endswith(":") or text.endswith("：")):
        return True

    return bool(re.match(r"^(第[一二三四五六七八九十0-9]+[章节]|[一二三四五六七八九十0-9]+[、.．])", text))


def clean_heading(line):
    return line.strip().lstrip("#").strip().rstrip(":：")


def split_by_heading_or_blank(text, default_title):
    sections = []
    current_title = default_title
    current_lines = []

    def flush_section():
        nonlocal current_title, current_lines
        content = "\n".join(current_lines).strip()

        if content:
            sections.append((current_title, content))

        current_title = default_title
        current_lines = []

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if is_heading(line):
            flush_section()
            current_title = clean_heading(line)
            continue

        if not line:
            flush_section()
            continue

        current_lines.append(line)

    flush_section()
    return sections


def split_long_content(content, max_length=800):
    if len(content) <= max_length:
        return [content]

    chunks = []
    current = ""
    sentences = re.split(r"(?<=[。！？.!?])\s*", content)

    for sentence in sentences:
        if not sentence:
            continue

        if len(current) + len(sentence) > max_length and current:
            chunks.append(current.strip())
            current = sentence
        else:
            current += sentence

    if current.strip():
        chunks.append(current.strip())

    return chunks


def extract_keyword(title, content):
    text = f"{title}\n{content}"
    matched_keywords = [keyword for keyword in KEYWORDS if keyword in text]

    if matched_keywords:
        return "、".join(matched_keywords)

    return title[:40]


def build_chunks(text, source_title):
    chunks = []
    sections = split_by_heading_or_blank(text, source_title)

    for title, content in sections:
        for chunk_content in split_long_content(content):
            chunks.append(
                {
                    "title": title,
                    "keyword": extract_keyword(title, chunk_content),
                    "content": chunk_content,
                }
            )

    return chunks


def import_txt_material(txt_path, subject="数据结构"):
    path = Path(txt_path)

    if not path.exists():
        raise FileNotFoundError(f"找不到 txt 文件：{path}")

    text = path.read_text(encoding="utf-8")
    source_title = path.stem
    chunks = build_chunks(text, source_title)
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as connection:
        ensure_material_chunks_table(connection)
        cursor = connection.cursor()
        cursor.executemany(
            """
            INSERT INTO material_chunks
            (material_id, subject, title, keyword, content, source_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    None,
                    subject,
                    chunk["title"],
                    chunk["keyword"],
                    chunk["content"],
                    "txt",
                    created_at,
                )
                for chunk in chunks
            ],
        )
        connection.commit()

    print(f"导入完成：{len(chunks)} 个 chunk")


def main():
    parser = argparse.ArgumentParser(description="导入 txt 学习资料到 material_chunks 表")
    parser.add_argument("txt_path", help="txt 文件路径")
    parser.add_argument("--subject", default="数据结构", help="科目，默认：数据结构")
    args = parser.parse_args()

    import_txt_material(args.txt_path, args.subject)


if __name__ == "__main__":
    main()
