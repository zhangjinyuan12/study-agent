# style.css 逐行分析

> 对应文件：[style.css](style.css) · [index.html](index.html) · [app.js](app.js)

---

## 1. CSS 变量（根字号）

```css
:root {
    --bg: #eef3f8;
    --surface: #ffffff;
    --surface-soft: #f6f8fb;
    --text: #172033;
    --muted: #667085;
    --line: #d9e2ec;
    --primary: #2563eb;
    --primary-dark: #1d4ed8;
    --cyan: #0891b2;
    --green: #16a34a;
    --warning: #f59e0b;
    --shadow: 0 18px 45px rgba(31, 42, 68, 0.12);
    --radius: 8px;
}
```

| 语法 | 说明 |
|---|---|
| `:root` | CSS 伪类，匹配文档根元素 `<html>`，优先级高于 `html` 选择器，适合定义全局 CSS 自定义属性 |
| `--bg` | 页面背景色 — 浅灰蓝，用在 `body` 的渐变色中 |
| `--surface` | 卡片/面板背景色 — 纯白，用在 `.sidebar`、`.chat-panel` 等 |
| `--surface-soft` | 柔和背景 — 极浅灰，用在 `.empty-state` 占位区 |
| `--text` | 主文字色 — 深蓝灰 |
| `--muted` | 次要文字色 — 灰，用在描述文字、标签 |
| `--line` | 边框色 — 浅灰蓝，用在所有 `border: 1px solid` 的地方 |
| `--primary` | 品牌主色 — 蓝 `#2563eb`（Tailwind blue-600），用于按钮、链接、激活态 |
| `--primary-dark` | 主色深色变体，用于 hover 态 |
| `--cyan` | 青色，与 `--primary` 搭配做渐变（按钮、填充条） |
| `--green` | 绿色，用于成功状态标识 |
| `--warning` | 琥珀色，用于进度条等需要暖色提示处 |
| `--shadow` | 卡片阴影，`box-shadow: 0 18px 45px …` |
| `--radius` | 统一圆角 `8px` |

HTML 对应：`<html>`。整个页面的所有颜色和圆角都基于这组变量，一处更改全局生效。

---

## 2. 全局重置

```css
* {
    box-sizing: border-box;
}
```

| 含义 | 说明 |
|---|---|
| `*` | 通配选择器，选中**所有**元素 |
| `box-sizing: border-box` | 让 `padding` 和 `border` 计入元素总宽高，避免写 `width: 100%; padding: 18px` 时溢出 |

HTML 对应：所有标签继承此盒模型。

---

## 3. Body

```css
body {
    margin: 0;
    min-height: 100vh;
    font-family: "Microsoft YaHei", "PingFang SC", Arial, sans-serif;
    color: var(--text);
    background:
        radial-gradient(circle at top left, rgba(37, 99, 235, 0.12), transparent 30%),
        linear-gradient(135deg, #f7fbff 0%, var(--bg) 52%, #f3f7f5 100%);
}
```

| 语法 | 说明 |
|---|---|
| `margin: 0` | 清除浏览器默认 8px margin |
| `min-height: 100vh` | `vh` = viewport height，撑满视口高度 |
| `font-family` | 中文字体回退链：微软雅黑 → PingFang SC → Arial → 系统无衬线 |
| `color: var(--text)` | 引用 CSS 变量 `--text` |
| `background` | **两层背景叠加**：顶层 `radial-gradient` 在左上角打一束蓝光光晕；底层 `linear-gradient` 从左上到右下从白渐变到浅灰再到极浅绿。逗号分隔多个背景，前者在上 |

HTML 对应：`<body>` 标签。

---

## 4. 表单元素统一

```css
button,
input {
    font: inherit;
}
```

| 语法 | 说明 |
|---|---|
| `button, input` | 分组选择器 |
| `font: inherit` | 简写属性，强制按钮和输入框继承 `body` 的字号字族，否则浏览器默认的 `font-size: smaller` 或 `font-family: monospace` 会破坏统一性 |

---

## 5. 全局按钮

```css
button {
    cursor: pointer;
}
```

所有按钮鼠标悬停时显示手型指针。

---

## 6. `.app` 容器

```css
.app {
    min-height: 100vh;
}
```

HTML 对应：`<div class="app">`，包住整个页面。撑满视口高度，确保背景覆盖完整。

---

## 7. 顶部导航栏 `.top-header`

```css
.top-header {
    height: 82px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
    padding: 18px 28px;
    color: #ffffff;
    background: linear-gradient(120deg, #14213d 0%, #1f4aa8 58%, #0f8ea8 100%);
    box-shadow: 0 10px 26px rgba(20, 33, 61, 0.22);
}
```

| 属性 | 说明 |
|---|---|
| `height: 82px` | 固定高度，配合 `.layout` 的 `calc(100vh - 82px)` 使左侧和主区域填满剩余空间 |
| `display: flex` + `align-items: center` | 垂直居中标题和 `Demo Badge` |
| `justify-content: space-between` | 标题在左，badge 在右，两端对齐 |
| `background: linear-gradient(120deg, ...)` | 深蓝到蓝到青的斜向渐变，与 `body` 的渐变形成呼应 |
| `box-shadow` | 底部投影，产生浮起效果 |

CSS 特殊技巧：
- `height: 82px` + `.layout` 的 `height: calc(100vh - 82px)` 形成经典**固定头 + 自适应内容**布局

HTML 对应：
```html
<header class="top-header">
    <div>
        <h1>StudyAgent</h1>
        <p>面向大学生...</p>
    </div>
    <span class="demo-badge">Demo Mode</span>
</header>
```

---

## 8. `.top-header` 内部标题

```css
.top-header h1 {
    margin: 0;
    font-size: 26px;
    line-height: 1.1;
    letter-spacing: 0;
}

.top-header p {
    margin: 7px 0 0;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.82);
}
```

| 语法 | 说明 |
|---|---|
| `.top-header h1` | 后代选择器，只命中 header 内的 `<h1>` |
| `letter-spacing: 0` | 显式将字间距归零，覆盖可能的浏览器默认值 |
| `color: rgba(255, 255, 255, 0.82)` | 半透明白色，比纯白更柔和，与深色背景形成层次 |

---

## 9. Demo Badge

```css
.demo-badge {
    flex: 0 0 auto;
    padding: 8px 13px;
    border: 1px solid rgba(255, 255, 255, 0.38);
    border-radius: 999px;
    font-size: 13px;
    color: #ffffff;
    background: rgba(255, 255, 255, 0.14);
}
```

| 语法 | 说明 |
|---|---|
| `flex: 0 0 auto` | flex 简写：不放大、不缩小、宽度由内容决定，确保 badge 不会被压缩 |
| `border-radius: 999px` | 超大圆角 = 胶囊形（药丸按钮），值大于宽高的一半即变椭圆 |
| `background: rgba(255, 255, 255, 0.14)` | 半透明背景，透出下方 header 渐变，产生毛玻璃质感 |

HTML 对应：`<span class="demo-badge">Demo Mode</span>`

---

## 10. 三栏主布局 `.layout`

```css
.layout {
    display: grid;
    grid-template-columns: 220px minmax(0, 1fr) 330px;
    gap: 18px;
    height: calc(100vh - 82px);
    min-height: 620px;
    padding: 18px;
}
```

这是整个布局的核心，详细拆解：

| 属性 | 含义 |
|---|---|
| `display: grid` | CSS Grid 布局 |
| `grid-template-columns: 220px minmax(0, 1fr) 330px` | **三列**：左侧 220px（菜单）、中间 `minmax(0, 1fr)` 弹性宽度（聊天区）、右侧 330px（工具面板） |
| `minmax(0, 1fr)` | `1fr` 的默认最小值是 `auto`，当内容过宽时可能溢出。`minmax(0, 1fr)` 强制最小值 0，确保中间列能收缩到 0 而不撑破 grid |
| `height: calc(100vh - 82px)` | 将 header 的 82px 从视口高度中减去，让 layout 填满剩余空间 |
| `gap: 18px` | grid 子项间距，等同于 `row-gap` + `column-gap` |

HTML 对应：
```html
<main class="layout">
    <aside class="sidebar">...</aside>
    <section class="workspace">...</section>
    <aside class="tool-panel">...</aside>
</main>
```

---

## 11. 面板统一样式

