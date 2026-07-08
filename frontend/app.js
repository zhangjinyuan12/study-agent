/* ===================================================================
 * API 端点配置
 * =================================================================== */

// 后端 FastAPI 服务地址（默认端口 8000）。
// 如果后端使用不同的端口或部署到其他地址，修改此值即可。
const API_BASE_URL = "http://localhost:8000";

const CHAT_API_URL_RULE = `${API_BASE_URL}/chat`;
const CHAT_API_URL_AGENT = `${API_BASE_URL}/chat-agent`;
const CHAT_SEARCH_API_URL = `${API_BASE_URL}/chat-search`;
const TOOL_LOGS_API_URL = `${API_BASE_URL}/tool-logs`;

/* ===================================================================
 * DOM 元素引用
 * =================================================================== */
const workspace = document.querySelector(".workspace");
const chatMessages = document.getElementById("chatMessages");
const chatForm = document.getElementById("chatForm");
const chatPanel = document.querySelector(".chat-panel");
const dashboard = document.querySelector(".dashboard");
const messageInput = document.getElementById("messageInput");
const toolList = document.getElementById("toolList");
const menuItems = document.querySelectorAll(".menu-item");
const exampleButtons = document.querySelectorAll(".example-button");
const sendButton = chatForm.querySelector("button[type='submit']");

/* ===================================================================
 * 状态变量
 * =================================================================== */
let isRequesting = false;           // 是否正在请求后端
let currentMode = "agent";           // 当前 Agent 模式: "agent" | "rule"

// 根据当前模式返回对应 API 地址
function getChatApiUrl() {
    return currentMode === "agent" ? CHAT_API_URL_AGENT : CHAT_API_URL_RULE;
}

let featureRequestId = 0;           // 递增 ID，用于忽略过期请求的回调

/* ===================================================================
 * 动态功能视图容器（JS 创建，与聊天面板互斥显示）
 * =================================================================== */
const featureView = document.createElement("section");
featureView.className = "feature-view is-hidden";
featureView.setAttribute("aria-label", "功能页面");
workspace.appendChild(featureView);

/* ===================================================================
 * 聊天消息操作
 * =================================================================== */

// 追加一条聊天消息（用户或 AI）
function addMessage(role, text) {
    const message = document.createElement("article");
    message.className = `message ${role === "user" ? "user-message" : "ai-message"}`;

    const roleLabel = document.createElement("div");
    roleLabel.className = "message-role";
    roleLabel.textContent = role === "user" ? "你" : "AI";

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    bubble.textContent = text;

    message.append(roleLabel, bubble);
    chatMessages.appendChild(message);
    scrollMessagesToBottom();

    return { message, bubble };
}

// 更新已有消息的文本内容（用于流式/加载态）
function updateMessage(messageRef, text) {
    messageRef.bubble.textContent = text;
    scrollMessagesToBottom();
}

// 滚动聊天区到底部
function scrollMessagesToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/* ===================================================================
 * 视图切换（智能问答 ↔ 功能模块）
 * =================================================================== */

// 激活指定的菜单项
function setActiveMenu(label) {
    menuItems.forEach((item) => {
        item.classList.toggle("active", item.textContent.trim() === label);
    });
}

// 切换到智能问答聊天视图（默认视图）
function showChatView() {
    featureRequestId += 1;
    setActiveMenu("智能问答");
    workspace.classList.remove("workspace--single");
    featureView.classList.add("is-hidden");
    chatPanel.classList.remove("is-hidden");
    dashboard.classList.remove("is-hidden");
    messageInput.focus();
}

// 切换到功能模块视图（学习任务、错题分析等）
function showFeatureView(title, description = "") {
    featureRequestId += 1;
    chatPanel.classList.add("is-hidden");
    dashboard.classList.add("is-hidden");
    workspace.classList.add("workspace--single");
    featureView.classList.remove("is-hidden");
    featureView.innerHTML = "";

    // 渲染标题栏
    const heading = document.createElement("div");
    heading.className = "panel-heading";

    const headingText = document.createElement("div");
    const titleElement = document.createElement("h2");
    titleElement.textContent = title;
    headingText.appendChild(titleElement);

    if (description) {
        const descriptionElement = document.createElement("p");
        descriptionElement.textContent = description;
        headingText.appendChild(descriptionElement);
    }

    heading.appendChild(headingText);
    featureView.appendChild(heading);
}

