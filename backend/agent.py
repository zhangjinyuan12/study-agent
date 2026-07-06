import re
import sys
from pathlib import Path


# tools.py 里目前使用了简单的脚本式导入 database.py。
# 这里把 backend 目录加入搜索路径，让 `uvicorn backend.main:app` 也能正常导入。
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from backend.tools import (  # noqa: E402
    make_study_plan,
    query_tasks,
    query_wrong_questions,
    save_tool_log,
    search_materials,
)


LEARNING_QUESTION_WORDS = [
    "是什么",
    "怎么实现",
    "如何实现",
    "怎么做",
    "怎么学",
    "怎么",
    "重点",
    "解释",
    "理解",
    "原理",
    "区别",
    "考什么",
]


KNOWLEDGE_KEYWORD_RULES = [
    (["B+树", "B+ 树"], "B+树"),
    (["B树", "B 树"], "B树"),
    (["拓扑排序"], "拓扑排序"),
    (["最短路径", "Dijkstra", "dijkstra", "Floyd", "floyd"], "最短路径"),
    (["图算法", "图"], "图算法"),
    (["排序算法", "排序"], "排序"),
    (["哈希表"], "哈希表"),
    (["线索二叉树"], "线索二叉树"),
    (["二叉树"], "二叉树"),
    (["队列"], "队列"),
    (["栈"], "栈"),
    (["KMP", "kmp"], "KMP"),
]


def run_agent(message: str):
    """规则版 StudyAgent：根据关键词选择工具，暂时不调用大模型。"""
    message = message or ""
    subject = extract_subject(message)
    available_hours = extract_available_hours(message)
    tool_calls = []
    answer_parts = []

    if "任务" in message:
        input_args = {"subject": subject}
        output_result = query_tasks(subject=subject)
        add_tool_call(tool_calls, "query_tasks", input_args, output_result)
        answer_parts.append(build_tasks_answer(output_result))

    if "错题" in message:
        input_args = {"subject": subject}
        output_result = query_wrong_questions(subject=subject)
        add_tool_call(tool_calls, "query_wrong_questions", input_args, output_result)
        answer_parts.append(build_wrong_questions_answer(output_result))

    if has_material_keyword(message):
        keyword = extract_material_keyword(message, subject)
        input_args = {"keyword": keyword}
        output_result = search_materials(keyword)
        add_tool_call(tool_calls, "search_materials", input_args, output_result)
        answer_parts.append(build_materials_answer(output_result, keyword))

    if "安排" in message or "复习计划" in message or "今晚" in message:
        input_args = {"subject": subject, "available_hours": available_hours}
        output_result = make_study_plan(subject, available_hours)
        add_tool_call(tool_calls, "make_study_plan", input_args, output_result)
        answer_parts.append(build_plan_answer(output_result, subject, available_hours))

    if not tool_calls:
        return {
            "answer": "你好，我是 StudyAgent。你可以问我学习任务、错题分析、资料检索，或让我帮你安排复习计划。",
            "tool_calls": [],
        }

    return {
        "answer": "\n\n".join(answer_parts),
        "tool_calls": tool_calls,
    }


def extract_subject(message: str):
    if "数据结构" in message:
        return "数据结构"
    if "CSAPP" in message:
        return "CSAPP"
    if "高等数学" in message or "高数" in message:
        return "高等数学"
    if "英语" in message:
        return "英语"
    return "数据结构"


def extract_available_hours(message: str):
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:个)?\s*(?:小时|h)", message, re.IGNORECASE)
    if not match:
        return 3

    hours = float(match.group(1))
    if hours.is_integer():
        return int(hours)
    return hours


def has_material_keyword(message: str):
    if "资料" in message:
        return True

    return extract_knowledge_keyword(message) is not None and has_learning_question_word(message)


def extract_material_keyword(message: str, subject: str):
    keyword = extract_knowledge_keyword(message)
    return keyword or subject


def extract_knowledge_keyword(message: str):
    for candidates, keyword in KNOWLEDGE_KEYWORD_RULES:
        for candidate in candidates:
            if candidate in message:
                return keyword
    return None


def has_learning_question_word(message: str):
    return any(word in message for word in LEARNING_QUESTION_WORDS)


def add_tool_call(tool_calls, tool_name, input_args, output_result):
    save_tool_log(tool_name, input_args, output_result)
    tool_calls.append(
        {
            "tool_name": tool_name,
            "input_args": input_args,
            "output_result": output_result,
        }
    )


def build_tasks_answer(result):
    tasks = result.get("tasks", [])
    if not tasks:
        return "没有查询到相关学习任务。"

    task_names = "、".join(task["title"] for task in tasks[:3])
    return f"你今天的学习任务主要包括：{task_names}等。{result.get('summary', '')}"


def build_wrong_questions_answer(result):
    statistics = result.get("statistics", [])
    if not statistics:
        return "没有查询到相关错题统计。"

    stat_text = "、".join(f"{item['knowledge_point']} {item['count']} 道" for item in statistics)
    top_points = "、".join(item["knowledge_point"] for item in result.get("top_weak_points", []))
    return f"共查询到 {result.get('total', 0)} 道错题，主要集中在：{stat_text}。建议优先复习：{top_points}。"


def build_materials_answer(result, keyword):
    materials = result.get("matched_materials", [])
    if not materials:
        return "暂时没有在资料库中找到相关内容，可以先补充该知识点资料。"

    first = materials[0]
    return f"查询到 {len(materials)} 条与“{keyword}”相关的资料。重点资料是《{first['title']}》：{first['content']}"


def build_plan_answer(result, subject, available_hours):
    plan = result.get("plan", [])
    if not plan:
        return f"暂时无法生成 {subject} 的复习计划。"

    plan_text = "；".join(f"{item['step']} {item['minutes']} 分钟" for item in plan)
    return f"已根据 {subject} 的错题和未完成任务生成 {available_hours} 小时复习计划：{plan_text}。{result.get('advice', '')}"