```css
.sidebar,
.chat-panel,
.feature-view,
.tool-panel,
.overview {
    border: 1px solid rgba(217, 226, 236, 0.86);
    border-radius: var(--radius);
    background: rgba(255, 255, 255, 0.92);
    box-shadow: var(--shadow);
}
```

五个面板共享白底、圆角、细边框和投影，视觉上统一为"浮在背景上的卡片"。

---

## 12. 侧边栏 `.sidebar`

```css
.sidebar {
    padding: 16px;
}

.sidebar nav {
    display: grid;
    gap: 10px;
}
```

| 属性 | 说明 |
|---|---|
| `padding: 16px` | 内边距让按钮与边框保持距离 |
| `display: grid` + `gap: 10px` | 菜单项纵向排列，间距 10px |

HTML 对应：
```html
<aside class="sidebar">
    <nav>
        <button class="menu-item active">智能问答</button>
        <button class="menu-item">学习任务</button>
        ...
    </nav>
</aside>
```

---

## 13. 菜单按钮 `.menu-item`

```css
.menu-item {
    width: 100%;
    min-height: 44px;
    padding: 0 14px;
    border: 1px solid transparent;
    border-radius: var(--radius);
    color: var(--muted);
    text-align: left;
    background: transparent;
    transition: all 0.2s ease;
}

.menu-item:hover,
.menu-item.active {
    color: var(--primary);
    border-color: rgba(37, 99, 235, 0.16);
    background: #eef5ff;
}
```

| 属性 | 说明 |
|---|---|
| `width: 100%` | 撑满 sidebar 宽度 |
| `min-height: 44px` | 无障碍最小点击区域 44px（WCAG 推荐） |
| `border: 1px solid transparent` | 预占边框空间，避免 hover 时布局跳动 |
| `transition: all 0.2s ease` | 颜色/边框/背景变化时 0.2s 平滑过渡 |
| `.menu-item:hover, .menu-item.active` | **分组选择器** — hover 和 active 态共用样式，蓝色文字 + 浅蓝背景 |

JS 对应：`app.js` 中的 `setActiveMenu(label)` 通过 `classList.toggle("active", ...)` 给当前菜单项添加 `.active` 类。

---

## 14. 工作区容器 `.workspace`

```css
.workspace {
    min-width: 0;
    display: grid;
    grid-template-rows: minmax(0, 1fr) auto;
    gap: 18px;
}
```

| 属性 | 说明 |
|---|---|
| `min-width: 0` | 防止 grid 子项溢出，与 `.layout` 的 `minmax(0, 1fr)` 同理 |
| `grid-template-rows: minmax(0, 1fr) auto` | 两行：上：聊天区（弹性撑满），下：仪表盘（按内容高度） |

HTML 对应：
```html
<section class="workspace">
    <section class="chat-panel">...</section>
    <section class="dashboard">...</section>
</section>
```

---

## 15. 隐藏辅助类

```css
.is-hidden {
    display: none !important;
}
```

| 语法 | 说明 |
|---|---|
| `!important` | 强制最高优先级，确保任何其他规则都无法覆盖隐藏状态 |

JS 对应：`app.js` 中多处调用 `.classList.add("is-hidden")` / `.classList.remove("is-hidden")` 来切换聊天面板、仪表盘和 feature-view 的显示。

---

## 16. 聊天面板 `.chat-panel`

```css
.chat-panel {
    min-height: 0;
    padding: 18px;
    display: grid;
    grid-template-rows: auto minmax(0, 1fr) auto auto;
    gap: 14px;
}
```

四行 grid 布局：
| 行 | 内容 | 高度 |
|---|---|---|
| `auto` | 面板标题（`.panel-heading`） | 内容决定 |
| `minmax(0, 1fr)` | 消息列表（`.chat-messages`） | 弹性撑满 |
| `auto` | 示例按钮区（`.example-area`） | 内容决定 |
| `auto` | 输入框（`.chat-input-bar`） | 内容决定 |

`min-height: 0` 让弹性行能正确收缩（grid 默认 `min-height: auto` 会阻止收缩）。

---

## 17. 功能性页面 `.feature-view`

```css
.feature-view {
    min-height: 0;
    padding: 18px;
    display: grid;
    grid-template-rows: auto auto minmax(0, 1fr);
    align-content: start;
    gap: 14px;
}
```

| 属性 | 说明 |
|---|---|
| `grid-template-rows: auto auto minmax(0, 1fr)` | 标题行 → 工具栏/搜索行 → 内容区（弹性撑满） |
| `align-content: start` | 让内容从顶部开始排列，避免内容少时被拉伸居中 |

JS 对应：`app.js` 的 `showFeatureView()` 负责填充这个区域的 HTML 内容，包括 `panel-heading`、搜索表单、`feature-answer` 等。

---

## 18. 功能展示区 `.feature-answer`

```css
.feature-answer {
    min-height: 180px;
    overflow-y: auto;
    padding: 14px;
    border: 1px solid var(--line);
    border-radius: var(--radius);
    color: #263244;
    line-height: 1.7;
    white-space: pre-line;
    background: linear-gradient(180deg, #fbfdff 0%, #f4f7fb 100%);
}
```

| 属性 | 说明 |
|---|---|
| `min-height: 180px` | 即使内容为空也保留一定高度，避免布局塌陷 |
| `overflow-y: auto` | 内容超出时可垂直滚动 |
| `white-space: pre-line` | 保留换行符 `\n`，且自动换行——JS 中 `"\n".join(...)` 的文本能正确显示分段 |
| `background: linear-gradient(180deg, ...)` | 从上到下的极浅渐变，与聊天消息区的背景一致 |

JS 对应：`createFeatureAnswerBox()` 创建此元素，`renderToolLogsPage`、`renderMaterialSearchPage` 等函数用它显示内容。

---

## 19. 资料搜索表单 `.feature-search`

```css
.feature-search {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 88px;
    gap: 10px;
}

.feature-search input {
    min-width: 0;
    height: 42px;
    padding: 0 13px;
    border: 1px solid #cdd8e5;
    border-radius: var(--radius);
    color: var(--text);
    background: #ffffff;
    outline: none;
}

.feature-search input:focus {
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}

.feature-search button {
    height: 42px;
    border: none;
    border-radius: var(--radius);
    color: #ffffff;
    font-weight: 700;
    background: linear-gradient(135deg, var(--primary) 0%, var(--cyan) 100%);
}
```

| 语法 | 说明 |
|---|---|
| `grid-template-columns: minmax(0, 1fr) 88px` | 输入框弹性撑满，搜索按钮固定 88px |
| `input:focus` | `:focus` 伪类，聚焦时蓝色边框 + 外发光 `box-shadow`（常见无障碍焦点指示器） |
| `outline: none` | 去掉浏览器默认的 `:focus` 轮廓，用自定义的 `box-shadow` 替代 |
| `background: linear-gradient(135deg, ...)` | 蓝→青渐变按钮，与 header 渐变和发送按钮风格统一 |

HTML 对应：`renderMaterialSearchPage()` 动态创建的 `<form class="feature-search">`。

---

## 20. 测试按钮网格

```css
.test-button-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
}
```

两列等宽网格，用于排列测试问题按钮。

JS 对应：`renderTestCasesPage()` 中创建 `buttonGrid`，class 为 `test-button-grid`。

---

## 21. 面板标题 `.panel-heading`

```css
.panel-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
}

.panel-heading h2,
.overview h2 {
    margin: 0;
    font-size: 18px;
    line-height: 1.2;
    letter-spacing: 0;
}

.panel-heading p {
    margin: 6px 0 0;
    color: var(--muted);
    font-size: 13px;
}
```

`flex` + 两端对齐，标题在左，可能的操作按钮在右。JS 中 `showFeatureView()` 创建的标题 HTML 结构与此选择器匹配。

---

## 22. 聊天消息区 `.chat-messages`

```css
.chat-messages {
    min-height: 210px;
    overflow-y: auto;
    padding: 14px;
    border: 1px solid var(--line);
    border-radius: var(--radius);
    background: linear-gradient(180deg, #fbfdff 0%, #f4f7fb 100%);
}
```

固定最小 210px，内容超出时滚动。背景渐变与 `.feature-answer` 一致，视觉统一。

HTML 对应：`<div class="chat-messages" id="chatMessages">`

---

## 23. 单条消息 `.message`

