from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.constants import CHUNK_SIZE, CHUNK_OVERLAP
from app.core.logger import logger

_model = None

def get_embedding_model():
    global _model
    if _model is None:
        logger.info("Loading embedding model BAAI/bge-small-en-v1.5")
        _model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    return _model

def generate_embedding(text: str) -> list[float]:
    model = get_embedding_model()
    return model.encode(text, normalize_embeddings=True).tolist()

def chunk_transcript(transcript: str) -> list[dict]:
    """
    Split plain text transcript into chunks.
    Used when no timing info is available (Whisper fallback).
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    texts = splitter.split_text(transcript)
    return [{"chunk_id": i, "text": text} for i, text in enumerate(texts)]

def chunk_timed_transcript(segments: list[dict]) -> list[dict]:
    """
    Chunk transcript segments that have 'start', 'duration', 'text'.
    Preserve start and end times for each chunk.
    Returns list of dicts with chunk_id, text, start_time, end_time.
    """
    chunks = []
    current_text = []
    current_start = None
    current_end = None
    char_count = 0

    for seg in segments:
        text = seg["text"]
        start = seg["start"]
        end = start + seg.get("duration", 0)

        if current_start is None:
            current_start = start

        current_text.append(text)
        char_count += len(text)
        current_end = end

        if char_count >= CHUNK_SIZE:
            chunk_text = " ".join(current_text)
            chunks.append({
                "text": chunk_text,
                "start_time": current_start,
                "end_time": current_end,
            })
            # Start new chunk with overlap logic (simple: keep last 100 chars)
            overlap_text = chunk_text[-CHUNK_OVERLAP:]
            current_text = [overlap_text] if overlap_text else []
            current_start = None
            current_end = None
            char_count = len(overlap_text)

    # Last chunk
    if current_text:
        chunk_text = " ".join(current_text)
        chunks.append({
            "text": chunk_text,
            "start_time": current_start,
            "end_time": current_end,
        })

    # Assign chunk IDs after creation
    for i, chunk in enumerate(chunks):
        chunk["chunk_id"] = i
    return chunks