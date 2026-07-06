import json

from database import execute_query, execute_update


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
    """使用 LIKE 从学习资料内容中搜索关键词。"""
    sql = """
        SELECT *
        FROM materials
        WHERE content LIKE ?
        ORDER BY subject ASC, id ASC
    """
    matched_materials = execute_query(sql, (f"%{keyword}%",))

    return {
        "matched_materials": matched_materials,
    }


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

    print("\n4. make_study_plan('数据结构', 3)")
    print(json.dumps(make_study_plan("数据结构", 3), ensure_ascii=False, indent=2))
