import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "study.db"


def create_tables(connection):
    cursor = connection.cursor()

    cursor.execute("DROP TABLE IF EXISTS tool_logs")
    cursor.execute("DROP TABLE IF EXISTS material_chunks")
    cursor.execute("DROP TABLE IF EXISTS materials")
    cursor.execute("DROP TABLE IF EXISTS wrong_questions")
    cursor.execute("DROP TABLE IF EXISTS tasks")

    cursor.execute(
        """
        CREATE TABLE tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL,
            priority INTEGER NOT NULL,
            due_date TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE wrong_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            question_title TEXT NOT NULL,
            knowledge_point TEXT NOT NULL,
            difficulty TEXT,
            mistake_reason TEXT,
            created_at TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE material_chunks (
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

    cursor.execute(
        """
        CREATE TABLE tool_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_name TEXT NOT NULL,
            input_args TEXT NOT NULL,
            output_result TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.commit()


def insert_sample_data(connection):
    tasks = [
        ("数据结构", "复习 B+树 插入与删除", "整理 B+树 的节点分裂、合并和范围查询过程。", "未完成", 5, "2026-07-06"),
        ("数据结构", "完成图算法练习", "完成 Dijkstra、Floyd、拓扑排序相关练习题。", "未完成", 5, "2026-07-06"),
        ("数据结构", "整理排序复杂度表", "比较快速排序、堆排序、归并排序的时间复杂度和稳定性。", "已完成", 4, "2026-07-05"),
        ("数据结构", "复盘哈希表冲突处理", "总结拉链法、开放定址法和负载因子。", "未完成", 4, "2026-07-07"),
        ("CSAPP", "阅读缓存章节", "阅读存储器层次结构和缓存命中率相关内容。", "未完成", 4, "2026-07-06"),
        ("CSAPP", "完成 Bomb Lab 记录", "整理 phase 1 到 phase 3 的调试过程。", "已完成", 3, "2026-07-04"),
        ("CSAPP", "预习链接章节", "理解符号表、重定位和静态链接。", "未完成", 3, "2026-07-08"),
        ("高等数学", "刷微分方程习题", "完成一阶线性微分方程和可分离变量方程练习。", "未完成", 4, "2026-07-06"),
        ("高等数学", "复习多元函数偏导", "整理链式法则和隐函数求导。", "已完成", 3, "2026-07-05"),
        ("高等数学", "完成极限错题订正", "回顾等价无穷小和洛必达法则使用条件。", "未完成", 3, "2026-07-07"),
        ("英语", "背诵六级高频词", "完成 30 个高频词记忆和例句复习。", "未完成", 2, "2026-07-06"),
        ("英语", "完成阅读理解训练", "限时完成两篇阅读理解并记录生词。", "已完成", 2, "2026-07-05"),
        ("英语", "整理作文模板", "整理图表作文和观点类作文常用句型。", "未完成", 2, "2026-07-08"),
    ]

    wrong_questions = [
        ("数据结构", "B+树 范围查询路径判断", "B+树", "中等", "没有理解叶子节点链表的作用", "2026-06-20"),
        ("数据结构", "B+树 插入后节点分裂", "B+树", "困难", "分裂后父节点关键字更新错误", "2026-06-22"),
        ("数据结构", "B+树 与 B 树对比", "B+树", "中等", "混淆数据存放位置", "2026-06-25"),
        ("数据结构", "B+树 删除后合并", "B+树", "困难", "没有判断节点关键字下限", "2026-06-28"),
        ("数据结构", "Dijkstra 算法松弛过程", "图算法", "中等", "最短距离数组更新顺序错误", "2026-06-18"),
        ("数据结构", "拓扑排序入度变化", "图算法", "简单", "忽略入度为 0 的新节点", "2026-06-21"),
        ("数据结构", "最小生成树算法选择", "图算法", "中等", "混淆 Prim 和 Kruskal 的适用场景", "2026-06-23"),
        ("数据结构", "Floyd 算法状态转移", "图算法", "困难", "中转点循环顺序错误", "2026-06-26"),
        ("数据结构", "快速排序最坏复杂度", "排序复杂度", "中等", "没有考虑有序数组退化情况", "2026-06-19"),
        ("数据结构", "堆排序建堆复杂度", "排序复杂度", "中等", "误以为建堆是 O(nlogn)", "2026-06-24"),
        ("数据结构", "归并排序稳定性判断", "排序复杂度", "简单", "稳定性定义掌握不牢", "2026-06-29"),
        ("数据结构", "哈希表拉链法查找", "哈希表", "简单", "平均查找长度计算错误", "2026-06-17"),
        ("数据结构", "开放定址法删除标记", "哈希表", "中等", "删除后破坏探测序列", "2026-06-27"),
        ("数据结构", "线索二叉树中序线索", "线索二叉树", "中等", "前驱后继判断错误", "2026-06-16"),
        ("数据结构", "线索二叉树遍历", "线索二叉树", "困难", "没有区分左右标志位", "2026-06-30"),
        ("CSAPP", "缓存组索引位计算", "缓存", "中等", "地址位划分不熟练", "2026-06-18"),
        ("CSAPP", "补码溢出判断", "整数表示", "简单", "忽略符号位变化", "2026-06-22"),
        ("CSAPP", "过程调用栈帧", "汇编与栈", "困难", "返回地址和局部变量位置混淆", "2026-06-25"),
        ("高等数学", "洛必达法则使用条件", "极限", "中等", "没有先判断未定式", "2026-06-20"),
        ("高等数学", "二重积分换元", "多元积分", "困难", "雅可比行列式遗漏", "2026-06-28"),
        ("英语", "长难句主干分析", "阅读理解", "中等", "从句层级划分错误", "2026-06-21"),
        ("英语", "作文连接词使用", "写作", "简单", "连接词重复且逻辑不清", "2026-06-23"),
    ]

    materials = [
        (
            "数据结构",
            "B+树 复习重点",
            "B+树 的所有关键字都会在叶子节点出现，叶子节点通常通过链表连接，适合数据库索引和范围查询。",
        ),
        (
            "数据结构",
            "图算法考前清单",
            "图算法需要重点掌握 Dijkstra、Floyd、拓扑排序、Prim 和 Kruskal，并能说清每种算法的适用场景。",
        ),
        (
            "数据结构",
            "排序复杂度对比",
            "快速排序平均复杂度为 O(nlogn)，最坏为 O(n^2)；归并排序稳定；堆排序原地但不稳定。",
        ),
        (
            "CSAPP",
            "缓存与局部性",
            "CSAPP 中缓存章节重点包括时间局部性、空间局部性、缓存行、组索引和命中率分析。",
        ),
        (
            "高等数学",
            "微分方程方法",
            "一阶微分方程常见方法包括变量分离、齐次方程化简和一阶线性方程公式法。",
        ),
        (
            "英语",
            "六级阅读技巧",
            "英语阅读可以先看题干定位关键词，再回到原文分析长难句和转折关系。",
        ),
    ]

    cursor = connection.cursor()
    cursor.executemany(
        """
        INSERT INTO tasks (subject, title, description, status, priority, due_date)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        tasks,
    )
    cursor.executemany(
        """
        INSERT INTO wrong_questions
        (subject, question_title, knowledge_point, difficulty, mistake_reason, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        wrong_questions,
    )
    cursor.executemany(
        """
        INSERT INTO materials (subject, title, content)
        VALUES (?, ?, ?)
        """,
        materials,
    )
    connection.commit()


def init_database():
    DATA_DIR.mkdir(exist_ok=True)

    with sqlite3.connect(DB_PATH) as connection:
        create_tables(connection)
        insert_sample_data(connection)

    print(f"数据库初始化完成：{DB_PATH}")


if __name__ == "__main__":
    init_database()
