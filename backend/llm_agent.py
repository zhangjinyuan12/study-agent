import re
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from backend.tools import (  # noqa: E402
    add_material_chunk,
    make_study_plan,
    query_tasks,
    query_wrong_questions,
    save_tool_log,
    search_materials,
)


LEARNING_QUESTION_WORDS = [
    "是什么",
    "怎么理解",
    "如何理解",
    "怎么实现",
    "如何实现",
    "怎么做",
    "重点",
    "解释",
    "原理",
    "区别",
]


MATERIAL_KEYWORD_RULES = [
    (["B+树", "B+ 树"], "B+树"),
    (["B树", "B 树"], "B树"),
    (["KMP", "kmp"], "KMP"),
    (["哈希表"], "哈希表"),
    (["Dijkstra", "dijkstra", "Floyd", "floyd", "最短路径"], "最短路径"),
    (["拓扑排序"], "拓扑排序"),
    (["图算法", "图"], "图算法"),
    (["排序算法", "排序"], "排序"),
    (["红黑树"], "红黑树"),
    (["AVL树", "AVL 树"], "AVL树"),
    (["并查集"], "并查集"),
    (["线段树"], "线段树"),
]


FALLBACK_REMOVE_WORDS = [
    *LEARNING_QUESTION_WORDS,
    "请问",
    "我想知道",
    "帮我看看",
    "一下",
]