// 创建功能模块的回答输出区域
function createFeatureAnswerBox(initialText = "正在分析中...") {
    const answerBox = document.createElement("div");
    answerBox.className = "feature-answer";
    answerBox.textContent = initialText;
    featureView.appendChild(answerBox);
    return answerBox;
}

/* ===================================================================
 * 清空聊天 & 请求状态控制
 * =================================================================== */

// 清空聊天记录（带确认）
function clearChat() {
    if (!confirm("确定要清空所有聊天记录吗？")) {
        return;
    }

    const messages = chatMessages.querySelectorAll(".message");
    messages.forEach((el) => el.remove());

    addMessage("ai", "你好，我是 StudyAgent。你可以询问学习任务、错题分布、资料重点或复习安排，我会根据输入模拟调用多个学习管理工具并生成回答。");

    setToolPanelMessage("等待用户提问后显示工具调用过程。");
    scrollMessagesToBottom();
}

// 设置请求加载状态（锁定/解锁输入控件）
function setRequestingState(isLoading) {
    isRequesting = isLoading;
    messageInput.disabled = isLoading;
    sendButton.disabled = isLoading;

    exampleButtons.forEach((button) => {
        button.disabled = isLoading;
    });

    const modeButtons = document.querySelectorAll(".mode-btn");
    modeButtons.forEach((button) => {
        button.disabled = isLoading;
    });
}

/* ===================================================================
 * 右侧工具调用面板操作
 * =================================================================== */

// 显示工具面板占位消息
function setToolPanelMessage(text) {
    toolList.innerHTML = "";

    const emptyState = document.createElement("div");
    emptyState.className = "empty-state";
    emptyState.textContent = text;

    toolList.appendChild(emptyState);
}

/* ===================================================================
 * 工具调用渲染
 * =================================================================== */

// 格式化 JSON 为可读字符串
function formatJson(value) {
    try {
        return JSON.stringify(value ?? {}, null, 2);
    } catch (error) {
        return String(value);
    }
}

// 渲染工具调用卡片列表
function renderToolCalls(toolCalls) {
    toolList.innerHTML = "";

    if (!Array.isArray(toolCalls) || toolCalls.length === 0) {
        setToolPanelMessage("本次回答没有调用工具。");
        return;
    }

    toolCalls.forEach((tool) => {
        const card = document.createElement("article");
        card.className = "tool-card";

        const header = document.createElement("div");
        header.className = "tool-card-header";

        const name = document.createElement("div");
        name.className = "tool-name";
        name.textContent = tool.tool_name || "unknown_tool";

        const status = document.createElement("span");
        status.className = "status-success";
        status.textContent = "状态：成功";

        header.append(name, status);

        const params = createToolField("输入参数", formatReadableArgs(tool.input_args));
        const result = createToolField("输出结果摘要", buildToolSummary(tool));
        const rawJson = createRawJsonSection(tool);

        card.append(header, params, result, rawJson);
        toolList.appendChild(card);
    });
}

// 格式化输入参数为可读文本
function formatReadableArgs(inputArgs) {
    const args = inputArgs || {};
    const entries = Object.entries(args).filter(([, value]) => value !== null && value !== undefined && value !== "");

    if (entries.length === 0) {
        return "无输入参数";
    }

    return entries
        .map(([key, value]) => `${key}: ${formatSimpleValue(value)}`)
        .join("\n");
}

// 简单值格式化（数组用顿号连接）
function formatSimpleValue(value) {
    if (Array.isArray(value)) {
        return value.join("、");
    }

    if (typeof value === "object" && value !== null) {
        return JSON.stringify(value);
    }

    return String(value);
}

