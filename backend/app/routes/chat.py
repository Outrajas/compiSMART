import json
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from app.rag.retriever import retrieve_context
from app.rag.prompts import build_prompt
from app.rag.citation_builder import build_citations
from app.core.config import settings
from app.core.logger import logger
from app.db.sqlite import add_chat_message, get_chat_history
from groq import Groq

router = APIRouter(tags=["chat"])

class Source(BaseModel):
    video_id: str
    chunk_id: Optional[int] = None

class ChatRequest(BaseModel):
    session_id: str
    question: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]

def _process_chat(question: str, session_id: str):
    """
    Core logic: retrieve, build prompt with history, call Groq.
    Returns (answer, sources).
    """
    # Load conversation history
    history = get_chat_history(session_id, limit=10)

    # Retrieve fresh context
    context = retrieve_context(question)
    prompt = build_prompt(question, context, history)
    sources = build_citations(context)

    client = Groq(api_key=settings.groq_api_key)
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    answer = response.choices[0].message.content

    # Persist messages
    add_chat_message(session_id, "user", question)
    add_chat_message(session_id, "assistant", answer)

    return answer, sources

# Non‑streaming endpoint
@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        answer, sources = _process_chat(request.question, request.session_id)
        return ChatResponse(answer=answer, sources=sources)
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Streaming endpoint
@router.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    session_id = request.session_id
    question = request.question

    # Load history, retrieve context
    history = get_chat_history(session_id, limit=10)
    context = retrieve_context(question)
    prompt = build_prompt(question, context, history)
    sources = build_citations(context)

    async def event_generator():
        full_answer = ""
        try:
            client = Groq(api_key=settings.groq_api_key)
            stream = client.chat.completions.create(
                model=settings.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                stream=True,
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    full_answer += token
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                    await asyncio.sleep(0)

            # Store the conversation after streaming complete
            add_chat_message(session_id, "user", question)
            add_chat_message(session_id, "assistant", full_answer)

            # Send sources
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )