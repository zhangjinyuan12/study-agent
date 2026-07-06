const CHAT_API_URL = "http://127.0.0.1:8000/chat";
const TOOL_LOGS_API_URL = "http://127.0.0.1:8000/tool-logs";

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

let isRequesting = false;
let featureRequestId = 0;

const featureView = document.createElement("section");
featureView.className = "feature-view is-hidden";
featureView.setAttribute("aria-label", "功能页面");
workspace.appendChild(featureView);

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

function updateMessage(messageRef, text) {
    messageRef.bubble.textContent = text;
    scrollMessagesToBottom();
}

function setActiveMenu(label) {
    menuItems.forEach((item) => {
        item.classList.toggle("active", item.textContent.trim() === label);
    });
}

function showChatView() {
    featureRequestId += 1;
    setActiveMenu("智能问答");
    featureView.classList.add("is-hidden");
    chatPanel.classList.remove("is-hidden");
    dashboard.classList.remove("is-hidden");
    messageInput.focus();
}

function showFeatureView(title, description = "") {
    featureRequestId += 1;
    chatPanel.classList.add("is-hidden");
    dashboard.classList.add("is-hidden");
    featureView.classList.remove("is-hidden");
    featureView.innerHTML = "";

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

function createFeatureAnswerBox(initialText = "正在分析中...") {
    const answerBox = document.createElement("div");
    answerBox.className = "feature-answer";
    answerBox.textContent = initialText;
    featureView.appendChild(answerBox);
    return answerBox;
}

function scrollMessagesToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function setRequestingState(isLoading) {
    isRequesting = isLoading;
    messageInput.disabled = isLoading;
    sendButton.disabled = isLoading;

    exampleButtons.forEach((button) => {
        button.disabled = isLoading;
    });
}

function setToolPanelMessage(text) {
    toolList.innerHTML = "";

    const emptyState = document.createElement("div");
    emptyState.className = "empty-state";
    emptyState.textContent = text;

    toolList.appendChild(emptyState);
}

function formatJson(value) {
    try {
        return JSON.stringify(value ?? {}, null, 2);
    } catch (error) {
        return String(value);
    }
}

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

function formatSimpleValue(value) {
    if (Array.isArray(value)) {
        return value.join("、");
    }

    if (typeof value === "object" && value !== null) {
        return JSON.stringify(value);
    }

    return String(value);
}

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

function buildMaterialsSummary(result) {
    const materials = Array.isArray(result.matched_materials) ? result.matched_materials : [];
    const snippets = materials
        .slice(0, 2)
        .map((material) => {
            const title = material.title || "未命名资料";
            const content = material.content ? ` - ${truncateText(material.content, 80)}` : "";
            return `- ${title}${content}`;
        })
        .join("\n");

    return [
        `查询到资料片段: ${materials.length} 个`,
        snippets || "暂无资料摘要"
    ].join("\n");
}

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

function truncateText(text, maxLength) {
    if (text.length <= maxLength) {
        return text;
    }

    return `${text.slice(0, maxLength)}...`;
}

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

async function callChatApi(message) {
    const response = await fetch(CHAT_API_URL, {
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

async function runFeatureChat(message, answerBox) {
    const currentRequestId = ++featureRequestId;
    answerBox.textContent = "正在分析中...";
    setToolPanelMessage("正在调用后端工具...");

    try {
        const data = await callChatApi(message);

        if (currentRequestId !== featureRequestId) {
            return;
        }

        answerBox.textContent = data.answer || "后端已返回，但没有生成回答。";
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

function renderAutoChatPage(title, message) {
    setActiveMenu(title);
    showFeatureView(title, `自动向 StudyAgent 提问：${message}`);
    const answerBox = createFeatureAnswerBox();
    runFeatureChat(message, answerBox);
}

function renderMaterialSearchPage() {
    setActiveMenu("资料检索");
    showFeatureView("资料检索", "输入知识点后，系统会调用 /chat 检索相关学习资料。");

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

    form.addEventListener("submit", (event) => {
        event.preventDefault();
        const keyword = input.value.trim() || "B+树";
        runFeatureChat(`${keyword}的重点是什么？`, answerBox);
    });
}

async function renderToolLogsPage() {
    setActiveMenu("工具日志");
    showFeatureView("工具日志", "后续可在这里查看后端保存的工具调用记录。");
    const answerBox = createFeatureAnswerBox("正在检查工具日志接口...");
    const currentRequestId = ++featureRequestId;
    setToolPanelMessage("工具日志页面暂不调用智能体工具。");

    try {
        const response = await fetch(TOOL_LOGS_API_URL);

        if (currentRequestId !== featureRequestId) {
            return;
        }

        if (response.status === 404) {
            answerBox.textContent = "工具日志接口尚未实现，下一阶段将接入后端日志查询。";
            return;
        }

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const logs = await response.json();
        answerBox.textContent = formatToolLogs(logs);
    } catch (error) {
        if (currentRequestId !== featureRequestId) {
            return;
        }

        console.error("Tool logs request failed:", error);
        answerBox.textContent = "后端服务未连接，请先启动 FastAPI 后端。";
        setToolPanelMessage("后端服务未连接，请先启动 FastAPI 后端。");
    }
}

function formatToolLogs(logs) {
    if (!Array.isArray(logs) || logs.length === 0) {
        return "工具日志接口已返回，但暂无日志数据。";
    }

    return logs
        .slice(0, 8)
        .map((log, index) => `${index + 1}. ${log.tool_name || "unknown_tool"}`)
        .join("\n");
}

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
        updateMessage(loadingMessage, data.answer || "后端已返回，但没有生成回答。");
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

exampleButtons.forEach((button) => {
    button.addEventListener("click", () => {
        sendQuestion(button.dataset.question);
    });
});

menuItems.forEach((button) => {
    button.addEventListener("click", () => {
        handleMenuClick(button.textContent.trim());
    });
});

chatForm.addEventListener("submit", (event) => {
    event.preventDefault();
    sendQuestion(messageInput.value);
    messageInput.value = "";
});
