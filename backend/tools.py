import json
import sqlite3

from database import execute_query, execute_update, get_connection


def query_tasks(subject=None, status=None):
    """查询学习任务，可按科目和状态筛选。"""
    sql = "SELECT * FROM tasks WHERE 1 = 1"
    params = []

    if subject:
        sql += " AND subject = ?"
        params.append(subject)

    if status:
        sql += " AND status = ?"
        params.append(status)

    sql += " ORDER BY priority DESC, due_date ASC, id ASC"
    tasks = execute_query(sql, params)

    finished_count = sum(1 for task in tasks if task["status"] == "已完成")
    unfinished_count = sum(1 for task in tasks if task["status"] != "已完成")
    summary = f"共查询到 {len(tasks)} 个任务，已完成 {finished_count} 个，未完成 {unfinished_count} 个。"

    return {
        "tasks": tasks,
        "summary": summary,
    }


def query_wrong_questions(subject=None):
    """按知识点统计错题数量。"""
    sql = """
        SELECT knowledge_point, COUNT(*) AS count
        FROM wrong_questions
        WHERE 1 = 1
    """
    params = []

    if subject:
        sql += " AND subject = ?"
        params.append(subject)

    sql += """
        GROUP BY knowledge_point
        ORDER BY count DESC, knowledge_point ASC
    """

    statistics = execute_query(sql, params)
    total = sum(item["count"] for item in statistics)
    top_weak_points = statistics[:3]

    return {
        "total": total,
        "statistics": statistics,
        "top_weak_points": top_weak_points,
    }


def search_materials(keyword):
    """优先从资料切块表检索，兼容旧 materials 表。"""
    chunk_results = search_material_chunks(keyword)

    if chunk_results:
        return {
            "matched_materials": chunk_results,
        }

    return search_legacy_materials(keyword)