```css
.message {
    display: flex;
    gap: 10px;
    margin-bottom: 13px;
}

.message:last-child {
    margin-bottom: 0;
}

.message-role {
    width: 34px;
    height: 34px;
    flex: 0 0 34px;
    display: grid;
    place-items: center;
    border-radius: 50%;
    font-size: 12px;
    font-weight: 700;
    color: #ffffff;
    background: var(--primary);
}

.user-message {
    flex-direction: row-reverse;
}

.user-message .message-role {
    background: #0f766e;
}
```

| 语法 | 说明 |
|---|---|
| `flex: 0 0 34px` | 不放大、不缩小、固定 34px，保障头像圆形不变形 |
| `place-items: center` | grid 简写 = `align-items: center; justify-items: center`，文字水平垂直居中 |
| `border-radius: 50%` | 50% 圆角 = 正圆（宽高相等时） |
| `.user-message` | `flex-direction: row-reverse` 让用户消息头像在右、气泡在左 |
| `.user-message .message-role` | 用户头像用深绿色区分于 AI 的蓝色 |

HTML 对应：`addMessage()` 动态创建的结构：
```html
<article class="message ai-message">
    <div class="message-role">AI</div>
    <div class="message-bubble">...</div>
</article>
```

---

## 24. 消息气泡 `.message-bubble`

```css
.message-bubble {
    max-width: min(680px, calc(100% - 44px));
    padding: 11px 13px;
    border-radius: var(--radius);
    color: #263244;
    line-height: 1.7;
    font-size: 14px;
    background: #ffffff;
    border: 1px solid #e3e9f1;
    box-shadow: 0 8px 20px rgba(31, 42, 68, 0.08);
    white-space: pre-line;
}
```

| 语法 | 说明 |
|---|---|
| `max-width: min(680px, calc(100% - 44px))` | `min()` 取两者较小值：不超过 680px，同时留出 44px 给头像（34px + gap 10px）|
| `white-space: pre-line` | 保留 `\n` 换行，与 `.feature-answer` 一致 |

JS 对应：`addMessage()` 中的 `bubble.textContent = text`。

```css
.user-message .message-bubble {
    color: #ffffff;
    border-color: transparent;
    background: linear-gradient(135deg, var(--primary) 0%, var(--cyan) 100%);
}
```

用户消息气泡使用蓝→青渐变填充、白色文字、无边框，与 AI 消息的白底灰边框形成视觉区分。

---

## 25. 示例问题按钮 `.example-area` / `.example-button`

```css
.example-area {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
}

.example-button {
    min-height: 40px;
    padding: 8px 11px;
    border: 1px solid #d7e2ef;
    border-radius: var(--radius);
    color: #245178;
    text-align: left;
    background: #f7fbff;
    transition: all 0.18s ease;
}

.example-button:hover {
    border-color: rgba(37, 99, 235, 0.42);
    color: var(--primary-dark);
    background: #edf6ff;
    transform: translateY(-1px);
}
```

| 语法 | 说明 |
|---|---|
| `repeat(2, minmax(0, 1fr))` | 两列等宽网格 |
| `transform: translateY(-1px)` | 悬停时微微上移 1px，配合背景色变化形成按压感 |
| `transition: all 0.18s ease` | 0.18s 过渡，比 `.menu-item` 的 0.2s 略快，触感更轻快 |

HTML 对应：
```html
<div class="example-area">
    <button class="example-button" data-question="...">...</button>
</div>
```

JS 中 `renderTestCasesPage()` 也复用 `.example-button` 样式创建测试按钮网格。

---

## 26. 聊天输入栏 `.chat-input-bar`

```css
.chat-input-bar {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 86px;
    gap: 10px;
}

.chat-input-bar input {
    min-width: 0;
    height: 42px;
    padding: 0 13px;
    border: 1px solid #cdd8e5;
    border-radius: var(--radius);
    color: var(--text);
    background: #ffffff;
    outline: none;
}

.chat-input-bar input:focus {
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}

.chat-input-bar button {
    height: 42px;
    border: none;
    border-radius: var(--radius);
    color: #ffffff;
    font-weight: 700;
    background: linear-gradient(135deg, var(--primary) 0%, var(--cyan) 100%);
    box-shadow: 0 10px 18px rgba(37, 99, 235, 0.18);
}
```

