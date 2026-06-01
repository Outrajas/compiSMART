import json
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from app.rag.retriever import (
    plan_intent,
    get_session_state,
    update_session_state,
    retrieve_context,
    dataset_has_videos
)
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
    follow_up: Optional[str] = None

client = Groq(api_key=settings.groq_api_key)

def _process_chat(question: str, session_id: str, dataset_id: str, platform: str):
    logger.info(f"USER: {question}")

    # 1. Check dataset existence
    has_dataset = dataset_has_videos(dataset_id) if dataset_id else False

    # 2. Intent planning (LLM decides needs_retrieval and style)
    plan = plan_intent(question, has_dataset, client)
    needs_retrieval = plan.get("needs_retrieval", has_dataset)  # default to retrieval if dataset exists
    style = plan.get("style", "analytical")
    logger.info(f"Intent plan: needs_retrieval={needs_retrieval}, style={style}")

    # 3. Always fetch metadata (if dataset exists) for context; fetch chunks only if needed
    context = {}
    if has_dataset:
        # Metadata is always useful for analytics
        context = retrieve_context(question, dataset_id, platform, needs_retrieval=needs_retrieval)
    else:
        # No dataset: empty context
        context = {"all_metadata": [], "chunks": [], "analytics_summary": {}, "hook_summary": "", "semantic_profiles": []}

    # 4. Map style to prompt intent string
    if style == "verbatim":
        prompt_intent = "transcript_query"
    elif style == "concise":
        prompt_intent = "dataset_simple"
    elif style == "analytical":
        prompt_intent = "dataset_deep"
    else:
        prompt_intent = "dataset_deep"  # fallback

    # 5. Build prompt
    history = get_chat_history(session_id, limit=5)
    prompt = build_prompt(question, context, history, platform, intent=prompt_intent)

    # 6. Structured Context Debug Logging
    logger.info(
        f"\n=================== RAG CONTEXT DEBUG ===================\n"
        f"VIDEOS: {len(context.get('all_metadata', []))}\n"
        f"ANALYTICS: {1 if context.get('analytics_summary') else 0}\n"
        f"CHUNKS: {len(context.get('chunks', []))}\n"
        f"=========================================================\n"
    )
    for c in context.get("chunks", [])[:10]:
        logger.info(f"CHUNK ({c.get('video_id', 'unknown')}): {c.get('text', '')[:100]}")

    logger.info(f"Prompt length: {len(prompt)} chars, ~{len(prompt)//4} tokens")

    # 7. Call LLM
    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3 if style in ("concise", "verbatim") else 0.7,
        )
        answer = response.choices[0].message.content
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        answer = f"Sorry, I encountered an error: {str(e)}"

    # 8. Follow‑up suggestion (optional, for analytical queries)
    follow_up = None
    if style == "analytical" and context.get("all_metadata"):
        try:
            follow_prompt = f"Based on the user's question and your answer, suggest one short follow-up question (max 15 words) that a creator might ask next.\nUser: {question}\nAnswer: {answer}\nFollow-up:"
            follow_resp = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": follow_prompt}],
                temperature=0.5,
                max_tokens=50,
            )
            follow_up = follow_resp.choices[0].message.content.strip()
        except:
            pass

    # 9. Update session memory
    update_session_state(
        session_id,
        last_intent=plan.get("intent", "unknown"),
        last_topic=question[:100],
        active_videos=[v["video_id"] for v in context.get("all_metadata", [])],
    )

    # 10. Save to chat history
    add_chat_message(session_id, "user", question)
    add_chat_message(session_id, "assistant", answer)

    # 11. Build sources (only if metadata exists)
    sources = build_citations(context) if context.get("all_metadata") else []

    return answer, sources, follow_up

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        answer, sources, follow_up = _process_chat(
            request.question, request.session_id, request.dataset_id, request.platform
        )
        return ChatResponse(answer=answer, sources=sources, follow_up=follow_up)
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    answer, sources, follow_up = _process_chat(
        request.question, request.session_id, request.dataset_id, request.platform
    )
    async def gen():
        for word in answer.split():
            yield f"data: {json.dumps({'type': 'token', 'content': word + ' '})}\n\n"
            await asyncio.sleep(0.02)
        yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
        if follow_up:
            yield f"data: {json.dumps({'type': 'follow_up', 'content': follow_up})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream")