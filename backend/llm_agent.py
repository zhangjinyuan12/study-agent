import json
import os
import re
import sys
from pathlib import Path

import requests


BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from backend.tools import (  # noqa: E402
    add_material_chunk,
    add_task,
    add_wrong_question,
    make_study_plan,
    query_tasks,
    query_wrong_questions,
    save_tool_log,
    search_materials,
    update_task_status,
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

LLM_SYSTEM_PROMPT = """
你是 StudyAgent 的工具选择器。
你的任务不是直接回答用户，而是判断是否需要调用工具，并返回严格 JSON。
只能从允许的工具列表中选择工具。
不能编造工具名。
不能输出 Markdown。
不能输出解释文字。
只能输出 JSON。

允许的工具包括：

1. query_tasks
功能：查询学习任务
参数：
- subject，可选，默认 数据结构
- status，可选

2. query_wrong_questions
功能：查询错题统计
参数：
- subject，可选，默认 数据结构

3. search_materials
功能：根据关键词检索学习资料
参数：
- keyword，必填

4. make_study_plan
功能：生成复习计划
参数：
- subject，可选，默认 数据结构
- available_hours，可选，默认 3

5. add_material_chunk
功能：添加资料片段
参数：
- subject，可选，默认 数据结构
- title，必填
- keyword，必填
- content，必填
- source_type，可选，默认 user_added
- pinned，可选，默认 0

6. add_wrong_question
功能：添加错题
参数：
- subject，必填
- knowledge_point，必填
- question，必填
- reason，必填

7. add_task
功能：添加学习任务
参数：
- subject，必填
- title，必填
- description，可选
- status，可选，默认 未完成
- priority，可选，默认 3
- due_date，可选

8. update_task_status
功能：更新任务状态
参数：
- title，必填
- status，必填，例如 已完成 或 未完成
- match_mode，可选，exact 或 contains

写入类工具包括：
- add_material_chunk
- add_wrong_question
- add_task
- update_task_status

只有用户输入中明确包含添加、记录、新增、保存、更新、修改、标记、完成等词时，才允许选择写入类工具。
普通提问不能自动写入数据库。
例如：
“红黑树是什么？”
只能调用 search_materials，不能调用 add_material_chunk。

如果需要工具，输出：
{
  "need_tools": true,
  "tool_calls": [
    {
      "name": "工具名称",
      "args": {}
    }
  ],
  "reason": "选择工具的简短原因"
}

如果不需要工具，输出：
{
  "need_tools": false,
  "tool_calls": [],
  "reason": "不需要工具的原因"
}
""".strip()

ALLOWED_TOOL_NAMES = {
    "query_tasks",
    "query_wrong_questions",
    "search_materials",
    "make_study_plan",
    "add_material_chunk",
    "add_wrong_question",
    "add_task",
    "update_task_status",
}

WRITE_TOOL_NAMES = {
    "add_material_chunk",
    "add_wrong_question",
    "add_task",
    "update_task_status",
}

WRITE_INTENT_WORDS = ["添加", "记录", "新增", "保存", "更新", "修改", "标记", "完成", "设为", "改成", "改为"]

REQUIRED_TOOL_ARGS = {
    "search_materials": ["keyword"],
    "add_material_chunk": ["title", "keyword", "content"],
    "add_wrong_question": ["subject", "knowledge_point", "question", "reason"],
    "add_task": ["subject", "title"],
    "update_task_status": ["title", "status"],
}


def get_llm_config():
    return {
        "mode": os.getenv("LLM_MODE", "mock").strip().lower(),
        "api_key": os.getenv("LLM_API_KEY", "").strip(),
        "base_url": os.getenv("LLM_BASE_URL", "https://api.deepseek.com/chat/completions").strip(),
        "model": os.getenv("LLM_MODEL", "deepseek-v4-flash").strip(),
    }


def is_llm_debug_enabled():
    return os.getenv("LLM_DEBUG", "1").strip() not in {"0", "false", "False"}


def debug_log(message: str):
    if is_llm_debug_enabled():
        print(message, flush=True)


def call_real_llm_for_tool_selection(message: str):
    config = get_llm_config()

    if not config["api_key"]:
        raise RuntimeError("LLM_API_KEY is missing")

    if not config["base_url"] or not config["model"]:
        raise RuntimeError("LLM_BASE_URL or LLM_MODEL is missing")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['api_key']}",
    }

    payload = {
        "model": config["model"],
        "messages": [
            {"role": "system", "content": LLM_SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
        "temperature": 0,
        "stream": False,
        "response_format": {
            "type": "json_object",
        },
        "thinking": {
        "type": "disabled",
        },
    }

    debug_log("[llm_agent] REAL LLM REQUEST")
    debug_log(f"[llm_agent] POST {config['base_url']}")
    debug_log(f"[llm_agent] model={config['model']}")
    debug_log(f"[llm_agent] api_key={mask_api_key(config['api_key'])}")

    try:
        response = requests.post(config["base_url"], headers=headers, json=payload, timeout=15)
        response.raise_for_status()
    except requests.HTTPError as error:
        response_text = error.response.text if error.response is not None else ""
        if should_retry_without_thinking(response_text):
            payload.pop("thinking", None)
            debug_log("[llm_agent] RETRY_WITHOUT_THINKING")
            response = requests.post(config["base_url"], headers=headers, json=payload, timeout=15)
            response.raise_for_status()
        else:
            raise

    debug_log("[llm_agent] REAL LLM RESPONSE OK")
    debug_log(f"[llm_agent] status_code={response.status_code}")

    data = response.json()
    return data["choices"][0]["message"]["content"]


def mask_api_key(api_key: str):
    if not api_key:
        return "<missing>"

    if len(api_key) <= 8:
        return f"{api_key[:2]}***"

    return f"{api_key[:4]}***{api_key[-4:]}"


def should_retry_without_thinking(response_text: str):
    lowered_text = response_text.lower()
    return (
        "thinking" in lowered_text
        or "unsupported" in lowered_text
        or "not support" in lowered_text
        or "invalid" in lowered_text
        or "extra" in lowered_text
    )


def parse_llm_tool_json(text: str):
    candidate = (text or "").strip()

    fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", candidate, flags=re.DOTALL | re.IGNORECASE)
    if fence_match:
        candidate = fence_match.group(1).strip()

    start_index = candidate.find("{")
    end_index = candidate.rfind("}")
    if start_index != -1 and end_index != -1 and end_index > start_index:
        candidate = candidate[start_index : end_index + 1]

    data = json.loads(candidate)

    if not isinstance(data, dict):
        raise ValueError("LLM output must be a JSON object")

    if "need_tools" not in data or "tool_calls" not in data:
        raise ValueError("LLM output missing need_tools or tool_calls")

    if not isinstance(data["tool_calls"], list):
        raise ValueError("tool_calls must be a list")

    return data


def validate_tool_calls(tool_calls, message):
    validated_tool_calls = []

    for tool_call in tool_calls:
        if not isinstance(tool_call, dict):
            continue

        tool_name = tool_call.get("name")
        input_args = tool_call.get("args", {}) or {}

        if tool_name not in ALLOWED_TOOL_NAMES:
            continue

        if not isinstance(input_args, dict):
            continue

        if tool_name in WRITE_TOOL_NAMES and not has_write_intent(message):
            continue

        normalized_args = normalize_tool_args(tool_name, input_args, message)
        required_args = REQUIRED_TOOL_ARGS.get(tool_name, [])

        if any(not normalized_args.get(arg_name) for arg_name in required_args):
            continue

        validated_tool_calls.append(
            {
                "name": tool_name,
                "args": normalized_args,
            }
        )

    return validated_tool_calls


def normalize_tool_args(tool_name, input_args, message):
    args = dict(input_args)

    if tool_name in {"query_tasks", "query_wrong_questions", "make_study_plan"}:
        args.setdefault("subject", extract_subject(message))

    if tool_name == "make_study_plan":
        args.setdefault("available_hours", extract_available_hours(message))

    if tool_name == "add_material_chunk":
        args.setdefault("subject", extract_subject(message))
        args.setdefault("source_type", "user_added")
        args.setdefault("pinned", 0)

    if tool_name == "add_task":
        args.setdefault("status", "未完成")
        args.setdefault("priority", 3)
        args.setdefault("description", "")
        args.setdefault("due_date", "")

    if tool_name == "update_task_status":
        args.pop("match_mode", None)

    return args


def has_write_intent(message: str):
    return any(word in message for word in WRITE_INTENT_WORDS)


def llm_select_tools(message: str):
    debug_log("[llm_agent] llm_select_tools entered")
    config = get_llm_config()
    debug_log(f"[llm_agent] LLM_MODE={config['mode']}")
    debug_log(f"[llm_agent] LLM_BASE_URL={config['base_url']}")
    debug_log(f"[llm_agent] LLM_MODEL={config['model']}")
    debug_log(f"[llm_agent] LLM_API_KEY_SET={bool(config['api_key'])}")
    debug_log(f"[llm_agent] LLM_API_KEY_MASKED={mask_api_key(config['api_key'])}")

    if config["mode"] != "real":
        debug_log("[llm_agent] USE_MOCK_MODE: LLM_MODE is not real")
        return mock_llm_select_tools(message)

    if not config["api_key"] or not config["base_url"] or not config["model"]:
        debug_log("[llm_agent] USE_MOCK_MODE: real config missing")
        return mock_llm_select_tools(message)

    try:
        debug_log("[llm_agent] USE_REAL_MODE")
        debug_log("[llm_agent] about to call real LLM for tool selection")
        llm_response_text = call_real_llm_for_tool_selection(message)
        parsed_response = parse_llm_tool_json(llm_response_text)

        if not parsed_response.get("need_tools"):
            return {
                "need_tools": False,
                "tool_calls": [],
                "reason": parsed_response.get("reason", "模型判断不需要调用工具。"),
            }

        validated_tool_calls = validate_tool_calls(parsed_response.get("tool_calls", []), message)

        if not validated_tool_calls:
            raise ValueError("No valid tool calls after validation")

        return {
            "need_tools": True,
            "tool_calls": validated_tool_calls,
            "reason": parsed_response.get("reason", "模型选择工具。"),
        }
    except Exception as error:
        debug_log("[llm_agent] FALLBACK_TO_MOCK")
        debug_log(f"[llm_agent] reason={error}")
        return mock_llm_select_tools(message)


def mock_llm_select_tools(message: str):
    """Mock 大模型工具选择函数，后续真实接入大模型时替换这里即可。"""
    debug_log("[llm_agent] mock_llm_select_tools entered")
    message = message or ""
    tool_calls = []
    reasons = []

    if has_add_wrong_question_intent(message):
        parsed = parse_add_wrong_question_message(message)
        args = parsed["args"] if parsed["success"] else {"parse_error": parsed["error"]}
        tool_calls.append({"name": "add_wrong_question", "args": args})
        reasons.append("用户明确希望记录错题。")
        return {
            "need_tools": True,
            "tool_calls": tool_calls,
            "reason": "；".join(reasons),
        }

    if has_add_task_intent(message):
        parsed = parse_add_task_message(message)
        args = parsed["args"] if parsed["success"] else {"parse_error": parsed["error"]}
        tool_calls.append({"name": "add_task", "args": args})
        reasons.append("用户明确希望添加学习任务。")
        return {
            "need_tools": True,
            "tool_calls": tool_calls,
            "reason": "；".join(reasons),
        }

    if has_update_task_intent(message):
        parsed = parse_update_task_message(message)
        args = parsed["args"] if parsed["success"] else {"parse_error": parsed["error"]}
        tool_calls.append({"name": "update_task_status", "args": args})
        reasons.append("用户明确希望更新任务状态。")
        return {
            "need_tools": True,
            "tool_calls": tool_calls,
            "reason": "；".join(reasons),
        }

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


def parse_add_wrong_question_message(message: str):
    subject = extract_named_field(message, "科目") or extract_subject(message)
    knowledge_point = extract_named_field(message, "知识点")
    question = extract_named_field(message, "题目")
    reason = extract_named_field(message, "原因", stop_at_next_field=False)

    if not knowledge_point or not question or not reason:
        return {
            "success": False,
            "error": "添加错题格式不正确，请使用：添加错题：科目=数据结构；知识点=红黑树；题目=...；原因=...",
            "args": {},
        }

    return {
        "success": True,
        "error": "",
        "args": {
            "subject": subject,
            "knowledge_point": knowledge_point,
            "question": question,
            "reason": reason,
        },
    }


def parse_add_task_message(message: str):
    subject = extract_named_field(message, "科目") or extract_subject(message)
    title = extract_named_field(message, "标题")
    description = extract_named_field(message, "描述")
    priority = extract_named_field(message, "优先级") or 3
    due_date = extract_named_field(message, "截止日期", stop_at_next_field=False)

    if not title:
        return {
            "success": False,
            "error": "添加任务格式不正确，请使用：添加任务：科目=数据结构；标题=...；描述=...；优先级=...；截止日期=...",
            "args": {},
        }

    try:
        priority = int(priority)
    except (TypeError, ValueError):
        priority = 3

    return {
        "success": True,
        "error": "",
        "args": {
            "subject": subject,
            "title": title,
            "description": description,
            "status": "未完成",
            "priority": priority,
            "due_date": due_date,
        },
    }


def parse_update_task_message(message: str):
    title = extract_named_field(message, "标题")
    status = extract_named_field(message, "状态", stop_at_next_field=False)

    if not title or not status:
        return {
            "success": False,
            "error": "更新任务格式不正确，请使用：更新任务：标题=...；状态=...",
            "args": {},
        }

    return {
        "success": True,
        "error": "",
        "args": {
            "title": title,
            "status": status,
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

        if input_args.get("parse_error"):
            output_result = {
                "success": False,
                "message": input_args["parse_error"],
            }
        elif tool_name == "query_tasks":
            output_result = query_tasks(**input_args)
        elif tool_name == "query_wrong_questions":
            output_result = query_wrong_questions(**input_args)
        elif tool_name == "search_materials":
            output_result = search_materials(**input_args)
        elif tool_name == "make_study_plan":
            output_result = make_study_plan(**input_args)
        elif tool_name == "add_material_chunk":
            output_result = add_material_chunk(**input_args)
        elif tool_name == "add_wrong_question":
            output_result = add_wrong_question(**input_args)
        elif tool_name == "add_task":
            output_result = add_task(**input_args)
        elif tool_name == "update_task_status":
            output_result = update_task_status(**input_args)
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
        return "你好，我是 StudyAgent。当前新版 Agent 支持查询任务、分析错题、检索资料、制定复习计划，也可以按指定格式添加资料、错题和学习任务。"

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
        elif tool_name == "add_wrong_question":
            answer_parts.append(build_add_wrong_question_answer(output))
        elif tool_name == "add_task":
            answer_parts.append(build_add_task_answer(output))
        elif tool_name == "update_task_status":
            answer_parts.append(build_update_task_status_answer(output))
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


def build_add_wrong_question_answer(output):
    if output.get("success"):
        return f"错题添加成功，wrong_question_id={output.get('wrong_question_id')}。"

    return output.get("message", "错题添加失败，请检查输入格式。")


def build_add_task_answer(output):
    if output.get("success"):
        return f"任务添加成功，task_id={output.get('task_id')}。"

    return output.get("message", "任务添加失败，请检查输入格式。")


def build_update_task_status_answer(output):
    if output.get("success"):
        return f"任务状态已更新，更新数量：{output.get('updated_count', 0)}。"

    return output.get("message", "任务状态更新失败。")


def run_llm_agent(message: str):
    try:
        debug_log("[llm_agent] run_llm_agent entered")
        debug_log(f"[llm_agent] raw_message={message}")
        message = (message or "").strip()
        debug_log(f"[llm_agent] normalized_message={message}")

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


def has_add_wrong_question_intent(message: str):
    return "添加错题" in message or "新增错题" in message or "记录错题" in message or "加入错题本" in message


def has_add_task_intent(message: str):
    return "添加任务" in message or "新增任务" in message or "加入任务" in message or "记录任务" in message


def has_update_task_intent(message: str):
    return (
        "更新任务" in message
        or "修改任务" in message
        or "标记任务" in message
        or "标记为已完成" in message
        or "完成任务" in message
    )


def has_learning_question_word(message: str):
    return any(word in message for word in LEARNING_QUESTION_WORDS)