| 属性 | 说明 |
|---|---|
| `grid-template-columns: minmax(0, 1fr) 86px` | 输入框弹性撑满，发送按钮固定 86px |
| `box-shadow: 0 10px 18px rgba(37, 99, 235, 0.18)` | 按钮底部投影，产生浮起感，与 `.message-bubble` 的阴影风格一致 |

HTML 对应：
```html
<form class="chat-input-bar" id="chatForm">
    <input id="messageInput" type="text" ...>
    <button type="submit">发送</button>
</form>
```

---

## 27. 仪表盘 `.dashboard` / `.stat-grid` / `.stat-card`

```css
.dashboard {
    display: grid;
    grid-template-columns: minmax(260px, 1fr) minmax(300px, 1.05fr);
    gap: 18px;
}

.stat-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
}

.stat-card {
    min-height: 94px;
    padding: 15px;
    border: 1px solid rgba(217, 226, 236, 0.88);
    border-radius: var(--radius);
    background: rgba(255, 255, 255, 0.94);
    box-shadow: 0 12px 28px rgba(31, 42, 68, 0.09);
}

.stat-card span {
    display: block;
    color: var(--muted);
    font-size: 13px;
}

.stat-card strong {
    display: block;
    margin-top: 12px;
    font-size: 28px;
    line-height: 1;
    color: #17325f;
}
```

| 属性 | 说明 |
|---|---|
| `grid-template-columns: minmax(260px, 1fr) minmax(300px, 1.05fr)` | 左侧统计卡片（最小 260px）和右侧概览（最小 300px，权重 1.05 略宽）|
| `display: block` + `span`/`strong` | 标签在上，数字在下，各占一行 |

HTML 对应：
```html
<article class="stat-card">
    <span>今日任务</span>
    <strong>6</strong>
</article>
```

---

## 28. 学习概览 `.overview` / `.progress-list` / `.progress-track`

```css
.overview {
    padding: 16px;
}

.progress-list {
    display: grid;
    gap: 13px;
    margin-top: 14px;
}

.progress-meta {
    display: flex;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 7px;
    color: #334155;
    font-size: 14px;
}

.progress-track {
    height: 10px;
    overflow: hidden;
    border-radius: 999px;
    background: #e7edf5;
}

.progress-fill {
    height: 100%;
    border-radius: inherit;
}
```

| 语法 | 说明 |
|---|---|
| `.progress-fill` | `border-radius: inherit` 继承父级 `.progress-track` 的 `border-radius: 999px`，让填充条两端保持圆角 |
| `overflow: hidden` | 确保填充条不溢出轨道 |

HTML 对应：
```html
<section class="overview">
    <div class="progress-list">
        <div class="progress-item">
            <div class="progress-meta"><span>数据结构</span><strong>75%</strong></div>
            <div class="progress-track">
                <div class="progress-fill fill-data-structure"></div>
            </div>
        </div>
    </div>
</section>
```

---

## 29. 三色进度条

```css
.fill-data-structure {
    width: 75%;
    background: linear-gradient(90deg, var(--primary) 0%, #06b6d4 100%);
}

.fill-csapp {
    width: 60%;
    background: linear-gradient(90deg, #0f766e 0%, #22c55e 100%);
}

.fill-math {
    width: 50%;
    background: linear-gradient(90deg, var(--warning) 0%, #f97316 100%);
}
```

| 类名 | 宽度 | 渐变色 | 对应科目 |
|---|---|---|---|
| `.fill-data-structure` | 75% | 蓝→青 | 数据结构（主色调） |
| `.fill-csapp` | 60% | 深绿→绿 | CSAPP |
| `.fill-math` | 50% | 琥珀→橙 | 高等数学（暖色，较低完成度） |

三个科目的宽度和颜色都不同，形成直观的视觉对比。

---

## 30. 工具面板 `.tool-panel`

```css
.tool-panel {
    min-height: 0;
    padding: 18px;
    display: grid;
    grid-template-rows: auto minmax(0, 1fr);
    gap: 14px;
}
```

两行：标题（自动高度）+ 工具调用列表（弹性撑满）。

