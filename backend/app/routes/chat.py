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
from app.models.chat import ChatRequest
from groq import Groq

router = APIRouter(tags=["chat"])

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]

def _process_chat(question: str, session_id: str, dataset_id: str, platform: str):
    logger.info(f"USER QUESTION: {question}")          # debug
    history = get_chat_history(session_id, limit=10)
    context = retrieve_context(question, dataset_id=dataset_id, platform=platform)
    prompt = build_prompt(question, context, history, platform=platform)
    logger.info(f"FINAL PROMPT (first 500 chars): {prompt[:500]}")  # debug

    client = Groq(api_key=settings.groq_api_key)
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    answer = response.choices[0].message.content
    logger.info(f"ANSWER (first 300 chars): {answer[:300]}")

    add_chat_message(session_id, "user", question)
    add_chat_message(session_id, "assistant", answer)
    return answer, build_citations(context)

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        answer, sources = _process_chat(request.question, request.session_id, request.dataset_id, request.platform)
        return ChatResponse(answer=answer, sources=sources)
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    session_id = request.session_id
    dataset_id = request.dataset_id
    platform = request.platform
    question = request.question

    logger.info(f"STREAM USER QUESTION: {question}")
    history = get_chat_history(session_id, limit=10)
    context = retrieve_context(question, dataset_id=dataset_id, platform=platform)
    prompt = build_prompt(question, context, history, platform=platform)
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

            add_chat_message(session_id, "user", question)
            add_chat_message(session_id, "assistant", full_answer)

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