// 根据工具名称构建结果摘要
function buildToolSummary(tool) {
    const toolName = tool.tool_name || "";
    const result = tool.output_result || {};

    if (toolName === "query_tasks") {
        return buildTasksSummary(result);
    }

    if (toolName === "query_wrong_questions") {
        return buildWrongQuestionsSummary(result);
    }

    if (toolName === "search_materials") {
        return buildMaterialsSummary(result);
    }

    if (toolName === "make_study_plan") {
        return buildStudyPlanSummary(result, tool.input_args || {});
    }

    return "工具已返回结果，可点击下方按钮查看原始 JSON。";
}

// 学习任务工具的结果摘要
function buildTasksSummary(result) {
    const tasks = Array.isArray(result.tasks) ? result.tasks : [];
    const finishedCount = tasks.filter((task) => task.status === "已完成").length;
    const unfinishedCount = tasks.length - finishedCount;
    const taskTitles = tasks.slice(0, 3).map((task) => `- ${task.title}`).join("\n");

    return [
        `查询到任务: ${tasks.length} 个`,
        `已完成: ${finishedCount} 个`,
        `未完成: ${unfinishedCount} 个`,
        taskTitles ? `前 3 个任务:\n${taskTitles}` : "暂无任务标题"
    ].join("\n");
}

// 错题分析工具的结果摘要
function buildWrongQuestionsSummary(result) {
    const weakPoints = Array.isArray(result.top_weak_points) ? result.top_weak_points : [];
    const fallbackStats = Array.isArray(result.statistics) ? result.statistics.slice(0, 3) : [];
    const topPoints = weakPoints.length > 0 ? weakPoints.slice(0, 3) : fallbackStats;
    const pointText = topPoints.map((item) => `- ${item.knowledge_point}: ${item.count} 道`).join("\n");

    return [
        `共查询到错题: ${result.total || 0} 道`,
        pointText ? `前三个薄弱知识点:\n${pointText}` : "暂无薄弱知识点统计"
    ].join("\n");
}

// 资料检索工具的结果摘要
function buildMaterialsSummary(result) {
    const materials = Array.isArray(result.matched_materials) ? result.matched_materials : [];
    const snippets = materials
        .slice(0, 2)
        .map((material) => {
            const title = material.title || "未命名资料";
            // const content = material.content ? ` - ${truncateText(material.content, 80)}` : "";
            const content = material.content ? ` - ${material.content}` : "";
            return `- ${title}${content}`;
        })
        .join("\n");

    return [
        `查询到资料片段: ${materials.length} 个`,
        snippets || "暂无资料摘要"
    ].join("\n");
}

// 学习计划工具的结果摘要
function buildStudyPlanSummary(result, inputArgs) {
    const plan = Array.isArray(result.plan) ? result.plan : [];
    const steps = plan.map((item) => `- ${item.step}: ${item.minutes} 分钟`).join("\n");
    const advice = result.advice ? `建议: ${result.advice}` : "暂无建议";

    return [
        `计划步骤数量: ${plan.length} 个`,
        steps || "暂无计划步骤",
        advice
    ].join("\n");
}

// 截断文本（超过 maxLength 加省略号）
function truncateText(text, maxLength) {
    if (text.length <= maxLength) {
        return text;
    }

    return `${text.slice(0, maxLength)}...`;
}

// 创建可展开/收起原始 JSON 的区块
function createRawJsonSection(tool) {
    const wrapper = document.createElement("div");
    wrapper.className = "tool-field raw-json-section";

    const toggleButton = document.createElement("button");
    toggleButton.type = "button";
    toggleButton.className = "raw-json-toggle";
    toggleButton.textContent = "查看原始 JSON";

    const rawContent = document.createElement("pre");
    rawContent.className = "raw-json";
    rawContent.textContent = formatJson({
        input_args: tool.input_args || {},
        output_result: tool.output_result || {}
    });

    toggleButton.addEventListener("click", () => {
        const isOpen = rawContent.classList.toggle("open");
        toggleButton.textContent = isOpen ? "收起 JSON" : "查看原始 JSON";
    });

    wrapper.append(toggleButton, rawContent);
    return wrapper;
}

// 创建工具参数字段（标签 + 代码内容）
function createToolField(label, value) {
    const field = document.createElement("div");
    field.className = "tool-field";

    const title = document.createElement("span");
    title.textContent = label;

    const content = document.createElement("code");
    content.textContent = value;

    field.append(title, content);
    return field;
}