HTML 对应：
```html
<aside class="tool-panel">
    <div class="panel-heading">...</div>
    <div class="tool-list" id="toolList">...</div>
</aside>
```

---

## 31. 工具调用卡 `.tool-list` / `.tool-card`

```css
.tool-list {
    min-height: 0;
    overflow-y: auto;
    display: grid;
    align-content: start;
    gap: 12px;
    padding-right: 4px;
}

.tool-card {
    padding: 14px;
    border: 1px solid #dae5f1;
    border-radius: var(--radius);
    background: #fbfdff;
    box-shadow: 0 10px 24px rgba(31, 42, 68, 0.08);
}

.tool-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 10px;
}

.tool-name {
    font-weight: 800;
    color: #17325f;
    overflow-wrap: anywhere;
}

.status-success {
    flex: 0 0 auto;
    padding: 4px 8px;
    border-radius: 999px;
    color: #166534;
    font-size: 12px;
    background: #dcfce7;
}
```

| 语法 | 说明 |
|---|---|
| `align-content: start` | 卡片从顶部排列，不拉伸 |
| `overflow-wrap: anywhere` | 超长工具名可在任意字符处断行，防止溢出 |
| `.status-success` | 绿色胶囊标签"✅ 成功" |

JS 对应：`renderToolCalls(data.tool_calls)` 动态创建这些 `.tool-card` 结构。

---

## 32. 工具调用字段 `.tool-field`

```css
.tool-field {
    margin-top: 9px;
}

.tool-field span {
    display: block;
    margin-bottom: 4px;
    color: var(--muted);
    font-size: 12px;
}

.tool-field code {
    display: block;
    padding: 8px;
    border: 1px solid #e3e9f1;
    border-radius: 6px;
    color: #24324a;
    font-family: Consolas, "Courier New", monospace;
    font-size: 12px;
    line-height: 1.5;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    background: #f4f7fb;
}
```

`code` 标签等宽字体 + `pre-wrap`，用于显示 JSON 格式的输入/输出参数。

JS 对应：`createToolField(label, value)` 生成此结构。

---

## 33. JSON 折叠面板

```css
.raw-json-section {
    display: grid;
    gap: 8px;
}

.raw-json-toggle {
    justify-self: start;
    min-height: 32px;
    padding: 6px 10px;
    border: 1px solid #d7e2ef;
    border-radius: var(--radius);
    color: #245178;
    font-size: 12px;
    background: #f7fbff;
}

.raw-json-toggle:hover {
    border-color: rgba(37, 99, 235, 0.42);
    color: var(--primary-dark);
    background: #edf6ff;
}

.raw-json {
    display: none;
    max-height: 220px;
    overflow: auto;
    margin: 0;
    padding: 10px;
    border: 1px solid #d7e2ef;
    border-radius: 6px;
    color: #24324a;
    font-family: Consolas, "Courier New", monospace;
    font-size: 12px;
    line-height: 1.5;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    background: #f4f7fb;
}

.raw-json.open {
    display: block;
}
```

| 语法 | 说明 |
|---|---|
| `.raw-json` 默认 `display: none` | JSON 内容默认折叠隐藏 |
| `.raw-json.open` | JS 切换 `.open` 类时显示为 `block` |
| `justify-self: start` | 按钮左对齐，不拉伸 |
| `max-height: 220px` | JSON 面板最大高度，超出滚动 |

JS 对应：`createRawJsonSection(tool)` 创建按钮 + pre 结构，点击按钮 `classList.toggle("open")` 切换显示。

---

## 34. 空状态

```css
.empty-state {
    display: grid;
    min-height: 140px;
    place-items: center;
    padding: 18px;
    border: 1px dashed #c9d6e4;
    border-radius: var(--radius);
    color: var(--muted);
    text-align: center;
    background: var(--surface-soft);
}
```

`border: dashed` 虚线与普通面板的实线边框区分，`place-items: center` 让提示文字在 140px 区域内居中。背景使用 `--surface-soft` 柔和色，视觉上标记为"占位区"。

HTML 对应：
```html
<div class="empty-state">等待用户提问后显示工具调用过程。</div>
```

---

## 35. 断点响应式

### 1180px 断点

