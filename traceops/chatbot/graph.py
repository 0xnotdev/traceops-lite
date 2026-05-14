from typing import Optional, TypedDict
import logging

from langgraph.graph import StateGraph, END

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from traceops.chatbot.documents import get_vectorstore
from traceops.core.config import settings


logger = logging.getLogger(__name__)


# ── Graph state ──────────────────────────────────────────
class ChatState(TypedDict):
    question: str
    retrieved_chunks: list[str]
    sources: list[str]
    answer: str
    session_id: str
    error: Optional[str]


# ── Node: retrieve relevant documents ────────────────────
def retrieve_node(state: ChatState) -> ChatState:
    logger.info(f"Retrieving for: {state['question'][:60]}")

    vs = get_vectorstore()

    results = vs.similarity_search(
        state["question"],
        k=3,
    )

    chunks = [
        doc.page_content
        for doc in results
    ]

    sources = [
        doc.metadata.get("source", "unknown")
        for doc in results
    ]

    state["retrieved_chunks"] = chunks
    state["sources"] = sources

    return state


# ── Node: generate answer with Gemini ────────────────────
def generate_node(state: ChatState) -> ChatState:
    context = "\n\n---\n\n".join(state["retrieved_chunks"])

    messages = [
        SystemMessage(
            content=(
                "You are an HR assistant. "
                "Answer the user's question using ONLY "
                "the provided context. "
                "If context is insufficient, say so clearly.\n\n"
                f"CONTEXT:\n{context}"
            )
        ),
        HumanMessage(content=state["question"]),
    ]

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=settings.gemini_api_key,
        temperature=0,
    )

    response = llm.invoke(messages)

    state["answer"] = response.content

    return state

# ── Build the graph ───────────────────────────────────────
def build_rag_graph():
    g = StateGraph(ChatState)

    g.add_node("retrieve", retrieve_node)
    g.add_node("generate", generate_node)

    g.set_entry_point("retrieve")

    g.add_edge("retrieve", "generate")
    g.add_edge("generate", END)

    return g.compile()


rag_graph = build_rag_graph()