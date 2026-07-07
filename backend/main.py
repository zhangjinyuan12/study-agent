from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .agent import run_agent
from .database import execute_query
from .llm_agent import run_llm_agent
from .tool_registry import TOOLS


app = FastAPI(title="StudyAgent Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


@app.get("/health")
def health():
    return {"status": "ok", "message": "StudyAgent backend is running"}


@app.post("/chat")
def chat(request: ChatRequest):
    message = request.message.strip()

    if not message:
        return {
            "success": False,
            "answer": "请输入有效的问题。",
            "tool_calls": [],
        }

    try:
        result = run_agent(message)
        return {
            "success": True,
            "answer": result.get("answer", ""),
            "tool_calls": result.get("tool_calls", []),
        }
    except Exception as error:
        return {
            "success": False,
            "answer": f"后端处理请求时发生错误：{error}",
            "tool_calls": [],
        }


@app.post("/chat-agent")
def chat_agent(request: ChatRequest):
    return run_llm_agent(request.message)


@app.get("/tool-logs")
def get_tool_logs():
    logs = execute_query(
        """
        SELECT id, tool_name, input_args, output_result, created_at
        FROM tool_logs
        ORDER BY id DESC
        LIMIT 20
        """
    )
    return {"logs": logs}


@app.get("/tools")
def get_tools():
    return {"tools": TOOLS}
