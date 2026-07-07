TOOLS = [
    {
        "name": "query_tasks",
        "description": "查询学习任务，可按科目和任务状态筛选。",
        "parameters": {
            "subject": "可选，课程名称，例如：数据结构、CSAPP、高等数学、英语。",
            "status": "可选，任务状态，例如：未完成、已完成。"
        },
        "returns": {
            "tasks": "任务列表。",
            "summary": "任务总数、已完成数量和未完成数量摘要。"
        }
    },
    {
        "name": "query_wrong_questions",
        "description": "查询错题统计，并按知识点分组。",
        "parameters": {
            "subject": "可选，课程名称，例如：数据结构。"
        },
        "returns": {
            "total": "错题总数。",
            "statistics": "按知识点统计的错题数量。",
            "top_weak_points": "前三个薄弱知识点。"
        }
    },
    {
        "name": "search_materials",
        "description": "根据关键词从学习资料中检索内容。",
        "parameters": {
            "keyword": "必填，检索关键词，例如：B+树、排序、图算法。"
        },
        "returns": {
            "matched_materials": "匹配到的资料列表。"
        }
    },
    {
        "name": "make_study_plan",
        "description": "根据错题统计和未完成任务生成简单复习计划。",
        "parameters": {
            "subject": "必填，课程名称，例如：数据结构。",
            "available_hours": "必填，可用复习时间，单位为小时。"
        },
        "returns": {
            "plan": "复习步骤列表。",
            "advice": "复习建议。"
        }
    },
    {
        "name": "add_material_chunk",
        "description": "向资料库新增一条学习资料片段。",
        "parameters": {
            "subject": "必填，课程名称，例如：数据结构。",
            "title": "必填，资料标题。",
            "keyword": "必填，检索关键词。",
            "content": "必填，资料正文内容。",
            "source_type": "可选，资料来源类型，默认 user_added。",
            "pinned": "可选，是否置顶，默认 0。"
        },
        "returns": {
            "success": "是否添加成功。",
            "message": "操作提示。",
            "chunk_id": "新增资料片段 id。"
        }
    },
    {
        "name": "add_wrong_question",
        "description": "向错题本新增一条错题记录。",
        "parameters": {
            "subject": "必填，科目，例如：数据结构。",
            "knowledge_point": "必填，知识点，例如：红黑树。",
            "question": "必填，错题内容。",
            "reason": "必填，错误原因。"
        },
        "returns": {
            "success": "是否添加成功。",
            "message": "操作提示。",
            "wrong_question_id": "新增错题 id。"
        }
    },
    {
        "name": "add_task",
        "description": "新增一条学习任务。",
        "parameters": {
            "subject": "必填，科目，例如：数据结构。",
            "title": "必填，任务标题。",
            "description": "可选，任务描述。",
            "status": "可选，任务状态，默认未完成。",
            "priority": "可选，优先级，默认 3。",
            "due_date": "可选，截止日期。"
        },
        "returns": {
            "success": "是否添加成功。",
            "message": "操作提示。",
            "task_id": "新增任务 id。"
        }
    },
    {
        "name": "update_task_status",
        "description": "根据任务标题更新任务状态。",
        "parameters": {
            "title": "必填，任务标题。",
            "status": "必填，任务状态，例如：已完成、未完成。"
        },
        "returns": {
            "success": "是否更新成功。",
            "message": "操作提示。",
            "updated_count": "更新的任务数量。"
        }
    }
]