def search_material_chunks(keyword):
    sql = """
        SELECT id, title, subject, content, source_type
        FROM material_chunks
        WHERE title LIKE ? OR keyword LIKE ? OR content LIKE ?
        ORDER BY
            pinned DESC,
            CASE
                WHEN title = ? OR keyword = ? THEN 0
                WHEN title LIKE ? OR keyword LIKE ? THEN 1
                ELSE 2
            END ASC,
            use_count DESC,
            id ASC
        LIMIT 5
    """
    like_keyword = f"%{keyword}%"

    try:
        matched_chunks = execute_query(
            sql,
            (
                like_keyword,
                like_keyword,
                like_keyword,
                keyword,
                keyword,
                like_keyword,
                like_keyword,
            ),
        )
    except sqlite3.OperationalError:
        return []

    for chunk in matched_chunks:
        execute_update(
            """
            UPDATE material_chunks
            SET use_count = use_count + 1,
                last_accessed = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (chunk["id"],),
        )

    return matched_chunks


def search_legacy_materials(keyword):
    sql = """
        SELECT id, title, subject, content
        FROM materials
        WHERE title LIKE ? OR content LIKE ?
        ORDER BY subject ASC, id ASC
        LIMIT 5
    """
    like_keyword = f"%{keyword}%"
    matched_materials = execute_query(sql, (like_keyword, like_keyword))

    for material in matched_materials:
        material["source_type"] = "seed"

    return {
        "matched_materials": matched_materials,
    }


def add_material_chunk(subject, title, keyword, content, source_type="user_added", pinned=0):
    """向 material_chunks 表新增一条资料片段。"""
    ensure_material_chunks_table()

    sql = """
        INSERT INTO material_chunks
        (material_id, subject, title, keyword, content, source_type, pinned, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """
    params = (
        None,
        subject,
        title,
        keyword,
        content,
        source_type,
        pinned,
    )

    with get_connection() as connection:
        cursor = connection.execute(sql, params)
        connection.commit()
        chunk_id = cursor.lastrowid

    return {
        "success": True,
        "message": "资料已添加",
        "chunk_id": chunk_id,
    }


def add_wrong_question(subject, knowledge_point, question, reason):
    """向 wrong_questions 表新增一条错题记录。"""
    try:
        sql = """
            INSERT INTO wrong_questions
            (subject, question_title, knowledge_point, difficulty, mistake_reason, created_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """

        with get_connection() as connection:
            cursor = connection.execute(
                sql,
                (
                    subject,
                    question,
                    knowledge_point,
                    "",
                    reason,
                ),
            )
            connection.commit()
            wrong_question_id = cursor.lastrowid

        return {
            "success": True,
            "message": "错题已添加",
            "wrong_question_id": wrong_question_id,
        }
    except Exception as error:
        return {
            "success": False,
            "message": "错题添加失败",
            "error": str(error),
        }


def add_task(subject, title, description="", status="未完成", priority=3, due_date=""):
    """向 tasks 表新增一条学习任务。"""
    try:
        sql = """
            INSERT INTO tasks
            (subject, title, description, status, priority, due_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """

        with get_connection() as connection:
            cursor = connection.execute(
                sql,
                (
                    subject,
                    title,
                    description,
                    status,
                    int(priority),
                    due_date,
                ),
            )
            connection.commit()
            task_id = cursor.lastrowid

        return {
            "success": True,
            "message": "任务已添加",
            "task_id": task_id,
        }
    except Exception as error:
        return {
            "success": False,
            "message": "任务添加失败",
            "error": str(error),
        }


def update_task_status(title, status):
    """根据任务标题修改任务状态。"""
    sql = """
        UPDATE tasks
        SET status = ?
        WHERE title = ?
    """
    updated_count = execute_update(sql, (status, title))

    if updated_count == 0:
        return {
            "success": False,
            "message": "没有找到对应任务",
            "updated_count": 0,
        }

    return {
        "success": True,
        "message": "任务状态已更新",
        "updated_count": updated_count,
    }


def ensure_material_chunks_table():
    with get_connection() as connection:
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


def make_study_plan(subject, available_hours):
    """根据错题统计和未完成任务生成简单复习计划。"""
    wrong_result = query_wrong_questions(subject)
    task_result = query_tasks(subject=subject, status="未完成")

    weak_points = wrong_result["top_weak_points"]
    unfinished_tasks = task_result["tasks"]
    plan = []

    try:
        hours = float(available_hours)
    except (TypeError, ValueError):
        hours = 1.0

    if hours <= 0:
        hours = 1.0

    total_minutes = int(hours * 60)
    review_minutes = max(20, int(total_minutes * 0.45))
    task_minutes = max(20, int(total_minutes * 0.40))
    summary_minutes = max(10, total_minutes - review_minutes - task_minutes)

    if weak_points:
        point_names = "、".join(point["knowledge_point"] for point in weak_points)
        plan.append(
            {
                "step": "错题高频知识点复习",
                "minutes": review_minutes,
                "content": f"优先复习 {point_names}，先看概念，再做对应错题。",
            }
        )

    if unfinished_tasks:
        selected_tasks = unfinished_tasks[:2]
        task_names = "、".join(task["title"] for task in selected_tasks)
        plan.append(
            {
                "step": "高优先级任务推进",
                "minutes": task_minutes,
                "content": f"按优先级完成：{task_names}。",
            }
        )

    plan.append(
        {
            "step": "总结与自测",
            "minutes": summary_minutes,
            "content": "整理仍不熟的知识点，做 5 到 10 道小题检查掌握情况。",
        }
    )

    advice = "建议先处理错题最多的知识点，再完成高优先级未完成任务，最后用自测确认复习效果。"

    return {
        "plan": plan,
        "advice": advice,
    }


def save_tool_log(tool_name, input_args, output_result):
    """保存工具调用日志，输入和输出用 JSON 字符串存入数据库。"""
    sql = """
        INSERT INTO tool_logs (tool_name, input_args, output_result)
        VALUES (?, ?, ?)
    """
    params = (
        tool_name,
        json.dumps(input_args, ensure_ascii=False),
        json.dumps(output_result, ensure_ascii=False),
    )
    return execute_update(sql, params)


if __name__ == "__main__":
    print("1. query_tasks('数据结构')")
    print(json.dumps(query_tasks("数据结构"), ensure_ascii=False, indent=2))

    print("\n2. query_wrong_questions('数据结构')")
    print(json.dumps(query_wrong_questions("数据结构"), ensure_ascii=False, indent=2))

    print("\n3. search_materials('B+树')")
    print(json.dumps(search_materials("B+树"), ensure_ascii=False, indent=2))

    print("\n4. search_materials('KMP')")
    print(json.dumps(search_materials("KMP"), ensure_ascii=False, indent=2))

    print("\n5. search_materials('哈希表')")
    print(json.dumps(search_materials("哈希表"), ensure_ascii=False, indent=2))

    print("\n6. search_materials('最短路径')")
    print(json.dumps(search_materials("最短路径"), ensure_ascii=False, indent=2))

    print("\n7. make_study_plan('数据结构', 3)")
    print(json.dumps(make_study_plan("数据结构", 3), ensure_ascii=False, indent=2))
