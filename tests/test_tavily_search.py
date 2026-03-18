import operator
from typing import TypedDict, Annotated, Literal

from dotenv import load_dotenv
import os

from app.tool.tavily_search import tavily_search

from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from langchain_community.chat_models import ChatTongyi

# 加载 .env
load_dotenv()

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")

model = ChatTongyi(model="qwen-turbo", api_key=DASHSCOPE_API_KEY)

# ===== 状态定义 =====
class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]


# ===== 注册 tool =====
tools = [tavily_search]
tool_node = ToolNode(tools)

# 关键：绑定 tool
model_with_tools = model.bind_tools(tools)


# ===== LLM 节点 =====
def llm_call(state: MessagesState):
    response = model_with_tools.invoke(
        [
            SystemMessage(
                content="You are a research assistant. Use tools when needed."
            )
        ] + state["messages"]
    )
    return {"messages": [response]}


# ===== 判断是否调用 tool =====
def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    last_message = state["messages"][-1]

    if getattr(last_message, "tool_calls", None):
        return "tool_node"
    return END


# ===== 构建 graph =====
builder = StateGraph(MessagesState)

builder.add_node("llm_call", llm_call)
builder.add_node("tool_node", tool_node)

builder.add_edge(START, "llm_call")
builder.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
builder.add_edge("tool_node", "llm_call")

graph = builder.compile()


# ===== 运行 =====
result = graph.invoke(
    {
        "messages": [
            HumanMessage(content="What is Notion pricing? Use web search.")
        ]
    }
)

# ===== 输出 =====
for msg in result["messages"]:
    print(msg)