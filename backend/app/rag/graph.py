from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, List
from app.rag.retriever import retrieve_context
from app.rag.prompts import build_prompt
from app.rag.citation_builder import build_citations
from app.core.config import settings
from app.core.logger import logger
from groq import Groq

class GraphState(TypedDict):
    question: str
    answer: Optional[str]
    sources: Optional[List[dict]]   # now list of dicts
    error: Optional[str]

def retrieve_node(state: GraphState) -> GraphState:
    return state

def generate_node(state: GraphState) -> GraphState:
    try:
        question = state["question"]
        context = retrieve_context(question)
        prompt = build_prompt(question, context)
        sources = build_citations(context)   # returns list

        client = Groq(api_key=settings.groq_api_key)
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        answer = response.choices[0].message.content

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "error": None
        }
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        return {
            "question": state["question"],
            "answer": "Sorry, I couldn't generate an answer at this time.",
            "sources": [],
            "error": str(e)
        }

workflow = StateGraph(GraphState)
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("generate", generate_node)
workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", END)
graph = workflow.compile()