```css
@media (max-width: 1180px) {
    .layout {
        grid-template-columns: 190px minmax(0, 1fr);
        height: auto;
        min-height: calc(100vh - 82px);
    }

    .tool-panel {
        grid-column: 1 / -1;
        max-height: 360px;
    }
}
```

| 语法 | 说明 |
|---|---|
| `@media (max-width: 1180px)` | 视口宽度 ≤ 1180px 时触发 |
| `grid-template-columns: 190px minmax(0, 1fr)` | 从三栏变为两栏，右侧工具面板移到最后 |
| `grid-column: 1 / -1` | 工具面板跨越所有列（`-1` 是显式 grid 的最后一列），整行显示 |
| `height: auto` | 允许 layout 高度随内容增长，不再固定为 `calc(100vh - 82px)` |

### 860px 断点

```css
@media (max-width: 860px) {
    .top-header {
        height: auto;
        align-items: flex-start;
        padding: 16px;
        flex-direction: column;
    }

    .layout {
        grid-template-columns: 1fr;
        height: auto;
        min-height: 0;
        padding: 14px;
    }

    .sidebar nav {
        grid-template-columns: repeat(3, minmax(0, 1fr));
    }

    .menu-item {
        text-align: center;
        padding: 0 8px;
    }

    .dashboard {
        grid-template-columns: 1fr;
    }

    .example-area,
    .stat-grid,
    .test-button-grid {
        grid-template-columns: 1fr;
    }

    .chat-messages {
        max-height: 360px;
    }
}
```

| 语法 | 说明 |
|---|---|
| `flex-direction: column` | header 变为纵向堆叠，标题在上、badge 在下 |
| `grid-template-columns: 1fr` | 单列布局，所有面板竖直排列 |
| `grid-template-columns: repeat(3, 1fr)` | 左侧菜单从纵向变为 3 列网格 |
| 各 `grid-template-columns: 1fr` | 所有网格都变为单列 |

### 520px 断点

```css
@media (max-width: 520px) {
    .top-header h1 { font-size: 22px; }
    .sidebar nav { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .chat-panel, .tool-panel, .overview, .sidebar { padding: 14px; }
    .chat-input-bar { grid-template-columns: 1fr; }
    .feature-search { grid-template-columns: 1fr; }
    .chat-input-bar button { width: 100%; }
}
```

手机断点：进一步缩小内边距，菜单变 2 列，输入框和搜索框变为上下结构（按钮独占一行并 100% 宽度）。

---

## 总结：CSS 与 HTML/JS 的对应关系

| CSS 类 | 定义位置（HTML） | 操作位置（JS） |
|---|---|---|
| `.menu-item` / `.active` | `index.html` 中的 `<button class="menu-item">` | `setActiveMenu()` 切换 active |
| `.is-hidden` | 无静态 HTML | `showChatView()`、`showFeatureView()` 切换 |
| `.feature-view` / `.feature-answer` | 无静态 HTML | `app.js` 第 18 行 `createElement("section")` |
| `.feature-search` | 无静态 HTML | `renderMaterialSearchPage()` 动态创建 |
| `.test-button-grid` | 无静态 HTML | `renderTestCasesPage()` 动态创建 |
| `.tool-card` / `.tool-card-header` / `.tool-name` / `.status-success` | 无静态 HTML | `renderToolCalls()` 动态创建 |
| `.tool-field` / `.raw-json-section` / `.raw-json-toggle` / `.raw-json` | 无静态 HTML | `createToolField()`、`createRawJsonSection()` |
| `.empty-state` | `index.html` 的 `#toolList` 内的默认内容 | JS 清空并填入工具卡片 |
| `.chat-panel` / `.chat-messages` / `.message` / `.message-bubble` | `index.html` | `addMessage()`、`updateMessage()` |
| `.stat-card` / `.overview` / `.progress-*` | `index.html` 静态写死 | 无 JS 操作（纯静态展示） |
| `.dashboard` | `index.html` 静态 | `showChatView()`/`showFeatureView()` 切换显示/隐藏 |

整个 CSS 采用 **CSS 变量 + Grid + Flex + 渐变色 + 投影** 的风格体系，通过 3 个断点实现从桌面到手机的完整响应式降级，所有 JS 动态创建的 HTML 结构都有对应的 CSS 类名与之匹配。