/* ===================================================================
 * API 交互
 * =================================================================== */

// 调用后端聊天 API（POST /chat 或 /chat-agent）
async function callChatApi(message) {
    const response = await fetch(getChatApiUrl(), {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            message
        })
    });

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }

    return response.json();
}

// 调用后端聊天 API（固定使用 /chat-agent）
async function callChatApiWithAgent(message) {
    const response = await fetch(CHAT_API_URL_AGENT, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            message
        })
    });

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }

    return response.json();
}

// 调用资料检索专用 API（跟随当前 agent/rule 模式，但只触发 search_materials）
async function callChatSearchApi(message) {
    const response = await fetch(CHAT_SEARCH_API_URL, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            message
        })
    });

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }

    return response.json();
}

// 在功能模块视图中调用后端并显示结果
async function runFeatureChat(message, answerBox, useAgent = false) {
    const currentRequestId = ++featureRequestId;
    answerBox.textContent = "正在分析中...";
    setToolPanelMessage("正在调用后端工具...");

    try {
        // 如果 useAgent 为 true，则固定使用 /chat-agent；否则根据当前模式决定
        const data = useAgent ? await callChatApiWithAgent(message) : await callChatApi(message);

        // 如果用户在此期间切换了视图，忽略此回调
        if (currentRequestId !== featureRequestId) {
            return;
        }

        if (data.success === false) {
            answerBox.textContent = data.answer || data.error || "后端返回错误，请稍后重试。";
        } else {
            answerBox.textContent = data.answer || "后端已返回，但没有生成回答。";
        }
        renderToolCalls(data.tool_calls);
    } catch (error) {
        if (currentRequestId !== featureRequestId) {
            return;
        }

        console.error("Feature request failed:", error);
        answerBox.textContent = "后端服务未连接，请先启动 FastAPI 后端。";
        setToolPanelMessage("后端服务未连接，请先启动 FastAPI 后端。");
    }
}

/* ===================================================================
 * 各功能模块页面渲染
 * =================================================================== */

// 通用：自动提问并显示回答（学习任务、错题分析共用）
function renderAutoChatPage(title, message) {
    setActiveMenu(title);
    showFeatureView(title, `自动向 StudyAgent 提问：${message}`);
    const answerBox = createFeatureAnswerBox();
    runFeatureChat(message, answerBox);
}

// 资料检索页面（带搜索输入框，固定使用 /chat-agent 模块）
function renderMaterialSearchPage() {
    setActiveMenu("资料检索");
    showFeatureView("资料检索", "输入知识点，系统会通过专用检索接口查找相关学习资料。");

    const form = document.createElement("form");
    form.className = "feature-search";

    const input = document.createElement("input");
    input.type = "text";
    input.value = "B+树";
    input.placeholder = "输入知识点，例如 B+树、排序、图算法";

    const button = document.createElement("button");
    button.type = "submit";
    button.textContent = "搜索";

    form.append(input, button);
    featureView.appendChild(form);

    const answerBox = createFeatureAnswerBox("请输入知识点并点击搜索。");

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const keyword = input.value.trim() || "B+树";
        answerBox.textContent = "正在检索...";
        setToolPanelMessage("正在调用资料检索工具...");

        try {
            const data = await callChatSearchApi(keyword);
            if (data.success === false) {
                answerBox.textContent = data.answer || "后端返回错误，请稍后重试。";
            } else {
                answerBox.textContent = data.answer || "未检索到相关内容。";
            }
            renderToolCalls(data.tool_calls);
        } catch (error) {
            console.error("Search request failed:", error);
            answerBox.textContent = "后端服务未连接，请先启动 FastAPI 后端。";
            setToolPanelMessage("后端服务未连接。");
        }
    });
}

// 工具日志页面（接口尚未实现，占位）
async function renderToolLogsPage() {
    setActiveMenu("工具日志");
    showFeatureView("工具日志", "后续可在这里查看后端保存的工具调用记录。");
    const answerBox = createFeatureAnswerBox("工具日志接口尚未实现，下一阶段将接入后端日志查询。");
    setToolPanelMessage("工具日志页面暂不调用智能体工具。");
}