def llm_select_tools(message: str):
    """Mock 大模型工具选择函数，后续真实接入大模型时替换这里即可。"""
    message = message or ""
    tool_calls = []
    reasons = []

    if has_add_material_intent(message):
        parsed = parse_add_material_message(message)
        args = parsed["args"] if parsed["success"] else {"parse_error": parsed["error"]}
        tool_calls.append({"name": "add_material_chunk", "args": args})
        reasons.append("用户希望添加资料到资料库。")
        return {
            "need_tools": True,
            "tool_calls": tool_calls,
            "reason": "；".join(reasons),
        }

    if "任务" in message:
        tool_calls.append({"name": "query_tasks", "args": {"subject": extract_subject(message)}})
        reasons.append("用户询问学习任务。")

    if "错题" in message:
        tool_calls.append({"name": "query_wrong_questions", "args": {"subject": extract_subject(message)}})
        reasons.append("用户询问错题情况。")

    if "安排" in message or "复习计划" in message or "今晚" in message:
        tool_calls.append(
            {
                "name": "make_study_plan",
                "args": {
                    "subject": extract_subject(message),
                    "available_hours": extract_available_hours(message),
                },
            }
        )
        reasons.append("用户需要安排复习计划。")

    if has_learning_question_word(message):
        keyword = extract_material_keyword(message) or extract_subject(message)
        tool_calls.append({"name": "search_materials", "args": {"keyword": keyword}})
        reasons.append("用户提出知识点学习型问题，需要检索资料。")

    return {
        "need_tools": len(tool_calls) > 0,
        "tool_calls": tool_calls,
        "reason": "；".join(reasons) if reasons else "未匹配到需要调用工具的意图。",
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


def extract_material_keyword(message: str):
    for candidates, keyword in MATERIAL_KEYWORD_RULES:
        for candidate in candidates:
            if candidate in message:
                return keyword

    keyword = message
    for word in FALLBACK_REMOVE_WORDS:
        keyword = keyword.replace(word, "")

    keyword = re.sub(r"[？?。，,：:！!；;、\s]", "", keyword)

    if not keyword or len(keyword) < 2:
        return None

    return keyword


def parse_add_material_message(message: str):
    subject = extract_named_field(message, "科目") or extract_subject(message)
    title = extract_named_field(message, "标题")
    keyword = extract_named_field(message, "关键词")
    content = extract_named_field(message, "内容", stop_at_next_field=False)

    missing_fields = []
    if not title:
        missing_fields.append("标题")
    if not keyword:
        missing_fields.append("关键词")
    if not content:
        missing_fields.append("内容")

    if missing_fields:
        return {
            "success": False,
            "error": f"添加资料格式错误，缺少字段：{'、'.join(missing_fields)}。",
            "args": {},
        }

    return {
        "success": True,
        "error": "",
        "args": {
            "subject": subject,
            "title": title,
            "keyword": keyword,
            "content": content,
            "source_type": "user_added",
            "pinned": 0,
        },
    }


def extract_named_field(message: str, field_name: str, stop_at_next_field=True):
    if stop_at_next_field:
        pattern = rf"{field_name}\s*=\s*(.*?)(?:；|;|$)"
    else:
        pattern = rf"{field_name}\s*=\s*(.*)$"

    match = re.search(pattern, message, flags=re.DOTALL)
    if not match:
        return ""

    return match.group(1).strip().strip("；;")


def execute_tool_calls(tool_calls: list):
    tool_calls_result = []

    for tool_call in tool_calls:
        tool_name = tool_call.get("name", "")
        input_args = tool_call.get("args", {}) or {}

        if tool_name == "query_tasks":
            output_result = query_tasks(**input_args)
        elif tool_name == "query_wrong_questions":
            output_result = query_wrong_questions(**input_args)
        elif tool_name == "search_materials":
            output_result = search_materials(**input_args)
        elif tool_name == "make_study_plan":
            output_result = make_study_plan(**input_args)
        elif tool_name == "add_material_chunk":
            if input_args.get("parse_error"):
                output_result = {
                    "success": False,
                    "message": input_args["parse_error"],
                }
            else:
                output_result = add_material_chunk(**input_args)
        else:
            output_result = {
                "success": False,
                "message": f"未知工具：{tool_name}",
            }

        save_tool_log(tool_name, input_args, output_result)
        tool_calls_result.append(
            {
                "tool_name": tool_name,
                "input_args": input_args,
                "output_result": output_result,
            }
        )

    return tool_calls_result


def build_final_answer(message: str, tool_results: list):
    if not tool_results:
        return "你好，我是 StudyAgent。当前新版 Agent 支持查询任务、分析错题、检索资料、制定复习计划，也可以按指定格式添加资料。"

    answer_parts = []

    for result in tool_results:
        tool_name = result["tool_name"]
        output = result["output_result"]

        if tool_name == "query_tasks":
            answer_parts.append(build_tasks_answer(output))
        elif tool_name == "query_wrong_questions":
            answer_parts.append(build_wrong_questions_answer(output))
        elif tool_name == "search_materials":
            answer_parts.append(build_materials_answer(output))
        elif tool_name == "make_study_plan":
            answer_parts.append(build_study_plan_answer(output))
        elif tool_name == "add_material_chunk":
            answer_parts.append(build_add_material_answer(output))
        else:
            answer_parts.append(f"{tool_name} 已执行。")

    return "\n\n".join(answer_parts)


def build_tasks_answer(output):
    tasks = output.get("tasks", [])
    titles = "、".join(task["title"] for task in tasks[:3])
    return f"共查询到 {len(tasks)} 个学习任务。主要任务包括：{titles or '暂无任务'}。"


def build_wrong_questions_answer(output):
    top_points = output.get("top_weak_points", [])
    point_text = "、".join(f"{item['knowledge_point']} {item['count']} 道" for item in top_points)
    return f"共查询到 {output.get('total', 0)} 道错题。主要薄弱知识点：{point_text or '暂无统计'}。"


def build_materials_answer(output):
    materials = output.get("matched_materials", [])

    if not materials:
        return "资料库暂未找到相关内容，可以通过添加资料补充。"

    snippets = []
    for material in materials[:2]:
        content = material.get("content", "")
        if len(content) > 120:
            content = f"{content[:120]}..."
        snippets.append(f"《{material.get('title', '未命名资料')}》：{content}")

    return f"检索到 {len(materials)} 条相关资料。\n" + "\n".join(snippets)


def build_study_plan_answer(output):
    plan = output.get("plan", [])
    steps = "；".join(f"{item['step']} {item['minutes']} 分钟" for item in plan)
    advice = output.get("advice", "")
    return f"已生成复习计划：{steps or '暂无计划步骤'}。{advice}"


def build_add_material_answer(output):
    if output.get("success"):
        return f"资料添加成功，chunk_id={output.get('chunk_id')}。"

    return output.get("message", "资料添加失败，请检查输入格式。")


def run_llm_agent(message: str):
    try:
        message = (message or "").strip()

        if not message:
            return {
                "success": False,
                "answer": "请输入有效的问题。",
                "tool_calls": [],
            }

        selection = llm_select_tools(message)

        if not selection.get("need_tools"):
            return {
                "success": True,
                "answer": build_final_answer(message, []),
                "tool_calls": [],
            }

        tool_results = execute_tool_calls(selection.get("tool_calls", []))
        answer = build_final_answer(message, tool_results)

        return {
            "success": True,
            "answer": answer,
            "tool_calls": tool_results,
        }
    except Exception as error:
        return {
            "success": False,
            "answer": "Agent 调用失败，请检查后端日志。",
            "tool_calls": [],
            "error": str(error),
        }


def has_add_material_intent(message: str):
    return "添加资料" in message or "加入资料库" in message or "保存到资料库" in message


def has_learning_question_word(message: str):
    return any(word in message for word in LEARNING_QUESTION_WORDS)