// 格式化工具日志列表
function formatToolLogs(logs) {
    if (!Array.isArray(logs) || logs.length === 0) {
        return "工具日志接口已返回，但暂无日志数据。";
    }

    return logs
        .slice(0, 8)
        .map((log, index) => `${index + 1}. ${log.tool_name || "unknown_tool"}`)
        .join("\n");
}

// 测试用例页面（快速测试按钮集合）
function renderTestCasesPage() {
    setActiveMenu("测试用例");
    showFeatureView("测试用例", "点击测试问题，快速验证 /chat 的回答和工具调用。");

    const testQuestions = [
        "我今天有哪些学习任务？",
        "我最近数据结构错题集中在哪些知识点？",
        "B+树的重点是什么？",
        "排序算法怎么实现？",
        "我今晚有 3 小时，明天考数据结构，帮我安排复习计划。",
        "你好"
    ];

    const buttonGrid = document.createElement("div");
    buttonGrid.className = "test-button-grid";

    const answerBox = createFeatureAnswerBox("请选择一个测试问题。");

    testQuestions.forEach((question) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "example-button";
        button.textContent = question;
        button.addEventListener("click", () => {
            runFeatureChat(question, answerBox);
        });
        buttonGrid.appendChild(button);
    });

    featureView.insertBefore(buttonGrid, answerBox);
}

/* ===================================================================
 * 菜单点击分发
 * =================================================================== */
function handleMenuClick(label) {
    if (label === "智能问答") {
        showChatView();
        return;
    }

    if (label === "学习任务") {
        renderAutoChatPage("学习任务", "我今天有哪些学习任务？");
        return;
    }

    if (label === "错题分析") {
        renderAutoChatPage("错题分析", "我最近数据结构错题集中在哪些知识点？");
        return;
    }

    if (label === "资料检索") {
        renderMaterialSearchPage();
        return;
    }

    if (label === "工具日志") {
        renderToolLogsPage();
        return;
    }

    if (label === "测试用例") {
        renderTestCasesPage();
    }
}

/* ===================================================================
 * 消息发送（示例问题 & 手动输入），调用后端 API
 * =================================================================== */

// 统一处理示例问题和手动输入，并调用真实 FastAPI 后端。
async function sendQuestion(question) {
    const cleanQuestion = question.trim();

    if (!cleanQuestion || isRequesting) {
        return;
    }

    addMessage("user", cleanQuestion);
    const loadingMessage = addMessage("ai", "正在分析中...");
    setToolPanelMessage("正在调用后端工具...");
    setRequestingState(true);

    try {
        const data = await callChatApi(cleanQuestion);
        if (data.success === false) {
            updateMessage(loadingMessage, data.answer || data.error || "后端返回错误，请稍后重试。");
        } else {
            updateMessage(loadingMessage, data.answer || "后端已返回，但没有生成回答。");
        }
        renderToolCalls(data.tool_calls);
    } catch (error) {
        console.error("Chat request failed:", error);
        updateMessage(loadingMessage, "后端服务未连接，请先启动 FastAPI 后端。");
        setToolPanelMessage("后端服务未连接，请先启动 FastAPI 后端。");
    } finally {
        setRequestingState(false);
        messageInput.focus();
    }
}

/* ===================================================================
 * 事件绑定
 * =================================================================== */

// 示例问题按钮点击事件
exampleButtons.forEach((button) => {
    button.addEventListener("click", () => {
        sendQuestion(button.dataset.question);
    });
});

// 侧边栏菜单点击事件
menuItems.forEach((button) => {
    button.addEventListener("click", () => {
        handleMenuClick(button.textContent.trim());
    });
});

// 聊天输入框提交事件
chatForm.addEventListener("submit", (event) => {
    event.preventDefault();
    sendQuestion(messageInput.value);
    messageInput.value = "";
});

// 清空聊天按钮
const clearChatBtn = document.getElementById("clearChatBtn");
clearChatBtn.addEventListener("click", clearChat);

// Agent 模式切换
const modeButtons = document.querySelectorAll(".mode-btn");
modeButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
        modeButtons.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        currentMode = btn.dataset.mode;
    });
});
